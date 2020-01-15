from typing import Optional, Tuple

from fastapi import HTTPException
from starlette import status
from starlette.requests import Request

from httpx_oauth.oauth2 import BaseOAuth2, OAuth2Token


class OAuth2AuthorizeCallback:

    client: BaseOAuth2
    route_name: Optional[str]
    redirect_url: Optional[str]

    def __init__(
        self, client: BaseOAuth2, route_name: str = None, redirect_url: str = None
    ):
        assert (route_name is not None and redirect_url is None) or (
            route_name is None and redirect_url is not None
        ), "You should either set route_name or redirect_url"
        self.client = client
        self.route_name = route_name
        self.redirect_url = redirect_url

    async def __call__(
        self, request: Request, code: str = None, state: str = None, error: str = None
    ) -> Tuple[OAuth2Token, Optional[str]]:
        if code is None or error is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error if error is not None else None,
            )

        if self.route_name:
            redirect_url = request.url_for(self.route_name)
        elif self.redirect_url:
            redirect_url = self.redirect_url

        access_token = await self.client.get_access_token(code, redirect_url)

        return access_token, state
