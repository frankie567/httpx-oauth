import sys

if sys.version_info < (3, 8):
    from typing_extensions import Literal, Protocol, TypedDict  # pragma: no cover
else:
    from typing import Literal, Protocol, TypedDict  # pragma: no cover

__all__ = ["Literal", "Protocol", "TypedDict"]
