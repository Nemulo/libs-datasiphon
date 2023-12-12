import typing as t


class QueryBuilder:
    OPS = ['eq', 'ne', 'gt', 'ge', 'lt', 'le', 'in_', 'nin']
    KW = ['order_by', 'limit', 'offset']

    @staticmethod
    def eq(column: t.Any, value: t.Any) -> t.Any:
        pass

    @staticmethod
    def ne(column: t.Any, value: t.Any) -> t.Any:
        pass

    @staticmethod
    def gt(column: t.Any, value: t.Any) -> t.Any:
        pass

    @staticmethod
    def ge(column: t.Any, value: t.Any) -> t.Any:
        pass

    @staticmethod
    def lt(column: t.Any, value: t.Any) -> t.Any:
        pass

    @staticmethod
    def le(column: t.Any, value: t.Any) -> t.Any:
        pass

    @staticmethod
    def in_(column: t.Any, value: t.Any) -> t.Any:
        pass

    @staticmethod
    def nin(column: t.Any, value: t.Any) -> t.Any:
        pass

    @classmethod
    def _op(cls, op):
        return getattr(cls, op)
    


class FilterFormatError(Exception):
    pass


class FilterColumnError(Exception):
    pass


class InvalidOperatorError(Exception):
    pass


class InvalidValueError(Exception):
    pass
