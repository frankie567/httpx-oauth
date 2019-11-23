from typing import List, Optional
from urllib.parse import urlencode

import httpx


class RefreshTokenNotSupportedError(Exception):
    pass


class RevokeTokenNotSupportedError(Exception):
    pass


class OAuth2:

    client_id: str
    client_secret: str
    authorize_endpoint: str
    access_token_endpoint: str
    refresh_token_endpoint: Optional[str]
    revoke_token_endpoint: Optional[str]

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        authorize_endpoint: str,
        access_token_endpoint: str,
        revoke_token_endpoint: Optional[str] = None,
        refresh_token_endpoint: Optional[str] = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorize_endpoint = authorize_endpoint
        self.access_token_endpoint = access_token_endpoint
        self.refresh_token_endpoint = refresh_token_endpoint
        self.revoke_token_endpoint = revoke_token_endpoint

    async def get_authorization_url(
        self, redirect_uri: str, state: str = None, scope: Optional[List[str]] = None
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
            return response.json()

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
            return response.json()

    async def revoke_token(self, token: str, token_type_hint: str = None):
        if self.revoke_token_endpoint is None:
            raise RevokeTokenNotSupportedError()

        async with httpx.AsyncClient() as client:
            data = {"token": token}

            if token_type_hint is not None:
                data["token_type_hint"] = token_type_hint

            await client.post(
                self.revoke_token_endpoint, data=data
            )
