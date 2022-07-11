from typing import Any, Dict, List, Optional, Tuple, cast

from httpx_oauth.errors import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2

AUTHORIZE_ENDPOINT = "https://discord.com/api/oauth2/authorize"
ACCESS_TOKEN_ENDPOINT = "https://discord.com/api/oauth2/token"
REVOKE_TOKEN_ENDPOINT = "https://discord.com/api/oauth2/token/revoke"
BASE_SCOPES = ("identify", "email")
PROFILE_ENDPOINT = "https://discord.com/api/users/@me"


class DiscordOAuth2(BaseOAuth2[Dict[str, Any]]):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scopes: Optional[List[str]] = BASE_SCOPES,
        name: str = "discord",
    ):
        super().__init__(
            client_id,
            client_secret,
            AUTHORIZE_ENDPOINT,
            ACCESS_TOKEN_ENDPOINT,
            ACCESS_TOKEN_ENDPOINT,
            REVOKE_TOKEN_ENDPOINT,
            name=name,
            base_scopes=scopes,
        )

    async def get_id_email(self, token: str) -> Tuple[str, str]:
        async with self.get_httpx_client() as client:
            response = await client.get(
                PROFILE_ENDPOINT,
                headers={**self.request_headers, "Authorization": f"Bearer {token}"},
            )

            if response.status_code >= 400:
                raise GetIdEmailError(response.json())

            data = cast(Dict[str, Any], response.json())

            user_id = data["id"]

            if (
                "verified" not in data or "email" not in data
            ):  # No email on discord account
                raise GetIdEmailError({"error": "Email not provided"})
            elif not data["verified"]:  # Email present, but not verified
                raise GetIdEmailError({"error": "Email not verified"})
            else:
                user_email = data["email"]

            return user_id, user_email
