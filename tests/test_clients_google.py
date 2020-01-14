import re

import pytest
import respx

from httpx_oauth.clients.google import GoogleOAuth2, PROFILE_ENDPOINT
from httpx_oauth.errors import GetProfileError

client = GoogleOAuth2("CLIENT_ID", "CLIENT_SECRET")


def test_google_oauth2():
    assert client.authorize_endpoint == "https://accounts.google.com/o/oauth2/v2/auth"
    assert client.access_token_endpoint == "https://oauth2.googleapis.com/token"
    assert client.refresh_token_endpoint == "https://oauth2.googleapis.com/token"
    assert client.revoke_token_endpoint == "https://accounts.google.com/o/oauth2/revoke"
    assert client.base_scopes == [
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
    ]
    assert client.name == "google"


class TestGoogleGetProfile:
    @pytest.mark.asyncio
    @respx.mock
    async def test_google_get_profile(self, get_respx_call_args):
        request = respx.get(
            re.compile(f"^{PROFILE_ENDPOINT}"), status_code=200, content={"foo": "bar"}
        )

        result = await client.get_profile("TOKEN")
        url, headers, content = await get_respx_call_args(request)

        assert "key=TOKEN" in url.query
        assert "personFields=" in url.query
        assert result == {"foo": "bar"}

    @pytest.mark.asyncio
    @respx.mock
    async def test_google_get_profile_error(self, get_respx_call_args):
        respx.get(
            re.compile(f"^{PROFILE_ENDPOINT}"), status_code=400, content={"foo": "bar"}
        )

        with pytest.raises(GetProfileError) as excinfo:
            await client.get_profile("TOKEN")

        assert type(excinfo.value.args[0]) == dict
        assert excinfo.value.args[0] == {"foo": "bar"}
