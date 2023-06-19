# OAuth2

## Generic client

A generic OAuth2 class is provided to adapt to any OAuth2-compliant service. You can instantiate it like this:

```py
from httpx_oauth.oauth2 import OAuth2

client = OAuth2(
    "CLIENT_ID",
    "CLIENT_SECRET",
    "AUTHORIZE_ENDPOINT",
    "ACCESS_TOKEN_ENDPOINT",
    refresh_token_endpoint="REFRESH_TOKEN_ENDPOINT",
    revoke_token_endpoint="REVOKE_TOKEN_ENDPOINT",
)
```

Note that `refresh_token_endpoint` and `revoke_token_endpoint` are optional since not every services propose to refresh and revoke tokens.

### Available methods

#### `get_authorization_url`

Returns the authorization URL where you should redirect the user to ask for their approval.

!!! abstract "Parameters"
    * `redirect_uri: str`: Your callback URI where the user will be redirected after the service prompt.
    * `state: str = None`: Optional string that will be returned back in the callback parameters to allow you to retrieve state information.
    * `scope: Optional[List[str]] = None`: Optional list of scopes to ask for.
    * `extras_params: Optional[Dict[str, Any]] = None`: Optional dictionary containing parameters specific to the service.

!!! example
    ```py
    authorization_url = await client.get_authorization_url(
        "https://www.tintagel.bt/oauth-callback", scope=["SCOPE1", "SCOPE2", "SCOPE3"],
    )
    ```

#### `get_access_token`

Returns an [`OAuth2Token` object](#oauth2token-class) for the service given the authorization code passed in the redirection callback.

Raises a `GetAccessTokenError` if an error occurs.

!!! abstract "Parameters"
    * `code: str`: The authorization code passed in the redirection callback.
    * `redirect_uri: str`: The exact same `redirect_uri` you passed to the authorization URL.
    * `code_verifier: Optional[str]`: Optional code verifier in a [PKCE context](https://datatracker.ietf.org/doc/html/rfc7636).

!!! example
    ```py
    access_token = await client.get_access_token("CODE", "https://www.tintagel.bt/oauth-callback")
    ```

#### `refresh_token`

Returns a fresh [`OAuth2Token` object](#oauth2token-class) for the service given a refresh token.

Raises a `RefreshTokenNotSupportedError` if no `refresh_token_endpoint` was provided.

!!! abstract "Parameters"
    * `refresh_token: str`: A valid refresh token for the service.

!!! example
    ```py
    access_token = await client.refresh_token("REFRESH_TOKEN")
    ```

#### `revoke_token`

Revokes a token.

Raises a `RevokeTokenNotSupportedError` if no `revoke_token_endpoint` was provided.

!!! abstract "Parameters"
    * `token: str`: A token or refresh token to revoke.
    * `token_type_hint: str = None`: Optional hint for the service to help it determine if it's a token or refresh token. Usually either `token` or `refresh_token`.

!!! example
    ```py
    await client.revoke_token("TOKEN")
    ```

#### `get_id_email`

Returns the id and the email (if available) of the authenticated user from the API provider. **It assumes you have asked for the required scopes**.

Raises a `GetIdEmailError` if an error occurs.

!!! abstract "Parameters"
    * `token: str`: A valid access token.

!!! example
    ```py
    user_id, user_email = await client.get_id_email("TOKEN")
    ```

### `OAuth2Token` class

This class is a wrapper around a standard `Dict[str, Any]` that bears the response of `get_access_token`. Properties can vary greatly from a service to another but, usually, you can get access token like this:

```py
access_token = token["access_token"]
```

#### `is_expired`

A utility method is provided to quickly determine if the token is still valid or needs to be refreshed.

!!! example
    ```py
    if token.is_expired():
        token = await client.refresh_token(token["refresh_token"])
        # Save token to DB

    access_token = token["access_token"]
    # Do something useful with this access token
    ```

## Provided clients

We provide several ready-to-use clients for widely used services with configured endpoints and specificites took into account.

### OpenID

Generic client for providers following the [OpenID Connect protocol](https://openid.net/connect/). Besides the Client ID and the Client Secret, you'll have to provide the OpenID configuration endpoint, allowing the client to discover the required endpoints automatically. By convention, it's usually served under the path `.well-known/openid-configuration`.

```py
from httpx_oauth.clients.openid import OpenID

client = OpenID("CLIENT_ID", "CLIENT_SECRET", "https://example.fief.dev/.well-known/openid-configuration")
```

* ❓ `refresh_token`: depends if the OpenID provider supports it
* ❓ `revoke_token`: depends if the OpenID provider supports it

### Discord

```py
from httpx_oauth.clients.discord import DiscordOAuth2

client = DiscordOAuth2("CLIENT_ID", "CLIENT_SECRET")
```

* ✅ `refresh_token`
* ✅ `revoke_token`

!!! warning "Warning about `get_id_email`"
    Email is optional for Discord accounts, so the email might be `None`.

### Facebook

```py
from httpx_oauth.clients.facebook import FacebookOAuth2

client = FacebookOAuth2("CLIENT_ID", "CLIENT_SECRET")
```

* ❌ `refresh_token`
* ❌ `revoke_token`

#### `get_long_lived_access_token`

Returns an [`OAuth2Token` object](#oauth2token-class) with a [**long-lived access token**](https://developers.facebook.com/docs/facebook-login/access-tokens/refreshing/) given a short-lived access token.

Raises a `GetLongLivedAccessTokenError` if an error occurs.

!!! abstract "Parameters"
    * `token: str`: A short-lived access token given by `get_access_token`.

!!! example
    ```py
    long_lived_access_token = await client.get_long_lived_access_token("TOKEN")
    ```

### GitHub

```py
from httpx_oauth.clients.github import GitHubOAuth2

client = GitHubOAuth2("CLIENT_ID", "CLIENT_SECRET")
```

* ❌ `refresh_token`
* ❌ `revoke_token`

!!! tip
    You should enable **Email addresses** permission in the **Permissions & events** section of your GitHub app parameters. You can find it at [https://github.com/settings/apps/{YOUR_APP}/permissions](https://github.com/settings/apps/{YOUR_APP}/permissions).

### Google

```py
from httpx_oauth.clients.google import GoogleOAuth2

client = GoogleOAuth2("CLIENT_ID", "CLIENT_SECRET")
```

* ✅ `refresh_token`
* ✅ `revoke_token`

### Kakao

```py
from httpx_oauth.clients.kakao import KakaoOAuth2

client = KakaoOAuth2("CLIENT_ID", "CLIENT_SECRET")
```

* ✅ `refresh_token`
* ✅ `revoke_token`

### LinkedIn

```py
from httpx_oauth.clients.linkedin import LinkedInOAuth2

client = LinkedInOAuth2("CLIENT_ID", "CLIENT_SECRET")
```

* ✅ `refresh_token` (only for [selected partners](https://docs.microsoft.com/en-us/linkedin/shared/authentication/programmatic-refresh-tokens))
* ❌ `revoke_token`

### NAVER

```py
from httpx_oauth.clients.naver import NaverOAuth2

client = NaverOAuth2("CLIENT_ID", "CLIENT_SECRET")
```

* ✅ `refresh_token`
* ✅ `revoke_token`

### Okta

Based on the [OpenID client](#openid). You need to provide the domain of your Okta domain for automatically discovering the required endpoints.

```py
from httpx_oauth.clients.okta import OktaOAuth2

client = OktaOAuth2("CLIENT_ID", "CLIENT_SECRET", "example.okta.com")
```

* ✅ `refresh_token`
* ✅ `revoke_token`

### Reddit

```py
from httpx_oauth.clients.reddit import RedditOAuth2

client = RedditOAuth2("CLIENT_ID", "CLIENT_SECRET")
```

* ✅ `refresh_token`
* ✅ `revoke_token`

!!! warning "Warning about `get_id_email`"
    Reddit API never return email addresses. Thus, e-mail will *always* be `None`.

### FranceConnect

```py
from httpx_oauth.clients.franceconnect import FranceConnectOAuth2

client = FranceConnectOAuth2("CLIENT_ID", "CLIENT_SECRET")
```

* ❌ `refresh_token`
* ❌ `revoke_token`

!!! tip "Integration server"
    Since you need to go through a [heavy validation process](https://partenaires.franceconnect.gouv.fr/monprojet/cadrage) before getting your client ID and secret, you can use during development the [integration server with demo credentials](https://partenaires.franceconnect.gouv.fr/fcp/fournisseur-service). You can enable this mode by setting the `integration` flag to `True`.

    ```py
    from httpx_oauth.clients.franceconnect import FranceConnectOAuth2

    client = FranceConnectOAuth2("CLIENT_ID", "CLIENT_SECRET", integration=True)
    ```

### Shopify

The OAuth2 client for Shopify allows you to authenticate shop owners so your app can make calls to the [Shopify Admin API](https://shopify.dev/docs/api/admin). Besides the Client ID and Secret, you'll need the **shop subdomain** of the shop you need to access.

```py
from httpx_oauth.clients.shopify import ShopifyOAuth2

client = ShopifyOAuth2("CLIENT_ID", "CLIENT_SECRET", "my-shop")
```

* ❌ `refresh_token`
* ❌ `revoke_token`

!!! warning "`get_id_email` is based on the `Shop` resource"
    The implementation of `get_id_email` calls the [Get Shop endpoint](https://shopify.dev/docs/api/admin-rest/2023-04/resources/shop#get-shop) of the Shopify Admin API. It means that it'll return you the **ID of the shop** and the **email of the shop owner**.

## Customize HTTPX client

By default, requests are made using [`httpx.AsyncClient`](https://www.python-httpx.org/api/#asyncclient) with default parameters. If you wish to customize settings, like setting timeout or proxies, you can do this by overloading the `get_httpx_client` method.

```py
from typing import AsyncContextManager

import httpx
from httpx_oauth.oauth2 import OAuth2


class OAuth2CustomTimeout(OAuth2):
    def get_httpx_client(self) -> AsyncContextManager[httpx.AsyncClient]:
        return httpx.AsyncClient(timeout=10.0)  # Use a default 10s timeout everywhere.


client = OAuth2CustomTimeout(
    "CLIENT_ID",
    "CLIENT_SECRET",
    "AUTHORIZE_ENDPOINT",
    "ACCESS_TOKEN_ENDPOINT",
    refresh_token_endpoint="REFRESH_TOKEN_ENDPOINT",
    revoke_token_endpoint="REVOKE_TOKEN_ENDPOINT",
)
```
