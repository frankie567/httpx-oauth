import asyncio
import json
import os
import sys
from typing import Any

import httpx
import pytest


@pytest.fixture
def load_mock():
    def _load_mock(name: str) -> dict[Any, Any]:
        mock_path = os.path.join(os.path.dirname(__file__), "mock", f"{name}.json")
        with open(mock_path) as mock_file:
            return json.load(mock_file)

    return _load_mock


@pytest.fixture
def get_respx_call_args():
    async def _get_respx_call_args(
        mock,
    ) -> tuple[httpx.URL, httpx.Headers, str]:
        request_call = mock.calls[0][0]

        content = ""
        async for c in request_call.stream:
            content += c.decode("utf-8")

        return request_call.url, request_call.headers, content

    return _get_respx_call_args


@pytest.fixture
def patch_async_method(mocker):
    minor_version = sys.version_info.minor

    def _patch_async_method(instance, method: str, return_value: Any):
        if minor_version < 8:
            future: Any = asyncio.Future()
            future.set_result(return_value)
            mocker.patch.object(instance, method, return_value=future)
        else:
            from unittest.mock import AsyncMock

            async_mock = AsyncMock()
            async_mock.return_value = return_value
            mocker.patch.object(instance, method, side_effect=async_mock)

    return _patch_async_method
