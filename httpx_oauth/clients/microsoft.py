from typing import Any, Dict, List, Optional, Tuple, cast

from httpx_oauth.exceptions import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2

AUTHORIZE_ENDPOINT = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
ACCESS_TOKEN_ENDPOINT = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
BASE_SCOPES = ["User.Read"]
PROFILE_ENDPOINT = "https://graph.microsoft.com/v1.0/me"


LOGO_SVG = """
<svg width="100%" height="100%" viewBox="0 0 110 110" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xml:space="preserve" xmlns:serif="http://www.serif.com/" style="fill-rule:evenodd;clip-rule:evenodd;stroke-linejoin:round;stroke-miterlimit:2;">
    <rect x="0" y="0" width="51.927" height="51.927" style="fill:rgb(241,81,27);fill-rule:nonzero;"/>
    <rect x="57.334" y="0" width="51.926" height="51.927" style="fill:rgb(128,204,40);fill-rule:nonzero;"/>
    <rect x="0" y="57.354" width="51.925" height="51.927" style="fill:rgb(0,173,239);fill-rule:nonzero;"/>
    <rect x="57.334" y="57.354" width="51.926" height="51.927" style="fill:rgb(251,188,9);fill-rule:nonzero;"/>
</svg>
"""


class MicrosoftGraphOAuth2(BaseOAuth2[Dict[str, Any]]):
    """OAuth2 client for Microsoft Graph API."""

    display_name = "Microsoft"
    logo_svg = LOGO_SVG

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tenant: str = "common",
        scopes: Optional[List[str]] = BASE_SCOPES,
        name: str = "microsoft",
    ):
        """
        Args:
            client_id: The client ID provided by the OAuth2 provider.
            client_secret: The client secret provided by the OAuth2 provider.
            tenant: The tenant to use for the authorization URL.
            scopes: The default scopes to be used in the authorization URL.
            name: A unique name for the OAuth2 client.
        """
        access_token_endpoint = ACCESS_TOKEN_ENDPOINT.format(tenant=tenant)
        super().__init__(
            client_id,
            client_secret,
            AUTHORIZE_ENDPOINT.format(tenant=tenant),
            access_token_endpoint,
            access_token_endpoint,
            name=name,
            base_scopes=scopes,
            token_endpoint_auth_method="client_secret_post",
        )

    def get_authorization_url(
        self, redirect_uri, state=None, scope=None, extras_params=None
    ):
        if extras_params is None:
            extras_params = {}
        extras_params["response_mode"] = "query"
        return super().get_authorization_url(
            redirect_uri, state=state, scope=scope, extras_params=extras_params
        )

    async def get_id_email(self, token: str) -> Tuple[str, Optional[str]]:
        async with self.get_httpx_client() as client:
            response = await client.get(
                PROFILE_ENDPOINT,
                headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code >= 400:
                raise GetIdEmailError(response=response)

            data = cast(Dict[str, Any], response.json())

            return data["id"], data["userPrincipalName"]
