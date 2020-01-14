from typing import Any, Dict

import httpx

from httpx_oauth.errors import GetProfileError
from httpx_oauth.oauth2 import BaseOAuth2

AUTHORIZE_ENDPOINT = "https://www.linkedin.com/oauth/v2/authorization"
ACCESS_TOKEN_ENDPOINT = "https://www.linkedin.com/oauth/v2/accessToken"
BASE_SCOPES = ["r_emailaddress", "r_liteprofile"]
PROFILE_ENDPOINT = "https://api.linkedin.com/v2/me"


class LinkedInOAuth2(BaseOAuth2[Dict[str, Any]]):
    def __init__(self, client_id: str, client_secret: str, name: str = "linkedin"):
        super().__init__(
            client_id,
            client_secret,
            AUTHORIZE_ENDPOINT,
            ACCESS_TOKEN_ENDPOINT,
            ACCESS_TOKEN_ENDPOINT,
            name=name,
            base_scopes=BASE_SCOPES,
        )

    async def get_profile(self, token: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                PROFILE_ENDPOINT, headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code >= 400:
                raise GetProfileError(response.json())

            return response.json()
