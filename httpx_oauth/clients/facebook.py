from typing import Any, Dict, Tuple, cast

import httpx

from httpx_oauth.errors import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2, OAuth2Token

AUTHORIZE_ENDPOINT = "https://www.facebook.com/v5.0/dialog/oauth"
ACCESS_TOKEN_ENDPOINT = "https://graph.facebook.com/v5.0/oauth/access_token"
BASE_SCOPES = ["email", "public_profile"]
PROFILE_ENDPOINT = "https://graph.facebook.com/v5.0/me"


class GetLongLivedAccessTokenError(Exception):
    pass


class FacebookOAuth2(BaseOAuth2[Dict[str, Any]]):
    def __init__(self, client_id: str, client_secret: str, name: str = "facebook"):
        super().__init__(
            client_id,
            client_secret,
            AUTHORIZE_ENDPOINT,
            ACCESS_TOKEN_ENDPOINT,
            name=name,
            base_scopes=BASE_SCOPES,
        )

    async def get_long_lived_access_token(self, token: str):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.access_token_endpoint,
                data={
                    "grant_type": "fb_exchange_token",
                    "fb_exchange_token": token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )

            data = cast(Dict[str, Any], response.json())

            if response.status_code == 400:
                raise GetLongLivedAccessTokenError(data)

            return OAuth2Token(data)

    async def get_id_email(self, token: str) -> Tuple[str, str]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                PROFILE_ENDPOINT, params={"fields": "id,email", "access_token": token},
            )

            if response.status_code >= 400:
                raise GetIdEmailError(response.json())

            data = cast(Dict[str, Any], response.json())

            return data["id"], data["email"]
