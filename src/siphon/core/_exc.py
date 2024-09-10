class SihponError(Exception):
    """
    Base exception for all Siphon exceptions.
    """

    pass


class InvalidValueTypeError(SihponError):
    """
    Exception raised when an invalid value type is provided.
    """

    pass


class NoSuchOperationError(SihponError):
    """
    Exception raised when an invalid operation is provided.
    """

    pass


class InvalidFilteringStructureError(SihponError):
    """
    Exception raised when an invalid filtering structure is provided.
    """

    pass


class ColumnError(SihponError):
    """
    Base exception for all column-related exceptions.
    """

    pass


class BadFormatError(SihponError):
    """
    Exception raised when an invalid format is provided.
    """

    pass


class FiltrationNotAllowed(SihponError):
    """
    Exception raised when an invalid filtration is provided.
    """

    pass


class CannotAdjustExpression(SihponError):
    """
    Exception raised when an adjustment of an expression is not possible.
    """

    pass
