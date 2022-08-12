from httpx_oauth.branding import BrandingProtocol


def test_branding_protocol():
    assert BrandingProtocol.__annotations__["display_name"] == str
    assert BrandingProtocol.__annotations__["logo_svg"] == str
