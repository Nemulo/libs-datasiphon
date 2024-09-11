class SiphonError(Exception):
    """
    Base exception for all Siphon exceptions.
    """

    pass


class InvalidValueTypeError(SiphonError):
    """
    Exception raised when an invalid value type is provided.
    """

    pass


class NoSuchOperationError(SiphonError):
    """
    Exception raised when an invalid operation is provided.
    """

    pass


class InvalidFilteringStructureError(SiphonError):
    """
    Exception raised when an invalid filtering structure is provided.
    """

    pass


class ColumnError(SiphonError):
    """
    Base exception for all column-related exceptions.
    """

    pass


class BadFormatError(SiphonError):
    """
    Exception raised when an invalid format is provided.
    """

    pass


class FiltrationNotAllowed(SiphonError):
    """
    Exception raised when an invalid filtration is provided.
    """

    pass


class CannotAdjustExpression(SiphonError):
    """
    Exception raised when an adjustment of an expression is not possible.
    """

    pass
