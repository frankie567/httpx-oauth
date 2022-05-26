from typing import Any, Dict, List, Optional, Tuple, cast

import httpx

import httpx_oauth.oauth2 as oauth
from httpx_oauth.errors import GetIdEmailError

AUTHORIZE_ENDPOINT = "https://www.reddit.com/api/v1/authorize"
ACCESS_TOKEN_ENDPOINT = "https://www.reddit.com/api/v1/access_token"
REFRESH_ENDPOINT = ACCESS_TOKEN_ENDPOINT
REVOKE_ENDPOINT = "https://www.reddit.com/api/v1/revoke_token"
IDENTITY_ENDPOINT = "https://oauth.reddit.com/api/v1/me"

BASE_SCOPES = ["identity"]


class RedditOAuth2(oauth.BaseOAuth2[Dict[str, Any]]):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scopes: Optional[List[str]] = None,
        name: str = "reddit",
    ):
        if scopes is None:
            scopes = BASE_SCOPES

        super().__init__(
            client_id,
            client_secret,
            AUTHORIZE_ENDPOINT,
            ACCESS_TOKEN_ENDPOINT,
            REFRESH_ENDPOINT,
            REVOKE_ENDPOINT,
            name=name,
            base_scopes=scopes,
        )

        # Below fixes typing of the parent class, which marks these as Optional
        self.refresh_token_endpoint: str
        self.revoke_token_endpoint: str

    async def get_access_token(
        self, code: str, redirect_uri: str, code_verifier: str = None
    ) -> oauth.OAuth2Token:
        async with self.get_httpx_client() as client:
            response = await client.post(
                self.access_token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                auth=(self.client_id, self.client_secret),
                headers=self.request_headers,
            )

            data = cast(Dict[str, Any], response.json())

            if response.status_code >= httpx.codes.BAD_REQUEST or "error" in data:
                raise oauth.GetAccessTokenError(data)

            return oauth.OAuth2Token(data)

    async def refresh_token(self, refresh_token: str) -> oauth.OAuth2Token:
        async with self.get_httpx_client() as client:
            response = await client.post(
                self.refresh_token_endpoint,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                auth=(self.client_id, self.client_secret),
                headers=self.request_headers,
            )

            data = cast(Dict[str, Any], response.json())

            if response.status_code >= httpx.codes.BAD_REQUEST or "error" in data:
                raise oauth.RefreshTokenError(data)

            return oauth.OAuth2Token(data)

    async def revoke_token(
        self,
        token: str,
        token_type_hint: Optional[str] = None,
    ) -> None:
        async with self.get_httpx_client() as client:
            data = {"token": token}

            if token_type_hint is not None:
                data["token_type_hint"] = token_type_hint

            response = await client.post(
                self.revoke_token_endpoint,
                data=data,
                auth=(self.client_id, self.client_secret),
                headers=self.request_headers,
            )

            if response.status_code >= httpx.codes.BAD_REQUEST:
                raise oauth.RevokeTokenError()

    async def get_id_email(self, token: str) -> Tuple[str, str]:
        # Reddit does not expose user's e-mail address via the API, e-mail will be
        # an empty string

        async with self.get_httpx_client() as client:
            headers = self.request_headers.copy()
            headers["Authorization"] = f"Bearer {token}"

            response = await client.get(
                IDENTITY_ENDPOINT,
                headers=headers,
            )

            # Reddit doesn't return any useful JSON in case of auth failures
            # on oauth.reddit.com endpoints, so we simulate our own
            if response.status_code != httpx.codes.OK:
                raise GetIdEmailError({"error": response.status_code})

            data = cast(Dict[str, Any], response.json())
            return data["name"], ""
