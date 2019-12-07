from typing import Optional, Tuple

from fastapi import HTTPException
from starlette import status

from httpx_oauth.oauth2 import BaseOAuth2, OAuth2Token


class OAuth2AuthorizeCallback:

    client: BaseOAuth2
    redirect_uri: str

    def __init__(self, client: BaseOAuth2, redirect_uri: str):
        self.client = client
        self.redirect_uri = redirect_uri

    async def __call__(
        self, code: str = None, state: str = None, error: str = None
    ) -> Tuple[OAuth2Token, Optional[str]]:
        if code is None or error is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error if error is not None else None,
            )

        access_token = await self.client.get_access_token(code, self.redirect_uri)

        return access_token, state
