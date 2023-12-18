import base64
import re
from typing import Callable
from urllib.parse import parse_qsl

import httpx
import pytest
import respx

import httpx_oauth.clients.reddit as reddit
import httpx_oauth.oauth2 as oauth
from httpx_oauth.errors import GetIdEmailError

FAKE_CLIENT_ID = "fake-client-id-1234567"
FAKE_CLIENT_SECRET = "fake-client-secret-12345678901"
FAKE_AUTHORIZATION_CODE = "fake-authorization-code-123456"
FAKE_REDIRECT_URI = "http://example.com/redirect/"
FAKE_ACCESS_TOKEN = "12345678-fake-access-token-123456789012"
FAKE_REFRESH_TOKEN = "12345678-fake-refresh-token-12345678901"


client = reddit.RedditOAuth2(FAKE_CLIENT_ID, FAKE_CLIENT_SECRET)

response_unauthorized = httpx.Response(
    httpx.codes.UNAUTHORIZED,
    json={
        "error": httpx.codes.UNAUTHORIZED,
        "message": "Unauthorized",
    },
)


def b64encode(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("utf-8")


def require_auth(response: httpx.Response) -> Callable[[httpx.Request], httpx.Response]:
    def require_auth_inner(request: httpx.Request) -> httpx.Response:
        expected_auth_header = (
            f"Basic {b64encode(f'{FAKE_CLIENT_ID}:{FAKE_CLIENT_SECRET}')}"
        )

        if request.headers.get("Authorization", None) != expected_auth_header:
            return response_unauthorized

        return response

    return require_auth_inner


def test_reddit_defaults():
    assert client.authorize_endpoint == "https://www.reddit.com/api/v1/authorize"
    assert client.access_token_endpoint == "https://www.reddit.com/api/v1/access_token"
    assert client.refresh_token_endpoint == "https://www.reddit.com/api/v1/access_token"
    assert client.revoke_token_endpoint == "https://www.reddit.com/api/v1/revoke_token"
    assert client.base_scopes == ["identity"]
    assert client.name == "reddit"


class TestRedditGetAccessToken:
    response_success = httpx.Response(
        httpx.codes.OK,
        json={
            "access_token": FAKE_ACCESS_TOKEN,
            "token_type": "bearer",
            "expires_in": 3600,
            "scope": "identity",
        },
    )

    response_error = httpx.Response(
        httpx.codes.OK,  # sic, Reddit returns 200 upon errors on this endpoint
        json={
            "error": "invalid_grant",
        },
    )

    @pytest.mark.asyncio
    @respx.mock
    async def test_bad_auth(self):
        respx.post(re.compile(f"^{reddit.ACCESS_TOKEN_ENDPOINT}")).mock(
            side_effect=require_auth(self.response_success),
        )

        invalid_client = reddit.RedditOAuth2(
            "INVALID_CLIENT_ID", "INVALID_CLIENT_SECRET"
        )

        with pytest.raises(oauth.GetAccessTokenError) as e:
            await invalid_client.get_access_token(
                FAKE_AUTHORIZATION_CODE, FAKE_REDIRECT_URI
            )

        assert isinstance(e.value.args[0], dict)
        assert e.value.args[0] == response_unauthorized.json()

    @pytest.mark.asyncio
    @respx.mock
    async def test_success(self, get_respx_call_args):
        request = respx.post(re.compile(f"^{reddit.ACCESS_TOKEN_ENDPOINT}")).mock(
            side_effect=require_auth(self.response_success),
        )

        token = await client.get_access_token(
            FAKE_AUTHORIZATION_CODE, FAKE_REDIRECT_URI
        )
        url, headers, content = await get_respx_call_args(request)
        content_url_decoded = parse_qsl(content)

        assert ("grant_type", "authorization_code") in content_url_decoded
        assert ("code", FAKE_AUTHORIZATION_CODE) in content_url_decoded
        assert ("redirect_uri", FAKE_REDIRECT_URI) in content_url_decoded

        # Check the subset, since httpx-oauth lib also adds a calculated "expires_at"
        assert self.response_success.json().items() <= token.items()

    @pytest.mark.asyncio
    @respx.mock
    async def test_error(self):
        respx.post(re.compile(f"^{reddit.ACCESS_TOKEN_ENDPOINT}")).mock(
            side_effect=require_auth(self.response_error)
        )

        with pytest.raises(oauth.GetAccessTokenError) as e:
            await client.get_access_token(
                "INVALID_AUTHORIZATION_CODE", FAKE_REDIRECT_URI
            )

        assert isinstance(e.value.args[0], dict)
        assert e.value.args[0] == self.response_error.json()


class TestRedditRefreshToken:
    response_success = httpx.Response(
        httpx.codes.OK,
        json={
            "access_token": FAKE_ACCESS_TOKEN,
            "token_type": "bearer",
            "expires_in": 3600,
            "refresh_token": FAKE_REFRESH_TOKEN,
            "scope": "identity",
        },
    )

    response_error = httpx.Response(
        httpx.codes.BAD_REQUEST,
        json={
            "error": httpx.codes.BAD_REQUEST,
            "message": "Bad Request",
        },
    )

    @pytest.mark.asyncio
    @respx.mock
    async def test_bad_auth(self):
        respx.post(re.compile(f"^{reddit.REFRESH_ENDPOINT}")).mock(
            side_effect=require_auth(self.response_success),
        )

        invalid_client = reddit.RedditOAuth2(
            "INVALID_CLIENT_ID", "INVALID_CLIENT_SECRET"
        )

        with pytest.raises(oauth.RefreshTokenError) as e:
            await invalid_client.refresh_token(FAKE_REFRESH_TOKEN)

        assert isinstance(e.value.args[0], dict)
        assert e.value.args[0] == response_unauthorized.json()

    @pytest.mark.asyncio
    @respx.mock
    async def test_success(self, get_respx_call_args):
        request = respx.post(re.compile(f"^{reddit.REFRESH_ENDPOINT}")).mock(
            side_effect=require_auth(self.response_success),
        )

        token = await client.refresh_token(FAKE_REFRESH_TOKEN)
        url, headers, content = await get_respx_call_args(request)
        content_url_decoded = parse_qsl(content)

        assert ("grant_type", "refresh_token") in content_url_decoded
        assert ("refresh_token", FAKE_REFRESH_TOKEN) in content_url_decoded

        # Check the subset, since httpx-oauth lib also adds a calculated "expires_at"
        assert self.response_success.json().items() <= token.items()

    @pytest.mark.asyncio
    @respx.mock
    async def test_error(self):
        respx.post(re.compile(f"^{reddit.REFRESH_ENDPOINT}")).mock(
            side_effect=require_auth(self.response_error)
        )

        with pytest.raises(oauth.RefreshTokenError) as e:
            await client.refresh_token("INVALID_REFRESH_TOKEN")

        assert isinstance(e.value.args[0], dict)
        assert e.value.args[0] == self.response_error.json()


class TestRedditRevokeToken:
    @pytest.mark.asyncio
    @respx.mock
    async def test_bad_auth(self):
        respx.post(re.compile(f"^{reddit.REVOKE_ENDPOINT}")).mock(
            side_effect=require_auth(httpx.Response(httpx.codes.OK)),
        )

        invalid_client = reddit.RedditOAuth2(
            "INVALID_CLIENT_ID", "INVALID_CLIENT_SECRET"
        )

        with pytest.raises(oauth.RevokeTokenError):
            await invalid_client.revoke_token(FAKE_REFRESH_TOKEN, "refresh_token")

    @pytest.mark.asyncio
    @respx.mock
    async def test_success(self, get_respx_call_args):
        request = respx.post(re.compile(f"^{reddit.REVOKE_ENDPOINT}")).mock(
            side_effect=require_auth(httpx.Response(httpx.codes.OK)),
        )

        await client.revoke_token(FAKE_REFRESH_TOKEN, "refresh_token")

        url, headers, content = await get_respx_call_args(request)
        content_url_decoded = parse_qsl(content)

        assert ("token", FAKE_REFRESH_TOKEN) in content_url_decoded
        assert ("token_type_hint", "refresh_token") in content_url_decoded


class TestRedditGetIdEmail:
    @pytest.mark.asyncio
    @respx.mock
    async def test_success(self, load_mock, get_respx_call_args):
        request = respx.get(re.compile(f"^{reddit.IDENTITY_ENDPOINT}")).mock(
            return_value=httpx.Response(
                httpx.codes.OK, json=load_mock("reddit_success_identity")
            )
        )

        user_id, user_email = await client.get_id_email(FAKE_ACCESS_TOKEN)
        url, headers, content = await get_respx_call_args(request)

        assert headers["Authorization"] == f"Bearer {FAKE_ACCESS_TOKEN}"
        assert user_id == "TheQuickBrownCatJumpsOverTheLazyDog"
        assert user_email is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_error(self):
        respx.get(re.compile(f"^{reddit.IDENTITY_ENDPOINT}")).mock(
            # Reddit often returns HTML in case of a bad request
            return_value=httpx.Response(httpx.codes.BAD_REQUEST, html="<!doctype html>")
        )

        with pytest.raises(GetIdEmailError) as excinfo:
            await client.get_id_email(FAKE_ACCESS_TOKEN)

        assert isinstance(excinfo.value.args[0], dict)
        assert excinfo.value.args[0] == {"error": httpx.codes.BAD_REQUEST}
