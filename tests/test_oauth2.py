import time

import pytest
import respx

from httpx_oauth.oauth2 import (
    GetAccessTokenError,
    OAuth2,
    OAuth2Token,
    RefreshTokenNotSupportedError,
    RefreshTokenError,
    RevokeTokenError,
    RevokeTokenNotSupportedError,
)

CLIENT_ID = "CLIENT_ID"
CLIENT_SECRET = "CLIENT_SECRET"
AUTHORIZE_ENDPOINT = "https://www.camelot.bt/authorize"
ACCESS_TOKEN_ENDPOINT = "https://www.camelot.bt/access-token"
REDIRECT_URI = "https://www.tintagel.bt/oauth-callback"
REFRESH_TOKEN_ENDPOINT = "https://www.camelot.bt/refresh"
REVOKE_TOKEN_ENDPOINT = "https://www.camelot.bt/revoke"

client = OAuth2(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_ENDPOINT, ACCESS_TOKEN_ENDPOINT)

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


class TestOAuth2Token:
    @pytest.mark.parametrize(
        "expires_at,expired", [(0, True), (time.time() + 3600, False)]
    )
    def test_expires_at(self, expires_at, expired):
        token = OAuth2Token({"access_token": "ACCESS_TOKEN", "expires_at": expires_at})

        assert token["access_token"] == "ACCESS_TOKEN"
        assert token.is_expired() is expired

    def test_expires_in(self):
        token = OAuth2Token({"access_token": "ACCESS_TOKEN", "expires_in": 3600})

        assert token["access_token"] == "ACCESS_TOKEN"
        assert token.is_expired() is False

    def test_no_expire(self):
        token = OAuth2Token({"access_token": "ACCESS_TOKEN"})

        assert token["access_token"] == "ACCESS_TOKEN"
        assert token.is_expired() is False


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

    @pytest.mark.asyncio
    async def test_get_authorization_url_with_extras_params(self):
        authorization_url = await client.get_authorization_url(
            REDIRECT_URI, extras_params={"PARAM1": "VALUE1", "PARAM2": "VALUE2"},
        )
        assert "PARAM1=VALUE1" in authorization_url
        assert "PARAM2=VALUE2" in authorization_url


class TestGetAccessToken:
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_access_token(self, load_mock, get_respx_call_args):
        request = respx.post(
            client.access_token_endpoint,
            content=load_mock("google_success_access_token"),
        )
        access_token = await client.get_access_token("CODE", REDIRECT_URI)

        url, headers, content = await get_respx_call_args(request)
        assert headers["Content-Type"] == "application/x-www-form-urlencoded"
        assert "grant_type=authorization_code" in content
        assert "code=CODE" in content
        assert "redirect_uri=https%3A%2F%2Fwww.tintagel.bt%2Foauth-callback" in content
        assert f"client_id={CLIENT_ID}" in content
        assert f"client_secret={CLIENT_SECRET}" in content

        assert type(access_token) == OAuth2Token
        assert "access_token" in access_token
        assert "token_type" in access_token
        assert access_token.is_expired() is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_access_token_error(self, load_mock):
        respx.post(
            client.access_token_endpoint, status_code=400, content=load_mock("error"),
        )

        with pytest.raises(GetAccessTokenError) as excinfo:
            await client.get_access_token("CODE", REDIRECT_URI)
        assert type(excinfo.value.args[0]) == dict
        assert "error" in excinfo.value.args[0]


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

        url, headers, content = await get_respx_call_args(request)
        assert headers["Content-Type"] == "application/x-www-form-urlencoded"
        assert "grant_type=refresh_token" in content
        assert "refresh_token=REFRESH_TOKEN" in content
        assert f"client_id={CLIENT_ID}" in content
        assert f"client_secret={CLIENT_SECRET}" in content

        assert type(access_token) == OAuth2Token
        assert "access_token" in access_token
        assert "token_type" in access_token
        assert access_token.is_expired() is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_refresh_token_error(self, load_mock):
        respx.post(
            client_refresh.refresh_token_endpoint,
            status_code=400,
            content=load_mock("error"),
        )

        with pytest.raises(RefreshTokenError) as excinfo:
            await client_refresh.refresh_token("REFRESH_TOKEN")
        assert type(excinfo.value.args[0]) == dict
        assert "error" in excinfo.value.args[0]


class TestRevokeToken:
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

        url, headers, content = await get_respx_call_args(request)
        assert headers["Content-Type"] == "application/x-www-form-urlencoded"
        assert "token=TOKEN" in content
        assert "token_type_hint=TOKEN_TYPE_HINT" in content

    @pytest.mark.asyncio
    @respx.mock
    async def test_revoke_token_error(self, load_mock):
        respx.post(
            client_revoke.revoke_token_endpoint,
            status_code=400,
            content=load_mock("error"),
        )

        with pytest.raises(RevokeTokenError) as excinfo:
            await client_revoke.revoke_token("TOKEN", "TOKEN_TYPE_HINT")
        assert type(excinfo.value.args[0]) == dict
        assert "error" in excinfo.value.args[0]


class TestGetIdEmail:
    @pytest.mark.asyncio
    async def test_not_implemented(self):
        with pytest.raises(NotImplementedError):
            await client.get_id_email("TOKEN")
