from typing import Any, Dict, List, Optional, Tuple

import httpx

from httpx_oauth.errors import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2, OAuth2Error

BASE_SCOPES = ["openid", "email"]


class OpenIDConfigurationError(OAuth2Error):
    pass


class OpenID(BaseOAuth2[Dict[str, Any]]):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        openid_configuration_endpoint: str,
        name: str = "openid",
        base_scopes: Optional[List[str]] = BASE_SCOPES,
    ):
        with httpx.Client() as client:
            response = client.get(openid_configuration_endpoint)
            if response.status_code >= 400:
                raise OpenIDConfigurationError(response.json())
            self.openid_configuration: Dict[str, Any] = response.json()

        token_endpoint = self.openid_configuration["token_endpoint"]
        refresh_token_supported = "refresh_token" in self.openid_configuration.get(
            "grant_types_supported", []
        )
        revocation_endpoint = self.openid_configuration.get("revocation_endpoint")
        token_endpoint_auth_methods_supported = self.openid_configuration.get(
            "token_endpoint_auth_methods_supported", ["client_secret_basic"]
        )
        revocation_endpoint_auth_methods_supported = self.openid_configuration.get(
            "revocation_endpoint_auth_methods_supported", ["client_secret_basic"]
        )

        super().__init__(
            client_id,
            client_secret,
            self.openid_configuration["authorization_endpoint"],
            token_endpoint,
            token_endpoint if refresh_token_supported else None,
            revocation_endpoint,
            name=name,
            base_scopes=base_scopes,
            token_endpoint_auth_method=token_endpoint_auth_methods_supported[0],
            revocation_endpoint_auth_method=revocation_endpoint_auth_methods_supported[
                0
            ]
            if revocation_endpoint
            else None,
        )

    async def get_id_email(self, token: str) -> Tuple[str, Optional[str]]:
        async with self.get_httpx_client() as client:
            response = await client.get(
                self.openid_configuration["userinfo_endpoint"],
                headers={**self.request_headers, "Authorization": f"Bearer {token}"},
            )

            if response.status_code >= 400:
                raise GetIdEmailError(response=response)

            data: Dict[str, Any] = response.json()

            return str(data["sub"]), data.get("email")
