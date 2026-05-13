import httpx


class HTTPXOAuthError(Exception):
    """Base exception class for every httpx-oauth errors."""

    message: str

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class GetProfileError(HTTPXOAuthError):
    """Error raised while retrieving user profile from provider API."""

    def __init__(
        self,
        message: str = "Error while retrieving user profile.",
        response: httpx.Response | None = None,
    ) -> None:
        self.response = response
        super().__init__(message)


class GetIdEmailError(GetProfileError):
    """Error raised while retrieving id and email from provider API."""

    def __init__(
        self,
        message: str = "Error while retrieving id and email.",
        response: httpx.Response | None = None,
    ) -> None:
        super().__init__(message, response)
