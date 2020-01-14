import re

import pytest
import respx

from httpx_oauth.clients.github import GitHubOAuth2, PROFILE_ENDPOINT
from httpx_oauth.errors import GetIdEmailError

client = GitHubOAuth2("CLIENT_ID", "CLIENT_SECRET")


def test_github_oauth2():
    assert client.authorize_endpoint == "https://github.com/login/oauth/authorize"
    assert client.access_token_endpoint == "https://github.com/login/oauth/access_token"
    assert client.refresh_token_endpoint is None
    assert client.revoke_token_endpoint is None
    assert client.base_scopes == ["user"]
    assert client.name == "github"


profile_response = {"id": 42, "email": "arthur@camelot.bt"}


class TestGitHubGetIdEmail:
    @pytest.mark.asyncio
    @respx.mock
    async def test_success(self, get_respx_call_args):
        request = respx.get(
            re.compile(f"^{PROFILE_ENDPOINT}"),
            status_code=200,
            content=profile_response,
        )

        user_id, user_email = await client.get_id_email("TOKEN")
        url, headers, content = await get_respx_call_args(request)

        assert headers["Authorization"] == "token TOKEN"
        assert user_id == "42"
        assert user_email == "arthur@camelot.bt"

    @pytest.mark.asyncio
    @respx.mock
    async def test_error(self, get_respx_call_args):
        respx.get(
            re.compile(f"^{PROFILE_ENDPOINT}"),
            status_code=400,
            content={"error": "message"},
        )

        with pytest.raises(GetIdEmailError) as excinfo:
            await client.get_id_email("TOKEN")

        assert type(excinfo.value.args[0]) == dict
        assert excinfo.value.args[0] == {"error": "message"}
