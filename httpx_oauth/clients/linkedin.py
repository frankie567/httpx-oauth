from typing import Any, Dict, Tuple, cast

import httpx

from httpx_oauth.errors import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2

AUTHORIZE_ENDPOINT = "https://www.linkedin.com/oauth/v2/authorization"
ACCESS_TOKEN_ENDPOINT = "https://www.linkedin.com/oauth/v2/accessToken"
BASE_SCOPES = ["r_emailaddress", "r_liteprofile", "r_basicprofile"]
PROFILE_ENDPOINT = "https://api.linkedin.com/v2/me"
EMAIL_ENDPOINT = "https://api.linkedin.com/v2/emailAddress"


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

    async def get_id_email(self, token: str) -> Tuple[str, str]:
        async with httpx.AsyncClient() as client:
            profile_response = await client.get(
                PROFILE_ENDPOINT,
                headers={"Authorization": f"Bearer {token}"},
                params={"projection": "(id)"},
            )

            if profile_response.status_code >= 400:
                raise GetIdEmailError(profile_response.json())

            email_response = await client.get(
                EMAIL_ENDPOINT,
                headers={"Authorization": f"Bearer {token}"},
                params={"q": "members", "projection": "(elements*(handle~))"},
            )

            if email_response.status_code >= 400:
                raise GetIdEmailError(email_response.json())

            profile_data = cast(Dict[str, Any], profile_response.json())
            user_id = profile_data["id"]

            email_data = cast(Dict[str, Any], email_response.json())
            user_email = email_data["elements"][0]["handle~"]["emailAddress"]

            return user_id, user_email
