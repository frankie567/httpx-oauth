import pytest
import respx

from httpx_oauth.oauth2 import OAuth2Token
from httpx_oauth.clients.facebook import FacebookOAuth2, GetLongLivedAccessTokenError

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


class TestGetLongLivedAccessToken:
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_long_lived_access_token(self, load_mock, get_respx_call_args):
        request = respx.post(
            client.access_token_endpoint,
            content=load_mock("facebook_success_long_lived_access_token"),
        )
        access_token = await client.get_long_lived_access_token("ACCESS_TOKEN")

        headers, content = await get_respx_call_args(request)
        assert headers["Content-Type"] == "application/x-www-form-urlencoded"
        assert "grant_type=fb_exchange_token" in content
        assert "fb_exchange_token=ACCESS_TOKEN" in content
        assert f"client_id={CLIENT_ID}" in content
        assert f"client_secret={CLIENT_SECRET}" in content

        assert type(access_token) == OAuth2Token
        assert "access_token" in access_token
        assert "token_type" in access_token
        assert access_token.is_expired() is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_long_lived_access_token_error(self, load_mock):
        respx.post(
            client.access_token_endpoint, status_code=400, content=load_mock("error"),
        )

        with pytest.raises(GetLongLivedAccessTokenError) as excinfo:
            await client.get_long_lived_access_token("ACCESS_TOKEN")
        assert type(excinfo.value.args[0]) == dict
        assert "error" in excinfo.value.args[0]
