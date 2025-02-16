# File: tests/test_clients_apple.py

import respx
from httpx import Response

from httpx_oauth.clients.apple import AppleOAuth2

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
    # Mock the GET to Apple’s .well-known/openid-configuration
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
