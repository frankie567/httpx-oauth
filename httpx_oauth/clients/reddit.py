from typing import Any, Dict, List, Optional, Tuple, cast

import httpx

from httpx_oauth.exceptions import GetIdEmailError
from httpx_oauth.oauth2 import (
    BaseOAuth2,
    GetAccessTokenError,
    OAuth2Token,
)

AUTHORIZE_ENDPOINT = "https://www.reddit.com/api/v1/authorize"
ACCESS_TOKEN_ENDPOINT = "https://www.reddit.com/api/v1/access_token"
REFRESH_ENDPOINT = ACCESS_TOKEN_ENDPOINT
REVOKE_ENDPOINT = "https://www.reddit.com/api/v1/revoke_token"
IDENTITY_ENDPOINT = "https://oauth.reddit.com/api/v1/me"

BASE_SCOPES = ["identity"]


LOGO_SVG = """
<svg width="256px" height="256px" viewBox="0 0 256 256" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" preserveAspectRatio="xMidYMid">
    <g>
        <circle fill="#FF4500" cx="128" cy="128" r="128"></circle>
        <path d="M213.149867,129.220267 C213.149867,118.843733 204.758756,110.603378 194.532978,110.603378 C189.498311,110.603378 184.918756,112.585956 181.562311,115.791644 C168.745244,106.635378 151.195022,100.6848 131.662222,99.9224889 L140.206933,59.9409778 L167.980089,65.8915556 C168.287289,72.9116444 174.084267,78.5578667 181.257956,78.5578667 C188.5824,78.5578667 194.532978,72.6072889 194.532978,65.28 C194.532978,57.9555556 188.5824,52.0049778 181.257956,52.0049778 C176.069689,52.0049778 171.490133,55.0570667 169.353956,59.4830222 L138.377956,52.9208889 C137.462044,52.7672889 136.546133,52.9208889 135.934578,53.3788444 C135.172267,53.8368 134.714311,54.5991111 134.563556,55.5150222 L125.100089,100.073244 C105.262933,100.6848 87.4083556,106.635378 74.4376889,115.945244 C71.0812444,112.739556 66.5016889,110.756978 61.4670222,110.756978 C51.0904889,110.756978 42.8501333,119.148089 42.8501333,129.373867 C42.8501333,137.002667 47.4268444,143.4112 53.8382222,146.312533 C53.5310222,148.141511 53.3802667,149.973333 53.3802667,151.958756 C53.3802667,180.644978 86.7996444,203.995022 128.001422,203.995022 C169.2032,203.995022 202.622578,180.798578 202.622578,151.958756 C202.622578,150.126933 202.468978,148.141511 202.164622,146.312533 C208.573156,143.4112 213.149867,136.849067 213.149867,129.220267 Z M85.2721778,142.495289 C85.2721778,135.170844 91.2227556,129.220267 98.5500444,129.220267 C105.874489,129.220267 111.825067,135.170844 111.825067,142.495289 C111.825067,149.819733 105.874489,155.773156 98.5500444,155.773156 C91.2227556,155.923911 85.2721778,149.819733 85.2721778,142.495289 Z M159.588978,177.746489 C150.432711,186.902756 133.036089,187.514311 128.001422,187.514311 C122.813156,187.514311 105.416533,186.749156 96.4110222,177.746489 C95.04,176.372622 95.04,174.236444 96.4110222,172.862578 C97.7848889,171.491556 99.9210667,171.491556 101.294933,172.862578 C107.094756,178.6624 119.303111,180.644978 128.001422,180.644978 C136.699733,180.644978 149.058844,178.6624 154.705067,172.862578 C156.078933,171.491556 158.215111,171.491556 159.588978,172.862578 C160.809244,174.236444 160.809244,176.372622 159.588978,177.746489 Z M157.1456,155.923911 C149.821156,155.923911 143.870578,149.973333 143.870578,142.648889 C143.870578,135.324444 149.821156,129.373867 157.1456,129.373867 C164.472889,129.373867 170.423467,135.324444 170.423467,142.648889 C170.423467,149.819733 164.472889,155.923911 157.1456,155.923911 Z" fill="#FFFFFF" fill-rule="nonzero"></path>
    </g>
</svg>
"""


class RedditOAuth2(BaseOAuth2[Dict[str, Any]]):
    """OAuth2 client for Reddit."""

    display_name = "Reddit"
    logo_svg = LOGO_SVG

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scopes: Optional[List[str]] = None,
        name: str = "reddit",
    ):
        """
        Args:
            client_id: The client ID provided by the OAuth2 provider.
            client_secret: The client secret provided by the OAuth2 provider.
            scopes: The default scopes to be used in the authorization URL.
            name: A unique name for the OAuth2 client.
        """
        if scopes is None:
            scopes = BASE_SCOPES

        super().__init__(
            client_id,
            client_secret,
            AUTHORIZE_ENDPOINT,
            ACCESS_TOKEN_ENDPOINT,
            REFRESH_ENDPOINT,
            REVOKE_ENDPOINT,
            name=name,
            base_scopes=scopes,
            token_endpoint_auth_method="client_secret_basic",
            revocation_endpoint_auth_method="client_secret_basic",
        )

    async def get_access_token(
        self, code: str, redirect_uri: str, code_verifier: Optional[str] = None
    ) -> OAuth2Token:
        oauth2_token = await super().get_access_token(code, redirect_uri, code_verifier)

        if "error" in oauth2_token:
            raise GetAccessTokenError(oauth2_token["error"])

        return oauth2_token

    async def get_id_email(self, token: str) -> Tuple[str, Optional[str]]:
        async with self.get_httpx_client() as client:
            headers = self.request_headers.copy()
            headers["Authorization"] = f"Bearer {token}"

            response = await client.get(
                IDENTITY_ENDPOINT,
                headers=headers,
            )

            # Reddit doesn't return any useful JSON in case of auth failures
            # on oauth.reddit.com endpoints, so we simulate our own
            if response.status_code != httpx.codes.OK:
                raise GetIdEmailError(response=response)

            data = cast(Dict[str, Any], response.json())
            return data["name"], None
