import re

import pytest
import respx

from httpx_oauth.clients.github import GitHubOAuth2, PROFILE_ENDPOINT
from httpx_oauth.errors import GetProfileError

client = GitHubOAuth2("CLIENT_ID", "CLIENT_SECRET")


def test_github_oauth2():
    assert client.authorize_endpoint == "https://github.com/login/oauth/authorize"
    assert client.access_token_endpoint == "https://github.com/login/oauth/access_token"
    assert client.refresh_token_endpoint is None
    assert client.revoke_token_endpoint is None
    assert client.base_scopes == ["user"]
    assert client.name == "github"


class TestGitHubGetProfile:
    @pytest.mark.asyncio
    @respx.mock
    async def test_github_get_profile(self, get_respx_call_args):
        request = respx.get(
            re.compile(f"^{PROFILE_ENDPOINT}"), status_code=200, content={"foo": "bar"}
        )

        result = await client.get_profile("TOKEN")
        url, headers, content = await get_respx_call_args(request)

        assert headers["Authorization"] == "token TOKEN"
        assert result == {"foo": "bar"}

    @pytest.mark.asyncio
    @respx.mock
    async def test_github_get_profile_error(self, get_respx_call_args):
        respx.get(
            re.compile(f"^{PROFILE_ENDPOINT}"), status_code=400, content={"foo": "bar"}
        )

        with pytest.raises(GetProfileError) as excinfo:
            await client.get_profile("TOKEN")

        assert type(excinfo.value.args[0]) == dict
        assert excinfo.value.args[0] == {"foo": "bar"}
