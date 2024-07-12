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

from httpx_oauth.errors import HTTPXOAuthError


class OAuth2Error(HTTPXOAuthError):
    """Base exception class for OAuth2 client errors."""

    pass


class NotSupportedAuthMethodError(OAuth2Error):
    def __init__(self, auth_method: str):
        super().__init__(f"Auth method {auth_method} is not supported.")


class MissingRevokeTokenAuthMethodError(OAuth2Error):
    def __init__(self):
        super().__init__("Missing revocation endpoint auth method.")


class RefreshTokenNotSupportedError(OAuth2Error):
    def __init__(self):
        super().__init__("Refresh token is not supported by this provider.")


class RevokeTokenNotSupportedError(OAuth2Error):
    def __init__(self):
        super().__init__("Revoke token is not supported by this provider.")


class OAuth2RequestError(OAuth2Error):
    def __init__(
        self, message: str, response: Union[httpx.Response, None] = None
    ) -> None:
        self.response = response
        super().__init__(message)


class GetAccessTokenError(OAuth2RequestError): ...


class RefreshTokenError(OAuth2RequestError): ...


class RevokeTokenError(OAuth2RequestError): ...


OAuth2ClientAuthMethod = Literal["client_secret_basic", "client_secret_post"]


def _check_valid_auth_method(auth_method: str) -> None:
    if auth_method not in get_args(OAuth2ClientAuthMethod):
        raise NotSupportedAuthMethodError(auth_method)


class OAuth2Token(Dict[str, Any]):
    def __init__(self, token_dict: Dict[str, Any]):
        if "expires_at" in token_dict:
            token_dict["expires_at"] = int(token_dict["expires_at"])
        elif "expires_in" in token_dict:
            token_dict["expires_at"] = int(time.time()) + int(token_dict["expires_in"])
        super().__init__(token_dict)

    def is_expired(self):
        if "expires_at" not in self:
            return False
        return time.time() > self["expires_at"]


T = TypeVar("T")


class BaseOAuth2(Generic[T]):
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
    ):
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

    async def refresh_token(self, refresh_token: str):
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
