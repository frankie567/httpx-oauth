import re

import pytest
import respx
from httpx import Response

from httpx_oauth.clients.kakao import KakaoOAuth2, PROFILE_ENDPOINT
from httpx_oauth.errors import GetIdEmailError

client = KakaoOAuth2("CLIENT_ID", "CLIENT_SECRET")


def test_kakao_oauth2():
    assert client.authorize_endpoint == "https://kauth.kakao.com/oauth/authorize"
    assert client.access_token_endpoint == "https://kauth.kakao.com/oauth/token"
    assert client.refresh_token_endpoint == "https://kauth.kakao.com/oauth/token"
    assert client.base_scopes == ["account_email",]
    assert client.name == "kakao"


profile_response = {
    "id": 4242424242,
    "kakao_account": {
        "email_needs_agreement": False,
        "is_email_valid": True,
        "is_email_verified": True,
        "email": "arthur@camelot.bt"
    }
}


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

        assert type(excinfo.value.args[0]) == dict
        assert excinfo.value.args[0] == {"msg": "failed message"}
