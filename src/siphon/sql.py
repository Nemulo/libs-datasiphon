from .base import (
    QueryBuilder,
    FilterFormatError,
    FilterColumnError,
    InvalidOperatorError,
    InvalidValueError,
    InvalidRestrictionModel,
    SiphonError,
)
import sqlalchemy as sa
import typing as t
from pydantic import BaseModel, model_validator, ValidationError
from pydantic.fields import FieldInfo
import re
from copy import copy
from sqlalchemy.sql.base import ReadOnlyColumnCollection
import datetime as dt


class SqlOrderFilter(BaseModel):
    direction: str = None
    column: str = None

    @model_validator(mode="after")
    def check_values(self):
        if self.direction is None or self.column is None:
            # Can happen only if created manually
            raise ValueError("Both direction and column must be set")

    @classmethod
    def parse(cls, data: str | list[str]) -> list["SqlOrderFilter"]:
        """
        Parse the order_by string

        :param data: The string to parse

        :raises InvalidValueError: If the string is invalid

        :return: The parsed string
        """
        direction_options = {"asc": "asc", "desc": "desc", "+": "asc", "-": "desc"}
        # Can happen only if created manually - user error
        if not isinstance(data, (str, list)):
            raise FilterFormatError(
                f"Invalid value for order_by: {data} - expected string, one of (asc|desc)(<column>), (+|-)(<column>), (<column>).(asc|desc)"
            )
        if isinstance(data, str):
            data = [data]
        parsed_data = []
        for item in data:
            if match := re.match(r"(asc|desc)\((.+)\)", item):
                parsed_data.append(cls(direction=match.group(1), column=match.group(2)))
            elif match := re.match(r"(\+|-)(.+)", item):
                parsed_data.append(cls(direction=direction_options[match.group(1)], column=match.group(2)))
            elif match := re.match(r"(.+)\.(asc|desc)", item):
                parsed_data.append(cls(direction=direction_options[match.group(2)], column=match.group(1)))
            else:
                raise InvalidValueError(
                    f"Invalid value for order_by: {item} - expected one of (asc|desc)(<column>), (+|-)(<column>), (<column>).(asc|desc)"
                )
        return parsed_data


class KeywordFilter(BaseModel):
    order_by: list = None
    limit: int = None
    offset: int = None

    def apply_on_query(self, query: sa.Select) -> sa.Select:
        """
        Apply the keyword filter on the query

        :param query: The query to apply on

        :return: The query with the keyword filter applied
        """
        for field in self.model_fields_set:
            # target only set fields
            query = SQL._kw(field, query, getattr(self, field))
        return query


class RestrictionModel(BaseModel):
    """
    Base Class for creating restriction models for siphon

    While it doesn't define any fields, it add some methods to provide
    intended behavior for restriction models
    """

    @property
    def sql_fields(self) -> dict[str, FieldInfo]:
        """
        Get the sql column fields of the model

        :return: The fields of the model
        """
        all_fields = self.model_fields.copy()
        # remove all keyword fields from `all_fields`
        for kw in SQL.__sql_kwargs__:  # type: ignore
            _ = all_fields.pop(kw, None)
        return all_fields

    @property
    def sql_keywords(self) -> dict[str, FieldInfo]:
        """
        Get the sql keyword fields of the model

        :return: The fields of the model
        """
        sql_fields = self.sql_fields
        all_fields = self.model_fields.copy()
        # remove all sql fields from `all_fields`
        for field in sql_fields:
            _ = all_fields.pop(field, None)
        return all_fields

    @property
    def filter_order_by(self) -> list[str] | None:
        return getattr(self, "order_by", [])

    @property
    def filter_limit(self) -> bool:
        return getattr(self, "limit", False)

    @property
    def filter_offset(self) -> bool:
        return getattr(self, "offset", False)

    @model_validator(mode="after")
    def check_values(self):
        """
        Check the values of the model

        :raises ValueError: If the model has invalid values
        """
        for field_info in self.sql_fields.values():
            # this validation is strictly for user error - if it happens, it's user error
            if field_info.annotation != list[str]:
                raise ValueError(
                    f"Invalid type: {field_info.annotation} for {field_info}, required: list of operators (list[str])"
                )
        for keyword_field, field_info in self.sql_keywords.items():
            if field_info.annotation != SQL.__sql_kwargs__[keyword_field]:
                raise ValueError(
                    f"Invalid type: {field_info.annotation} for {field_info}, required: {SQL.__sql_kwargs__[keyword_field]}"
                )


class FilterTypeParser:
    """
    Class for parsing filter types
    """

    @staticmethod
    def parse_type(type_: t.Type) -> t.Callable:
        """
        Parse the type string

        :param type_str: The string to parse

        :raises ValueError: If the string is invalid

        :return: The parsed string
        """
        if type_ in [int, float, str, bool]:
            return type_
        elif type_ == dt.datetime:
            return dt.datetime.fromisoformat
        else:
            raise ValueError(f"Unparsable type: {type_}")


class FilterBuilder:
    junctionMapping = {"and": sa.and_, "or": sa.or_}

    """
    Class for processing incoming filter (parsed by qstion package), no initial fields,
    but storing all incoming fields in extra field
    """

    @staticmethod
    def construct_clause(data: dict, query_columns: ReadOnlyColumnCollection) -> list[sa.ColumnElement]:
        current_clause = []
        for key, value in data.items():
            match key:
                case str() as keyword if keyword in SQL.__sql_kwargs__:
                    # not processing keywords in clause
                    continue
                case str() as junction if junction in ["and", "or"]:
                    clause_result = FilterBuilder.construct_clause(value, query_columns)
                    if len(clause_result) == 1:
                        current_clause.append(clause_result[0])
                    else:
                        current_clause.append(FilterBuilder.junctionMapping[junction](*clause_result))
                case str() as column_name:
                    column = query_columns[column_name]
                    clause_result = FilterBuilder.construct_column_clause(column, value)
                    current_clause.extend(clause_result)
        return current_clause

    @staticmethod
    def construct_column_clause(column: sa.Column, data: dict) -> sa.ColumnElement:
        current_clause = []
        for key, value in data.items():
            match key:
                case str() as op if op in SQL.OPS:
                    current_clause.append(SQL._op(op)(column, value))
                case str() as junction if junction in ["and", "or"]:
                    clause_result = FilterBuilder.construct_column_clause(column, value)
                    if len(clause_result) == 1:
                        current_clause.append(clause_result[0])
                    else:
                        current_clause.append(FilterBuilder.junctionMapping[junction](*clause_result))
        return current_clause

    @staticmethod
    def extract_keywords(data: dict) -> KeywordFilter:
        exported_data = {}
        for item in data:
            match item:
                case "order_by":
                    exported_data[item] = SqlOrderFilter.parse(data[item])
                case "limit":
                    exported_data[item] = data[item]
                case "offset":
                    exported_data[item] = data[item]
        return KeywordFilter(**exported_data)

    @staticmethod
    def check_values(data: dict, query_columns: ReadOnlyColumnCollection, /, filter_model: RestrictionModel):
        """
        Check the values of the model verifying that all fields are valid

        :param data: The data to check

        :raises ValueError: If the model has invalid values

        """
        junction_included = False
        for filter_key, filter_body in data.items():
            match filter_key:
                case str() as limit_or_offset if limit_or_offset in ["limit", "offset"]:
                    if not isinstance(filter_body, int):
                        raise FilterFormatError(
                            f"Invalid value: {filter_body} - expected integer for {limit_or_offset}"
                        )
                    if filter_model is not None:
                        if not getattr(filter_model, filter_key, False):
                            raise FilterColumnError(f"Usage of keyword disabled by restriction model: {filter_key}")
                case "order_by":
                    if not isinstance(filter_body, (list, str)):
                        raise FilterFormatError(
                            f"Invalid value: {filter_body} - expected list of strings or string for order_by"
                        )
                    parsed_order_by = SqlOrderFilter.parse(filter_body)
                    for order_instance in parsed_order_by:
                        if filter_model is not None:
                            if order_instance.column not in filter_model.filter_order_by:
                                raise FilterColumnError(
                                    f"Column filtering disabled by restriction model: {order_instance.column}"
                                )
                case str() as junction if junction in ["and", "or"]:
                    if junction_included:
                        raise FilterFormatError(f"Invalid filter: {filter_key} - expected only one of (and, or)")
                    junction_included = True
                    # do not pass key because it's not column name
                    FilterBuilder.check_nested(filter_body, query_columns, filter_model)
                case str() as column_name:
                    if filter_key not in query_columns:
                        raise FilterColumnError(f"Invalid column name: {filter_key} - column_name not in query columns")
                    if filter_model is not None:
                        if filter_key not in filter_model.sql_fields:
                            raise FilterColumnError(f"Column filtering disabled by restriction model: {filter_key}")
                    FilterBuilder.check_nested(filter_body, query_columns, filter_model, column_name)
                case _:
                    # nothing else is allowed
                    raise ValueError(
                        f"Invalid keyword: {filter_key} - expected one of (limit, offset, order_by, and, or) or column name"
                    )

    @staticmethod
    def check_nested(
        data: dict, query_columns: ReadOnlyColumnCollection, /, filter_model: RestrictionModel, current_key: str = None
    ) -> None:
        """
        Check the values of the model verifying that all fields are valid

        :param data: The data to check

        :raises ValueError: If the model has invalid values
        """
        junction_included = False
        if not isinstance(data, dict):
            raise FilterFormatError(f"Invalid filter: {data} - expected dictionary")
        for key, value in data.items():
            match key:
                case str() as junction if junction in ["and", "or"]:
                    if junction_included:
                        raise FilterFormatError(f"Invalid filter: {key} - expected only one of (and, or)")
                    junction_included = True
                    FilterBuilder.check_nested(value, query_columns, filter_model, current_key)
                case str() as op if op in SQL.OPS:
                    if current_key is None:
                        raise FilterFormatError(
                            f"Don't have column name to apply operation: {op} - expected column name"
                        )
                    if filter_model is not None:
                        if getattr(filter_model, current_key) != [] and op not in getattr(filter_model, current_key):
                            raise InvalidOperatorError(
                                f"Invalid operator: {op} - not allowed for column: {current_key}, allowed: {getattr(filter_model, current_key)}"
                            )
                    if op in ["in_", "nin"]:
                        if not isinstance(value, (list, tuple)):
                            raise InvalidValueError(f"Invalid value: {value} - expected list or tuple for {op}")
                        # instead of checking if each value has correct type, we will use constructor to do it and catch any type errors with InvalidValueError
                        try:
                            _ = [query_columns[current_key].type.python_type(item) for item in value]
                        except TypeError:
                            raise InvalidValueError(
                                f"Invalid value type for {current_key}: {value} - expected {query_columns[current_key].type.python_type}"
                            )
                    else:
                        try:
                            parse_func = FilterTypeParser.parse_type(query_columns[current_key].type.python_type)
                            _ = parse_func(value)
                        except (TypeError, ValueError):
                            raise InvalidValueError(
                                f"Cannot construct {current_key}'s {value=} - expected {query_columns[current_key].type.python_type}"
                            )
                case str() as column_name:
                    if current_key is not None:
                        raise FilterFormatError(
                            f"Invalid filter: {data} - expected one of (and, or) or operator for column: {current_key}, got: {column_name}"
                        )
                    else:  # VSCode - Insiders bug showing this as dead code
                        FilterBuilder.check_nested(value, query_columns, filter_model, column_name)


class SQL(QueryBuilder):
    """
    SQL query builder
    """

    __sql_kwargs__ = {"order_by": list[str], "limit": bool, "offset": bool}

    @staticmethod
    def dump_query_columns(query: sa.Select) -> ReadOnlyColumnCollection:
        """
        Dump all selected columns to dictionary

        :param query: The query to dump

        :return: The dumped columns
        """
        return copy(query.exported_columns)

    @staticmethod
    def validate_filter_model(filter_model: RestrictionModel, column_collection: ReadOnlyColumnCollection) -> None:
        """
        Validate the filter model against the columns of the statement

        :param filter_model: The model to validate
        :param column_collection: The columns to validate against

        :raises FilterColumnError: If the model has invalid columns
        """
        # Only for user error - if it happens, it's user error
        if not (isinstance(filter_model, RestrictionModel)):
            raise InvalidRestrictionModel(f"Invalid type: {type(filter_model)}, required: `RestrictionModel`")
        if not set(filter_model.sql_fields.keys()).issubset(set(column_collection.keys())):
            raise InvalidRestrictionModel(
                f"Invalid column: {set(filter_model.sql_fields.keys()) - set(column_collection.keys())} not found in select statement"
            )
        for field_name in filter_model.sql_fields:
            # Only for user error - if it happens, it's user error
            if not isinstance(getattr(filter_model, field_name), list):
                raise InvalidRestrictionModel(
                    f"Invalid type: {type(getattr(filter_model, field_name))}, required: list"
                )
            if not set(getattr(filter_model, field_name)).issubset(set(SQL.OPS)):
                raise InvalidOperatorError(
                    f"Invalid operator in filter model: {set(getattr(filter_model, field_name)) - set(SQL.OPS)}"
                )
        # verify that all order_by columns (if present) ar in query columns
        if filter_model.filter_order_by:
            if not set(filter_model.filter_order_by).issubset(set(column_collection.keys())):
                raise InvalidRestrictionModel(
                    f"Invalid column: {set(filter_model.filter_order_by) - set(column_collection.keys())} not found in select statement"
                )

    @classmethod
    def build(cls, query: sa.Select, qs_filter: dict, filter_model: RestrictionModel = None) -> sa.Select:
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
            raise SiphonError(f"Invalid query type: {type(query)}, required: `Select` statement")
        column_collection = cls.dump_query_columns(query)
        if filter_model is not None:
            cls.validate_filter_model(filter_model, column_collection)
        FilterBuilder.check_values(qs_filter, column_collection, filter_model)
        filter_data = FilterBuilder.construct_clause(qs_filter, column_collection)
        query = query.where(*filter_data)
        keyword_data = FilterBuilder.extract_keywords(qs_filter)
        query = keyword_data.apply_on_query(query)
        return query

    @staticmethod
    def eq(column: sa.Column, value: t.Any) -> sa.ColumnElement:
        process_type_func = FilterTypeParser.parse_type(column.type.python_type)
        return column == process_type_func(value)

    @staticmethod
    def ne(column: sa.Column, value: t.Any) -> sa.ColumnElement:
        process_type_func = FilterTypeParser.parse_type(column.type.python_type)
        return column != process_type_func(value)

    @staticmethod
    def gt(column: sa.Column, value: t.Any) -> sa.ColumnElement:
        process_type_func = FilterTypeParser.parse_type(column.type.python_type)
        return column > process_type_func(value)

    @staticmethod
    def ge(column: sa.Column, value: t.Any) -> sa.ColumnElement:
        process_type_func = FilterTypeParser.parse_type(column.type.python_type)
        return column >= process_type_func(value)

    @staticmethod
    def lt(column: sa.Column, value: t.Any) -> sa.ColumnElement:
        process_type_func = FilterTypeParser.parse_type(column.type.python_type)
        return column < process_type_func(value)

    @staticmethod
    def le(column: sa.Column, value: t.Any) -> sa.ColumnElement:
        process_type_func = FilterTypeParser.parse_type(column.type.python_type)
        return column <= process_type_func(value)

    @staticmethod
    def in_(column: sa.Column, value: t.Any) -> sa.ColumnElement:
        process_type_func = FilterTypeParser.parse_type(column.type.python_type)
        # last chance to sanitize the value
        if not isinstance(value, (list, tuple)):
            value = [process_type_func(value)]
        else:
            value = [column.type.python_type(item) for item in value]
        return column.in_(value)

    @staticmethod
    def nin(column: sa.Column, value: t.Any) -> sa.ColumnElement:
        process_type_func = FilterTypeParser.parse_type(column.type.python_type)
        # last chance to sanitize the value
        if not isinstance(value, (list, tuple)):
            value = [process_type_func(value)]
        else:
            value = [column.type.python_type(item) for item in value]
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
        ordering = {"asc": sa.asc, "desc": sa.desc}
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
        # Safety measure - should not happen
        if not isinstance(value, int):
            raise InvalidValueError(f"Invalid offset: {value}")
        return stm.offset(value)
