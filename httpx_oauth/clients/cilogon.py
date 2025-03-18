from typing import List, Optional, Final

from httpx_oauth.clients.openid import OpenID


BASE_SCOPES: Final = ["openid", "email"]
AVAILABLE_SCOPES: Final = ["openid", "email", "profile", "org.cilogon.userinfo"]

CILOGON_DOMAIN: Final = "cilogon.org"


class CILogonOAuth2(OpenID):
    """
    Academic OIDC service for the US research and education community.

    See https://www.cilogon.org/oidc for more information.
    """
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scopes: Optional[List[str]] = BASE_SCOPES,
        name: str = "CILogon",
    ):
        super().__init__(
            client_id,
            client_secret,
            f"https://{CILOGON_DOMAIN}/.well-known/openid-configuration",
            name=name,
            base_scopes=scopes,
        )
