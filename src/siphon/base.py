import typing as t


class QueryBuilder:
    OPS = ["eq", "ne", "gt", "ge", "lt", "le", "in_", "nin"]


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
