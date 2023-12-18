import re

import pytest
import respx
from httpx import Response

from httpx_oauth.clients.openid import OpenID, OpenIDConfigurationError
from httpx_oauth.errors import GetIdEmailError

openid_configuration_response = {
    "issuer": "https://example.fief.dev",
    "authorization_endpoint": "https://example.fief.dev/authorize",
    "token_endpoint": "https://example.fief.dev/api/token",
    "jwks_uri": "https://example.fief.dev/.well-known/jwks.json",
    "registration_endpoint": "https://example.fief.dev/register",
    "scopes_supported": ["openid", "offline_access"],
    "response_types_supported": [
        "code",
        "code id_token",
        "code token",
        "code id_token token",
    ],
    "response_modes_supported": ["query", "fragment"],
    "grant_types_supported": ["authorization_code", "refresh_token"],
    "token_endpoint_auth_methods_supported": [
        "client_secret_basic",
        "client_secret_post",
    ],
    "service_documentation": "https://docs.fief.dev",
    "code_challenge_methods_supported": ["plain", "S256"],
    "userinfo_endpoint": "https://example.fief.dev/api/userinfo",
    "subject_types_supported": ["public"],
    "id_token_signing_alg_values_supported": ["RS256"],
    "id_token_encryption_alg_values_supported": ["RSA-OAEP-256"],
    "id_token_encryption_enc_values_supported": ["A256CBC-HS512"],
    "userinfo_signing_alg_values_supported": ["none"],
    "claims_supported": ["email", "tenant_id"],
    "request_parameter_supported": False,
}


@pytest.fixture
@respx.mock
def client() -> OpenID:
    respx.get(
        re.compile("https://example.fief.dev/.well-known/openid-configuration")
    ).mock(return_value=Response(200, json=openid_configuration_response))
    return OpenID(
        "CLIENT_ID",
        "CLIENT_SECRET",
        "https://example.fief.dev/.well-known/openid-configuration",
    )


@respx.mock
def test_openid_configuration_error():
    respx.get(
        re.compile("https://example.fief.dev/.well-known/openid-configuration")
    ).mock(return_value=Response(400, json={"error": "message"}))
    with pytest.raises(OpenIDConfigurationError):
        OpenID(
            "CLIENT_ID",
            "CLIENT_SECRET",
            "https://example.fief.dev/.well-known/openid-configuration",
        )


@respx.mock
def test_openid(client: OpenID):
    assert client.authorize_endpoint == "https://example.fief.dev/authorize"
    assert client.access_token_endpoint == "https://example.fief.dev/api/token"
    assert client.refresh_token_endpoint == "https://example.fief.dev/api/token"
    assert client.revoke_token_endpoint is None
    assert client.base_scopes == ["openid", "email"]
    assert client.name == "openid"


userinfo_response = {"sub": 42, "email": "arthur@camelot.bt"}


class TestOpenIdGetIdEmail:
    @pytest.mark.asyncio
    @respx.mock
    async def test_success(self, client: OpenID, get_respx_call_args):
        request = respx.get("https://example.fief.dev/api/userinfo").mock(
            return_value=Response(200, json=userinfo_response)
        )

        user_id, user_email = await client.get_id_email("TOKEN")
        url, headers, content = await get_respx_call_args(request)

        assert headers["Authorization"] == "Bearer TOKEN"
        assert headers["Accept"] == "application/json"
        assert user_id == "42"
        assert user_email == "arthur@camelot.bt"

    @pytest.mark.asyncio
    @respx.mock
    async def test_error(self, client: OpenID):
        respx.get(re.compile("https://example.fief.dev/api/userinfo")).mock(
            return_value=Response(400, json={"error": "message"})
        )

        with pytest.raises(GetIdEmailError) as excinfo:
            await client.get_id_email("TOKEN")

        assert isinstance(excinfo.value.args[0], dict)
        assert excinfo.value.args[0] == {"error": "message"}
