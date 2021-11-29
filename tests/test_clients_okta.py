import re

import pytest
import respx
from httpx import Response

from httpx_oauth.clients.okta import OktaOAuth2
from httpx_oauth.errors import GetIdEmailError

OKTA_BASE_URL = "test-okta-base-url.okta.com"

client = OktaOAuth2("CLIENT_ID", "CLIENT_SECRET", OKTA_BASE_URL)


def test_okta_oauth2():
    assert client.authorize_endpoint == f"https://{OKTA_BASE_URL}/oauth2/v1/authorize"
    assert client.access_token_endpoint == f"https://{OKTA_BASE_URL}/oauth2/v1/token"
    assert client.refresh_token_endpoint == f"https://{OKTA_BASE_URL}/oauth2/v1/token"
    assert client.revoke_token_endpoint == f"https://{OKTA_BASE_URL}/oauth2/v1/revoke"
    assert client.base_scopes == ["openid", "email"]
    assert client.name == "okta"


profile_response = {"sub": 42, "email": "arthur@camelot.bt"}
profile_response_no_public_email = {"sub": 42, "email": None}


class TestOktaGetIdEmail:
    @pytest.mark.asyncio
    @respx.mock
    async def test_success(self, get_respx_call_args):
        request = respx.get(re.compile(f"^{client.profile}")).mock(
            return_value=Response(200, json=profile_response)
        )

        user_id, user_email = await client.get_id_email("TOKEN")
        _, headers, _ = await get_respx_call_args(request)

        assert headers["Authorization"] == "Bearer TOKEN"
        assert headers["Accept"] == "application/json"
        assert user_id == "42"
        assert user_email == "arthur@camelot.bt"

    @pytest.mark.asyncio
    @respx.mock
    async def test_error(self):
        respx.get(re.compile(f"^{client.profile}")).mock(
            return_value=Response(400, json={"error": "message"})
        )

        with pytest.raises(GetIdEmailError) as excinfo:
            await client.get_id_email("TOKEN")

        assert type(excinfo.value.args[0]) == dict
        assert excinfo.value.args[0] == {"error": "message"}
