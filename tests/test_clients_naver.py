import re

import pytest
import respx
from httpx import Response

from httpx_oauth.clients.naver import NaverOAuth2, PROFILE_ENDPOINT
from httpx_oauth.errors import GetIdEmailError

client = NaverOAuth2("CLIENT_ID", "CLIENT_SECRET")


def test_naver_oauth2():
    assert client.authorize_endpoint == "https://nid.naver.com/oauth2.0/authorize"
    assert client.access_token_endpoint == "https://nid.naver.com/oauth2.0/token"
    assert client.refresh_token_endpoint == "https://nid.naver.com/oauth2.0/token"
    assert client.revoke_token_endpoint == "https://nid.naver.com/oauth2.0/token"
    assert client.base_scopes == []
    assert client.name == "naver"


profile_response = {
    "resultcode": "00",
    "message": "success",
    "response": {
        "id": "424242424242424242424242",
        "email": "example@naver.com",
    }
}

profile_no_email_response = {
    "resultcode": "00",
    "message": "success",
    "response": {
        "id": "424242424242424242424242",
    }
}


class TestDiscordGetIdEmail:
    @pytest.mark.asyncio
    @respx.mock
    async def test_success(self, get_respx_call_args):
        request = respx.post(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(200, json=profile_response)
        )

        user_id, user_email = await client.get_id_email("TOKEN")
        _, headers, _ = await get_respx_call_args(request)

        assert headers["Authorization"] == "Bearer TOKEN"
        assert headers["Accept"] == "application/json"
        assert user_id == "424242424242424242424242"
        assert user_email == "example@naver.com"

    @pytest.mark.asyncio
    @respx.mock
    async def test_error(self):
        respx.post(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(400, json={"error": "message"})
        )

        with pytest.raises(GetIdEmailError) as excinfo:
            await client.get_id_email("TOKEN")

        assert type(excinfo.value.args[0]) == dict
        assert excinfo.value.args[0] == {"error": "message"}

    @pytest.mark.asyncio
    @respx.mock
    async def test_no_email(self):
        respx.post(re.compile(f"^{PROFILE_ENDPOINT}$")).mock(
            return_value=Response(200, json=profile_no_email_response)
        )

        user_id, user_email = await client.get_id_email("TOKEN")

        assert user_id == "424242424242424242424242"
        assert user_email is None
