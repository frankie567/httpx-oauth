from typing_extensions import TypedDict

from httpx_oauth.oauth2 import BaseOAuth2

AUTHORIZE_ENDPOINT = "https://github.com/login/oauth/authorize"
ACCESS_TOKEN_ENDPOINT = "https://github.com/login/oauth/access_token"


class GitHubOAuth2AuthorizeParams(TypedDict, total=False):
    login: str
    allow_signup: bool


class GitHubOAuth2(BaseOAuth2[GitHubOAuth2AuthorizeParams]):
    def __init__(self, client_id: str, client_secret: str):
        super().__init__(
            client_id, client_secret, AUTHORIZE_ENDPOINT, ACCESS_TOKEN_ENDPOINT,
        )
