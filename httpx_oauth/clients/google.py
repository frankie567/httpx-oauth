from typing import Any, Dict, Tuple, cast

import httpx
from typing_extensions import Literal, TypedDict

from httpx_oauth.errors import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2

AUTHORIZE_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
ACCESS_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
REVOKE_TOKEN_ENDPOINT = "https://accounts.google.com/o/oauth2/revoke"
BASE_SCOPES = [
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
]
PROFILE_ENDPOINT = "https://people.googleapis.com/v1/people/me"


class GoogleOAuth2AuthorizeParams(TypedDict, total=False):
    access_type: Literal["online", "offline"]
    include_granted_scopes: bool
    login_hint: str
    prompt: Literal["none", "consent", "select_account"]


class GoogleOAuth2(BaseOAuth2[GoogleOAuth2AuthorizeParams]):
    def __init__(self, client_id: str, client_secret: str, name="google"):
        super().__init__(
            client_id,
            client_secret,
            AUTHORIZE_ENDPOINT,
            ACCESS_TOKEN_ENDPOINT,
            ACCESS_TOKEN_ENDPOINT,
            REVOKE_TOKEN_ENDPOINT,
            name=name,
            base_scopes=BASE_SCOPES,
        )

    async def _get_profile_data(self, token: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                PROFILE_ENDPOINT,
                params={"personFields": "names,emailAddresses"},
                headers={**self.request_headers, "Authorization": f"Bearer {token}"},
            )

            if response.status_code >= 400:
                raise GetIdEmailError(response.json())

            data = cast(Dict[str, Any], response.json())

            return data

    async def get_profile(self, token: str) -> Dict[str, Any]:
        data = await self._get_profile_data(token)

        data_dict = {}
        data_dict['user_id'] = data["resourceName"]
        
        data_dict['email'] = next(
            email["value"]
            for email in data["emailAddresses"]
            if email["metadata"]["primary"]
        )

        data_dict['display_name'] = next(name['displayName'] for name in data['names'])
        data_dict['first_name'] = next(name['givenName'] for name in data['names'])
        data_dict['last_name'] = next (name['familyName'] for name in data['names'])
    

        return data_dict

    async def get_id_email(self, token: str) -> Tuple[str, str]:
        data = await self._get_profile_data(token)
            
        user_id = data["resourceName"]
        user_email = next(
            email["value"]
            for email in data["emailAddresses"]
            if email["metadata"]["primary"]
        )

        return user_id, user_email
