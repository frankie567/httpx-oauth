import json
from typing import Any, Dict, List, Optional, Tuple, cast

from httpx_oauth.exceptions import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2

AUTHORIZE_ENDPOINT = "https://kauth.kakao.com/oauth/authorize"
ACCESS_TOKEN_ENDPOINT = "https://kauth.kakao.com/oauth/token"
REFRESH_TOKEN_ENDPOINT = ACCESS_TOKEN_ENDPOINT
REVOKE_TOKEN_ENDPOINT = "https://kapi.kakao.com/v1/user/unlink"
PROFILE_ENDPOINT = "https://kapi.kakao.com/v2/user/me"
BASE_SCOPES = ["profile_nickname", "account_email"]
PROFILE_PROPERTIES = ["kakao_account.email"]

LOGO_SVG = """
<svg stroke-width="0" role="img" viewBox="0 0 24 24" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg">
  <path d="M3.0743 10.4403l.655.4728-1.6101 2.0192 1.8647 2.2373-.646.5004-2.201-2.6924zm-2.2376 5.102H0V8.5121l.8367-.182zm20.944-4.3837c-.4364 0-.7715.1637-1.0049.4912-.2338.3274-.3505.8064-.3505 1.437 0 .6247.1167 1.096.3505 1.4143.2334.3183.5685.4775 1.0049.4775.4423 0 .7804-.1593 1.0143-.4775.2332-.3182.35-.7896.35-1.4142 0-.6307-.1168-1.1097-.35-1.4371-.234-.3275-.572-.4912-1.0143-.4912m0-.673c.691 0 1.234.2245 1.6277.673.3944.4488.5916 1.0915.5916 1.9283 0 .8244-.1955 1.4583-.5868 1.901-.3909.4422-.9356.6637-1.6325.6637-.691 0-1.234-.2215-1.6277-.6638-.3944-.4426-.5916-1.0765-.5916-1.901 0-.8367.1984-1.4794.5957-1.9282.3973-.4485.9385-.673 1.6236-.673m-5.534 4.4658a1.496 1.496 0 0 0 .3576-.0456 2.8804 2.8804 0 0 0 .3713-.1181 2.0066 2.0066 0 0 0 .3488-.1774 2.0778 2.0778 0 0 0 .2895-.2229v-1.1641h-.8693c-.441 0-.7626.0758-.9645.2274-.2025.1516-.3031.391-.3031.7185 0 .5214.2563.7822.7697.7822m-1.5704-.7458c0-.5032.1682-.887.5045-1.1504.337-.2638.826-.396 1.4691-.396h.964v-.3182c0-.77-.3393-1.155-1.0185-1.155-.2184 0-.447.0304-.6869.091-.2398.0608-.4594.1365-.659.2274l-.2457-.5913c.2487-.1394.517-.2469.8047-.323.2878-.0754.5685-.1136.8414-.1136 1.176 0 1.7646.6276 1.7646 1.8826v3.1833h-.6188l-.1-.5457c-.2488.2001-.5134.3547-.796.464-.2817.1092-.55.1637-.8046.1637-.4429 0-.7899-.1258-1.0416-.3775-.2515-.2517-.3772-.5987-.3772-1.0413m-1.6508-3.7653l.655.4728-1.6095 2.0192 1.864 2.2373-.6454.5004-2.201-2.6924zm-2.237 5.102h-.8367V8.5121l.8368-.182zm-4.4936-.5909c.1148 0 .2339-.0151.3576-.0456a2.8794 2.8794 0 0 0 .3713-.1181 1.9842 1.9842 0 0 0 .3488-.1774 2.0477 2.0477 0 0 0 .29-.2229v-1.1641h-.8698c-.4404 0-.762.0758-.9645.2274-.202.1516-.3031.391-.3031.7185 0 .5214.2563.7822.7697.7822m-1.5704-.7458c0-.5032.1682-.887.5052-1.1504.3363-.2638.826-.396 1.4684-.396h.9646v-.3182c0-.77-.3399-1.155-1.019-1.155-.218 0-.4471.0304-.6863.091-.2398.0608-.4595.1365-.6597.2274l-.2457-.5913c.2487-.1394.517-.2469.8053-.323.2878-.0754.5684-.1136.8408-.1136 1.1766 0 1.7646.6276 1.7646 1.8826v3.1833h-.6182l-.1001-.5457c-.2487.2001-.514.3547-.7958.464-.282.1092-.5501.1637-.8053.1637-.4423 0-.7893-.1258-1.041-.3775-.2516-.2517-.3778-.5987-.3778-1.0413Z"></path>
</svg>
"""


class KakaoOAuth2(BaseOAuth2[Dict[str, Any]]):
    """OAuth2 client for Kakao."""

    display_name = "Kakao"
    logo_svg = LOGO_SVG

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scopes: Optional[List[str]] = BASE_SCOPES,
        name: str = "kakao",
    ):
        """
        Args:
            client_id: The client ID provided by the OAuth2 provider.
            client_secret: The client secret provided by the OAuth2 provider.
            scopes: The default scopes to be used in the authorization URL.
            name: A unique name for the OAuth2 client.
        """
        super().__init__(
            client_id,
            client_secret,
            AUTHORIZE_ENDPOINT,
            ACCESS_TOKEN_ENDPOINT,
            refresh_token_endpoint=REFRESH_TOKEN_ENDPOINT,
            revoke_token_endpoint=REVOKE_TOKEN_ENDPOINT,
            name=name,
            base_scopes=scopes,
            token_endpoint_auth_method="client_secret_post",
            revocation_endpoint_auth_method="client_secret_post",
        )

    async def get_id_email(self, token: str) -> Tuple[str, Optional[str]]:
        async with self.get_httpx_client() as client:
            response = await client.post(
                PROFILE_ENDPOINT,
                params={"property_keys": json.dumps(PROFILE_PROPERTIES)},
                headers={**self.request_headers, "Authorization": f"Bearer {token}"},
            )

            if response.status_code >= 400:
                raise GetIdEmailError(response=response)

            payload = cast(Dict[str, Any], response.json())
            account_id = str(payload["id"])
            email = payload["kakao_account"].get("email")
            return account_id, email
