from typing import Any, Dict, List, Optional, Tuple, cast

import httpx

from httpx_oauth.errors import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2, OAuth2Token

# Available fields
# https://developers.facebook.com/docs/graph-api/reference/user

AUTHORIZE_ENDPOINT = "https://www.facebook.com/v5.0/dialog/oauth"
ACCESS_TOKEN_ENDPOINT = "https://graph.facebook.com/v5.0/oauth/access_token"
BASE_SCOPES = ["email", "public_profile"]
BASE_FIELDS = [
    "id",
    "email",
]
PROFILE_ENDPOINT = "https://graph.facebook.com/v5.0/me"


class GetLongLivedAccessTokenError(Exception):
    pass


class FacebookOAuth2(BaseOAuth2[Dict[str, Any]]):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scopes: Optional[List[str]] = BASE_SCOPES,
        fields: Optional[List[str]] = BASE_FIELDS,
        name: str = "facebook",
    ):
        super().__init__(
            client_id,
            client_secret,
            AUTHORIZE_ENDPOINT,
            ACCESS_TOKEN_ENDPOINT,
            name=name,
            base_scopes=scopes,
            base_fields=fields,
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

    async def get_id_email(self, token: str) -> Tuple[str, str, Dict]:
        async with httpx.AsyncClient() as client:
            fields = "id,email"

            for base_field in self.base_fields:
                if base_field == "first_name" and "first_name" not in fields:
                    fields += ",first_name"
                elif base_field == "last_name" and "last_name" not in fields:
                    fields += ",last_name"
                elif base_field == "picture" and "picture" not in fields:
                    fields += ",picture"

            response = await client.get(
                PROFILE_ENDPOINT,
                params={"fields": fields, "access_token": token},
            )

            if response.status_code >= 400:
                raise GetIdEmailError(response.json())

            data = cast(Dict[str, Any], response.json())

            extra_data = {}

            if "first_name" in fields:
                extra_data.update({"first_name": data["first_name"]})

            if "last_name" in fields:
                extra_data.update({"last_name": data["last_name"]})

            if "picture" in fields:
                extra_data.update(
                    {
                        "picture": {
                            "url": data["picture"]["data"]["url"],
                            "default": data["picture"]["data"]["is_silhouette"],
                        }
                    }
                )

            return data["id"], data["email"], extra_data
