"""Custom exceptions for the Logarithmic application."""


class LogarithmicException(Exception):
    """Base exception for all Logarithmic errors."""

    pass


class FileAccessError(LogarithmicException):
    """Raised when a file cannot be accessed or read."""

    pass


class InvalidPathError(LogarithmicException):
    """Raised when a provided file path is invalid."""

    pass
