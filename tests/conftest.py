import json
import os
from typing import Any, Dict, Tuple

import pytest
from respx import HTTPXMock


@pytest.fixture()
def load_mock():
    def _load_mock(name: str) -> Dict[Any, Any]:
        mock_path = os.path.join(os.path.dirname(__file__), "mock", f"{name}.json")
        with open(mock_path) as mock_file:
            return json.load(mock_file)

    return _load_mock


@pytest.fixture()
def get_respx_call_args():
    def _get_respx_call_args(mock: HTTPXMock) -> Tuple[Dict[str, str], str]:
        request_call = mock.calls[0][0]
        return request_call.headers, request_call.content.decode("utf-8")

    return _get_respx_call_args
