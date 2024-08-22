import json
import re

import pytest
import respx
from httpx import HTTPError, Response

from httpx_oauth.clients.github import EMAILS_ENDPOINT, PROFILE_ENDPOINT, GitHubOAuth2
from httpx_oauth.exceptions import GetIdEmailError
from httpx_oauth.oauth2 import OAuth2Token, RefreshTokenError

client = GitHubOAuth2("CLIENT_ID", "CLIENT_SECRET")


def test_github_oauth2():
    assert client.authorize_endpoint == "https://github.com/login/oauth/authorize"
    assert client.access_token_endpoint == "https://github.com/login/oauth/access_token"
    assert (
        client.refresh_token_endpoint == "https://github.com/login/oauth/access_token"
    )
    assert client.revoke_token_endpoint is None
    assert client.base_scopes == ["user", "user:email"]
    assert client.name == "github"


profile_response = {"id": 42, "email": "arthur@camelot.bt"}
profile_response_no_public_email = {"id": 42, "email": None}
emails_response = [{"email": "arthur@camelot.bt"}]


@pytest.mark.asyncio
class TestGitHubRefreshToken:
    @respx.mock
    async def test_refresh_token(self, load_mock, get_respx_call_args):
        request = respx.post(client.refresh_token_endpoint).mock(
            return_value=Response(200, json=load_mock("github_success_refresh_token"))
        )
        access_token = await client.refresh_token("REFRESH_TOKEN")

        url, headers, content = await get_respx_call_args(request)
        assert headers["Content-Type"] == "application/x-www-form-urlencoded"
        assert headers["Accept"] == "application/json"
        assert "grant_type=refresh_token" in content
        assert "refresh_token=REFRESH_TOKEN" in content
        assert "client_id=CLIENT_ID" in content
        assert "client_secret=CLIENT_SECRET" in content

        assert type(access_token) is OAuth2Token
        assert "access_token" in access_token
        assert "token_type" in access_token
        assert access_token.is_expired() is False

    @respx.mock
    async def test_refresh_token_status_error(self, load_mock):
        respx.post(client.refresh_token_endpoint).mock(
            return_value=Response(400, json=load_mock("error"))
        )

        with pytest.raises(RefreshTokenError) as excinfo:
            await client.refresh_token("REFRESH_TOKEN")
        assert isinstance(excinfo.value.response, Response)

    @respx.mock
    async def test_refresh_token_http_error(self, load_mock):
        respx.post(client.refresh_token_endpoint).mock(side_effect=HTTPError("ERROR"))

        with pytest.raises(RefreshTokenError) as excinfo:
            await client.refresh_token("REFRESH_TOKEN")
        assert excinfo.value.response is None

    @respx.mock
    async def test_refresh_token_200_error(self):
        error_response = {
            "error": "bad_refresh_token",
            "error_description": "The refresh token passed is incorrect or expired.",
            "error_uri": "https://docs.github.com",
        }

        respx.post(client.refresh_token_endpoint).mock(
            return_value=Response(
                200,
                headers={"content-type": "application/json"},
                content=json.dumps(error_response),
            )
        )

        with pytest.raises(RefreshTokenError) as excinfo:
            await client.refresh_token("REFRESH_TOKEN")
        assert isinstance(excinfo.value.response, Response)

    @respx.mock
    async def test_refresh_token_json_error(self):
        respx.post(client.refresh_token_endpoint).mock(
            return_value=Response(200, text="NOT JSON")
        )

        with pytest.raises(RefreshTokenError) as excinfo:
            await client.refresh_token("REFRESH_TOKEN")
        assert isinstance(excinfo.value.response, Response)


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

        assert isinstance(excinfo.value.response, Response)

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

        assert isinstance(excinfo.value.response, Response)
