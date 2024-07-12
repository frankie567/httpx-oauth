from typing import Any, Dict, List, Optional, Tuple

import httpx

from httpx_oauth.exceptions import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2, OAuth2RequestError

BASE_SCOPES = ["openid", "email"]


class OpenIDConfigurationError(OAuth2RequestError):
    """
    Raised when an error occurred while fetching the OpenID configuration.
    """


class OpenID(BaseOAuth2[Dict[str, Any]]):
    """
    Generic client for providers following the [OpenID Connect protocol](https://openid.net/connect/).

    Besides the Client ID and the Client Secret, you'll have to provide the OpenID configuration endpoint, allowing the client to discover the required endpoints automatically. By convention, it's usually served under the path `.well-known/openid-configuration`.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        openid_configuration_endpoint: str,
        name: str = "openid",
        base_scopes: Optional[List[str]] = BASE_SCOPES,
    ):
        """
        Args:
            client_id: The client ID provided by the OAuth2 provider.
            client_secret: The client secret provided by the OAuth2 provider.
            openid_configuration_endpoint: OpenID Connect discovery endpoint URL.
            name: A unique name for the OAuth2 client.
            base_scopes: The base scopes to be used in the authorization URL.

        Raises:
            OpenIDConfigurationError:
                An error occurred while fetching the OpenID configuration.

        Examples:
            ```py
            from httpx_oauth.clients.openid import OpenID

            client = OpenID("CLIENT_ID", "CLIENT_SECRET", "https://example.fief.dev/.well-known/openid-configuration")
            ``
        """
        with httpx.Client() as client:
            try:
                response = client.get(openid_configuration_endpoint)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise OpenIDConfigurationError(str(e), e.response) from e
            except httpx.HTTPError as e:
                raise OpenIDConfigurationError(str(e)) from e
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
