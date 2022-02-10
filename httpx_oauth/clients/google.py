from typing import Any, Dict, List, Optional, Tuple, cast

import httpx
from typing_extensions import Literal, TypedDict

from httpx_oauth.errors import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2

# Available fields
# https://developers.google.com/people/api/rest/v1/people/get

AUTHORIZE_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
ACCESS_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
REVOKE_TOKEN_ENDPOINT = "https://accounts.google.com/o/oauth2/revoke"
BASE_SCOPES = [
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
]
BASE_FIELDS = [
    "id",
    "email"
]
PROFILE_ENDPOINT = "https://people.googleapis.com/v1/people/me"


class GoogleOAuth2AuthorizeParams(TypedDict, total=False):
    access_type: Literal["online", "offline"]
    include_granted_scopes: bool
    login_hint: str
    prompt: Literal["none", "consent", "select_account"]


class GoogleOAuth2(BaseOAuth2[GoogleOAuth2AuthorizeParams]):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scope: Optional[List[str]] = BASE_SCOPES,
        fields: Optional[List[str]] = BASE_FIELDS,
        name="google",
    ):
        super().__init__(
            client_id,
            client_secret,
            AUTHORIZE_ENDPOINT,
            ACCESS_TOKEN_ENDPOINT,
            ACCESS_TOKEN_ENDPOINT,
            REVOKE_TOKEN_ENDPOINT,
            name=name,
            base_scopes=scope,
            base_fields=fields,
        )

    async def get_id_email(self, token: str) -> Tuple[str, str, Dict]:
        async with httpx.AsyncClient() as client:
            fields = "emailAddresses"
            for base_field in self.base_fields:
                if (base_field == "first_name" or base_field == "last_name") and "names" not in fields:
                    fields += ",names"
                elif base_field == "picture" and "photos" not in fields:
                    fields += ",photos"

            response = await client.get(
                PROFILE_ENDPOINT,
                params={"personFields": fields},
                headers={**self.request_headers, "Authorization": f"Bearer {token}"},
            )

            if response.status_code >= 400:
                raise GetIdEmailError(response.json())

            data = cast(Dict[str, Any], response.json())

            user_id = data["resourceName"]
            user_email = next(
                email["value"]
                for email in data["emailAddresses"]
                if email["metadata"]["primary"]
            )

            extra_data = {}

            if "names" in fields:
                extra_data.update({
                    "first_name": next(
                        name["givenName"]
                        for name in data["names"]
                        if name["metadata"]["primary"]
                    ),
                    "last_name": next(
                        name["familyName"]
                        for name in data["names"]
                        if name["metadata"]["primary"]
                    ),
                })

            if "photos" in fields:
                extra_data.update({
                    "picture": next(
                        {"url": photo["url"], "default": photo["default"]}
                        for photo in data["photos"]
                        if photo["metadata"]["primary"]
                    ),
                })

            return user_id, user_email, extra_data
