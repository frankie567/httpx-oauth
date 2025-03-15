# Litestar

Utilities are provided to ease the integration of an OAuth2 process in [Litestar](https://litestar.dev/).

## `OAuth2AuthorizeCallback`

Dependency callable to handle the authorization callback. It reads the query parameters and returns the access token and the state.

```py
from httpx_oauth.integrations.litestar import OAuth2AuthorizeCallback, AccessTokenState
from httpx_oauth.oauth2 import OAuth2
from litestar import Litestar, get
from litestar.di import Provide
from litestar.params import Dependency

client = OAuth2("CLIENT_ID", "CLIENT_SECRET", "AUTHORIZE_ENDPOINT", "ACCESS_TOKEN_ENDPOINT")
oauth2_authorize_callback = OAuth2AuthorizeCallback(client, "oauth-callback")

@get("/oauth-callback", name="oauth-callback")
async def oauth_callback(
    access_token_state: AccessTokenState = Dependency(skip_validation=True),
) -> AccessTokenState:
    token, state = access_token_state
    # Do something useful

app = Litestar(route_handlers=[oauth_callback],dependencies={"access_token_state": Provide(oauth2_authorize_callback)})


```

[Reference](./reference/httpx_oauth.integrations.litestar.md){ .md-button }
{ .buttons }

### Custom exception handler

If an error occurs inside the callback logic (the user denied access, the authorization code is invalid...), the dependency will raise [OAuth2AuthorizeCallbackError][httpx_oauth.integrations.litestar.OAuth2AuthorizeCallbackError].

It inherits from Litestar's [HTTPException][litestar.exceptions.HTTPException], so it's automatically handled by the default Litestar exception handler. You can customize this behavior by implementing your own exception handler for `OAuth2AuthorizeCallbackError`.

```py
from httpx_oauth.integrations.litestar import OAuth2AuthorizeCallbackError
from litestar import Litestar
from litestar.response import Response

async def oauth2_authorize_callback_error_handler(request: Request, exc: OAuth2AuthorizeCallbackError) -> Response:
    detail = exc.detail
    status_code = exc.status_code
    return Response(
        status_code=status_code,
        content={"message": "The OAuth2 callback failed", "detail": detail},
    )

app = Litestar(exception_handlers={OAuth2AuthorizeCallbackError: oauth2_authorize_callback_error_handler})
```
