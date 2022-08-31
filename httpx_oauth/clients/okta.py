from typing import List, Optional

from httpx_oauth.clients.openid import OpenID

BASE_SCOPES = ["openid", "email"]


class OktaOAuth2(OpenID):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        okta_domain: str,
        scopes: Optional[List[str]] = BASE_SCOPES,
        name: str = "okta",
    ):
        super().__init__(
            client_id,
            client_secret,
            f"https://{okta_domain}/.well-known/openid-configuration",
            name=name,
            base_scopes=scopes,
        )
