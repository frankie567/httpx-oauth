import pytest
from litestar import Litestar, get
from litestar import status_codes as status
from litestar.di import Provide
from litestar.params import Dependency
from litestar.testing import TestClient
from pytest_mock import MockerFixture

from httpx_oauth.integrations.litestar import AccessTokenState, OAuth2AuthorizeCallback
from httpx_oauth.oauth2 import GetAccessTokenError, OAuth2

CLIENT_ID = "CLIENT_ID"
CLIENT_SECRET = "CLIENT_SECRET"
AUTHORIZE_ENDPOINT = "https://www.camelot.bt/authorize"
ACCESS_TOKEN_ENDPOINT = "https://www.camelot.bt/access-token"
REDIRECT_URL = "https://www.tintagel.bt/callback"
ROUTE_NAME = "callback"

client = OAuth2(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_ENDPOINT, ACCESS_TOKEN_ENDPOINT)
oauth2_authorize_callback_route_name = OAuth2AuthorizeCallback(
    client, route_name=ROUTE_NAME
)
oauth2_authorize_callback_redirect_url = OAuth2AuthorizeCallback(
    client, redirect_url=REDIRECT_URL
)


@get(
    "/authorize-route-name",
    dependencies={"access_token_state": Provide(oauth2_authorize_callback_route_name)},
)
async def authorize_route_name(
    access_token_state: AccessTokenState = Dependency(skip_validation=True),
) -> AccessTokenState:
    return access_token_state


@get(
    "/authorize-redirect-url",
    dependencies={
        "access_token_state": Provide(oauth2_authorize_callback_redirect_url)
    },
)
async def authorize_redirect_url(
    access_token_state: AccessTokenState = Dependency(skip_validation=True),
) -> AccessTokenState:
    return access_token_state


@get("/callback", name="callback")
async def callback() -> dict:
    return {}


app = Litestar(route_handlers=[authorize_route_name, authorize_redirect_url, callback])

test_client = TestClient(app=app)


@pytest.mark.parametrize(
    "route,expected_redirect_url",
    [
        ("/authorize-route-name", "http://testserver.local/callback"),
        ("/authorize-redirect-url", "https://www.tintagel.bt/callback"),
    ],
)
class TestOAuth2AuthorizeCallback:
    def test_oauth2_authorize_missing_code(self, route, expected_redirect_url):
        response = test_client.get(route)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_oauth2_authorize_error(self, route, expected_redirect_url):
        response = test_client.get(route, params={"error": "access_denied"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"status_code": 400, "detail": "access_denied"}

    def test_oauth2_authorize_get_access_token_error(
        self, mocker: MockerFixture, route, expected_redirect_url
    ):
        get_access_token_mock = mocker.patch.object(
            client, "get_access_token", side_effect=GetAccessTokenError("ERROR")
        )

        response = test_client.get(route, params={"code": "CODE"})

        get_access_token_mock.assert_called_once_with(
            "CODE", expected_redirect_url, None
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        # by default, litestar will only return `Internal Server Error` as the detail on a response.
        # we are adding the ERROR to the `extra` payload
        assert response.json() == {
            "status_code": 500,
            "detail": "Internal Server Error",
            "extra": {"message": "ERROR"},
        }

    def test_oauth2_authorize_without_state(
        self, patch_async_method, route, expected_redirect_url
    ):
        patch_async_method(client, "get_access_token", return_value="ACCESS_TOKEN")

        response = test_client.get(route, params={"code": "CODE"})

        client.get_access_token.assert_called()
        client.get_access_token.assert_called_once_with(
            "CODE", expected_redirect_url, None
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == ["ACCESS_TOKEN", None]

    def test_oauth2_authorize_code_verifier_without_state(
        self, patch_async_method, route, expected_redirect_url
    ):
        patch_async_method(client, "get_access_token", return_value="ACCESS_TOKEN")

        response = test_client.get(
            route, params={"code": "CODE", "code_verifier": "CODE_VERIFIER"}
        )

        client.get_access_token.assert_called()
        client.get_access_token.assert_called_once_with(
            "CODE", expected_redirect_url, "CODE_VERIFIER"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == ["ACCESS_TOKEN", None]

    def test_oauth2_authorize_with_state(
        self, patch_async_method, route, expected_redirect_url
    ):
        patch_async_method(client, "get_access_token", return_value="ACCESS_TOKEN")

        response = test_client.get(route, params={"code": "CODE", "state": "STATE"})

        client.get_access_token.assert_called()
        client.get_access_token.assert_called_once_with(
            "CODE", expected_redirect_url, None
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == ["ACCESS_TOKEN", "STATE"]

    def test_oauth2_authorize_with_state_and_code_verifier(
        self, patch_async_method, route, expected_redirect_url
    ):
        patch_async_method(client, "get_access_token", return_value="ACCESS_TOKEN")

        response = test_client.get(
            route,
            params={"code": "CODE", "state": "STATE", "code_verifier": "CODE_VERIFIER"},
        )

        client.get_access_token.assert_called()
        client.get_access_token.assert_called_once_with(
            "CODE", expected_redirect_url, "CODE_VERIFIER"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == ["ACCESS_TOKEN", "STATE"]
