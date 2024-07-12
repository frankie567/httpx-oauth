import json
import time
from typing import (
    Any,
    AsyncContextManager,
    Dict,
    Generic,
    List,
    Literal,
    Mapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    get_args,
)
from urllib.parse import urlencode

import httpx

from httpx_oauth.exceptions import HTTPXOAuthError


class OAuth2Error(HTTPXOAuthError):
    """Base exception class for OAuth2 client errors."""

    pass


class NotSupportedAuthMethodError(OAuth2Error):
    """Error raised when an unsupported authentication method is used."""

    def __init__(self, auth_method: str):
        super().__init__(f"Auth method {auth_method} is not supported.")


class MissingRevokeTokenAuthMethodError(OAuth2Error):
    """Error raised when the revocation endpoint auth method is missing."""

    def __init__(self):
        super().__init__("Missing revocation endpoint auth method.")


class RefreshTokenNotSupportedError(OAuth2Error):
    """
    Error raised when trying to refresh a token
    on a provider that does not support it.
    """

    def __init__(self):
        super().__init__("Refresh token is not supported by this provider.")


class RevokeTokenNotSupportedError(OAuth2Error):
    """
    Error raised when trying to revole a token
    on a provider that does not support it.
    """

    def __init__(self):
        super().__init__("Revoke token is not supported by this provider.")


class OAuth2RequestError(OAuth2Error):
    """
    Base exception class for OAuth2 request errors.
    """

    def __init__(
        self, message: str, response: Union[httpx.Response, None] = None
    ) -> None:
        self.response = response
        super().__init__(message)


class GetAccessTokenError(OAuth2RequestError):
    """Error raised when an error occurs while getting an access token."""


class RefreshTokenError(OAuth2RequestError):
    """Error raised when an error occurs while refreshing a token."""


class RevokeTokenError(OAuth2RequestError):
    """Error raised when an error occurs while revoking a token."""


OAuth2ClientAuthMethod = Literal["client_secret_basic", "client_secret_post"]
"""Supported OAuth2 client authentication methods."""


def _check_valid_auth_method(auth_method: str) -> None:
    if auth_method not in get_args(OAuth2ClientAuthMethod):
        raise NotSupportedAuthMethodError(auth_method)


class OAuth2Token(Dict[str, Any]):
    """
    Wrapper around a standard `Dict[str, Any]` that bears the response
    of a successful token request.

    Properties can vary greatly from a service to another but, usually,
    you can get access token like this:

    Examples:
        ```py
        access_token = token["access_token"]
        ```
    """

    def __init__(self, token_dict: Dict[str, Any]):
        if "expires_at" in token_dict:
            token_dict["expires_at"] = int(token_dict["expires_at"])
        elif "expires_in" in token_dict:
            token_dict["expires_at"] = int(time.time()) + int(token_dict["expires_in"])
        super().__init__(token_dict)

    def is_expired(self) -> bool:
        """
        Checks if the token is expired.

        Returns:
            True if the token is expired, False otherwise
        """
        if "expires_at" not in self:
            return False
        return time.time() > self["expires_at"]


T = TypeVar("T")


class BaseOAuth2(Generic[T]):
    """
    Base OAuth2 client.

    This class provides a base implementation for OAuth2 clients. If you need to use a generic client, use [OAuth2][httpx_oauth.oauth2.OAuth2] instead.
    """

    name: str
    client_id: str
    client_secret: str
    authorize_endpoint: str
    access_token_endpoint: str
    refresh_token_endpoint: Optional[str]
    revoke_token_endpoint: Optional[str]
    base_scopes: Optional[List[str]]
    token_endpoint_auth_method: OAuth2ClientAuthMethod
    revocation_endpoint_auth_method: Optional[OAuth2ClientAuthMethod]
    request_headers: Dict[str, str]

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        authorize_endpoint: str,
        access_token_endpoint: str,
        refresh_token_endpoint: Optional[str] = None,
        revoke_token_endpoint: Optional[str] = None,
        *,
        name: str = "oauth2",
        base_scopes: Optional[List[str]] = None,
        token_endpoint_auth_method: OAuth2ClientAuthMethod = "client_secret_post",
        revocation_endpoint_auth_method: Optional[OAuth2ClientAuthMethod] = None,
    ):
        """
        Args:
            client_id: The client ID provided by the OAuth2 provider.
            client_secret: The client secret provided by the OAuth2 provider.
            authorize_endpoint: The authorization endpoint URL.
            access_token_endpoint: The access token endpoint URL.
            refresh_token_endpoint: The refresh token endpoint URL.
                If not supported, set it to `None`.
            revoke_token_endpoint: The revoke token endpoint URL.
                If not supported, set it to `None`.
            name: A unique name for the OAuth2 client.
            base_scopes: The base scopes to be used in the authorization URL.
            token_endpoint_auth_method: The authentication method to be used in the token endpoint.
            revocation_endpoint_auth_method: The authentication method to be used in the revocation endpoint.
                If the revocation endpoint is not supported, set it to `None`.

        Raises:
            NotSupportedAuthMethodError:
                The provided authentication method is not supported.
            MissingRevokeTokenAuthMethodError:
                The revocation endpoint auth method is missing.
        """
        _check_valid_auth_method(token_endpoint_auth_method)
        if revocation_endpoint_auth_method is not None:
            _check_valid_auth_method(revocation_endpoint_auth_method)
        if (
            revoke_token_endpoint is not None
            and revocation_endpoint_auth_method is None
        ):
            raise MissingRevokeTokenAuthMethodError()

        self.client_id = client_id
        self.client_secret = client_secret
        self.authorize_endpoint = authorize_endpoint
        self.access_token_endpoint = access_token_endpoint
        self.refresh_token_endpoint = refresh_token_endpoint
        self.revoke_token_endpoint = revoke_token_endpoint
        self.name = name
        self.base_scopes = base_scopes
        self.token_endpoint_auth_method = token_endpoint_auth_method
        self.revocation_endpoint_auth_method = revocation_endpoint_auth_method

        self.request_headers = {
            "Accept": "application/json",
        }

    async def get_authorization_url(
        self,
        redirect_uri: str,
        state: Optional[str] = None,
        scope: Optional[List[str]] = None,
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[Literal["plain", "S256"]] = None,
        extras_params: Optional[T] = None,
    ) -> str:
        """
        Builds the authorization URL
        where the user should be redirected to authorize the application.

        Args:
            redirect_uri: The URL where the user will be redirected after authorization.
            state: An opaque value used by the client to maintain state
                between the request and the callback.
            scope: The scopes to be requested.
                If not provided, `base_scopes` will be used.
            code_challenge: Optional
                [PKCE](https://datatracker.ietf.org/doc/html/rfc7636)) code challenge.
            code_challenge_method: Optional
                [PKCE](https://datatracker.ietf.org/doc/html/rfc7636)) code challenge
                method.
            extras_params: Optional extra parameters specific to the service.

        Returns:
            The authorization URL.

        Examples:
            ```py
            authorization_url = await client.get_authorization_url(
                "https://www.tintagel.bt/oauth-callback", scope=["SCOPE1", "SCOPE2", "SCOPE3"],
            )
            ```py
        """
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
        }

        if state is not None:
            params["state"] = state

        # Provide compatibility with current scope from the endpoint
        _scope = scope or self.base_scopes
        if _scope is not None:
            params["scope"] = " ".join(_scope)

        if code_challenge is not None:
            params["code_challenge"] = code_challenge

        if code_challenge_method is not None:
            params["code_challenge_method"] = code_challenge_method

        if extras_params is not None:
            params = {**params, **extras_params}  # type: ignore

        return f"{self.authorize_endpoint}?{urlencode(params)}"

    async def get_access_token(
        self, code: str, redirect_uri: str, code_verifier: Optional[str] = None
    ) -> OAuth2Token:
        """
        Requests an access token using the authorization code obtained
        after the user has authorized the application.

        Args:
            code: The authorization code.
            redirect_uri: The URL where the user was redirected after authorization.
            code_verifier: Optional code verifier used
                in the [PKCE](https://datatracker.ietf.org/doc/html/rfc7636)) flow.

        Returns:
            An access token response dictionary.

        Raises:
            GetAccessTokenError: An error occurred while getting the access token.

        Examples:
            ```py
            access_token = await client.get_access_token("CODE", "https://www.tintagel.bt/oauth-callback")
            ```
        """
        async with self.get_httpx_client() as client:
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            }

            if code_verifier:
                data["code_verifier"] = code_verifier

            request, auth = self.build_request(
                client,
                "POST",
                self.access_token_endpoint,
                auth_method=self.token_endpoint_auth_method,
                data=data,
            )
            response = await self.send_request(
                client, request, auth, exc_class=GetAccessTokenError
            )
            data = self.get_json(response, exc_class=GetAccessTokenError)
            return OAuth2Token(data)

    async def refresh_token(self, refresh_token: str) -> OAuth2Token:
        """
        Requests a new access token using a refresh token.

        Args:
            refresh_token: The refresh token.

        Returns:
            An access token response dictionary.

        Raises:
            RefreshTokenError: An error occurred while refreshing the token.
            RefreshTokenNotSupportedError: The provider does not support token refresh.

        Examples:
            ```py
            access_token = await client.refresh_token("REFRESH_TOKEN")
            ```
        """
        if self.refresh_token_endpoint is None:
            raise RefreshTokenNotSupportedError()

        async with self.get_httpx_client() as client:
            request, auth = self.build_request(
                client,
                "POST",
                self.refresh_token_endpoint,
                auth_method=self.token_endpoint_auth_method,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
            )
            response = await self.send_request(
                client, request, auth, exc_class=RefreshTokenError
            )
            data = self.get_json(response, exc_class=RefreshTokenError)
            return OAuth2Token(data)

    async def revoke_token(
        self, token: str, token_type_hint: Optional[str] = None
    ) -> None:
        """
        Revokes a token.

        Args:
            token: A token or refresh token to revoke.
            token_type_hint: Optional hint for the service to help it determine
                if it's a token or refresh token.
                Usually either `token` or `refresh_token`.

        Returns:
            None

        Raises:
            RevokeTokenError: An error occurred while revoking the token.
            RevokeTokenNotSupportedError: The provider does not support token revoke.
        """
        if self.revoke_token_endpoint is None:
            raise RevokeTokenNotSupportedError()

        async with self.get_httpx_client() as client:
            data = {"token": token}

            if token_type_hint is not None:
                data["token_type_hint"] = token_type_hint

            request, auth = self.build_request(
                client,
                "POST",
                self.revoke_token_endpoint,
                auth_method=self.token_endpoint_auth_method,
                data=data,
            )
            await self.send_request(client, request, auth, exc_class=RevokeTokenError)

        return None

    async def get_id_email(self, token: str) -> Tuple[str, Optional[str]]:
        """
        Returns the id and the email (if available) of the authenticated user
        from the API provider.

        **It assumes you have asked for the required scopes**.

        Args:
            token: The access token.

        Returns:
            A tuple with the id and the email of the authenticated user.


        Raises:
            httpx_oauth.exceptions.GetIdEmailError:
                An error occurred while getting the id and email.

        Examples:
            ```py
            user_id, user_email = await client.get_id_email("TOKEN")
            ```
        """
        raise NotImplementedError()

    def get_httpx_client(self) -> AsyncContextManager[httpx.AsyncClient]:
        return httpx.AsyncClient()

    def build_request(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        *,
        auth_method: Union[OAuth2ClientAuthMethod, None] = None,
        data: Union[Mapping[str, Any], None] = None,
    ) -> Tuple[httpx.Request, Union[httpx.Auth, None]]:
        if data is not None:
            data = {
                **data,
                **(
                    {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    }
                    if auth_method == "client_secret_post"
                    else {}
                ),
            }

        request = client.build_request(
            method,
            url,
            data=data,
            headers=self.request_headers,
        )

        auth = None
        if auth_method == "client_secret_basic":
            auth = httpx.BasicAuth(self.client_id, self.client_secret)

        return request, auth

    async def send_request(
        self,
        client: httpx.AsyncClient,
        request: httpx.Request,
        auth: Union[httpx.Auth, None],
        *,
        exc_class: Type[OAuth2RequestError],
    ) -> httpx.Response:
        try:
            response = await client.send(request, auth=auth)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise exc_class(str(e), e.response) from e
        except httpx.HTTPError as e:
            raise exc_class(str(e)) from e

        return response

    def get_json(
        self, response: httpx.Response, *, exc_class: Type[OAuth2RequestError]
    ) -> Dict[str, Any]:
        try:
            return cast(Dict[str, Any], response.json())
        except json.decoder.JSONDecodeError as e:
            message = "Invalid JSON content"
            raise exc_class(message, response) from e


OAuth2 = BaseOAuth2[Dict[str, Any]]
"""
Generic OAuth2 client.

Examples:
    ```py
    from httpx_oauth.oauth2 import OAuth2

    client = OAuth2(
        "CLIENT_ID",
        "CLIENT_SECRET",
        "AUTHORIZE_ENDPOINT",
        "ACCESS_TOKEN_ENDPOINT",
        refresh_token_endpoint="REFRESH_TOKEN_ENDPOINT",
        revoke_token_endpoint="REVOKE_TOKEN_ENDPOINT",
    )
    ```
"""

__all__ = [
    "BaseOAuth2",
]
