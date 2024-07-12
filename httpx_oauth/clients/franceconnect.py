import secrets
from typing import Any, Dict, List, Literal, Optional, Tuple, TypedDict

from httpx_oauth.exceptions import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2

ENDPOINTS = {
    "integration": {
        "authorize": "https://fcp.integ01.dev-franceconnect.fr/api/v1/authorize",
        "access_token": "https://fcp.integ01.dev-franceconnect.fr/api/v1/token",
        "profile": "https://fcp.integ01.dev-franceconnect.fr/api/v1/userinfo",
    },
    "production": {
        "authorize": "https://app.franceconnect.gouv.fr/api/v1/authorize",
        "access_token": "https://app.franceconnect.gouv.fr/api/v1/token",
        "profile": "https://app.franceconnect.gouv.fr/api/v1/userinfo",
    },
}
BASE_SCOPES = ["openid", "email"]


LOGO_SVG = """
<svg clip-rule="evenodd" fill-rule="evenodd" stroke-linejoin="round" stroke-miterlimit="2" viewBox="0 0 63 73" xml:space="preserve" xmlns="http://www.w3.org/2000/svg"><path d="M18 22v34.9l30.2 17.5 30.3-17.5V22L48.2 4.5 18 22Z" fill="#fff" fill-rule="nonzero" transform="translate(-17 -3.3)"/><path d="M48.2 3.3 17 21.4v36.1l31.3 18 31.3-18V21.4L48.2 3.3zm30.3 53.6L48.2 74.4 18 56.9V22L48.2 4.5 78.5 22v34.9z" fill="#034ea2" fill-rule="nonzero" transform="translate(-17 -3.3)"/><path d="m62.6 20.8-13.7-7.9-13.7 7.9-9.3 5.4v26.5l23 13.3 23-13.3V26.2l-9.3-5.4z" fill="#0069cc" fill-rule="nonzero" transform="translate(-17 -3.3)"/><path d="M64.3 39.4 56 25.1l-7.1-12.2V66l23-13.3-7.6-13.3z" fill="#034ea2" fill-rule="nonzero" transform="translate(-17 -3.3)"/><path d="m56 25.1 8.3 14.3 7.6-13.2-9.3-5.4-6.6 4.3z" fill="#0069cc" fill-rule="nonzero" transform="translate(-17 -3.3)"/><path d="m62.6 20.8-13.7-7.9L56 25.1l6.6-4.3z" fill="#ed1c24" fill-rule="nonzero" transform="translate(-17 -3.3)"/><path d="m56 25.1-7.1-12.2L56 25.1z" fill="#0069cc" fill-rule="nonzero" transform="translate(-17 -3.3)"/><path d="M60.1 24v16.6V24z" fill="#0069cc" transform="translate(-17 -3.3)"/><path d="M71.9 52.7V26.2l-7.6 13.2 7.6 13.3zM64.3 39.4l7.6 13.3-7.6-13.3z" fill="#ed1c24" fill-rule="nonzero" transform="translate(-17 -3.3)"/><path d="m33.6 39.4 8.3-14.3 7-12.2V66l-23-13.3 7.7-13.3z" fill="#0069cc" fill-rule="nonzero" transform="translate(-17 -3.3)"/><path d="m41.9 25.1-8.3 14.3-7.7-13.2 9.3-5.4 6.7 4.3z" fill="#ed1c24" fill-rule="nonzero" transform="translate(-17 -3.3)"/><path d="m35.2 20.8 13.7-7.9-7 12.2-6.7-4.3z" fill="#034ea2" fill-rule="nonzero" transform="translate(-17 -3.3)"/><path d="m41.9 25.1 7-12.2-7 12.2z" fill="#0069cc" fill-rule="nonzero" transform="translate(-17 -3.3)"/><path d="M37.7 24v16.6V24z" fill="#0069cc" transform="translate(-17 -3.3)"/><path d="M25.9 52.7V26.2l7.7 13.2-7.7 13.3z" fill="#034ea2" fill-rule="nonzero" transform="translate(-17 -3.3)"/><path d="m33.6 39.4-7.7 13.3 7.7-13.3z" fill="#0069cc" fill-rule="nonzero" transform="translate(-17 -3.3)"/><g fill-rule="nonzero"><path d="M57.4 42h1.2l.7.2c-.1.6-1 .7-1.4 1.3h-.2c-.2.1-.1.5-.3.5-.2-.1-.4 0-.7.1.3.3.7.5 1.1.4.1 0 .2.1.2.3l.1-.1.1.1v.3c-.2.3-.6.2-.9.2H59c.4-.2 0-.9.3-1.2-.1 0 0-.2-.2-.2l.4-.4.4-.2c0-.1-.3-.2-.2-.4.4-.3.8-.7.6-1.2-.1-.2-.7-.2-1-.3-.4-.1-.8 0-1.2.1-.4 0-.7.2-1.1.3l-1.4.8 1.8-.6z" fill="#034ea2" transform="translate(-17 -3.3)"/><path d="m63 46.4-.8-1.1c-.3-.5-.7-.9-.8-1.5-.2-.6 0-1.1 0-1.7 0-1.1-.3-2.2-.6-3.2l-.5-1.6-.4-.9v-.5l.8-.8c.2-.4 0-.9-.3-1.1-.5-.2-.4.5-.8.7h-.2c-.1-.2.1-.3.2-.4l-.1-.2-.7-.2c-.8-1-1.8-1.5-2.9-1.9l.9.1c.5.1 1.1 0 1.5-.2s.4-.7.5-1.1c.1-.1 0-.2 0-.4l-.3-.6-.2-.3c-.8-.9-3.9-3.5-9.7-3.1-2.5.2-5.6.9-9.2 2.7l-.4.1c-.6.3-1.4.8-1.9 1.4-.6.7-1.1 1.5-1.3 2.4-.9.6-1.5 1.5-2 2.4-.6 1.2-1.4 2.2-1.4 3.5v.2l.2 1.1.5 2.4.3 1.2c.2.4 0 .9.3 1.3.1.2.1.5.4.6v.3l.2.1v.3c.6.7 1.3 1.3 1.7 2.1.2.4-.7.2-1.1.1-.7-.3-1.2-.9-1.8-1.4l-.1.1c.3.5 1.4 1.1.8 1.5-.3.2-.7-.2-.9.1-.1.1 0 .3 0 .4-.4-.3-.9-.1-1.3-.3-.3-.1-.4-.6-.7-.6-.9-.2-1.8-.4-2.8-.4h-.2c-.9-.1-1.8-.2-2.6-.1V49c.8-.2 1.6-.4 2.4-.4H28.6l-1 .1c-.8.1-1.6.4-2.4.7v1l1.3.2 1.5.4c.7.2 1.2.5 1.8.8l.7.6c.4.2.9.2 1.2 0h.4c1.1-.3 2.2-.6 2.9-1.5l.1.1c-.2.6-.2 1.2-.6 1.8 0 .1-.1.2.1.3h.1l-.1.1.3.1c-.4.1-.7.2-.9.5l.2.1-.4.2.1.1-.1.1v.2l-.4.2c.3.2.5 0 .8 0-.8.3-1.4.8-2.2 1l-.1.2c.2.1.4-.1.6-.1l-1.2.7 2.4 1.4c1-.6 1.9-1.3 2.7-2.2l.1.1c-.2.7-.6 1.2-1.2 1.7l-1 .7 1.8 1 1.2-.7.4.1c.6-.6 1.3-1.3 2.3-1.1l.1.1.1-.1-.1.1-.8.6c-.1.1 0 .1.1.1l.9-.6-.1.3a16 16 0 0 0-2.3 2.2l9.5 5.5 1.1-1.5c1.8-2.6 4.4-6.1 5.2-6.9.3-.2.6-.2 1-.3 1.2 0 2.5.3 3.7.4l.4.1c.4.1.9 0 1.4-.1.5-.2 1.1-.5 1.3-1.1.2-.5.3-1.1 0-1.6-.5-.6.4-.9.7-1.3.2-.4-.2-.6-.2-.9-.1-.1-.4-.1-.5-.3.5-.2 1.3-.7.9-1.3-.2-.4-.6-.9-.2-1.3.5-.3 1.3-.3 1.5-.8.6-1-.3-1.7-.7-2.4zm-3.1-3.6c-.1.1.2.2.2.4l-.4.2-.4.4c.1 0 0 .2.2.2-.3.4.2 1.1-.3 1.2-.5.2-1.1.2-1.7 0 .3-.1.7.1.9-.2v-.3l-.1-.1-.1.1-.2-.3c-.4.1-.8-.1-1.1-.4.2-.1.4-.2.7-.1.2 0 .1-.4.3-.5h.2c.4-.6 1.3-.8 1.4-1.3l-.7-.2h-1.2c-.6.2-1.1.2-1.6.5l1.4-.8c.4-.1.7-.3 1.1-.3.4-.1.9-.2 1.2-.1.4.1.9.1 1 .3a2 2 0 0 1-.8 1.3z" fill="#fff" transform="translate(-17 -3.3)"/></g></svg>
"""


class FranceConnectOAuth2AuthorizeParams(TypedDict, total=False):
    nonce: str


class FranceConnectOAuth2(BaseOAuth2[FranceConnectOAuth2AuthorizeParams]):
    display_name = "FranceConnect"
    logo_svg = LOGO_SVG

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        integration: bool = False,
        scopes: Optional[List[str]] = BASE_SCOPES,
        name="franceconnect",
    ):
        endpoints = ENDPOINTS["integration"] if integration else ENDPOINTS["production"]
        super().__init__(
            client_id,
            client_secret,
            endpoints["authorize"],
            endpoints["access_token"],
            refresh_token_endpoint=None,
            revoke_token_endpoint=None,
            name=name,
            base_scopes=scopes,
        )
        self.profile_endpoint = endpoints["profile"]

    async def get_authorization_url(
        self,
        redirect_uri: str,
        state: Optional[str] = None,
        scope: Optional[List[str]] = None,
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[Literal["plain", "S256"]] = None,
        extras_params: Optional[FranceConnectOAuth2AuthorizeParams] = None,
    ) -> str:
        _extras_params = extras_params or {}

        # nonce is required for FranceConnect
        if _extras_params.get("nonce") is None:
            _extras_params["nonce"] = secrets.token_urlsafe()

        return await super().get_authorization_url(
            redirect_uri, state, scope, extras_params=_extras_params
        )

    async def get_id_email(self, token: str) -> Tuple[str, Optional[str]]:
        async with self.get_httpx_client() as client:
            response = await client.get(
                self.profile_endpoint,
                headers={**self.request_headers, "Authorization": f"Bearer {token}"},
            )

            if response.status_code >= 400:
                raise GetIdEmailError(response=response)

            data: Dict[str, Any] = response.json()

            return str(data["sub"]), data.get("email")
