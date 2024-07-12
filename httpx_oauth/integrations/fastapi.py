from typing import Any, Dict, Optional, Tuple, Union

import httpx
from fastapi import HTTPException
from starlette import status
from starlette.requests import Request

from httpx_oauth.oauth2 import BaseOAuth2, GetAccessTokenError, OAuth2Error, OAuth2Token


class OAuth2AuthorizeCallbackError(HTTPException, OAuth2Error):
    """
    Error raised when an error occurs during the OAuth2 authorization callback.

    It inherits from [HTTPException][fastapi.HTTPException], so you can either keep
    the default FastAPI error handling or implement a
    [dedicated exception handler](https://fastapi.tiangolo.com/tutorial/handling-errors/#install-custom-exception-handlers).
    """

    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Union[Dict[str, str], None] = None,
        response: Union[httpx.Response, None] = None,
    ) -> None:
        self.response = response
        super().__init__(status_code, detail, headers)


class OAuth2AuthorizeCallback:
    """
    Dependency callable to handle the authorization callback. It reads the query parameters and returns the access token and the state.

    Examples:
        ```py
        from fastapi import FastAPI, Depends
        from httpx_oauth.integrations.fastapi import OAuth2AuthorizeCallback
        from httpx_oauth.oauth2 import OAuth2

        client = OAuth2("CLIENT_ID", "CLIENT_SECRET", "AUTHORIZE_ENDPOINT", "ACCESS_TOKEN_ENDPOINT")
        oauth2_authorize_callback = OAuth2AuthorizeCallback(client, "oauth-callback")
        app = FastAPI()

        @app.get("/oauth-callback", name="oauth-callback")
        async def oauth_callback(access_token_state=Depends(oauth2_authorize_callback)):
            token, state = access_token_state
            # Do something useful
        ```
    """

    client: BaseOAuth2
    route_name: Optional[str]
    redirect_url: Optional[str]

    def __init__(
        self,
        client: BaseOAuth2,
        route_name: Optional[str] = None,
        redirect_url: Optional[str] = None,
    ):
        """
        Args:
            client: An [OAuth2][httpx_oauth.oauth2.BaseOAuth2] client.
            route_name: Name of the callback route, as defined in the `name` parameter of the route decorator.
            redirect_url: Full URL to the callback route.
        """
        assert (route_name is not None and redirect_url is None) or (
            route_name is None and redirect_url is not None
        ), "You should either set route_name or redirect_url"
        self.client = client
        self.route_name = route_name
        self.redirect_url = redirect_url

    async def __call__(
        self,
        request: Request,
        code: Optional[str] = None,
        code_verifier: Optional[str] = None,
        state: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Tuple[OAuth2Token, Optional[str]]:
        if code is None or error is not None:
            raise OAuth2AuthorizeCallbackError(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error if error is not None else None,
            )

        if self.route_name:
            redirect_url = str(request.url_for(self.route_name))
        elif self.redirect_url:
            redirect_url = self.redirect_url

        try:
            access_token = await self.client.get_access_token(
                code, redirect_url, code_verifier
            )
        except GetAccessTokenError as e:
            raise OAuth2AuthorizeCallbackError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=e.message,
                response=e.response,
            ) from e

        return access_token, state
