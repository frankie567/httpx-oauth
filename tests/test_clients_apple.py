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
    assert client.refresh_token_endpoint == "https://appleid.apple.com/auth/token"
    # Apple might return "revocation_endpoint" in future versions or not
    # ...
    assert client.name == "apple"
    assert "openid" in client.base_scopes
    assert "email" in client.base_scopes


def test_get_id_email_from_id_token_success():
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

    # Test the method
    user_id, email = client.get_id_email_from_id_token(oauth_token)
    assert user_id == "000958.280e99fb24734730a496b16e104683c4.0408"
    assert email == "some_email@whatever.com"


def test_get_id_email_from_id_token_no_id_token():
    client = AppleOAuth2(
        client_id="com.example.service",
        team_id="ABCD1234EF",
        key_id="ABC123DEFG",
        private_key=TEST_PRIVATE_KEY,
    )

    # Test with missing id_token
    oauth_token = OAuth2Token({})
    with pytest.raises(AppleOAuthError) as exc:
        client.get_id_email_from_id_token(oauth_token)
    assert str(exc.value) == AppleOAuthError.NO_ID_TOKEN


def test_get_id_email_from_id_token_no_subject():
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

    with pytest.raises(AppleOAuthError) as exc:
        client.get_id_email_from_id_token(oauth_token)
    assert str(exc.value) == AppleOAuthError.NO_SUBJECT
