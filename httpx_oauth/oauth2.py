import time
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar, cast
from urllib.parse import urlencode

import httpx

from httpx_oauth.errors import HTTPXOAuthError


class OAuth2Error(HTTPXOAuthError):
    """Base exception class for OAuth2 client errors."""

    pass


class RefreshTokenNotSupportedError(OAuth2Error):
    pass


class RevokeTokenNotSupportedError(OAuth2Error):
    pass


class GetAccessTokenError(OAuth2Error):
    pass


class RefreshTokenError(OAuth2Error):
    pass


class RevokeTokenError(OAuth2Error):
    pass


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

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        authorize_endpoint: str,
        access_token_endpoint: str,
        refresh_token_endpoint: Optional[str] = None,
        revoke_token_endpoint: Optional[str] = None,
        name: str = "oauth2",
        base_scopes: Optional[List[str]] = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorize_endpoint = authorize_endpoint
        self.access_token_endpoint = access_token_endpoint
        self.refresh_token_endpoint = refresh_token_endpoint
        self.revoke_token_endpoint = revoke_token_endpoint
        self.name = name
        self.base_scopes = base_scopes

    async def get_authorization_url(
        self,
        redirect_uri: str,
        state: str = None,
        scope: Optional[List[str]] = None,
        extras_params: Optional[T] = None,
    ) -> str:
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
        }

        if state is not None:
            params["state"] = state

        if scope is not None:
            params["scope"] = " ".join(scope)

        if extras_params is not None:
            params = {**params, **extras_params}  # type: ignore

        return f"{self.authorize_endpoint}?{urlencode(params)}"

    async def get_access_token(self, code: str, redirect_uri: str):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.access_token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )

            data = cast(Dict[str, Any], response.json())

            if response.status_code == 400:
                raise GetAccessTokenError(data)

            return OAuth2Token(data)

    async def refresh_token(self, refresh_token: str):
        if self.refresh_token_endpoint is None:
            raise RefreshTokenNotSupportedError()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.refresh_token_endpoint,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )

            data = cast(Dict[str, Any], response.json())

            if response.status_code == 400:
                raise RefreshTokenError(data)

            return OAuth2Token(data)

    async def revoke_token(self, token: str, token_type_hint: str = None):
        if self.revoke_token_endpoint is None:
            raise RevokeTokenNotSupportedError()

        async with httpx.AsyncClient() as client:
            data = {"token": token}

            if token_type_hint is not None:
                data["token_type_hint"] = token_type_hint

            response = await client.post(self.revoke_token_endpoint, data=data)

            if response.status_code == 400:
                raise RevokeTokenError(response.json())

    async def get_id_email(self, token: str) -> Tuple[str, str]:
        raise NotImplementedError()


OAuth2 = BaseOAuth2[Dict[str, Any]]
