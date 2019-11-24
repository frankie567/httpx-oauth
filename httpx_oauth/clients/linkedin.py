from typing import Any, Dict

from httpx_oauth.oauth2 import BaseOAuth2

AUTHORIZE_ENDPOINT = "https://www.linkedin.com/oauth/v2/authorization"
ACCESS_TOKEN_ENDPOINT = "https://www.linkedin.com/oauth/v2/accessToken"


class LinkedInOAuth2(BaseOAuth2[Dict[str, Any]]):
    def __init__(self, client_id: str, client_secret: str):
        super().__init__(
            client_id,
            client_secret,
            AUTHORIZE_ENDPOINT,
            ACCESS_TOKEN_ENDPOINT,
            ACCESS_TOKEN_ENDPOINT,
        )
