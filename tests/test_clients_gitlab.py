import json
import re

import pytest
import respx
from httpx import HTTPError, Response

from httpx_oauth.clients.gitlab import PROFILE_ENDPOINT, GitLabOAuth2
from httpx_oauth.exceptions import GetIdEmailError
from httpx_oauth.oauth2 import OAuth2Token, RefreshTokenError

client = GitLabOAuth2("CLIENT_ID", "CLIENT_SECRET")


def test_gitlab_oauth2():
    assert client.authorize_endpoint == "https://gitlab.com/oauth/authorize"
    assert client.access_token_endpoint == "https://gitlab.com/oauth/token"
    assert client.refresh_token_endpoint == "https://gitlab.com/oauth/token"
    assert client.revoke_token_endpoint is None
    assert client.base_scopes == ["read_user"]
    assert client.name == "gitlab"
    assert client.base_url == "https://gitlab.com"


def test_gitlab_oauth2_custom_base_url():
    custom_client = GitLabOAuth2(
        "CLIENT_ID", "CLIENT_SECRET", base_url="https://gitlab.example.com"
    )
    assert custom_client.authorize_endpoint == "https://gitlab.example.com/oauth/authorize"
    assert custom_client.access_token_endpoint == "https://gitlab.example.com/oauth/token"
    assert custom_client.refresh_token_endpoint == "https://gitlab.example.com/oauth/token"
    assert custom_client.revoke_token_endpoint is None
    assert custom_client.base_scopes == ["read_user"]
    assert custom_client.name == "gitlab"
    assert custom_client.base_url == "https://gitlab.example.com"


def test_gitlab_oauth2_custom_base_url_trailing_slash():
    custom_client = GitLabOAuth2(
        "CLIENT_ID", "CLIENT_SECRET", base_url="https://gitlab.example.com/"
    )
    assert custom_client.base_url == "https://gitlab.example.com"
    assert custom_client.authorize_endpoint == "https://gitlab.example.com/oauth/authorize"


def test_gitlab_oauth2_custom_name():
    custom_client = GitLabOAuth2(
        "CLIENT_ID", "CLIENT_SECRET", name="custom_gitlab"
    )
    assert custom_client.name == "custom_gitlab"


def test_gitlab_oauth2_custom_scopes():
    custom_client = GitLabOAuth2(
        "CLIENT_ID", "CLIENT_SECRET", scopes=["read_user", "api"]
    )
    assert custom_client.base_scopes == ["read_user", "api"]


profile_response = {"id": 42, "email": "arthur@camelot.bt", "username": "arthur"}
profile_response_no_email = {"id": 42, "email": None, "username": "arthur"}


@pytest.mark.asyncio
class TestGitLabRefreshToken:
    @respx.mock
    async def test_refresh_token(self, load_mock, get_respx_call_args):
        request = respx.post(client.refresh_token_endpoint).mock(
            return_value=Response(200, json=load_mock("gitlab_success_refresh_token"))
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
            "error": "invalid_grant",
            "error_description": "The provided authorization grant is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client.",
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


class TestGitLabGetIdEmail:
    @pytest.mark.asyncio
    @respx.mock
    async def test_success(self, get_respx_call_args):
        request = respx.get(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
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
    async def test_success_no_email(self, get_respx_call_args):
        request = respx.get(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(200, json=profile_response_no_email)
        )

        user_id, user_email = await client.get_id_email("TOKEN")
        _, headers, _ = await get_respx_call_args(request)

        assert headers["Authorization"] == "Bearer TOKEN"
        assert headers["Accept"] == "application/json"
        assert user_id == "42"
        assert user_email is None

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
    async def test_custom_base_url(self):
        custom_client = GitLabOAuth2(
            "CLIENT_ID", "CLIENT_SECRET", base_url="https://gitlab.example.com"
        )
        custom_profile_endpoint = "https://gitlab.example.com/api/v4/user"

        request = respx.get(re.compile(f"^{custom_profile_endpoint}")).mock(
            return_value=Response(200, json=profile_response)
        )

        user_id, user_email = await custom_client.get_id_email("TOKEN")

        assert user_id == "42"
        assert user_email == "arthur@camelot.bt"
        assert request.called


class TestGitLabGetProfile:
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_profile_success(self, load_mock, get_respx_call_args):
        request = respx.get(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(200, json=load_mock("gitlab_success_profile"))
        )

        profile = await client.get_profile("TOKEN")
        _, headers, _ = await get_respx_call_args(request)

        assert headers["Authorization"] == "Bearer TOKEN"
        assert headers["Accept"] == "application/json"
        assert profile["id"] == 42
        assert profile["username"] == "arthur"
        assert profile["email"] == "arthur@camelot.bt"
        assert profile["name"] == "Arthur Pendragon"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_profile_error(self):
        respx.get(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(401, json={"error": "unauthorized"})
        )

        from httpx_oauth.exceptions import GetProfileError

        with pytest.raises(GetProfileError) as excinfo:
            await client.get_profile("TOKEN")

        assert isinstance(excinfo.value.response, Response)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_profile_custom_base_url(self, load_mock):
        custom_client = GitLabOAuth2(
            "CLIENT_ID", "CLIENT_SECRET", base_url="https://gitlab.example.com"
        )
        custom_profile_endpoint = "https://gitlab.example.com/api/v4/user"

        request = respx.get(re.compile(f"^{custom_profile_endpoint}")).mock(
            return_value=Response(200, json=load_mock("gitlab_success_profile"))
        )

        profile = await custom_client.get_profile("TOKEN")

        assert profile["id"] == 42
        assert request.called

