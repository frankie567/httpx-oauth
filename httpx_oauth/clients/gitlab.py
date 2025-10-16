from typing import Any, cast, override

import httpx
from httpx_oauth.exceptions import GetIdEmailError, GetProfileError
from httpx_oauth.oauth2 import BaseOAuth2, OAuth2Token, RefreshTokenError

# GitLab OAuth2 endpoints (for gitlab.com)
AUTHORIZE_ENDPOINT = "https://gitlab.com/oauth/authorize"
ACCESS_TOKEN_ENDPOINT = "https://gitlab.com/oauth/token"
REFRESH_TOKEN_ENDPOINT = "https://gitlab.com/oauth/token"
REVOKE_TOKEN_ENDPOINT = "https://gitlab.com/oauth/revoke"
BASE_SCOPES = ["read_user"]
PROFILE_ENDPOINT = "https://gitlab.com/api/v4/user"

LOGO_SVG = """
<svg width="256px" height="231px" viewBox="0 0 256 231" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" preserveAspectRatio="xMidYMid">
    <g>
        <path d="M128.075,236.075 L47.104,75.773 L47.104,75.773 L209.046,75.773 L209.046,75.773 L128.075,236.075 L128.075,236.075 Z" fill="#E24329"></path>
        <path d="M128.075,236.074 L47.104,75.772 L0.007,75.772 L128.075,236.074 Z" fill="#FC6D26"></path>
        <path d="M0.007,75.772 L0.007,75.772 L10.675,108.933 C11.398,111.134 12.878,113.032 14.823,114.278 L128.075,236.074 L0.007,75.772 Z" fill="#FCA326"></path>
        <path d="M0.007,75.772 L47.104,75.772 L25.465,17.847 C24.012,13.603 17.326,13.603 15.873,17.847 L0.007,75.772 Z" fill="#E24329"></path>
        <path d="M128.075,236.074 L209.046,75.772 L256.144,75.772 L128.075,236.074 Z" fill="#FC6D26"></path>
        <path d="M256.144,75.772 L256.144,75.772 L245.476,108.933 C244.752,111.134 243.273,113.032 241.327,114.278 L128.075,236.074 L256.144,75.772 Z" fill="#FCA326"></path>
        <path d="M256.144,75.772 L209.046,75.772 L230.685,17.847 C232.138,13.603 238.824,13.603 240.277,17.847 L256.144,75.772 Z" fill="#E24329"></path>
    </g>
</svg>
"""


class GitLabOAuth2(BaseOAuth2[dict[str, Any]]):
    """OAuth2 client for GitLab."""

    display_name: str = "GitLab"
    logo_svg: str = LOGO_SVG

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = "https://gitlab.com",  # to support self-hosted instances
        scopes: list[str] | None = BASE_SCOPES,
        name: str = "gitlab",
    ):
        """
        Args:
            client_id: The client ID provided by the OAuth2 provider.
            client_secret: The client secret provided by the OAuth2 provider.
            base_url: The base URL of the GitLab instance. Defaults to "https://gitlab.com".
            scopes: The default scopes to be used in the authorization URL.
            name: A unique name for the OAuth2 client.
        """
        base_url = base_url.rstrip("/")
        # Build endpoints based on base_url
        if base_url == "https://gitlab.com":
            # Use predefined constants for gitlab.com
            authorize_endpoint = AUTHORIZE_ENDPOINT
            access_token_endpoint = ACCESS_TOKEN_ENDPOINT
            refresh_token_endpoint = REFRESH_TOKEN_ENDPOINT
        else:
            # Build endpoints for custom GitLab instances
            authorize_endpoint = f"{base_url}/oauth/authorize"
            access_token_endpoint = f"{base_url}/oauth/token"
            refresh_token_endpoint = f"{base_url}/oauth/token"

        super().__init__(
            client_id,
            client_secret,
            authorize_endpoint,
            access_token_endpoint,
            refresh_token_endpoint,
            name=name,
            base_scopes=scopes,
            token_endpoint_auth_method="client_secret_post",
            revocation_endpoint_auth_method="client_secret_post",
        )

        self.base_url: str = base_url
        self._profile_endpoint: str = f"{base_url}/api/v4/user"

    async def refresh_token(self, refresh_token: str) -> OAuth2Token:
        """
        Requests a new access token using a refresh token.

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
        assert self.refresh_token_endpoint is not None
        async with self.get_httpx_client() as client:
            request, auth = self.build_request(
                client,
                "POST",
                self.refresh_token_endpoint,
                auth_method=self.token_endpoint_auth_method,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
            )
            response = await self.send_request(
                client, request, auth, exc_class=RefreshTokenError
            )

            data = self.get_json(response, exc_class=RefreshTokenError)

            # GitLab sends errors with a 200 status code in some cases
            if "error" in data:
                raise RefreshTokenError(cast(str, data["error"]), response)

            return OAuth2Token(data)

    @override
    async def get_profile(self, token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(
            headers={**self.request_headers, "Authorization": f"Bearer {token}"}
        ) as client:
            response = await client.get(self._profile_endpoint)

            if response.status_code >= 400:
                raise GetProfileError(response=response)

            return cast("dict[str, Any]", response.json())

    @override
    async def get_id_email(self, token: str) -> tuple[str, str | None]:
        """Returns the id and the email (if available) of the authenticated user
        from the API provider.

        Args:
            token: The access token.

        Returns:
            A tuple with the id and the email of the authenticated user.

        Raises:
            httpx_oauth.exceptions.GetIdEmailError:
                An error occurred while getting the id and email.

        Examples:
            ```py
            user_id, user_email = await client.get_id_email("TOKEN")
            ```
        """
        try:
            profile = await self.get_profile(token)
        except GetProfileError as e:
            raise GetIdEmailError(response=e.response) from e

        # GitLab returns numeric ID, convert to string
        user_id = str(profile["id"])
        email = profile.get("email")

        return user_id, email
