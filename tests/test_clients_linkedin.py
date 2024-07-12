import re

import pytest
import respx
from httpx import Response

from httpx_oauth.clients.linkedin import (
    EMAIL_ENDPOINT,
    PROFILE_ENDPOINT,
    LinkedInOAuth2,
)
from httpx_oauth.exceptions import GetIdEmailError

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
        profile_request = respx.get(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(200, json=profile_response)
        )
        email_request = respx.get(re.compile(f"^{EMAIL_ENDPOINT}")).mock(
            return_value=Response(200, json=email_response)
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
    async def test_profile_error(self):
        respx.get(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(400, json={"error": "message"})
        )
        respx.get(re.compile(f"^{EMAIL_ENDPOINT}")).mock(
            return_value=Response(200, json=email_response)
        )

        with pytest.raises(GetIdEmailError) as excinfo:
            await client.get_id_email("TOKEN")

        assert isinstance(excinfo.value.response, Response)

    @pytest.mark.asyncio
    @respx.mock
    async def test_email_error(self):
        respx.get(re.compile(f"^{PROFILE_ENDPOINT}")).mock(
            return_value=Response(200, json=profile_response)
        )
        respx.get(re.compile(f"^{EMAIL_ENDPOINT}")).mock(
            return_value=Response(400, json={"error": "message"})
        )

        with pytest.raises(GetIdEmailError) as excinfo:
            await client.get_id_email("TOKEN")

        assert isinstance(excinfo.value.response, Response)
