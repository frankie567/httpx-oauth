# File: httpx_oauth/clients/apple.py

import time
from typing import Optional

import jwt  # PyJWT or any library that can sign JWTs

from httpx_oauth.clients.openid import OpenID
from httpx_oauth.oauth2 import OAuth2Token

APPLE_OPENID_CONFIG = "https://appleid.apple.com/.well-known/openid-configuration"
# The default OIDC scopes. Apple's docs generally require "openid" and "email".
# "name" scope is often used to request the user's name on first login.
BASE_SCOPES = ["openid", "email", "name"]


class AppleOAuthError(Exception):
    """Errors raised by Apple OAuth client."""

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
        token_ttl_seconds: int = 5 * 30 * 24 * 3600,  # ~5 months
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

        # Generate a short-lived client_secret (JWT) signed with your Apple key.
        client_secret_jwt = self._generate_apple_client_secret(
            client_id=client_id,
            team_id=team_id,
            key_id=key_id,
            private_key=private_key,
            issuer=issuer,
            token_lifetime=token_ttl_seconds,
        )

        super().__init__(
            client_id=client_id,
            client_secret=client_secret_jwt,  # The signed JWT
            openid_configuration_endpoint=APPLE_OPENID_CONFIG,
            name=name,
            base_scopes=base_scopes,
        )

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

    def get_id_email_from_id_token(
        self, token: OAuth2Token
    ) -> tuple[str, Optional[str]]:
        """
        Get user ID and email from Apple ID token.

        Apple does not have a userinfo endpoint, so we need to decode the ID token
        ourselves.
        """
        id_token = token.get("id_token")
        if not id_token:
            raise AppleOAuthError(AppleOAuthError.NO_ID_TOKEN)

        claims = jwt.decode(id_token, options={"verify_signature": False})

        user_id = claims.get("sub")
        if not user_id:
            raise AppleOAuthError(AppleOAuthError.NO_SUBJECT)

        email = claims.get("email")
        return user_id, email

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
            # Apple docs typically say "ES256" for the .p8 keys from Apple.
            "alg": "ES256",
        }
        payload = {
            "iss": team_id,
            "iat": now,
            "exp": now + token_lifetime,
            "aud": issuer,
            "sub": client_id,
        }

        # Using PyJWT (pip install PyJWT).
        # If your Apple private key is RSA, you'd set algorithm="RS256".
        token = jwt.encode(
            payload,
            private_key,
            algorithm="ES256",
            headers=headers,
        )

        return token
