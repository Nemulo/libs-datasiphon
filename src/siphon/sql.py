from .base import QueryBuilder, FilterFormatError, FilterColumnError, InvalidOperatorError, InvalidValueError, InvalidRestrictionModel
import sqlalchemy as sa
import typing as t
from pydantic import BaseModel, model_validator, ValidationError
import re


class SqlColumnFilter(BaseModel):
    eq: t.Any = None
    ne: t.Any = None
    gt: t.Any = None
    ge: t.Any = None
    lt: t.Any = None
    le: t.Any = None
    in_: t.Any = None
    nin: t.Any = None

    def validate_against_query(self, column: sa.Column):
        """
        Validate the filter against the query

        :param query: The query to validate against

        :raises FilterColumnError: If the filter has invalid columns
        """
        # 1. validate for every operation correct type -> every operation except in_ and nin
        # has to be the same type as column (in_ and nin can be list of given type)
        for operation in self.model_fields_set:
            if operation in ['in_', 'nin']:
                if not all([isinstance(value, column.type.python_type) for value in getattr(self, operation)]):
                    raise InvalidValueError(
                        f"Invalid value: {getattr(self, operation)}")
            else:
                if not isinstance(getattr(self, operation), column.type.python_type):
                    raise InvalidValueError(
                        f"Invalid value: {getattr(self, operation)}")

    @model_validator(mode='after')
    def check_values(self):
        if self.model_fields_set == set():
            raise ValueError("At least one operation must be set")


class RestrictedFilter(SqlColumnFilter):
    def __init__(self, allowed_operations: t.List[str] = None, **kwargs):
        super().__init__(**kwargs)
        if allowed_operations is not None:
            if not self.model_fields_set.issubset(set(allowed_operations)):
                raise InvalidOperatorError(
                    f"Invalid operations: {self.model_fields_set - set(allowed_operations)} are restricted for this filter")


class SqlOrderFilter(BaseModel):
    direction: str = None
    column: str = None

    @model_validator(mode='after')
    def check_values(self):
        if self.direction is None or self.column is None:
            raise ValueError("Both direction and column must be set")

    @classmethod
    def parse(cls, data: str | list[str]) -> list['SqlOrderFilter']:
        """
        Parse the order_by string

        :param data: The string to parse

        :raises InvalidValueError: If the string is invalid

        :return: The parsed string
        """
        direction_options = {
            'asc': 'asc',
            'desc': 'desc',
            '+': 'asc',
            '-': 'desc'
        }
        if not isinstance(data, (str, list)):
            raise FilterFormatError(
                f"Invalid value for order_by: {data} - expected string, one of (asc|desc)(<column>), (+|-)(<column>), (<column>).(asc|desc)")
        if isinstance(data, str):
            data = [data]
        parsed_data = []
        for item in data:
            if match := re.match(r'(asc|desc)\((.+)\)', item):
                parsed_data.append(cls(direction=match.group(1), column=match.group(2)))
            elif match := re.match(r'(\+|-)(.+)', item):
                parsed_data.append(cls(direction=direction_options[match.group(1)], column=match.group(2)))
            elif match := re.match(r'(.+)\.(asc|desc)', item):
                parsed_data.append(cls(direction=direction_options[match.group(2)], column=match.group(1)))
            else:
                raise InvalidValueError(
                    f"Invalid value for order_by: {item} - expected one of (asc|desc)(<column>), (+|-)(<column>), (<column>).(asc|desc)")
        return parsed_data

    def validate_against_query(self, query: sa.Select):
        """
        Validate the filter against the query

        :param query: The query to validate against

        :raises FilterColumnError: If the filter has invalid columns
        """
        if self.column not in query.exported_columns:
            raise FilterColumnError(
                f"Invalid column: {self.column} not found in select statement")


class KeywordFilter(BaseModel):
    order_by: list = None
    limit: int = None
    offset: int = None


class SQL(QueryBuilder):
    """
    SQL query builder
    """
    KW = {
        'order_by': SqlOrderFilter.parse,
        'limit': int,
        'offset': int
    }

    @staticmethod
    def validate_filter_model_structure(
            input_filter: dict, filter_model: BaseModel, ignore_extra: bool = False) -> dict:
        """
        Validate the format of the model

        :param model: The model to validate
        :param filter_model: The model to validate against (allowed fields for filter)
        :param ignore_extra: Whether to ignore extra fields instead of raising an error

        :raises FilterFormatError: If the model has an invalid format
        :raises InvalidOperatorError: If the model has an invalid operator

        :returns validated filter
        """
        validated_filter = {}
        keyword_validation = {
            'order_by': (list, lambda x: set([item.column for item in SqlOrderFilter.parse(x[0])]).issubset(x[1])),
            'limit': (bool, lambda x: x[1]),
            'offset': (bool, lambda x: x[1])
        }
        for col_name, filter_body in input_filter.items():
            if col_name not in filter_model.model_fields.keys():
                if ignore_extra:
                    continue
                raise FilterFormatError(
                    f'Column {col_name} is not allowed in filter model')
            if col_name in keyword_validation:
                # just for validation of body
                # verify that keyword is in filter model as attribute and its type is correct
                if not isinstance(getattr(filter_model, col_name), keyword_validation[col_name][0]):
                    raise InvalidRestrictionModel(
                        f'Expected format for filter model item is {keyword_validation[col_name][0]}, allowed operations such as <colum_name>: {keyword_validation[col_name][0]} = [<allowed_operations>], or None'
                    )
                # verify that models' body evaluation function (based on dictionary above) returns True
                # create pair of provided body and provided restriction
                eval_pair = (filter_body, getattr(filter_model, col_name))
                column_evaluation = keyword_validation[col_name][1](eval_pair)
                if not column_evaluation:
                    raise FilterFormatError(
                        f'Invalid value for keyword: {col_name} -> restriction: {eval_pair[1]} not met')
                validated_filter[col_name] = filter_body
                continue

            model_body = getattr(filter_model, col_name)
            if not isinstance(model_body, (list, type(None))):
                raise InvalidRestrictionModel(
                    f'Expected format for filter model item is list, allowed operations such as <colum_name>: list = [<allowed_operations>], or None'
                )
            if model_body is not None:
                if not set(model_body).issubset(set(SQL.OPS)):
                    raise InvalidOperatorError(
                        f'Invalid operator in filter model: {set(model_body) - set(SQL.OPS)}')
            validated_filter[col_name] = filter_body
        return validated_filter

    @staticmethod
    def validate_filter_structure(filter_input: dict, strict: bool = True) -> dict:
        """
        Validate the format of the model

        :param model: The model to validate
        :param filter_model: The model to validate against (allowed fields for filter)

        :raises FilterFormatError: If the model has an invalid format
        :raises InvalidOperatorError: If the model has an invalid operator
        """
        validated_items = {}
        for col_name, filter_body in filter_input.items():
            try:
                if col_name in SQL.KW:
                    _ = SQL.KW[col_name](filter_body)
                else:
                    _ = SqlColumnFilter(**filter_body)
                validated_items[col_name] = filter_body
            except (ValidationError, TypeError):
                if not strict:
                    continue
                raise FilterFormatError(
                    f"Invalid value for keyword: {col_name}")
        return validated_items

    @staticmethod
    def validate_filter_columns(
        filter_columns: dict,
        query: sa.Select,
        filter_model: BaseModel = None,
        ignore_extra: bool = False
    ) -> tuple[dict[str, RestrictedFilter], KeywordFilter]:
        """
        Validate the columns of the model against the columns of the statement

        :param model: The model to validate
        :param stm: The statement to validate against

        :raises FilterColumnError: If the model has invalid columns
        """
        # 1. divide into filter columns and keyword columns
        # 2. if base model is provided
        # 2.1 compare base model to provided columns - if possible in separate function
        # 2.2 validate provided filter to base model
        # 3. validate filter against query
        parsed_filter = {}
        parsed_keywords = {}
        if filter_model is not None:
            processed_filter = SQL.validate_filter_model_structure(
                filter_columns, filter_model, ignore_extra=ignore_extra)
            SQL.validate_filter_model_columns(filter_model, query)
            for filter_key, filter_body in processed_filter.items():
                if filter_key in SQL.KW:
                    keyword_item = SQL.KW[filter_key](filter_body)
                    if isinstance(keyword_item, SqlOrderFilter):
                        keyword_item.validate_against_query(query)
                        # verify that all `order_by` columns are in allowed
                    parsed_keywords[filter_key] = keyword_item
                else:
                    filter_item = RestrictedFilter(
                        allowed_operations=getattr(filter_model, filter_key), **filter_body)
                    filter_item.validate_against_query(
                        query.exported_columns[filter_key])
                    parsed_filter[filter_key] = filter_item
        else:
            for filter_key, filter_body in filter_columns.items():
                if filter_key in SQL.KW:
                    keyword_item = SQL.KW[filter_key](filter_body)
                    if isinstance(
                            keyword_item, list) and all(
                            [isinstance(item, SqlOrderFilter) for item in keyword_item]):
                        _ = [item.validate_against_query(query) for item in keyword_item]
                    parsed_keywords[filter_key] = keyword_item
                else:
                    filter_item = SqlColumnFilter(**filter_body)
                    if query.exported_columns.get(filter_key) is None:
                        raise FilterColumnError(
                            f"Column couldn't be found in select query: {filter_key}"
                        )
                    filter_item.validate_against_query(
                        query.exported_columns[filter_key])
                    parsed_filter[filter_key] = filter_item
        keyword_data = KeywordFilter(**parsed_keywords)
        return parsed_filter, keyword_data

    @staticmethod
    def validate_filter_model_columns(
        filter_model: BaseModel,
        query: sa.Select
    ) -> None:
        """
        Validate the columns of the model against the columns of the statement

        :param model: The model to validate
        :param stm: The statement to validate against

        :raises FilterColumnError: If the model has invalid columns
        """
        # dump data to dictionary
        data = filter_model.model_dump()
        kw_arguments = {}
        for kw in SQL.KW:
            if kw in data:
                kw_arguments[kw] = data.pop(kw)
        # validate columns - every `order_by` column has to be in `select` statement
        if 'order_by' in kw_arguments:
            if not set(kw_arguments['order_by']).issubset(set(query.selected_columns.keys())):
                raise InvalidRestrictionModel(
                    f"Invalid column: {set(kw_arguments['order_by']) - set(query.selected_columns.keys())} not found in select statement")
        # validate columns - every column has to be in `select` statement
        if not set(data).issubset(set(query.selected_columns.keys())):
            raise InvalidRestrictionModel(
                f"Invalid column: {set(data) - set(query.selected_columns.keys())} not found in select statement")

    @classmethod
    def build(
            cls, query: sa.Select, qs_filter: dict, filter_model: BaseModel = None, ignore_extra_fields: bool = False,
            strict: bool = True) -> sa.Select:
        """
        Build a SQL query from a model

        :param query: The statement to build from
        :param qs_filter: The model to build from
        :param filter_model: The model to validate against (allowed fields for filter)
        :param ignore_extra_fields: Whether to ignore extra fields in filter compared to filter model
        :param strict: Whether to raise an error if the filter has invalid items or ignore them

        :raises TypeError: If the statement is not a Select statement
        :raises FilterFormatError: If the model has an invalid format
        :raises FilterColumnError: If the model has invalid columns
        :raises InvalidOperatorError: If the model has an invalid operator
        :raises InvalidValueError: If the model has an invalid value

        :return: The built statement
        """
        if not isinstance(query, sa.Select):
            raise TypeError(f"Invalid type: {type(query)}")

        validated_filter = cls.validate_filter_structure(qs_filter, strict=strict)
        filtered_columns, keyword_attributes = cls.validate_filter_columns(
            validated_filter, query, filter_model=filter_model, ignore_extra=ignore_extra_fields)
        for column_name, filters_ in filtered_columns.items():
            for operation in filters_.model_fields_set:
                query = query.where(cls._op(operation)(
                    query.exported_columns[column_name], getattr(filters_, operation)))
        for keyword in keyword_attributes.model_fields_set:
            if value := getattr(keyword_attributes, keyword):
                query = cls._kw(keyword, query, value)
        return query

    @staticmethod
    def eq(column: sa.Column, value: t.Any) -> sa.ColumnElement:
        return column == value

    @staticmethod
    def ne(column: sa.Column, value: t.Any) -> sa.ColumnElement:
        return column != value

    @staticmethod
    def gt(column: sa.Column, value: t.Any) -> sa.ColumnElement:
        return column > value

    @staticmethod
    def ge(column: sa.Column, value: t.Any) -> sa.ColumnElement:
        return column >= value

    @staticmethod
    def lt(column: sa.Column, value: t.Any) -> sa.ColumnElement:
        return column < value

    @staticmethod
    def le(column: sa.Column, value: t.Any) -> sa.ColumnElement:
        return column <= value

    @staticmethod
    def in_(column: sa.Column, value: t.Any) -> sa.ColumnElement:
        if not isinstance(value, (list, tuple)):
            value = [value]
        return column.in_(value)

    @staticmethod
    def nin(column: sa.Column, value: t.Any) -> sa.ColumnElement:
        if not isinstance(value, (list, tuple)):
            value = [value]
        return ~column.in_(value)

    @classmethod
    def _kw(cls, kw: str, stm: sa.Select, value: t.Any) -> sa.Select:
        return getattr(cls, kw)(stm, value)

    @staticmethod
    def order_by(stm: sa.Select, values: list[SqlOrderFilter]) -> sa.Select:
        """
        Apply an order_by to a statement

        :param stm: The statement to apply to
        :param value: The order_by to apply

        :raises InvalidOperatorError: If the order_by has an invalid operator

        :return: The statement with the order_by applied
        """
        ordering = {
            'asc': sa.asc,
            'desc': sa.desc
        }
        for order_instance in values:
            stm = stm.order_by(ordering[order_instance.direction](stm.exported_columns[order_instance.column]))
        return stm

    @staticmethod
    def limit(stm: sa.Select, value: int) -> sa.Select:
        """
        Limit a statement

        :param stm: The statement to limit
        :param value: The limit to apply

        :raises InvalidValueError: If the limit is not an integer

        :return: The statement with the limit applied
        """
        if not isinstance(value, int):
            raise InvalidValueError(f"Invalid limit: {value}")
        return stm.limit(value)

    @staticmethod
    def offset(stm: sa.Select, value: int) -> sa.Select:
        """
        Offset a statement

        :param stm: The statement to offset
        :param value: The offset to apply

        :raises InvalidValueError: If the offset is not an integer

        :return: The statement with the offset applied
        """
        if not isinstance(value, int):
            raise InvalidValueError(f"Invalid offset: {value}")
        return stm.offset(value)
