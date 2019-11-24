from httpx_oauth.clients.github import GitHubOAuth2


def test_github_oauth2():
    client = GitHubOAuth2("CLIENT_ID", "CLIENT_SECRET")

    assert client.authorize_endpoint == "https://github.com/login/oauth/authorize"
    assert client.access_token_endpoint == "https://github.com/login/oauth/access_token"
    assert client.refresh_token_endpoint is None
    assert client.revoke_token_endpoint is None
