from typing import Any, Dict, List, Optional, Tuple, cast

from httpx_oauth.errors import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2

AUTHORIZE_ENDPOINT = "https://id.twitch.tv/oauth2/authorize"
ACCESS_TOKEN_ENDPOINT = "https://id.twitch.tv/oauth2/token"
REVOKE_TOKEN_ENDPOINT = "https://id.twitch.tv/oauth2/revoke"
BASE_SCOPES = [
    "user:read:email",
    "user:read:follows",
    "user:read:subscriptions",
    "user:manage:whispers",
]

"""
If an ID or login name is not specified, the request to the user endpoint returns 
information about the user specified in the included access token.

https://dev.twitch.tv/docs/api/reference#get-users
"""
PROFILE_ENDPOINT = "https://api.twitch.tv/helix/users"

LOGO_SVG = """
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="256px" height="268px" viewBox="0 0 256 268" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" preserveAspectRatio="xMidYMid">
    <g>
        <path d="M17.4579119,0 L0,46.5559188 L0,232.757287 L63.9826001,232.757287 L63.9826001,267.690956 L98.9144853,267.690956 L133.811571,232.757287 L186.171922,232.757287 L256,162.954193 L256,0 L17.4579119,0 Z M40.7166868,23.2632364 L232.73141,23.2632364 L232.73141,151.29179 L191.992415,192.033461 L128,192.033461 L93.11273,226.918947 L93.11273,192.033461 L40.7166868,192.033461 L40.7166868,23.2632364 Z M104.724985,139.668381 L127.999822,139.668381 L127.999822,69.843872 L104.724985,69.843872 L104.724985,139.668381 Z M168.721862,139.668381 L191.992237,139.668381 L191.992237,69.843872 L168.721862,69.843872 L168.721862,139.668381 Z" fill="#5A3E85"></path>
    </g>
</svg>
"""


class TwitchOAuth2(BaseOAuth2[Dict[str, Any]]):
    display_name = "Twitch"
    logo_svg = LOGO_SVG

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scope: Optional[List[str]] = BASE_SCOPES,
        name="twitch",
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
        )

    async def get_id_email(self, token: str) -> Tuple[str, Optional[str]]:
        async with self.get_httpx_client() as client:
            response = await client.get(
                PROFILE_ENDPOINT,
                headers={
                    "Client-Id": self.client_id,
                    "Authorization": f"Bearer {token}",
                },
            )

            if response.status_code >= 400:
                raise GetIdEmailError(response.json())

            response_body = cast(Dict[str, Any], response.json())

            user_id = response_body["data"][0]["id"]

            """
            To include the user's verified email address in the response, you must use 
            a user access token that includes the 'user:read:email' scope.

            https://dev.twitch.tv/docs/api/reference#get-users
            """
            user_email = response_body["data"][0].get("email")

            return user_id, user_email
