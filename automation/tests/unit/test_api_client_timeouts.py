"""Unit tests for the default API request timeout in `api/client.py`.

Night run 329: a pipeline/agent create with no timeout hung ~16 min until the
peer dropped the connection. Every API-client request now carries a default
(connect, read) timeout unless the caller passes its own.
"""

from unittest import mock

import pytest
import requests
from api import client as client_mod
from config import settings


@pytest.fixture
def captured(monkeypatch):
    """Capture the kwargs that reach the transport instead of sending anything."""
    calls = []

    def fake_send(self, request, **kwargs):
        calls.append(kwargs)
        resp = requests.Response()
        resp.status_code = 200
        resp._content = b'{"result": {"success": true, "tools": []}}'
        resp.request = request
        return resp

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", fake_send)
    return calls


def test_retry_session_applies_default_timeout(captured):
    session = client_mod._create_retry_session()

    session.get("https://example.invalid/x")

    assert captured[-1]["timeout"] == (settings.api_connect_timeout, settings.api_read_timeout)


def test_explicit_timeout_wins(captured):
    session = client_mod._create_retry_session()

    session.post("https://example.invalid/x", timeout=5)

    assert captured[-1]["timeout"] == 5


def test_api_client_verbs_apply_default_timeout():
    api = client_mod.APIClient(base_url="https://example.invalid", api_token="t", project_id="1")
    for verb in ("get", "post", "put", "patch", "delete"):
        with mock.patch.object(client_mod.requests, verb) as sent:
            getattr(api, verb)("/x")
        assert sent.call_args.kwargs["timeout"] == (settings.api_connect_timeout, settings.api_read_timeout), verb


def test_api_client_explicit_timeout_wins():
    api = client_mod.APIClient(base_url="https://example.invalid", api_token="t", project_id="1")
    with mock.patch.object(client_mod.requests, "get") as sent:
        api.get("/x", timeout=3)
    assert sent.call_args.kwargs["timeout"] == 3


def test_sync_mcp_tools_read_timeout_outlasts_handshake(captured):
    toolkit_api = client_mod.ToolkitAPI.__new__(client_mod.ToolkitAPI)
    toolkit_api.base_url = "https://example.invalid"
    toolkit_api.project_id = "1"
    toolkit_api._session = client_mod._create_retry_session()

    toolkit_api.sync_mcp_tools("https://mcp.invalid", timeout=90)

    connect, read = captured[-1]["timeout"]
    assert connect == settings.api_connect_timeout
    assert read == 90 + settings.api_read_timeout
