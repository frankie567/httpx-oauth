from typing import Any, Dict, Tuple, cast

import httpx
from typing_extensions import TypedDict

from httpx_oauth.errors import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2

AUTHORIZE_ENDPOINT = "https://github.com/login/oauth/authorize"
ACCESS_TOKEN_ENDPOINT = "https://github.com/login/oauth/access_token"
BASE_SCOPES = ["user"]
PROFILE_ENDPOINT = "https://api.github.com/user"


class GitHubOAuth2AuthorizeParams(TypedDict, total=False):
    login: str
    allow_signup: bool


class GitHubOAuth2(BaseOAuth2[GitHubOAuth2AuthorizeParams]):
    def __init__(self, client_id: str, client_secret: str, name: str = "github"):
        super().__init__(
            client_id,
            client_secret,
            AUTHORIZE_ENDPOINT,
            ACCESS_TOKEN_ENDPOINT,
            name=name,
            base_scopes=BASE_SCOPES,
        )

    async def get_id_email(self, token: str) -> Tuple[str, str]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                PROFILE_ENDPOINT, headers={"Authorization": f"token {token}"},
            )

            if response.status_code >= 400:
                raise GetIdEmailError(response.json())

            data = cast(Dict[str, Any], response.json())

            return str(data["id"]), data["email"]
