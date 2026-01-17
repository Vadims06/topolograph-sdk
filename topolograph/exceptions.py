"""Custom exceptions for the Topolograph SDK."""


class TopolographError(Exception):
    """Base exception for all Topolograph SDK errors."""
    pass


class AuthenticationError(TopolographError):
    """Raised when authentication fails."""
    pass


class APIError(TopolographError):
    """Raised when an API request fails."""
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class NotFoundError(APIError):
    """Raised when a resource is not found (404)."""
    pass


class ValidationError(APIError):
    """Raised when request validation fails (400/405)."""
    pass
