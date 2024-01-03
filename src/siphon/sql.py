from .base import QueryBuilder, FilterFormatError, FilterColumnError, InvalidOperatorError, InvalidValueError
import sqlalchemy as sa
import typing as t


class SQL(QueryBuilder):
    """
    SQL query builder
    """

    @staticmethod
    def validate_fmt(model: dict):
        """
        Validate the format of the model

        :param model: The model to validate

        :raises FilterFormatError: If the model has an invalid format
        :raises InvalidOperatorError: If the model has an invalid operator
        """
        for key, value in model.items():
            if key in SQL.KW:
                if key == 'order_by' and not isinstance(value, dict):
                    raise FilterFormatError(
                        f"Invalid format: {key} -> {value}")
                continue
            if not isinstance(value, dict):
                raise FilterFormatError(f"Invalid format: {key} -> {value}")
            for op, value in value.items():
                if op not in SQL.OPS:
                    raise InvalidOperatorError(f"Invalid operator: {op}")

    @staticmethod
    def validate_cols(model: dict, stm: sa.Select):
        """
        Validate the columns of the model against the columns of the statement

        :param model: The model to validate
        :param stm: The statement to validate against

        :raises FilterColumnError: If the model has invalid columns
        """
        stm_cols = set(stm.selected_columns.keys())
        model_cols = set(model.keys()) - set(SQL.KW)
        if not model_cols.issubset(stm_cols):
            raise FilterColumnError(
                f"Invalid columns: {model_cols - stm_cols}")

    @classmethod
    def build(cls, stm: sa.Select, model: dict) -> sa.Select:
        """
        Build a SQL query from a model

        :param stm: The statement to build from
        :param model: The model to build from

        :raises TypeError: If the statement is not a Select statement
        :raises FilterFormatError: If the model has an invalid format
        :raises FilterColumnError: If the model has invalid columns
        :raises InvalidOperatorError: If the model has an invalid operator
        :raises InvalidValueError: If the model has an invalid value

        :return: The built statement
        """
        if not isinstance(stm, sa.Select):
            raise TypeError(f"Invalid type: {type(stm)}")
        cls.validate_fmt(model)
        cls.validate_cols(model, stm)
        for col, filters_ in model.items():
            if col in cls.KW:
                stm = cls._kw(col, stm, filters_)
            else:
                for op, value in filters_.items():
                    stm = stm.where(cls._op(op)(
                        stm.exported_columns[col], value))
        return stm

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
    def order_by(stm: sa.Select, value: dict) -> sa.Select:
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
        try:
            for direction, col in value.items():
                stm = stm.order_by(ordering[direction](
                    stm.exported_columns[col]))
        except KeyError:
            raise InvalidOperatorError(f"Invalid order_by: {value}")
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
