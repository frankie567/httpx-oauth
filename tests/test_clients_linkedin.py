import re

import pytest
import respx

from httpx_oauth.clients.linkedin import LinkedInOAuth2, PROFILE_ENDPOINT
from httpx_oauth.errors import GetProfileError

client = LinkedInOAuth2("CLIENT_ID", "CLIENT_SECRET")


def test_linkedin_oauth2():

    assert (
        client.authorize_endpoint == "https://www.linkedin.com/oauth/v2/authorization"
    )
    assert (
        client.access_token_endpoint == "https://www.linkedin.com/oauth/v2/accessToken"
    )
    assert (
        client.refresh_token_endpoint == "https://www.linkedin.com/oauth/v2/accessToken"
    )
    assert client.base_scopes == ["r_basicprofile"]
    assert client.revoke_token_endpoint is None
    assert client.name == "linkedin"


class TestLinkedInGetProfile:
    @pytest.mark.asyncio
    @respx.mock
    async def test_linkedin_get_profile(self, get_respx_call_args):
        request = respx.get(
            re.compile(f"^{PROFILE_ENDPOINT}"), status_code=200, content={"foo": "bar"}
        )

        result = await client.get_profile("TOKEN")
        url, headers, content = await get_respx_call_args(request)

        assert headers["Authorization"] == "Bearer TOKEN"
        assert result == {"foo": "bar"}

    @pytest.mark.asyncio
    @respx.mock
    async def test_linkedin_get_profile_error(self, get_respx_call_args):
        respx.get(
            re.compile(f"^{PROFILE_ENDPOINT}"), status_code=400, content={"foo": "bar"}
        )

        with pytest.raises(GetProfileError) as excinfo:
            await client.get_profile("TOKEN")

        assert type(excinfo.value.args[0]) == dict
        assert excinfo.value.args[0] == {"foo": "bar"}
