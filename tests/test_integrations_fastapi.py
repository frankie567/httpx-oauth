import asynctest
import pytest
from fastapi import Depends, FastAPI
from starlette import status
from starlette.testclient import TestClient

from httpx_oauth.integrations.fastapi import OAuth2AuthorizeCallback
from httpx_oauth.oauth2 import OAuth2

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
app = FastAPI()


@app.get("/authorize-route-name")
async def authorize_route_name(
    access_token_state=Depends(oauth2_authorize_callback_route_name),
):
    return access_token_state


@app.get("/authorize-redirect-url")
async def authorize_redirect_url(
    access_token_state=Depends(oauth2_authorize_callback_redirect_url),
):
    return access_token_state


@app.get("/callback", name="callback")
async def callback():
    pass


test_client = TestClient(app)


@pytest.mark.parametrize(
    "route,expected_redirect_url",
    [
        ("/authorize-route-name", "http://testserver/callback"),
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
        assert response.json() == {"detail": "access_denied"}

    def test_oauth2_authorize_without_state(self, route, expected_redirect_url):
        with asynctest.patch.object(client, "get_access_token") as mock:
            mock.return_value = "ACCESS_TOKEN"
            response = test_client.get(route, params={"code": "CODE"})

        mock.assert_called()
        mock.assert_awaited_once_with("CODE", expected_redirect_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == ["ACCESS_TOKEN", None]

    def test_oauth2_authorize_with_state(self, route, expected_redirect_url):
        with asynctest.patch.object(client, "get_access_token") as mock:
            mock.return_value = "ACCESS_TOKEN"
            response = test_client.get(route, params={"code": "CODE", "state": "STATE"})

        mock.assert_called()
        mock.assert_awaited_once_with("CODE", expected_redirect_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == ["ACCESS_TOKEN", "STATE"]
