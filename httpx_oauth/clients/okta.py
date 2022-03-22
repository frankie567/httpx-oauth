from typing import Any, Dict, List, Optional, Tuple, cast

import httpx

from httpx_oauth.errors import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2

BASE_SCOPES = ["openid", "email"]


class OktaOAuth2(BaseOAuth2[BaseOAuth2[Dict[str, Any]]]):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        okta_base_url: str,
        scopes: Optional[List[str]] = BASE_SCOPES,
        name: str = "okta",
    ):
        super().__init__(
            client_id,
            client_secret,
            f"https://{okta_base_url}/oauth2/v1/authorize",
            f"https://{okta_base_url}/oauth2/v1/token",
            f"https://{okta_base_url}/oauth2/v1/token",
            f"https://{okta_base_url}/oauth2/v1/revoke",
            name=name,
            base_scopes=scopes,
        )
        self.profile = f"https://{okta_base_url}/oauth2/v1/userinfo"

    async def get_id_email(self, token: str) -> Tuple[str, str]:
        async with httpx.AsyncClient(
            headers={**self.request_headers, "Authorization": f"Bearer {token}"}
        ) as client:
            response = await client.get(self.profile)

            if response.status_code >= 400:
                raise GetIdEmailError(response.json())

            data = cast(Dict[str, Any], response.json())

            user_id = data["sub"]
            email = data["email"]

            return str(user_id), email
