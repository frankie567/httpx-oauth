import re

import pytest
import respx
from httpx import Response

from httpx_oauth.clients.kakao import PROFILE_ENDPOINT, KakaoOAuth2
from httpx_oauth.errors import GetIdEmailError

client = KakaoOAuth2("CLIENT_ID", "CLIENT_SECRET")


def test_kakao_oauth2():
    assert client.authorize_endpoint == "https://kauth.kakao.com/oauth/authorize"
    assert client.access_token_endpoint == "https://kauth.kakao.com/oauth/token"
    assert client.refresh_token_endpoint == "https://kauth.kakao.com/oauth/token"
    assert client.revoke_token_endpoint == "https://kapi.kakao.com/v1/user/unlink"
    assert client.base_scopes == ["profile_nickname", "account_email"]
    assert client.name == "kakao"


profile_response = {"id": 4242424242, "kakao_account": {"email": "arthur@camelot.bt"}}

profile_no_email_response = {"id": 4242424242, "kakao_account": {}}


class TestKakaoGetIdEmail:
    @pytest.mark.asyncio
    @respx.mock
    async def test_success(self, get_respx_call_args):
        request = respx.post(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(200, json=profile_response)
        )

        user_id, user_email = await client.get_id_email("TOKEN")
        url, headers, _ = await get_respx_call_args(request)

        assert headers["Authorization"] == "Bearer TOKEN"
        assert headers["Accept"] == "application/json"
        assert user_id == "4242424242"
        assert user_email == "arthur@camelot.bt"

    @pytest.mark.asyncio
    @respx.mock
    async def test_error(self):
        respx.post(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(400, json={"msg": "failed message"})
        )

        with pytest.raises(GetIdEmailError) as excinfo:
            await client.get_id_email("TOKEN")

        assert isinstance(excinfo.value.args[0], dict)
        assert excinfo.value.args[0] == {"msg": "failed message"}

    @pytest.mark.asyncio
    @respx.mock
    async def test_no_email(self):
        respx.post(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(200, json=profile_no_email_response)
        )

        user_id, user_email = await client.get_id_email("TOKEN")

        assert user_id == "4242424242"
        assert user_email is None
