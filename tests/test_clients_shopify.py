import pytest
import respx
from httpx import Response

from httpx_oauth.clients.shopify import ShopifyOAuth2
from httpx_oauth.errors import GetIdEmailError

client = ShopifyOAuth2("CLIENT_ID", "CLIENT_SECRET", "my-shop")


def test_shopify_oauth2():
    assert (
        client.authorize_endpoint
        == "https://my-shop.myshopify.com/admin/oauth/authorize"
    )
    assert (
        client.access_token_endpoint
        == "https://my-shop.myshopify.com/admin/oauth/access_token"
    )
    assert client.refresh_token_endpoint is None
    assert client.revoke_token_endpoint is None
    assert client.base_scopes == ["read_orders"]
    assert client.name == "shopify"


profile_response = {
    "shop": {
        "id": 548380009,
        "name": "John Smith Test Store",
        "email": "j.smith@example.com",
        "domain": "shop.apple.com",
        "province": "California",
        "country": "US",
        "address1": "1 Infinite Loop",
        "zip": "95014",
        "city": "Cupertino",
        "source": None,
        "phone": "1231231234",
        "latitude": 45.45,
        "longitude": -75.43,
        "primary_locale": "en",
        "address2": "Suite 100",
        "created_at": "2007-12-31T19:00:00-05:00",
        "updated_at": "2023-06-14T14:21:51-04:00",
        "country_code": "US",
        "country_name": "United States",
        "currency": "USD",
        "customer_email": "customers@apple.com",
        "timezone": "(GMT-05:00) Eastern Time (US & Canada)",
        "iana_timezone": "America/New_York",
        "shop_owner": "John Smith",
        "money_format": "${{amount}}",
        "money_with_currency_format": "${{amount}} USD",
        "weight_unit": "lb",
        "province_code": "CA",
        "taxes_included": None,
        "auto_configure_tax_inclusivity": None,
        "tax_shipping": None,
        "county_taxes": True,
        "plan_display_name": "Shopify Plus",
        "plan_name": "enterprise",
        "has_discounts": True,
        "has_gift_cards": True,
        "myshopify_domain": "jsmith.myshopify.com",
        "google_apps_domain": None,
        "google_apps_login_enabled": None,
        "money_in_emails_format": "${{amount}}",
        "money_with_currency_in_emails_format": "${{amount}} USD",
        "eligible_for_payments": True,
        "requires_extra_payments_agreement": False,
        "password_enabled": False,
        "has_storefront": True,
        "finances": True,
        "primary_location_id": 655441491,
        "cookie_consent_level": "implicit",
        "visitor_tracking_consent_preference": "allow_all",
        "checkout_api_supported": True,
        "multi_location_enabled": True,
        "setup_required": False,
        "pre_launch_enabled": False,
        "enabled_presentment_currencies": ["USD"],
        "transactional_sms_disabled": False,
        "marketing_sms_consent_enabled_at_checkout": False,
    }
}


class TestShopifyGetIdEmail:
    @pytest.mark.asyncio
    @respx.mock
    async def test_success(self, get_respx_call_args):
        request = respx.get(client.profile_endpoint).mock(
            return_value=Response(200, json=profile_response)
        )

        user_id, user_email = await client.get_id_email("TOKEN")
        url, headers, content = await get_respx_call_args(request)

        assert headers["X-Shopify-Access-Token"] == "TOKEN"
        assert user_id == "548380009"
        assert user_email == "j.smith@example.com"

    @pytest.mark.asyncio
    @respx.mock
    async def test_error(self):
        respx.get(client.profile_endpoint).mock(
            return_value=Response(400, json={"error": "message"})
        )

        with pytest.raises(GetIdEmailError) as excinfo:
            await client.get_id_email("TOKEN")

        assert isinstance(excinfo.value.args[0], dict)
        assert excinfo.value.args[0] == {"error": "message"}
