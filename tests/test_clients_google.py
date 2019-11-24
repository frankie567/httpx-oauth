from httpx_oauth.clients.google import GoogleOAuth2


def test_google_oauth2():
    client = GoogleOAuth2("CLIENT_ID", "CLIENT_SECRET")

    assert client.authorize_endpoint == "https://accounts.google.com/o/oauth2/v2/auth"
    assert client.access_token_endpoint == "https://oauth2.googleapis.com/token"
    assert client.refresh_token_endpoint == "https://oauth2.googleapis.com/token"
    assert client.revoke_token_endpoint == "https://accounts.google.com/o/oauth2/revoke"
