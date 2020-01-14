import re

import pytest
import respx

from httpx_oauth.clients.linkedin import (
    EMAIL_ENDPOINT,
    LinkedInOAuth2,
    PROFILE_ENDPOINT,
)
from httpx_oauth.errors import GetIdEmailError

client = LinkedInOAuth2("CLIENT_ID", "CLIENT_SECRET")


def test_linkedin_oauth2():

    assert (
        client.authorize_endpoint == "https://www.linkedin.com/oauth/v2/authorization"
    )
    assert (
        client.access_token_endpoint == "https://www.linkedin.com/oauth/v2/accessToken"
    )
    assert (
        client.refresh_token_endpoint == "https://www.linkedin.com/oauth/v2/accessToken"
    )
    assert client.base_scopes == ["r_emailaddress", "r_liteprofile", "r_basicprofile"]
    assert client.revoke_token_endpoint is None
    assert client.name == "linkedin"


profile_response = {"id": "424242"}
email_response = {
    "elements": [
        {
            "handle": "urn:li:emailAddress:667536010",
            "handle~": {"emailAddress": "arthur@camelot.bt"},
        }
    ]
}


class TestLinkedInGetIdEmail:
    @pytest.mark.asyncio
    @respx.mock
    async def test_success(self, get_respx_call_args):
        profile_request = respx.get(
            re.compile(f"^{PROFILE_ENDPOINT}"),
            status_code=200,
            content=profile_response,
        )
        email_request = respx.get(
            re.compile(f"^{EMAIL_ENDPOINT}"), status_code=200, content=email_response
        )

        user_id, user_email = await client.get_id_email("TOKEN")
        profile_url, profile_headers, profile_content = await get_respx_call_args(
            profile_request
        )
        email_url, email_headers, email_content = await get_respx_call_args(
            email_request
        )

        assert profile_headers["Authorization"] == "Bearer TOKEN"
        assert email_headers["Authorization"] == "Bearer TOKEN"
        assert user_id == "424242"
        assert user_email == "arthur@camelot.bt"

    @pytest.mark.asyncio
    @respx.mock
    async def test_profile_error(self, get_respx_call_args):
        respx.get(
            re.compile(f"^{PROFILE_ENDPOINT}"),
            status_code=400,
            content={"error": "message"},
        )
        respx.get(
            re.compile(f"^{EMAIL_ENDPOINT}"), status_code=200, content=email_response,
        )

        with pytest.raises(GetIdEmailError) as excinfo:
            await client.get_id_email("TOKEN")

        assert type(excinfo.value.args[0]) == dict
        assert excinfo.value.args[0] == {"error": "message"}

    @pytest.mark.asyncio
    @respx.mock
    async def test_email_error(self, get_respx_call_args):
        respx.get(
            re.compile(f"^{PROFILE_ENDPOINT}"),
            status_code=200,
            content=profile_response,
        )
        respx.get(
            re.compile(f"^{EMAIL_ENDPOINT}"),
            status_code=400,
            content={"error": "message"},
        )

        with pytest.raises(GetIdEmailError) as excinfo:
            await client.get_id_email("TOKEN")

        assert type(excinfo.value.args[0]) == dict
        assert excinfo.value.args[0] == {"error": "message"}
