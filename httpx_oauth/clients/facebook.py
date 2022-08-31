from typing import Any, Dict, List, Optional, Tuple, cast

from httpx_oauth.errors import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2, OAuth2Token

AUTHORIZE_ENDPOINT = "https://www.facebook.com/v5.0/dialog/oauth"
ACCESS_TOKEN_ENDPOINT = "https://graph.facebook.com/v5.0/oauth/access_token"
BASE_SCOPES = ["email", "public_profile"]
PROFILE_ENDPOINT = "https://graph.facebook.com/v5.0/me"


LOGO_SVG = """
<svg width="256px" height="256px" viewBox="0 0 256 256" version="1.1" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid">
    <title>Facebook</title>
    <g>
        <path d="M256,128 C256,57.3075 198.6925,0 128,0 C57.3075,0 0,57.3075 0,128 C0,191.8885 46.80775,244.8425 108,254.445 L108,165 L75.5,165 L75.5,128 L108,128 L108,99.8 C108,67.72 127.1095,50 156.3475,50 C170.35175,50 185,52.5 185,52.5 L185,84 L168.8595,84 C152.95875,84 148,93.86675 148,103.98925 L148,128 L183.5,128 L177.825,165 L148,165 L148,254.445 C209.19225,244.8425 256,191.8885 256,128" fill="#1877F2"></path>
        <path d="M177.825,165 L183.5,128 L148,128 L148,103.98925 C148,93.86675 152.95875,84 168.8595,84 L185,84 L185,52.5 C185,52.5 170.35175,50 156.3475,50 C127.1095,50 108,67.72 108,99.8 L108,128 L75.5,128 L75.5,165 L108,165 L108,254.445 C114.51675,255.4675 121.196,256 128,256 C134.804,256 141.48325,255.4675 148,254.445 L148,165 L177.825,165" fill="#FFFFFF"></path>
    </g>
</svg>
"""


class GetLongLivedAccessTokenError(Exception):
    pass


class FacebookOAuth2(BaseOAuth2[Dict[str, Any]]):
    display_name = "Facebook"
    logo_svg = LOGO_SVG

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scopes: Optional[List[str]] = BASE_SCOPES,
        name: str = "facebook",
    ):
        super().__init__(
            client_id,
            client_secret,
            AUTHORIZE_ENDPOINT,
            ACCESS_TOKEN_ENDPOINT,
            name=name,
            base_scopes=scopes,
        )

    async def get_long_lived_access_token(self, token: str):
        async with self.get_httpx_client() as client:
            response = await client.post(
                self.access_token_endpoint,
                data={
                    "grant_type": "fb_exchange_token",
                    "fb_exchange_token": token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )

            data = cast(Dict[str, Any], response.json())

            if response.status_code >= 400:
                raise GetLongLivedAccessTokenError(data)

            return OAuth2Token(data)

    async def get_id_email(self, token: str) -> Tuple[str, Optional[str]]:
        async with self.get_httpx_client() as client:
            response = await client.get(
                PROFILE_ENDPOINT,
                params={"fields": "id,email", "access_token": token},
            )

            if response.status_code >= 400:
                raise GetIdEmailError(response.json())

            data = cast(Dict[str, Any], response.json())

            return data["id"], data.get("email")
