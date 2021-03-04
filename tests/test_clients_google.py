import re

import pytest
import respx
from httpx import Response

from httpx_oauth.clients.google import GoogleOAuth2, PROFILE_ENDPOINT
from httpx_oauth.errors import GetIdEmailError

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


profile_response = {
    "resourceName": "people/424242424242",
    "emailAddresses": [
        {"metadata": {"primary": True, "verified": True}, "value": "arthur@camelot.bt"},
        {"metadata": {"primary": False, "verified": True}, "value": "arthur@graal.com"},
    ],
}


class TestGoogleGetIdEmail:
    @pytest.mark.asyncio
    @respx.mock
    async def test_success(self, get_respx_call_args):
        request = respx.get(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(200, json=profile_response)
        )

        user_id, user_email = await client.get_id_email("TOKEN")
        url, headers, content = await get_respx_call_args(request)

        assert "personFields=emailAddresses" in url.query.decode("utf-8")
        assert headers["Authorization"] == "Bearer TOKEN"
        assert user_id == "people/424242424242"
        assert user_email == "arthur@camelot.bt"

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
