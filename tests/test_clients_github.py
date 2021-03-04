import re

import pytest
import respx
from httpx import Response

from httpx_oauth.clients.github import GitHubOAuth2, PROFILE_ENDPOINT, EMAILS_ENDPOINT
from httpx_oauth.errors import GetIdEmailError

client = GitHubOAuth2("CLIENT_ID", "CLIENT_SECRET")


def test_github_oauth2():
    assert client.authorize_endpoint == "https://github.com/login/oauth/authorize"
    assert client.access_token_endpoint == "https://github.com/login/oauth/access_token"
    assert client.refresh_token_endpoint is None
    assert client.revoke_token_endpoint is None
    assert client.base_scopes == ["user", "user:email"]
    assert client.name == "github"


profile_response = {"id": 42, "email": "arthur@camelot.bt"}
profile_response_no_public_email = {"id": 42, "email": None}
emails_response = [{"email": "arthur@camelot.bt"}]


class TestGitHubGetIdEmail:
    @pytest.mark.asyncio
    @respx.mock
    async def test_success(self, get_respx_call_args):
        request = respx.get(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(200, json=profile_response)
        )

        user_id, user_email = await client.get_id_email("TOKEN")
        _, headers, _ = await get_respx_call_args(request)

        assert headers["Authorization"] == "token TOKEN"
        assert headers["Accept"] == "application/json"
        assert user_id == "42"
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

    @pytest.mark.asyncio
    @respx.mock
    async def test_no_public_email_success(self, get_respx_call_args):
        respx.get(re.compile(f"^{PROFILE_ENDPOINT}$")).mock(
            return_value=Response(200, json=profile_response_no_public_email)
        )
        request = respx.get(re.compile(f"^{EMAILS_ENDPOINT}")).mock(
            return_value=Response(200, json=emails_response)
        )

        user_id, user_email = await client.get_id_email("TOKEN")
        _, headers, _ = await get_respx_call_args(request)

        assert headers["Authorization"] == "token TOKEN"
        assert headers["Accept"] == "application/json"
        assert user_id == "42"
        assert user_email == "arthur@camelot.bt"

    @pytest.mark.asyncio
    @respx.mock
    async def test_no_public_email_error(self):
        respx.get(re.compile(f"^{PROFILE_ENDPOINT}$")).mock(
            return_value=Response(200, json=profile_response_no_public_email)
        )
        respx.get(re.compile(f"^{EMAILS_ENDPOINT}")).mock(
            return_value=Response(400, json={"error": "message"})
        )

        with pytest.raises(GetIdEmailError) as excinfo:
            await client.get_id_email("TOKEN")

        assert type(excinfo.value.args[0]) == dict
        assert excinfo.value.args[0] == {"error": "message"}
