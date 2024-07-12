import re

import pytest
import respx
from httpx import Response

from httpx_oauth.clients.microsoft import PROFILE_ENDPOINT, MicrosoftGraphOAuth2
from httpx_oauth.exceptions import GetIdEmailError

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


profile_response = {"id": "424242", "userPrincipalName": "arthur@camelot.bt"}


class TestMicrosoftGetIdEmail:
    @pytest.mark.asyncio
    @respx.mock
    async def test_success(self, get_respx_call_args):
        request = respx.get(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(200, json=profile_response)
        )

        user_id, user_email = await client.get_id_email("TOKEN")
        url, headers, content = await get_respx_call_args(request)

        assert headers["Authorization"] == "Bearer TOKEN"
        assert user_id == "424242"
        assert user_email == "arthur@camelot.bt"

    @pytest.mark.asyncio
    @respx.mock
    async def test_error(self):
        respx.get(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(400, json={"error": "message"})
        )

        with pytest.raises(GetIdEmailError) as excinfo:
            await client.get_id_email("TOKEN")

        assert isinstance(excinfo.value.response, Response)
