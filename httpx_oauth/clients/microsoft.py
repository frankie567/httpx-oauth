from typing import Any, Dict, Tuple, cast

import httpx

from httpx_oauth.errors import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2

AUTHORIZE_ENDPOINT = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
ACCESS_TOKEN_ENDPOINT = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
BASE_SCOPES = ["User.Read"]
PROFILE_ENDPOINT = "https://graph.microsoft.com/v1.0/me"


class MicrosoftGraphOAuth2(BaseOAuth2[Dict[str, Any]]):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tenant: str = "common",
        name: str = "microsoft",
    ):
        access_token_endpoint = ACCESS_TOKEN_ENDPOINT.format(tenant=tenant)
        super().__init__(
            client_id,
            client_secret,
            AUTHORIZE_ENDPOINT.format(tenant=tenant),
            access_token_endpoint,
            access_token_endpoint,
            name=name,
            base_scopes=BASE_SCOPES,
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

    async def get_id_email(self, token: str) -> Tuple[str, str]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                PROFILE_ENDPOINT, headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code >= 400:
                raise GetIdEmailError(response.json())

            data = cast(Dict[str, Any], response.json())

            return data["id"], data["userPrincipalName"]
