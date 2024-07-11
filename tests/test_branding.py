from httpx_oauth.branding import BrandingProtocol


def test_branding_protocol():
    assert isinstance(BrandingProtocol.__annotations__["display_name"], type(str))
    assert isinstance(BrandingProtocol.__annotations__["logo_svg"], type(str))
