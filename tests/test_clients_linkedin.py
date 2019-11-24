from httpx_oauth.clients.linkedin import LinkedInOAuth2


def test_linkedin_oauth2():
    client = LinkedInOAuth2("CLIENT_ID", "CLIENT_SECRET")

    assert (
        client.authorize_endpoint == "https://www.linkedin.com/oauth/v2/authorization"
    )
    assert (
        client.access_token_endpoint == "https://www.linkedin.com/oauth/v2/accessToken"
    )
    assert (
        client.refresh_token_endpoint == "https://www.linkedin.com/oauth/v2/accessToken"
    )
    assert client.revoke_token_endpoint is None
