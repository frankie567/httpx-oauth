# Usage

## Create a client

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

## Generate an authorization URL

Use the [get_authorization_url][httpx_oauth.oauth2.BaseOAuth2.get_authorization_url] method to generate the authorization URL where you should redirect the user to ask for their approval.

```py
authorization_url = await client.get_authorization_url(
    "https://www.tintagel.bt/oauth-callback", scope=["SCOPE1", "SCOPE2", "SCOPE3"],
)
```

## Request an access token

Once you have the authorization code, use the [get_access_token][httpx_oauth.oauth2.BaseOAuth2.get_access_token] method to exchange it with a valid access token.

It returns an [OAuth2Token][httpx_oauth.oauth2.OAuth2Token] dictionary-like object.

```py
access_token = await client.get_access_token("CODE", "https://www.tintagel.bt/oauth-callback")
```


## Refresh an access token

For providers supporting it, you can ask for a fresh access token given a refresh token. For this, use the [refresh_token][httpx_oauth.oauth2.BaseOAuth2.refresh_token] method.

It returns an [OAuth2Token][httpx_oauth.oauth2.OAuth2Token] dictionary-like object.

```py
access_token = await client.refresh_token("REFRESH_TOKEN")
```

## Revoke an access or refresh token

For providers supporting it, you can ask to revoke an access or refresh token. For this, use the [revoke_token][httpx_oauth.oauth2.BaseOAuth2.revoke_token] method.

## Get authenticated user ID and email

For convenience, we provide a method that'll use a valid access token to query the provider API and get the ID and the email (if available) of the authenticated user. For this, use the [get_id_email][httpx_oauth.oauth2.BaseOAuth2.get_id_email] method.

This method is implemented specifically on each provider.

## Provided clients

Out-of-the box, we support lot of popular providers like [Google][httpx_oauth.clients.google] or [Facebook][httpx_oauth.clients.facebook], for which we provided dedicated classes with pre-configured endpoints.

[Clients reference](./reference/httpx_oauth.clients.md){ .md-button }
{: .buttons }

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
