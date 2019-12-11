from typing import Any, Dict

from httpx_oauth.oauth2 import BaseOAuth2

AUTHORIZE_ENDPOINT = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
ACCESS_TOKEN_ENDPOINT = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"


class MicrosoftGraphOAuth2(BaseOAuth2[Dict[str, Any]]):
    def __init__(self, client_id: str, client_secret: str, tenant: str = "common"):
        access_token_endpoint = ACCESS_TOKEN_ENDPOINT.format(tenant=tenant)
        super().__init__(
            client_id,
            client_secret,
            AUTHORIZE_ENDPOINT.format(tenant=tenant),
            access_token_endpoint,
            access_token_endpoint,
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
