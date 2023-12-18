import pytest
import respx
from httpx import Response

from httpx_oauth.clients.franceconnect import FranceConnectOAuth2
from httpx_oauth.errors import GetIdEmailError


@pytest.mark.parametrize(
    "integration,authorize,access_token,profile",
    [
        (
            False,
            "https://app.franceconnect.gouv.fr/api/v1/authorize",
            "https://app.franceconnect.gouv.fr/api/v1/token",
            "https://app.franceconnect.gouv.fr/api/v1/userinfo",
        ),
        (
            True,
            "https://fcp.integ01.dev-franceconnect.fr/api/v1/authorize",
            "https://fcp.integ01.dev-franceconnect.fr/api/v1/token",
            "https://fcp.integ01.dev-franceconnect.fr/api/v1/userinfo",
        ),
    ],
)
def test_franceconnect(
    integration: bool, authorize: str, access_token: str, profile: str
):
    client = FranceConnectOAuth2("CLIENT_ID", "CLIENT_SECRET", integration)
    assert client.authorize_endpoint == authorize
    assert client.access_token_endpoint == access_token
    assert client.refresh_token_endpoint is None
    assert client.revoke_token_endpoint is None
    assert client.profile_endpoint == profile
    assert client.base_scopes == ["openid", "email"]
    assert client.name == "franceconnect"


profile_response = {"sub": 42, "email": "arthur@camelot.bt"}


@pytest.fixture(params=[False, True])
def client(request: pytest.FixtureRequest) -> FranceConnectOAuth2:
    return FranceConnectOAuth2("CLIENT_ID", "CLIENT_SECRET", integration=request.param)


class TestFranceConnectGetAuthorizationURL:
    @pytest.mark.asyncio
    async def test_get_authorization_url(self, client: FranceConnectOAuth2):
        authorization_url = await client.get_authorization_url("REDIRECT_URI")
        assert "nonce=" in authorization_url


class TestFranceConnectGetIdEmail:
    @pytest.mark.asyncio
    @respx.mock
    async def test_success(self, client: FranceConnectOAuth2, get_respx_call_args):
        request = respx.get(path="/api/v1/userinfo").mock(
            return_value=Response(200, json=profile_response)
        )

        user_id, user_email = await client.get_id_email("TOKEN")
        url, headers, content = await get_respx_call_args(request)

        assert headers["Authorization"] == "Bearer TOKEN"
        assert headers["Accept"] == "application/json"
        assert user_id == "42"
        assert user_email == "arthur@camelot.bt"

    @pytest.mark.asyncio
    @respx.mock
    async def test_error(self, client: FranceConnectOAuth2):
        respx.get(path="/api/v1/userinfo").mock(
            return_value=Response(400, json={"error": "message"})
        )

        with pytest.raises(GetIdEmailError) as excinfo:
            await client.get_id_email("TOKEN")

        assert isinstance(excinfo.value.args[0], dict)
        assert excinfo.value.args[0] == {"error": "message"}
