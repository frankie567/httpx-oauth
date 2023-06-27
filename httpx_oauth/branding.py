from typing import Protocol


class BrandingProtocol(Protocol):
    display_name: str
    logo_svg: str
