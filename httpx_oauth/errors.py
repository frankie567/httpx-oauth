class HTTPXOAuthError(Exception):
    """Base exception class for every httpx-oauth errors."""

    pass


class GetProfileError(HTTPXOAuthError):
    """Error raised while retrieving user profile from provider API."""

    pass
