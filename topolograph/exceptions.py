"""Custom exceptions for the Topolograph SDK."""


class TopolographError(Exception):
    """Base exception for all Topolograph SDK errors."""
    pass


class APIError(TopolographError):
    """Raised when an API request fails."""
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthenticationError(APIError):
    """Raised when authentication fails (401)."""
    pass


class NotFoundError(APIError):
    """Raised when a resource is not found (404)."""
    pass


class ValidationError(APIError):
    """Raised when request validation fails (400/405)."""
    pass


class RateLimitError(APIError):
    """Raised when the server limits the request rate (429); retry_after is in seconds, if sent."""
    def __init__(self, message, status_code=429, response=None, retry_after=None):
        super().__init__(message, status_code=status_code, response=response)
        self.retry_after = retry_after
