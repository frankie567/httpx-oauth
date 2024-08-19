import re

import pytest
import respx
from httpx import HTTPError, Response

from httpx_oauth.clients.facebook import (
    PROFILE_ENDPOINT,
    FacebookOAuth2,
    GetLongLivedAccessTokenError,
)
from httpx_oauth.exceptions import GetIdEmailError
from httpx_oauth.oauth2 import OAuth2Token

CLIENT_ID = "CLIENT_ID"
CLIENT_SECRET = "CLIENT_SECRET"
REDIRECT_URI = "https://www.tintagel.bt/oauth-callback"

client = FacebookOAuth2("CLIENT_ID", "CLIENT_SECRET")


def test_facebook_oauth2():
    assert client.authorize_endpoint == "https://www.facebook.com/v5.0/dialog/oauth"
    assert (
        client.access_token_endpoint
        == "https://graph.facebook.com/v5.0/oauth/access_token"
    )
    assert client.refresh_token_endpoint is None
    assert client.revoke_token_endpoint is None
    assert client.base_scopes == ["email", "public_profile"]
    assert client.name == "facebook"


@pytest.mark.asyncio
class TestGetLongLivedAccessToken:
    @respx.mock
    async def test_get_long_lived_access_token(self, load_mock, get_respx_call_args):
        request = respx.post(client.access_token_endpoint).mock(
            return_value=Response(
                200, json=load_mock("facebook_success_long_lived_access_token")
            )
        )
        access_token = await client.get_long_lived_access_token("ACCESS_TOKEN")

        url, headers, content = await get_respx_call_args(request)
        assert headers["Content-Type"] == "application/x-www-form-urlencoded"
        assert "grant_type=fb_exchange_token" in content
        assert "fb_exchange_token=ACCESS_TOKEN" in content
        assert f"client_id={CLIENT_ID}" in content
        assert f"client_secret={CLIENT_SECRET}" in content

        assert type(access_token) is OAuth2Token
        assert "access_token" in access_token
        assert "token_type" in access_token
        assert access_token.is_expired() is False

    @respx.mock
    async def test_get_long_lived_access_token_error(self, load_mock):
        respx.post(client.access_token_endpoint).mock(
            return_value=Response(400, json=load_mock("error"))
        )

        with pytest.raises(GetLongLivedAccessTokenError) as excinfo:
            await client.get_long_lived_access_token("ACCESS_TOKEN")
        assert isinstance(excinfo.value.response, Response)

    @respx.mock
    async def test_get_long_lived_access_token_http_error(self):
        respx.post(client.access_token_endpoint).mock(side_effect=HTTPError("ERROR"))

        with pytest.raises(GetLongLivedAccessTokenError) as excinfo:
            await client.get_long_lived_access_token("ACCESS_TOKEN")
        assert excinfo.value.response is None

    @respx.mock
    async def test_get_long_lived_access_token_json_error(self):
        respx.post(client.access_token_endpoint).mock(
            return_value=Response(200, text="NOT JSON")
        )

        with pytest.raises(GetLongLivedAccessTokenError) as excinfo:
            await client.get_long_lived_access_token("ACCESS_TOKEN")
        assert isinstance(excinfo.value.response, Response)


profile_response = {"id": "424242", "email": "arthur@camelot.bt"}
profile_response_no_email = {"id": "424242"}


class TestFacebookGetIdEmail:
    @pytest.mark.asyncio
    @respx.mock
    async def test_success(self, get_respx_call_args):
        request = respx.get(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(200, json=profile_response)
        )

        user_id, user_email = await client.get_id_email("TOKEN")
        url, headers, content = await get_respx_call_args(request)

        assert "access_token=TOKEN" in url.query.decode("utf-8")
        assert user_id == "424242"
        assert user_email == "arthur@camelot.bt"

    @pytest.mark.asyncio
    @respx.mock
    async def test_success_no_email(self, get_respx_call_args):
        request = respx.get(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(200, json=profile_response_no_email)
        )

        user_id, user_email = await client.get_id_email("TOKEN")
        url, headers, content = await get_respx_call_args(request)

        assert "access_token=TOKEN" in url.query.decode("utf-8")
        assert user_id == "424242"
        assert user_email is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_error(self):
        respx.get(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            Response(400, json={"error": "message"})
        )

        with pytest.raises(GetIdEmailError) as excinfo:
            await client.get_id_email("TOKEN")

        assert isinstance(excinfo.value.response, Response)
