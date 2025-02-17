# File: tests/test_clients_apple.py

import jwt
import pytest
import respx
from httpx import Response

from httpx_oauth.clients.apple import AppleOAuth2, AppleOAuthError
from httpx_oauth.oauth2 import OAuth2Token

# Minimal mock data from the .well-known config
APPLE_CONFIG = {
    "issuer": "https://appleid.apple.com",
    "authorization_endpoint": "https://appleid.apple.com/auth/authorize",
    "token_endpoint": "https://appleid.apple.com/auth/token",
    "revocation_endpoint": "https://appleid.apple.com/auth/revoke",
    "jwks_uri": "https://appleid.apple.com/auth/keys",
    "response_types_supported": ["code"],
    "response_modes_supported": ["query", "fragment", "form_post"],
    "subject_types_supported": ["pairwise"],
    "id_token_signing_alg_values_supported": ["RS256"],
    "scopes_supported": ["openid", "email", "name"],
    "token_endpoint_auth_methods_supported": ["client_secret_post"],
    "claims_supported": [
        "aud",
        "email",
        "email_verified",
        "exp",
        "iat",
        "is_private_email",
        "iss",
        "nonce",
        "nonce_supported",
        "real_user_status",
        "sub",
        "transfer_sub",
    ],
}

TEST_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQgO/ZNqY6LDV2I40Sx
WUkqFZ5trpigPFtp4xTVqESj/o6gCgYIKoZIzj0DAQehRANCAATvBQgsrLhgNlob
ecSnPVbTXhMZGVkUZ812GLf2FnMfK643lq6vnHwAusNl7K9k9QVTQ/VskYd1Bedo
TvVZDLvp
-----END PRIVATE KEY-----"""


@respx.mock
def test_apple_oauth2_basic():
    # Mock the GET to Apple's .well-known/openid-configuration
    respx.get("https://appleid.apple.com/.well-known/openid-configuration").mock(
        return_value=Response(200, json=APPLE_CONFIG)
    )

    client = AppleOAuth2(
        client_id="com.example.service",
        team_id="ABCD1234EF",
        key_id="ABC123DEFG",
        private_key=TEST_PRIVATE_KEY,
    )

    assert client.authorize_endpoint == "https://appleid.apple.com/auth/authorize"
    assert client.access_token_endpoint == "https://appleid.apple.com/auth/token"
    assert client.name == "apple"
    assert "openid" in client.base_scopes
    assert "email" in client.base_scopes


@respx.mock
@pytest.mark.asyncio
async def test_get_access_token_stores_token():
    # Mock the GET to Apple's .well-known/openid-configuration
    respx.get("https://appleid.apple.com/.well-known/openid-configuration").mock(
        return_value=Response(200, json=APPLE_CONFIG)
    )

    client = AppleOAuth2(
        client_id="com.example.service",
        team_id="ABCD1234EF",
        key_id="ABC123DEFG",
        private_key=TEST_PRIVATE_KEY,
    )

    # Mock a successful token response
    mock_token_response = {
        "access_token": "mock_access_token",
        "token_type": "Bearer",
        "expires_in": 3600,
        "id_token": {"sub": "mock_id_token"},
    }

    # Mock the token endpoint with a pattern matcher to ensure required params
    route = respx.post("https://appleid.apple.com/auth/token")
    route.mock(return_value=Response(200, json=mock_token_response))

    # Get the token
    token = await client.get_access_token("mock_code", "mock_redirect_uri")

    # Verify the request was made with correct parameters
    assert route.called
    request = route.calls.last.request
    assert request.method == "POST"
    body = request.content.decode()
    assert "grant_type=authorization_code" in body
    assert "code=mock_code" in body
    assert "redirect_uri=mock_redirect_uri" in body
    assert "client_id=com.example.service" in body
    assert "client_secret=" in body  # The JWT will be different each time

    # Verify the token was stored internally
    assert client.oauth2_token is not None
    assert client.oauth2_token == token
    assert client.oauth2_token["access_token"] == "mock_access_token"
    assert client.oauth2_token["id_token"] == {"sub": "mock_id_token"}


@pytest.mark.asyncio
async def test_get_id_email_success():
    client = AppleOAuth2(
        client_id="com.example.service",
        team_id="ABCD1234EF",
        key_id="ABC123DEFG",
        private_key=TEST_PRIVATE_KEY,
    )

    # Mock a successful ID token response
    mock_id_token = {
        "iss": "https://appleid.apple.com",
        "aud": "app.bankroller.service",
        "exp": 1739779476,
        "iat": 1739693076,
        "sub": "000958.280e99fb24734730a496b16e104683c4.0408",
        "at_hash": "HAvzoBxRWwHVedDCT2AczQ",
        "email": "some_email@whatever.com",
        "email_verified": True,
        "auth_time": 1739693075,
        "nonce_supported": True,
    }

    # Create a JWT token from the mock response
    token = jwt.encode(mock_id_token, "secret", algorithm="HS256")
    oauth_token = OAuth2Token({"id_token": token})
    client.oauth2_token = oauth_token

    # Test the method
    user_id, email = await client.get_id_email("unused")
    assert user_id == "000958.280e99fb24734730a496b16e104683c4.0408"
    assert email == "some_email@whatever.com"


@pytest.mark.asyncio
async def test_get_id_email_no_id_token():
    client = AppleOAuth2(
        client_id="com.example.service",
        team_id="ABCD1234EF",
        key_id="ABC123DEFG",
        private_key=TEST_PRIVATE_KEY,
    )

    # Test with missing id_token
    oauth_token = OAuth2Token({})
    client.oauth2_token = oauth_token
    with pytest.raises(AppleOAuthError) as exc:
        await client.get_id_email("unused")
    assert str(exc.value) == AppleOAuthError.NO_ID_TOKEN


@pytest.mark.asyncio
async def test_get_id_email_no_subject():
    client = AppleOAuth2(
        client_id="com.example.service",
        team_id="ABCD1234EF",
        key_id="ABC123DEFG",
        private_key=TEST_PRIVATE_KEY,
    )

    # Mock an ID token without subject claim
    mock_id_token = {
        "iss": "https://appleid.apple.com",
        "aud": "app.bankroller.service",
        "email": "some_email@whatever.com",
    }

    token = jwt.encode(mock_id_token, "secret", algorithm="HS256")
    oauth_token = OAuth2Token({"id_token": token})
    client.oauth2_token = oauth_token
    with pytest.raises(AppleOAuthError) as exc:
        await client.get_id_email("unused")
    assert str(exc.value) == AppleOAuthError.NO_SUBJECT


@pytest.mark.asyncio
async def test_get_id_email_no_token():
    client = AppleOAuth2(
        client_id="com.example.service",
        team_id="ABCD1234EF",
        key_id="ABC123DEFG",
        private_key=TEST_PRIVATE_KEY,
    )

    with pytest.raises(AppleOAuthError) as exc:
        await client.get_id_email("unused")
    assert str(exc.value) == AppleOAuthError.NO_ACCESS_TOKEN
