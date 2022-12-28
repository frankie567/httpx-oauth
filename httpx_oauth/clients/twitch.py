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
<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
	 viewBox="0 0 2400 2800" style="enable-background:new 0 0 2400 2800;" xml:space="preserve">
<style type="text/css">
	.st0{fill:#FFFFFF;}
	.st1{fill:#9146FF;}
</style>
<g>
	<polygon class="st0" points="2200,1300 1800,1700 1400,1700 1050,2050 1050,1700 600,1700 600,200 2200,200 	"/>
	<g>
		<g id="Layer_1-2">
			<path class="st1" d="M500,0L0,500v1800h600v500l500-500h400l900-900V0H500z M2200,1300l-400,400h-400l-350,350v-350H600V200h1600
				V1300z"/>
			<rect x="1700" y="550" class="st1" width="200" height="600"/>
			<rect x="1150" y="550" class="st1" width="200" height="600"/>
		</g>
	</g>
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
