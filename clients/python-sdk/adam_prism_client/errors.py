"""
Adam Prism Client — Custom exception classes
فئات الأخطاء المخصصة للـ SDK
"""


class AdamPrismError(Exception):
    """Base exception for all Adam Prism SDK errors."""


class ConnectionError(AdamPrismError):
    """Raised when the client cannot connect to the API server."""


class TimeoutError(AdamPrismError):
    """Raised when a request times out."""


class APIError(AdamPrismError):
    """Raised when the API returns an error response."""

    def __init__(self, status_code: int, detail: str = "", response_data: dict | None = None):
        self.status_code = status_code
        self.detail = detail
        self.response_data = response_data or {}
        super().__init__(f"HTTP {status_code}: {detail or 'Unknown error'}")

    @classmethod
    def from_response(cls, status_code: int, body: dict) -> "APIError":
        detail = body.get("detail", "") or body.get("message", "")
        return cls(status_code, detail, body)


class NotFoundError(APIError):
    """Raised when a requested resource is not found (HTTP 404)."""

    def __init__(self, detail: str = "", response_data: dict | None = None):
        super().__init__(404, detail, response_data)


class ServerError(APIError):
    """Raised when the server returns a 5xx error."""

    def __init__(self, status_code: int, detail: str = "", response_data: dict | None = None):
        super().__init__(status_code, detail, response_data)


class ValidationError(APIError):
    """Raised when the request is invalid (HTTP 400)."""

    def __init__(self, detail: str = "", response_data: dict | None = None):
        super().__init__(400, detail, response_data)


class ServiceUnavailableError(APIError):
    """Raised when a required subsystem is not available (HTTP 503)."""

    def __init__(self, detail: str = "", response_data: dict | None = None):
        super().__init__(503, detail, response_data)
