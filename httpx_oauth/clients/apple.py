import time
from typing import Any, Optional

import jwt

from httpx_oauth.clients.openid import OpenID
from httpx_oauth.oauth2 import OAuth2Token, RefreshTokenError

APPLE_OPENID_CONFIG = "https://appleid.apple.com/.well-known/openid-configuration"
# The default OIDC scopes. Apple's docs generally require "openid" and "email".
# "name" scope is often used to request the user's name on first login.
BASE_SCOPES = ["openid", "email", "name"]

LOGO_SVG = """
<svg width="256px" height="256px" viewBox="0 0 24 24" version="1.1" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid">
    <title>Apple</title>
    <g>
        <path d="M18.71 19.5C17.88 20.74 17 21.95 15.66 21.97C14.32 22 13.89 21.18 12.37 21.18C10.84 21.18 10.37 21.95 9.09997 22C7.78997 22.05 6.79997 20.68 5.95997 19.47C4.24997 17 2.93997 12.45 4.69997 9.39C5.56997 7.87 7.12997 6.91 8.81997 6.88C10.1 6.86 11.32 7.75 12.11 7.75C12.89 7.75 14.37 6.68 15.92 6.84C16.57 6.87 18.39 7.1 19.56 8.82C19.47 8.88 17.39 10.1 17.41 12.63C17.44 15.65 20.06 16.66 20.09 16.67C20.06 16.74 19.67 18.11 18.71 19.5ZM13 3.5C13.73 2.67 14.94 2.04 15.94 2C16.07 3.17 15.6 4.35 14.9 5.19C14.21 6.04 13.07 6.7 11.95 6.61C11.8 5.46 12.36 4.26 13 3.5Z"/>
    </g>
</svg>
"""


class AppleOAuthError(Exception):
    """Errors raised by Apple OAuth client."""

    NO_ACCESS_TOKEN = "No access token found, you need to call get_access_token first"
    NO_ID_TOKEN = "No ID token found"
    NO_SUBJECT = "No subject claim found"


class AppleOAuth2(OpenID):
    """
    OAuth2 client for Sign In with Apple via OpenID Connect.

    Apple requires a signed JWT as the `client_secret`. This class
    generates that JWT on-the-fly when instantiated.

    References:
    - https://developer.apple.com/documentation/sign_in_with_apple
    - https://appleid.apple.com/.well-known/openid-configuration
    """

    display_name = "Apple"
    logo_svg = LOGO_SVG

    # The token response from Apple, see get_access_token for more details
    oauth2_token: OAuth2Token | None

    def __init__(
        self,
        client_id: str,
        team_id: str,
        key_id: str,
        private_key: str,
        *,
        issuer: str = "https://appleid.apple.com",
        base_scopes: Optional[list[str]] = None,
        name: str = "apple",
        # Apple allows a client_secret (JWT) up to 6 months validity
        client_secret_ttl_seconds: int = 5 * 30 * 24 * 3600,  # ~5 months
    ):
        """
        Args:
            client_id: For Apple, this is typically your "Services ID"
            team_id: Your Apple Developer Team ID
            key_id: The Key ID (from the private key in Apple Dev Portal)
            private_key: The full content of the .p8 private key
            issuer: Always "https://appleid.apple.com" for Apple
            base_scopes: Defaults to ["openid", "email", "name"]
            name: A unique name for the OAuth2 client
            token_ttl_seconds: How long the generated client_secret JWT remains valid
        """
        if base_scopes is None:
            base_scopes = BASE_SCOPES

        # Save the parameters for use when regenerating the client_secret JWT.
        self._client_id = client_id
        self._team_id = team_id
        self._key_id = key_id
        self._private_key = private_key
        self._issuer = issuer
        self._base_scopes = base_scopes
        self._name = name
        self._client_secret_ttl_seconds = client_secret_ttl_seconds

        # Generate a short-lived client_secret (JWT) signed with your Apple key.
        self.regenerate_client_secret_at = time.time() + client_secret_ttl_seconds
        client_secret_jwt = self._generate_apple_client_secret(
            client_id=client_id,
            team_id=team_id,
            key_id=key_id,
            private_key=private_key,
            issuer=issuer,
            token_lifetime=client_secret_ttl_seconds,
        )

        super().__init__(
            client_id=client_id,
            client_secret=client_secret_jwt,  # The signed JWT
            openid_configuration_endpoint=APPLE_OPENID_CONFIG,
            name=name,
            base_scopes=base_scopes,
            callback_method="POST",
        )

        self.oauth2_token = None

    async def get_authorization_url(
        self, redirect_uri, state=None, scope=None, extras_params=None
    ):
        if extras_params is None:
            extras_params = {}
        extras_params["response_mode"] = "form_post"
        super_url = await super().get_authorization_url(
            redirect_uri, state=state, scope=scope, extras_params=extras_params
        )
        return super_url

    # When building a request, regenerate the client secret JWT if it is expired.
    def build_request(self, client, method, url, *, auth_method=None, data=None):
        self._regenerate_client_secret()
        return super().build_request(
            client, method, url, auth_method=auth_method, data=data
        )

    async def get_access_token(
        self, code: str, redirect_uri: str, code_verifier: Optional[str] = None
    ) -> OAuth2Token:
        """
        Get access token from Apple.

        Apple does not have a userinfo endpoint, so we need to store the raw token
        response which includes the id_token in memory, so that future calls to
        get_id_email can use it.
        """
        token = await super().get_access_token(code, redirect_uri, code_verifier)
        self.oauth2_token = token

        return token

    async def refresh_token(self, refresh_token: str) -> OAuth2Token:
        """
        Requests a new access token using a refresh token.

        Args:
            refresh_token: The refresh token.

        Returns:
            An access token response dictionary.

        Raises:
            RefreshTokenError: An error occurred while refreshing the token.

        Examples:
            ```py
            access_token = await apple_client.refresh_token("REFRESH_TOKEN")
            ```
        """
        async with self.get_httpx_client() as client:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }

            request, auth = self.build_request(
                client,
                "POST",
                "https://appleid.apple.com/auth/token",
                auth_method=self.token_endpoint_auth_method,
                data=data,
            )

            response = await self.send_request(
                client, request, auth, exc_class=RefreshTokenError
            )
            data = self.get_json(response, exc_class=RefreshTokenError)
            token = OAuth2Token(data)
            self.oauth2_token = token
            return token

    # Apple does not have a userinfo endpoint, so we raise a NotImplementedError.
    def get_profile(self, token: str) -> dict[str, Any]:
        raise NotImplementedError()

    async def get_id_email(self, token: str) -> tuple[str, Optional[str]]:
        """
        Returns the id and the email (if available) of the authenticated user
        from the ID token.

        Apple does not provide a userinfo endpoint, so we decode the ID token instead.
        The ID token must have been saved during the initial token request.

        Args:
            token: The access token. Unused, but required by the OAuth2 client interface.

        Returns:
            A tuple with the id and the email of the authenticated user.

        Raises:
            httpx_oauth.exceptions.GetIdEmailError:
                An error occurred while getting the id and email.
            AppleOAuthError:
                The ID token was missing or invalid.
        """
        if self.oauth2_token is None:
            raise AppleOAuthError(AppleOAuthError.NO_ACCESS_TOKEN)

        id_token = self.oauth2_token.get("id_token")
        if not id_token:
            raise AppleOAuthError(AppleOAuthError.NO_ID_TOKEN)

        # We don't verify the signature here. This comes as part of the access token
        # in the OAuth redirect response, where we use the OAuth2 state to verify the request.
        claims = jwt.decode(id_token, options={"verify_signature": False})

        user_id = claims.get("sub")
        if not user_id:
            raise AppleOAuthError(AppleOAuthError.NO_SUBJECT)

        email = claims.get("email")
        return user_id, email

    # Regenerate the client secret JWT if it is expired.
    def _regenerate_client_secret(self):
        if time.time() > self.regenerate_client_secret_at:
            self.regenerate_client_secret_at = (
                time.time() + self._client_secret_ttl_seconds
            )
            self.client_secret = self._generate_apple_client_secret(
                client_id=self._client_id,
                team_id=self._team_id,
                key_id=self._key_id,
                private_key=self._private_key,
                issuer=self._issuer,
                token_lifetime=self._client_secret_ttl_seconds,
            )

    def _generate_apple_client_secret(
        self,
        client_id: str,
        team_id: str,
        key_id: str,
        private_key: str,
        issuer: str,
        token_lifetime: int,
    ) -> str:
        """
        Create a JWT for use as the `client_secret` in Apple OAuth.

        Apple-specific claims:
          - `iss` is your 10-character Team ID
          - `sub` is your Services ID (same as client_id)
          - `aud` is always "https://appleid.apple.com"
        """
        now = int(time.time())
        headers = {
            "kid": key_id,
            "alg": "ES256",
        }
        payload = {
            "iss": team_id,
            "iat": now,
            "exp": now + token_lifetime,
            "aud": issuer,
            "sub": client_id,
        }

        token = jwt.encode(
            payload,
            private_key,
            algorithm="ES256",
            headers=headers,
        )

        return token
