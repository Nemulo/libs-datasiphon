import typing as t


class QueryBuilder:
    OPS = ['eq', 'ne', 'gt', 'ge', 'lt', 'le', 'in_', 'nin']

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


class SiphonError(Exception):
    pass


class FilterFormatError(SiphonError):
    pass


class FilterColumnError(SiphonError):
    pass


class InvalidOperatorError(SiphonError):
    pass


class InvalidValueError(SiphonError):
    pass

class InvalidRestrictionModel(SiphonError):
    pass