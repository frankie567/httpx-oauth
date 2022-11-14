from typing import Any, Dict, List, Optional, Tuple, cast

import httpx_oauth.oauth2 as oauth
from httpx_oauth.errors import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2

AUTHORIZE_ENDPOINT = "https://nid.naver.com/oauth2.0/authorize"
ACCESS_TOKEN_ENDPOINT = "https://nid.naver.com/oauth2.0/token"
REFRESH_TOKEN_ENDPOINT = ACCESS_TOKEN_ENDPOINT
REVOKE_TOKEN_ENDPOINT = ACCESS_TOKEN_ENDPOINT
PROFILE_ENDPOINT = "https://openapi.naver.com/v1/nid/me"
BASE_SCOPES: List[str] = []

LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg" version="1.1" xml:space="preserve" width="40" height="40" viewBox="0 0 40 40">
  <g xmlns="http://www.w3.org/2000/svg" transform="translate(36,0)">
    <path d="m 0,0 h -32 c -2.2,0 -4,1.8 -4,4 v 32 c 0,2.2 1.8,4 4,4 H 0 c 2.2,0 4,-1.8 4,-4 V 4 C 4,1.8 2.2,0 0,0" style="fill:#03c75a;fill-opacity:1;fill-rule:nonzero;stroke:none"/>
  </g>
  <g xmlns="http://www.w3.org/2000/svg" transform="translate(17.332,18.662) scale(-1,1)">
    <path d="m 0,0 -5.683,8.135 h -4.711 V -7.064 h 4.935 V 1.071 L 0.224,-7.064 H 4.935 V 8.135 H 0 Z" style="fill:#ffffff;fill-opacity:1;fill-rule:nonzero;stroke:none"/>
  </g>
</svg>
"""


class NaverOAuth2(BaseOAuth2[Dict[str, Any]]):
    display_name = "Naver"
    logo_svg = LOGO_SVG

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scopes: Optional[List[str]] = BASE_SCOPES,
        name: str = "naver",
    ):
        super().__init__(
            client_id,
            client_secret,
            AUTHORIZE_ENDPOINT,
            ACCESS_TOKEN_ENDPOINT,
            refresh_token_endpoint=REFRESH_TOKEN_ENDPOINT,
            revoke_token_endpoint=REVOKE_TOKEN_ENDPOINT,
            name=name,
            base_scopes=scopes,
        )

    async def revoke_token(
        self, token: str, token_type_hint: Optional[str] = None
    ) -> None:
        async with self.get_httpx_client() as client:
            data = {
                "grant_type": "delete",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "access_token": token,
                "service_provider": "NAVER",
            }

            if token_type_hint is not None:
                data["token_type_hint"] = token_type_hint

            response = await client.post(
                cast(str, self.revoke_token_endpoint),
                data=data,
                headers=self.request_headers,
            )

            if response.status_code >= 400:
                raise oauth.RevokeTokenError()

    async def get_id_email(self, token: str) -> Tuple[str, Optional[str]]:
        async with self.get_httpx_client() as client:
            response = await client.post(
                PROFILE_ENDPOINT,
                headers={**self.request_headers, "Authorization": f"Bearer {token}"},
            )

            if response.status_code >= 400:
                raise GetIdEmailError(response.json())

            json = cast(Dict[str, Any], response.json())
            account_info: Dict[str, Any] = json["response"]
            return account_info["id"], account_info.get("email")
