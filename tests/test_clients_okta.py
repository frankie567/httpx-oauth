import respx
from httpx import Response

from httpx_oauth.clients.okta import OktaOAuth2

OKTA_DOMAIN = "foo.okta.com"

openid_configuration_response = {
    "issuer": "https://foo.okta.com",
    "authorization_endpoint": "https://foo.okta.com/oauth2/v1/authorize",
    "token_endpoint": "https://foo.okta.com/oauth2/v1/token",
    "userinfo_endpoint": "https://foo.okta.com/oauth2/v1/userinfo",
    "registration_endpoint": "https://foo.okta.com/oauth2/v1/clients",
    "jwks_uri": "https://foo.okta.com/oauth2/v1/keys",
    "response_types_supported": [
        "code",
        "id_token",
        "code id_token",
        "code token",
        "id_token token",
        "code id_token token",
    ],
    "response_modes_supported": ["query", "fragment", "form_post", "okta_post_message"],
    "grant_types_supported": [
        "authorization_code",
        "implicit",
        "refresh_token",
        "password",
        "urn:ietf:params:oauth:grant-type:device_code",
    ],
    "subject_types_supported": ["public"],
    "id_token_signing_alg_values_supported": ["RS256"],
    "scopes_supported": [
        "openid",
        "email",
        "profile",
        "address",
        "phone",
        "offline_access",
        "groups",
    ],
    "token_endpoint_auth_methods_supported": [
        "client_secret_basic",
        "client_secret_post",
        "client_secret_jwt",
        "private_key_jwt",
        "none",
    ],
    "claims_supported": [
        "iss",
        "ver",
        "sub",
        "aud",
        "iat",
        "exp",
        "jti",
        "auth_time",
        "amr",
        "idp",
        "nonce",
        "name",
        "nickname",
        "preferred_username",
        "given_name",
        "middle_name",
        "family_name",
        "email",
        "email_verified",
        "profile",
        "zoneinfo",
        "locale",
        "address",
        "phone_number",
        "picture",
        "website",
        "gender",
        "birthdate",
        "updated_at",
        "at_hash",
        "c_hash",
    ],
    "code_challenge_methods_supported": ["S256"],
    "introspection_endpoint": "https://foo.okta.com/oauth2/v1/introspect",
    "introspection_endpoint_auth_methods_supported": [
        "client_secret_basic",
        "client_secret_post",
        "client_secret_jwt",
        "private_key_jwt",
        "none",
    ],
    "revocation_endpoint": "https://foo.okta.com/oauth2/v1/revoke",
    "revocation_endpoint_auth_methods_supported": [
        "client_secret_basic",
        "client_secret_post",
        "client_secret_jwt",
        "private_key_jwt",
        "none",
    ],
    "end_session_endpoint": "https://foo.okta.com/oauth2/v1/logout",
    "request_parameter_supported": True,
    "request_object_signing_alg_values_supported": [
        "HS256",
        "HS384",
        "HS512",
        "RS256",
        "RS384",
        "RS512",
        "ES256",
        "ES384",
        "ES512",
    ],
    "device_authorization_endpoint": "https://foo.okta.com/oauth2/v1/device/authorize",
}


@respx.mock
def test_okta_oauth2():
    respx.get(f"https://{OKTA_DOMAIN}/.well-known/openid-configuration").mock(
        return_value=Response(200, json=openid_configuration_response)
    )

    client = OktaOAuth2("CLIENT_ID", "CLIENT_SECRET", OKTA_DOMAIN)
    assert client.authorize_endpoint == f"https://{OKTA_DOMAIN}/oauth2/v1/authorize"
    assert client.access_token_endpoint == f"https://{OKTA_DOMAIN}/oauth2/v1/token"
    assert client.refresh_token_endpoint == f"https://{OKTA_DOMAIN}/oauth2/v1/token"
    assert client.revoke_token_endpoint == f"https://{OKTA_DOMAIN}/oauth2/v1/revoke"
    assert client.base_scopes == ["openid", "email"]
    assert client.name == "okta"
