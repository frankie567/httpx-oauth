from typing import Any, Dict, List, Optional, Tuple, cast

from httpx_oauth.exceptions import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2, OAuth2Token

AUTHORIZE_ENDPOINT = "https://www.linkedin.com/oauth/v2/authorization"
ACCESS_TOKEN_ENDPOINT = "https://www.linkedin.com/oauth/v2/accessToken"
BASE_SCOPES = ["r_emailaddress", "r_liteprofile", "r_basicprofile"]
PROFILE_ENDPOINT = "https://api.linkedin.com/v2/me"
EMAIL_ENDPOINT = "https://api.linkedin.com/v2/emailAddress"


LOGO_SVG = """
<svg width="256px" height="256px" viewBox="0 0 256 256" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" preserveAspectRatio="xMidYMid">
    <g>
        <path d="M218.123122,218.127392 L180.191928,218.127392 L180.191928,158.724263 C180.191928,144.559023 179.939053,126.323993 160.463756,126.323993 C140.707926,126.323993 137.685284,141.757585 137.685284,157.692986 L137.685284,218.123441 L99.7540894,218.123441 L99.7540894,95.9665207 L136.168036,95.9665207 L136.168036,112.660562 L136.677736,112.660562 C144.102746,99.9650027 157.908637,92.3824528 172.605689,92.9280076 C211.050535,92.9280076 218.138927,118.216023 218.138927,151.114151 L218.123122,218.127392 Z M56.9550587,79.2685282 C44.7981969,79.2707099 34.9413443,69.4171797 34.9391618,57.260052 C34.93698,45.1029244 44.7902948,35.2458562 56.9471566,35.2436736 C69.1040185,35.2414916 78.9608713,45.0950217 78.963054,57.2521493 C78.9641017,63.090208 76.6459976,68.6895714 72.5186979,72.8184433 C68.3913982,76.9473153 62.7929898,79.26748 56.9550587,79.2685282 M75.9206558,218.127392 L37.94995,218.127392 L37.94995,95.9665207 L75.9206558,95.9665207 L75.9206558,218.127392 Z M237.033403,0.0182577091 L18.8895249,0.0182577091 C8.57959469,-0.0980923971 0.124827038,8.16056231 -0.001,18.4706066 L-0.001,237.524091 C0.120519052,247.839103 8.57460631,256.105934 18.8895249,255.9977 L237.033403,255.9977 C247.368728,256.125818 255.855922,247.859464 255.999,237.524091 L255.999,18.4548016 C255.851624,8.12438979 247.363742,-0.133792868 237.033403,0.000790807055" fill="#0A66C2"></path>
    </g>
</svg>
"""


class LinkedInOAuth2(BaseOAuth2[Dict[str, Any]]):
    """OAuth2 client for LinkedIn."""

    display_name = "LinkedIn"
    logo_svg = LOGO_SVG

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scopes: Optional[List[str]] = BASE_SCOPES,
        name: str = "linkedin",
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
            ACCESS_TOKEN_ENDPOINT,
            name=name,
            base_scopes=scopes,
            token_endpoint_auth_method="client_secret_post",
        )

    async def refresh_token(self, refresh_token: str) -> OAuth2Token:
        """
        Requests a new access token using a refresh token.

        !!! warning
            Only available for [selected partners](https://docs.microsoft.com/en-us/linkedin/shared/authentication/programmatic-refresh-tokens).

        Args:
            refresh_token: The refresh token.

        Returns:
            An access token response dictionary.

        Raises:
            RefreshTokenError: An error occurred while refreshing the token.
            RefreshTokenNotSupportedError: The provider does not support token refresh.

        Examples:
            ```py
            access_token = await client.refresh_token("REFRESH_TOKEN")
            ```
        """
        return await super().refresh_token(refresh_token)  # pragma: no cover

    async def get_id_email(self, token: str) -> Tuple[str, Optional[str]]:
        async with self.get_httpx_client() as client:
            profile_response = await client.get(
                PROFILE_ENDPOINT,
                headers={"Authorization": f"Bearer {token}"},
                params={"projection": "(id)"},
            )

            if profile_response.status_code >= 400:
                raise GetIdEmailError(response=profile_response)

            email_response = await client.get(
                EMAIL_ENDPOINT,
                headers={"Authorization": f"Bearer {token}"},
                params={"q": "members", "projection": "(elements*(handle~))"},
            )

            if email_response.status_code >= 400:
                raise GetIdEmailError(response=email_response)

            profile_data = cast(Dict[str, Any], profile_response.json())
            user_id = profile_data["id"]

            email_data = cast(Dict[str, Any], email_response.json())
            user_email = email_data["elements"][0]["handle~"]["emailAddress"]

            return user_id, user_email
