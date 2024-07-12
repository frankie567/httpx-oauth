from typing import List, Optional

from httpx_oauth.clients.openid import OpenID

BASE_SCOPES = ["openid", "email"]


class OktaOAuth2(OpenID):
    """OAuth2 client for Okta."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        okta_domain: str,
        scopes: Optional[List[str]] = BASE_SCOPES,
        name: str = "okta",
    ):
        """
        Args:
            client_id: The client ID provided by the OAuth2 provider.
            client_secret: The client secret provided by the OAuth2 provider.
            okta_domain: The Okta organization domain.
            scopes: The default scopes to be used in the authorization URL.
            name: A unique name for the OAuth2 client.
        """
        super().__init__(
            client_id,
            client_secret,
            f"https://{okta_domain}/.well-known/openid-configuration",
            name=name,
            base_scopes=scopes,
        )
