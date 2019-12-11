import pytest

from httpx_oauth.clients.microsoft import MicrosoftGraphOAuth2


def test_microsoft_graph_oauth2_default_tenant():
    client = MicrosoftGraphOAuth2("CLIENT_ID", "CLIENT_SECRET")

    assert (
        client.authorize_endpoint
        == "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    )
    assert (
        client.access_token_endpoint
        == "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    )
    assert (
        client.refresh_token_endpoint
        == "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    )
    assert client.revoke_token_endpoint is None


def test_microsoft_graph_oauth2_custom_tenant():
    client = MicrosoftGraphOAuth2("CLIENT_ID", "CLIENT_SECRET", "my_tenant")

    assert (
        client.authorize_endpoint
        == "https://login.microsoftonline.com/my_tenant/oauth2/v2.0/authorize"
    )
    assert (
        client.access_token_endpoint
        == "https://login.microsoftonline.com/my_tenant/oauth2/v2.0/token"
    )
    assert (
        client.refresh_token_endpoint
        == "https://login.microsoftonline.com/my_tenant/oauth2/v2.0/token"
    )
    assert client.revoke_token_endpoint is None


@pytest.mark.asyncio
async def test_microsoft_graph_oauth2_authorization_url():
    client = MicrosoftGraphOAuth2("CLIENT_ID", "CLIENT_SECRET")

    authorization_url = await client.get_authorization_url(
        "https://www.tintagel.bt/oauth-callback"
    )
    assert "response_mode=query" in authorization_url
