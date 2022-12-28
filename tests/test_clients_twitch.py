import re

import pytest
import respx
from httpx import Response

from httpx_oauth.clients.twitch import PROFILE_ENDPOINT, TwitchOAuth2
from httpx_oauth.errors import GetIdEmailError

client = TwitchOAuth2("CLIENT_ID", "CLIENT_SECRET")


def test_twitch_oauth2():
    assert client.authorize_endpoint == "https://id.twitch.tv/oauth2/authorize"
    assert client.access_token_endpoint == "https://id.twitch.tv/oauth2/token"
    assert client.refresh_token_endpoint == "https://id.twitch.tv/oauth2/token"
    assert client.revoke_token_endpoint == "https://id.twitch.tv/oauth2/revoke"
    assert client.base_scopes == [
        "user:read:email",
        "user:read:follows",
        "user:read:subscriptions",
        "user:manage:whispers",
    ]
    assert client.name == "twitch"


class TestTwitchGetIdEmail:
    @pytest.mark.asyncio
    @respx.mock
    async def test_success_with_email(self, get_respx_call_args):
        profile_response = {"data": [{"id": "12345", "email": "test.user@domain.com"}]}
        request = respx.get(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(200, json=profile_response)
        )

        user_id, user_email = await client.get_id_email("TOKEN")
        url, headers, content = await get_respx_call_args(request)

        assert headers["Authorization"] == "Bearer TOKEN"
        assert headers["Client-Id"] == client.client_id
        assert user_id == "12345"
        assert user_email == "test.user@domain.com"

    @pytest.mark.asyncio
    @respx.mock
    async def test_success_with_no_email(self, get_respx_call_args):
        profile_response = {"data": [{"id": "12345"}]}
        request = respx.get(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(200, json=profile_response)
        )

        user_id, user_email = await client.get_id_email("TOKEN")
        url, headers, content = await get_respx_call_args(request)

        assert headers["Authorization"] == "Bearer TOKEN"
        assert headers["Client-Id"] == client.client_id
        assert user_id == "12345"
        assert user_email is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_error(self):
        respx.get(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(400, json={"error": "message"})
        )

        with pytest.raises(GetIdEmailError) as excinfo:
            await client.get_id_email("TOKEN")

        assert type(excinfo.value.args[0]) == dict
        assert excinfo.value.args[0] == {"error": "message"}
