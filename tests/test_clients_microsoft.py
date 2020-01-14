import re

import pytest
import respx

from httpx_oauth.clients.microsoft import MicrosoftGraphOAuth2, PROFILE_ENDPOINT
from httpx_oauth.errors import GetProfileError

client = MicrosoftGraphOAuth2("CLIENT_ID", "CLIENT_SECRET")


def test_microsoft_graph_oauth2_default_tenant():

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
    assert client.base_scopes == ["User.Read"]
    assert client.name == "microsoft"


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


class TestGoogleGetProfile:
    @pytest.mark.asyncio
    @respx.mock
    async def test_microsoft_get_profile(self, get_respx_call_args):
        request = respx.get(
            re.compile(f"^{PROFILE_ENDPOINT}"), status_code=200, content={"foo": "bar"}
        )

        result = await client.get_profile("TOKEN")
        url, headers, content = await get_respx_call_args(request)

        assert headers["Authorization"] == "Bearer TOKEN"
        assert result == {"foo": "bar"}

    @pytest.mark.asyncio
    @respx.mock
    async def test_microsoft_get_profile_error(self, get_respx_call_args):
        respx.get(
            re.compile(f"^{PROFILE_ENDPOINT}"), status_code=400, content={"foo": "bar"}
        )

        with pytest.raises(GetProfileError) as excinfo:
            await client.get_profile("TOKEN")

        assert type(excinfo.value.args[0]) == dict
        assert excinfo.value.args[0] == {"foo": "bar"}
