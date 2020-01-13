# FastAPI

Utilities are provided to ease the integration of an OAuth2 process in [FastAPI](https://fastapi.tiangolo.com/).

## `OAuth2AuthorizeCallback`

Dependency callable to handle the authorization callback. It reads the query parameters and returns the access token and the state.

!!! abstract "Parameters"
    * `client: OAuth2`: The OAuth2 client.
    * `route_name: str`: Name of the callback route, as defined in the `name` parameter of the route decorator.

```py
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
