from typing import Any, Dict, List, Optional, Tuple, cast

import httpx
from typing_extensions import TypedDict

from httpx_oauth.errors import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2

AUTHORIZE_ENDPOINT = "https://github.com/login/oauth/authorize"
ACCESS_TOKEN_ENDPOINT = "https://github.com/login/oauth/access_token"
BASE_SCOPES = ["user", "user:email"]
PROFILE_ENDPOINT = "https://api.github.com/user"
EMAILS_ENDPOINT = "https://api.github.com/user/emails"


class GitHubOAuth2AuthorizeParams(TypedDict, total=False):
    login: str
    allow_signup: bool


class GitHubOAuth2(BaseOAuth2[GitHubOAuth2AuthorizeParams]):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scopes: Optional[List[str]] = BASE_SCOPES,
        name: str = "github",
    ):
        super().__init__(
            client_id,
            client_secret,
            AUTHORIZE_ENDPOINT,
            ACCESS_TOKEN_ENDPOINT,
            name=name,
            base_scopes=scopes,
        )

    async def get_id_email(self, token: str) -> Tuple[str, str]:
        async with httpx.AsyncClient(
            headers={**self.request_headers, "Authorization": f"token {token}"}
        ) as client:
            response = await client.get(PROFILE_ENDPOINT)

            if response.status_code >= 400:
                raise GetIdEmailError(response.json())

            data = cast(Dict[str, Any], response.json())

            id = data["id"]
            email = data["email"]

            # No public email, make a separate call to /user/emails
            if email is None:
                response = await client.get(EMAILS_ENDPOINT)

                if response.status_code >= 400:
                    raise GetIdEmailError(response.json())

                emails = cast(List[Dict[str, Any]], response.json())

                email = emails[0]["email"]

            return str(id), email
