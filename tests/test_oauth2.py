import pytest
import respx

from httpx_oauth.oauth2 import (
    OAuth2,
    RefreshTokenNotSupportedError,
    RevokeTokenNotSupportedError,
)

CLIENT_ID = "CLIENT_ID"
CLIENT_SECRET = "CLIENT_SECRET"
AUTHORIZE_ENDPOINT = "https://www.camelot.bt/authorize"
ACCESS_TOKEN_ENDPOINT = "https://www.camelot.bt/access-token"
REDIRECT_URI = "https://www.tintagel.bt/oauth-callback"
REFRESH_TOKEN_ENDPOINT = "https://www.camelot.bt/refresh"
REVOKE_TOKEN_ENDPOINT = "https://www.camelot.bt/revoke"

client = OAuth2(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_ENDPOINT, ACCESS_TOKEN_ENDPOINT,)

client_refresh = OAuth2(
    CLIENT_ID,
    CLIENT_SECRET,
    AUTHORIZE_ENDPOINT,
    ACCESS_TOKEN_ENDPOINT,
    refresh_token_endpoint=REFRESH_TOKEN_ENDPOINT,
)

client_revoke = OAuth2(
    CLIENT_ID,
    CLIENT_SECRET,
    AUTHORIZE_ENDPOINT,
    ACCESS_TOKEN_ENDPOINT,
    revoke_token_endpoint=REVOKE_TOKEN_ENDPOINT,
)


class TestGetAuthorizationURL:
    @pytest.mark.asyncio
    async def test_get_authorization_url(self):
        authorization_url = await client.get_authorization_url(REDIRECT_URI)
        assert authorization_url.startswith("https://www.camelot.bt/authorize")
        assert "response_type=code" in authorization_url
        assert f"client_id={CLIENT_ID}" in authorization_url
        assert (
            "redirect_uri=https%3A%2F%2Fwww.tintagel.bt%2Foauth-callback"
            in authorization_url
        )

    @pytest.mark.asyncio
    async def test_get_authorization_url_with_state(self):
        authorization_url = await client.get_authorization_url(
            REDIRECT_URI, state="STATE",
        )
        assert "state=STATE" in authorization_url

    @pytest.mark.asyncio
    async def test_get_authorization_url_with_scopes(self):
        authorization_url = await client.get_authorization_url(
            REDIRECT_URI, scope=["SCOPE1", "SCOPE2", "SCOPE3"],
        )
        assert "scope=SCOPE1+SCOPE2+SCOPE3" in authorization_url


class TestGetAccessToken:
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_access_token(self, load_mock, get_respx_call_args):
        request = respx.post(
            client.access_token_endpoint,
            content=load_mock("google_success_access_token"),
        )
        access_token = await client.get_access_token("CODE", REDIRECT_URI)

        headers, content = get_respx_call_args(request)
        assert headers["Content-Type"] == "application/x-www-form-urlencoded"
        assert "grant_type=authorization_code" in content
        assert "code=CODE" in content
        assert "redirect_uri=https%3A%2F%2Fwww.tintagel.bt%2Foauth-callback" in content
        assert f"client_id={CLIENT_ID}" in content
        assert f"client_secret={CLIENT_SECRET}" in content

        assert type(access_token) == dict
        assert "access_token" in access_token
        assert "token_type" in access_token


class TestRefreshToken:
    @pytest.mark.asyncio
    @respx.mock
    async def test_unsupported_refresh_token(self):
        with pytest.raises(RefreshTokenNotSupportedError):
            await client.refresh_token("REFRESH_TOKEN")

    @pytest.mark.asyncio
    @respx.mock
    async def test_refresh_token(self, load_mock, get_respx_call_args):
        request = respx.post(
            client_refresh.refresh_token_endpoint,
            content=load_mock("google_success_refresh_token"),
        )
        access_token = await client_refresh.refresh_token("REFRESH_TOKEN")

        headers, content = get_respx_call_args(request)
        assert headers["Content-Type"] == "application/x-www-form-urlencoded"
        assert "grant_type=refresh_token" in content
        assert "refresh_token=REFRESH_TOKEN" in content
        assert f"client_id={CLIENT_ID}" in content
        assert f"client_secret={CLIENT_SECRET}" in content

        assert type(access_token) == dict
        assert "access_token" in access_token
        assert "token_type" in access_token


class TestRevoleToken:
    @pytest.mark.asyncio
    @respx.mock
    async def test_unsupported_revoke_token(self):
        with pytest.raises(RevokeTokenNotSupportedError):
            await client.revoke_token("TOKEN")

    @pytest.mark.asyncio
    @respx.mock
    async def test_revoke_token(self, load_mock, get_respx_call_args):
        request = respx.post(client_revoke.revoke_token_endpoint)
        await client_revoke.revoke_token("TOKEN", "TOKEN_TYPE_HINT")

        headers, content = get_respx_call_args(request)
        assert headers["Content-Type"] == "application/x-www-form-urlencoded"
        assert "token=TOKEN" in content
        assert "token_type_hint=TOKEN_TYPE_HINT" in content
