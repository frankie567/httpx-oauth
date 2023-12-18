import re

import pytest
import respx
from httpx import Response

from httpx_oauth.clients.discord import PROFILE_ENDPOINT, DiscordOAuth2
from httpx_oauth.errors import GetIdEmailError

client = DiscordOAuth2("CLIENT_ID", "CLIENT_SECRET")


def test_discord_oauth2():
    assert client.authorize_endpoint == "https://discord.com/api/oauth2/authorize"
    assert client.access_token_endpoint == "https://discord.com/api/oauth2/token"
    assert client.refresh_token_endpoint == "https://discord.com/api/oauth2/token"
    assert client.revoke_token_endpoint == "https://discord.com/api/oauth2/token/revoke"
    assert client.base_scopes == ["identify", "email"]
    assert client.name == "discord"


profile_verified_email_response = {
    "id": "80351110224678912",
    "username": "Nelly",
    "discriminator": "1337",
    "avatar": "8342729096ea3675442027381ff50dfe",
    "verified": True,
    "email": "nelly@discord.com",
    "flags": 64,
    "banner": "06c16474723fe537c283b8efa61a30c8",
    "accent_color": 16711680,
    "premium_type": 1,
    "public_flags": 64,
}

profile_no_email_response = {
    "id": "80351110224678912",
    "username": "Nelly",
    "discriminator": "1337",
    "avatar": "8342729096ea3675442027381ff50dfe",
    "flags": 64,
    "banner": "06c16474723fe537c283b8efa61a30c8",
    "accent_color": 16711680,
    "premium_type": 1,
    "public_flags": 64,
}

profile_not_verified_email_response = {
    "id": "80351110224678912",
    "username": "Nelly",
    "discriminator": "1337",
    "avatar": "8342729096ea3675442027381ff50dfe",
    "verified": False,
    "email": "nelly@discord.com",
    "flags": 64,
    "banner": "06c16474723fe537c283b8efa61a30c8",
    "accent_color": 16711680,
    "premium_type": 1,
    "public_flags": 64,
}


class TestDiscordGetIdEmail:
    @pytest.mark.asyncio
    @respx.mock
    async def test_success(self, get_respx_call_args):
        request = respx.get(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(200, json=profile_verified_email_response)
        )

        user_id, user_email = await client.get_id_email("TOKEN")
        _, headers, _ = await get_respx_call_args(request)

        assert headers["Authorization"] == "Bearer TOKEN"
        assert headers["Accept"] == "application/json"
        assert user_id == "80351110224678912"
        assert user_email == "nelly@discord.com"

    @pytest.mark.asyncio
    @respx.mock
    async def test_error(self):
        respx.get(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(400, json={"error": "message"})
        )

        with pytest.raises(GetIdEmailError) as excinfo:
            await client.get_id_email("TOKEN")

        assert isinstance(excinfo.value.args[0], dict)
        assert excinfo.value.args[0] == {"error": "message"}

    @pytest.mark.asyncio
    @respx.mock
    async def test_no_email(self):
        respx.get(re.compile(f"^{PROFILE_ENDPOINT}$")).mock(
            return_value=Response(200, json=profile_no_email_response)
        )

        user_id, user_email = await client.get_id_email("TOKEN")

        assert user_id == "80351110224678912"
        assert user_email is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_email_not_verified_error(self):
        respx.get(re.compile(f"^{PROFILE_ENDPOINT}$")).mock(
            return_value=Response(200, json=profile_not_verified_email_response)
        )

        user_id, user_email = await client.get_id_email("TOKEN")

        assert user_id == "80351110224678912"
        assert user_email is None
