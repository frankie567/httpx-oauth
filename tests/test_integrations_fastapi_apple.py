# tests/test_integrations_fastapi_apple.py

import json

import pytest
import respx
from fastapi import Depends, FastAPI
from httpx import Response
from starlette import status
from starlette.testclient import TestClient

from httpx_oauth.clients.apple import AppleOAuth2
from httpx_oauth.integrations.fastapi import OAuth2AuthorizeCallback

########################################
# MOCKED .well-known CONFIG & VALID KEY
########################################

# Mock data from https://appleid.apple.com/.well-known/openid-configuration
APPLE_CONFIG = {
    "issuer": "https://appleid.apple.com",
    "authorization_endpoint": "https://appleid.apple.com/auth/authorize",
    "token_endpoint": "https://appleid.apple.com/auth/token",
    "userinfo_endpoint": "https://appleid.apple.com/auth/userinfo",
    "grant_types_supported": ["authorization_code", "refresh_token"],
    "token_endpoint_auth_methods_supported": ["client_secret_post"],
}

TEST_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQgO/ZNqY6LDV2I40Sx
WUkqFZ5trpigPFtp4xTVqESj/o6gCgYIKoZIzj0DAQehRANCAATvBQgsrLhgNlob
ecSnPVbTXhMZGVkUZ812GLf2FnMfK643lq6vnHwAusNl7K9k9QVTQ/VskYd1Bedo
TvVZDLvp
-----END PRIVATE KEY-----"""


########################################
# TEST APP + TWO CALLBACK INSTANCES
########################################

MOCK_REDIRECT_URL = "https://www.example.com/apple-redirect"
CALLBACK_ROUTE_NAME = "apple-callback"

########################################
# FIXTURES
########################################


@pytest.fixture
def apple_oauth_client():
    """Fixture that creates an AppleOAuth2 client with test credentials."""
    return AppleOAuth2(
        client_id="com.example.service",
        team_id="ABCD1234EF",
        key_id="ABC123DEFG",
        private_key=TEST_PRIVATE_KEY,
    )


@pytest.fixture
def apple_callback_route_name(apple_oauth_client):
    """Fixture that creates a callback using route_name."""
    return OAuth2AuthorizeCallback(
        client=apple_oauth_client,
        route_name=CALLBACK_ROUTE_NAME,
        include_raw_data=True,
    )


@pytest.fixture
def apple_callback_redirect_url(apple_oauth_client):
    """Fixture that creates a callback using redirect_url."""
    return OAuth2AuthorizeCallback(
        client=apple_oauth_client,
        redirect_url=MOCK_REDIRECT_URL,
        include_raw_data=True,
    )


@pytest.fixture
def app(apple_callback_route_name, apple_callback_redirect_url):
    """Fixture that creates the FastAPI test app with the Apple OAuth routes."""
    app = FastAPI()

    @app.get("/apple-callback", name=CALLBACK_ROUTE_NAME)
    async def apple_callback():
        """Callback route used when route_name=apple-callback."""
        return {"msg": "OK - Apple Callback", "route": "apple_callback"}

    @app.post("/authorize-apple-route-name", name="authorize-apple-route-name")
    async def authorize_apple_route_name(
        access_token_state_raw=Depends(apple_callback_route_name),
    ):
        """POST endpoint using route_name in the callback."""
        return access_token_state_raw

    @app.post("/authorize-apple-redirect-url", name="authorize-apple-redirect-url")
    async def authorize_apple_redirect_url(
        access_token_state_raw=Depends(apple_callback_redirect_url),
    ):
        """POST endpoint using an explicit redirect_url in the callback."""
        return access_token_state_raw

    return app


@pytest.fixture
def test_client(app):
    """Fixture that creates a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def patch_get_access_token(mocker, apple_oauth_client):
    """Fixture to patch the get_access_token method of the Apple client."""

    def _patch(return_value=None, side_effect=None):
        return mocker.patch.object(
            apple_oauth_client,
            "get_access_token",
            return_value=return_value,
            side_effect=side_effect,
        )

    return _patch


@pytest.fixture
def mock_apple_well_known():
    with respx.mock:
        respx.get("https://appleid.apple.com/.well-known/openid-configuration").mock(
            return_value=Response(200, json=APPLE_CONFIG)
        )
        yield


########################################
# TESTS
########################################


@pytest.mark.usefixtures("mock_apple_well_known")
@pytest.mark.parametrize(
    "url_route,expected_redirect",
    [
        ("/authorize-apple-route-name", "http://testserver/apple-callback"),
        ("/authorize-apple-redirect-url", MOCK_REDIRECT_URL),
    ],
)
class TestAppleIntegrationFastAPI:
    """
    Test suite covering Apple sign-in flows via FastAPI integration.
    """

    def test_success_form_post(
        self,
        url_route,
        expected_redirect,
        patch_get_access_token,
        test_client,
    ):
        """
        Valid form: code, state, user JSON => returns (access_token, state, raw_data).
        """
        patch_get_access_token(return_value="MOCK_APPLE_TOKEN")

        user_payload = {
            "name": {"firstName": "Joe", "lastName": "Shmoe"},
            "email": "joe@example.com",
        }
        resp = test_client.post(
            url_route,
            data={
                "code": "APPLE_CODE",
                "state": "APPLE_STATE",
                "user": json.dumps(user_payload),
            },
        )
        assert resp.status_code == status.HTTP_200_OK, resp.text

        data = resp.json()
        # Expect a 3-element list
        assert len(data) == 2
        access_token, returned_state = data
        assert access_token == "MOCK_APPLE_TOKEN"
        assert returned_state == "APPLE_STATE"


@pytest.mark.asyncio
class TestGetAppleAuthorizationURL:
    async def test_get_authorization_url(self, apple_oauth_client):
        authorization_url = await apple_oauth_client.get_authorization_url(
            redirect_uri=MOCK_REDIRECT_URL
        )
        assert "response_mode=form_post" in authorization_url
