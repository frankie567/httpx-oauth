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

        super().__init__(
            client_id,
            client_secret,
            self.openid_configuration["authorization_endpoint"],
            self.openid_configuration["token_endpoint"],
            token_endpoint if refresh_token_supported else None,
            self.openid_configuration.get("revocation_endpoint"),
            name,
            base_scopes,
        )

    async def get_id_email(self, token: str) -> Tuple[str, Optional[str]]:
        async with self.get_httpx_client() as client:
            response = await client.get(
                self.openid_configuration["userinfo_endpoint"],
                headers={**self.request_headers, "Authorization": f"Bearer {token}"},
            )

            if response.status_code >= 400:
                raise GetIdEmailError(response.json())

            data: Dict[str, Any] = response.json()

            return str(data["sub"]), data.get("email")
