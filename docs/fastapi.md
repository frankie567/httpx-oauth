# FastAPI

Utilities are provided to ease the integration of an OAuth2 process in [FastAPI](https://fastapi.tiangolo.com/).

## `OAuth2AuthorizeCallback`

Dependency callable to handle the authorization callback. It reads the query parameters and returns the access token and the state.

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

[Reference](./reference/httpx_oauth.integrations.fastapi.md){ .md-button }
{ .buttons }

### Custom exception handler

If an error occurs inside the callback logic (the user denied access, the authorization code is invalid...), the dependency will raise [OAuth2AuthorizeCallbackError][httpx_oauth.integrations.fastapi.OAuth2AuthorizeCallbackError].

It inherits from FastAPI's [HTTPException][fastapi.HTTPException], so it's automatically handled by the default FastAPI exception handler. You can customize this behavior by implementing your own exception handler for `OAuth2AuthorizeCallbackError`.

```py
from fastapi import FastAPI
from httpx_oauth.integrations.fastapi import OAuth2AuthorizeCallbackError

app = FastAPI()

@app.exception_handler(OAuth2AuthorizeCallbackError)
async def oauth2_authorize_callback_error_handler(request: Request, exc: OAuth2AuthorizeCallbackError):
    detail = exc.detail
    status_code = exc.status_code
    return JSONResponse(
        status_code=status_code,
        content={"message": "The OAuth2 callback failed", "detail": detail},
    )
```
