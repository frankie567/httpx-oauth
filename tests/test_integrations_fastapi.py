import asynctest
from fastapi import Depends, FastAPI
from starlette import status
from starlette.testclient import TestClient

from httpx_oauth.integrations.fastapi import OAuth2AuthorizeCallback
from httpx_oauth.oauth2 import OAuth2

CLIENT_ID = "CLIENT_ID"
CLIENT_SECRET = "CLIENT_SECRET"
AUTHORIZE_ENDPOINT = "https://www.camelot.bt/authorize"
ACCESS_TOKEN_ENDPOINT = "https://www.camelot.bt/access-token"
REDIRECT_URI = "https://www.tintagel.bt/oauth-callback"

client = OAuth2(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_ENDPOINT, ACCESS_TOKEN_ENDPOINT)
oauth2_authorize_callback = OAuth2AuthorizeCallback(client, REDIRECT_URI)
app = FastAPI()


@app.get("/authorize")
async def authorize(access_token_state=Depends(oauth2_authorize_callback)):
    return access_token_state


test_client = TestClient(app)


def test_oauth2_authorize_missing_code():
    response = test_client.get("/authorize")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_oauth2_authorize_error():
    response = test_client.get("/authorize", params={"error": "access_denied"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "access_denied"}


def test_oauth2_authorize_without_state():
    with asynctest.patch.object(client, "get_access_token") as mock:
        mock.return_value = "ACCESS_TOKEN"
        response = test_client.get("/authorize", params={"code": "CODE"})

    mock.assert_called()
    mock.assert_awaited_once_with("CODE", REDIRECT_URI)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == ["ACCESS_TOKEN", None]


def test_oauth2_authorize_with_state():
    with asynctest.patch.object(client, "get_access_token") as mock:
        mock.return_value = "ACCESS_TOKEN"
        response = test_client.get(
            "/authorize", params={"code": "CODE", "state": "STATE"}
        )

    mock.assert_called()
    mock.assert_awaited_once_with("CODE", REDIRECT_URI)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == ["ACCESS_TOKEN", "STATE"]
