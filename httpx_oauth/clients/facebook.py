from typing import Any, Dict, cast

import httpx

from httpx_oauth.oauth2 import BaseOAuth2, OAuth2Token

AUTHORIZE_ENDPOINT = "https://www.facebook.com/v5.0/dialog/oauth"
ACCESS_TOKEN_ENDPOINT = "https://graph.facebook.com/v5.0/oauth/access_token"


class GetLongLivedAccessTokenError(Exception):
    pass


class FacebookOAuth2(BaseOAuth2[Dict[str, Any]]):
    def __init__(self, client_id: str, client_secret: str):
        super().__init__(
            client_id, client_secret, AUTHORIZE_ENDPOINT, ACCESS_TOKEN_ENDPOINT,
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
