import re

import pytest
import respx
from httpx import Response

from httpx_oauth.clients.naver import PROFILE_ENDPOINT, NaverOAuth2
from httpx_oauth.errors import GetIdEmailError
from httpx_oauth.oauth2 import RevokeTokenError

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
    },
}

profile_no_email_response = {
    "resultcode": "00",
    "message": "success",
    "response": {
        "id": "424242424242424242424242",
    },
}


class TestNaverdGetIdEmail:
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

        assert isinstance(excinfo.value.args[0], dict)
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


class TestRevokeToken:
    @pytest.mark.asyncio
    @respx.mock
    async def test_revoke_token(self, get_respx_call_args):
        request = respx.post(client.revoke_token_endpoint).mock(
            return_value=Response(200)
        )
        await client.revoke_token("TOKEN", "TOKEN_TYPE_HINT")

        url, headers, content = await get_respx_call_args(request)
        assert headers["Content-Type"] == "application/x-www-form-urlencoded"
        assert headers["Accept"] == "application/json"
        assert "token=TOKEN" in content
        assert "token_type_hint=TOKEN_TYPE_HINT" in content

    @pytest.mark.asyncio
    @respx.mock
    async def test_revoke_token_error(self):
        respx.post(client.revoke_token_endpoint).mock(
            return_value=Response(400, json={"error": "message"})
        )

        with pytest.raises(RevokeTokenError):
            await client.revoke_token("TOKEN", "TOKEN_TYPE_HINT")
