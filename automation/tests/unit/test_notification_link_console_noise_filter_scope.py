"""Unit tests pinning the console-noise filter scope of the ELITEA-2261 /
ELITEA-2263 notification-link specs.

Regression coverage for the PR round-1 review finding: both specs shipped a
``KNOWN_BACKGROUND_NOISE_URL_MARKERS`` tuple matched by URL substring ALONE, so
``_flow_console_errors()`` dropped every console error naming
``/secrets/secrets/default/`` or ``/project_info/prompt_lib/`` **at any status**.
The signatures those specs' AFS § Network Behavior actually observed live are a
``403`` on the secrets probe and a ``500`` on project-info; a URL-only filter also
swallows a future ``500`` on the secrets probe or a ``404`` on project-info — i.e.
a genuine backend regression on a resource the flow passes through would ship
green. That is masking, not noise handling
(`.agents/testing.md` § *Merge gate*: "Do NOT widen the #1753 filter (or any
filter) to swallow 400s").

The fix pairs each URL marker with the status text observed for it, the same
shape every sibling spec uses (``_is_known_secrets_403`` in the chat suite,
``_is_known_554_warning`` pinned by ``test_credentials_console_filters_scope``).

These tests pin it from both sides:

1. Neither spec module may expose the URL-only ``KNOWN_BACKGROUND_NOISE_URL_MARKERS``
   symbol again — a copy-forward of the unscoped shape fails here first.
2. Each filter matches its two exact (status, resource) pairs and nothing else:
   not a status swap on the same resource, not the same status on a different
   resource, and never anything on the endpoints the flow itself drives.
"""

import pytest
from utils.console_errors import format_console_message

from tests.ui.admin import (
    test_notification_link_navigates_to_bucket,
    test_notification_link_navigates_to_conversation,
)

SPEC_MODULES = (
    test_notification_link_navigates_to_conversation,
    test_notification_link_navigates_to_bucket,
)

#: The two signatures the AFS recorded live on 2026-08-26 — the only ones that
#: may be dropped.
KNOWN_403_SECRETS = (
    "Failed to load resource: the server responded with a status of 403 ()",
    "http://localhost:5173/api/v2/secrets/secrets/default/399",
)
KNOWN_500_PROJECT_INFO = (
    "Failed to load resource: the server responded with a status of 500 ()",
    "http://localhost:5173/api/v2/elitea_core/project_info/prompt_lib/399/project-info",
)


class _FakeConsoleMessage:
    """Minimal stand-in for Playwright's ``ConsoleMessage`` — the three
    attributes ``format_console_message`` reads."""

    def __init__(self, text: str, url: str | None = None, msg_type: str = "error"):
        self.text = text
        self.type = msg_type
        self.location = {"url": url} if url else None


def _rendered(text: str, url: str | None = None) -> str:
    """Render exactly as the specs' live listener does, so these tests exercise
    the real string shape the filter sees at run time."""
    return format_console_message(_FakeConsoleMessage(text, url))


@pytest.fixture(params=SPEC_MODULES, ids=lambda m: m.__name__.rsplit(".", 1)[-1])
def spec(request):
    return request.param


def test_spec_does_not_reintroduce_the_url_only_filter(spec):
    """The unscoped shape is the defect — it must not come back by copy-forward."""
    assert not hasattr(spec, "KNOWN_BACKGROUND_NOISE_URL_MARKERS"), (
        f"{spec.__name__} re-introduced KNOWN_BACKGROUND_NOISE_URL_MARKERS; a "
        "URL-only console-noise filter drops every status on those resources, "
        "including a genuine backend regression. Pair each URL with the status "
        "text actually observed (KNOWN_BACKGROUND_NOISE_SIGNATURES)."
    )


@pytest.mark.parametrize(
    ("text", "url"),
    [KNOWN_403_SECRETS, KNOWN_500_PROJECT_INFO],
    ids=["secrets-403", "project-info-500"],
)
def test_documented_signatures_are_dropped(spec, text, url):
    """Both halves match — this is the noise the AFS documented."""
    assert spec._is_known_background_noise(_rendered(text, url)) is True


@pytest.mark.parametrize(
    ("text", "url"),
    [
        # Status swapped on the SAME resource — the exact hole the URL-only
        # filter left open.
        (
            "Failed to load resource: the server responded with a status of 500 ()",
            KNOWN_403_SECRETS[1],
        ),
        (
            "Failed to load resource: the server responded with a status of 404 ()",
            KNOWN_403_SECRETS[1],
        ),
        (
            "Failed to load resource: the server responded with a status of 403 ()",
            KNOWN_500_PROJECT_INFO[1],
        ),
        (
            "Failed to load resource: the server responded with a status of 400 (Bad Request)",
            KNOWN_500_PROJECT_INFO[1],
        ),
    ],
    ids=["secrets-500", "secrets-404", "project-info-403", "project-info-400"],
)
def test_status_swap_on_a_known_resource_is_not_dropped(spec, text, url):
    assert spec._is_known_background_noise(_rendered(text, url)) is False


@pytest.mark.parametrize(
    ("text", "url"),
    [
        # The known statuses, but on the endpoints the flow itself drives.
        (
            "Failed to load resource: the server responded with a status of 403 ()",
            "http://localhost:5173/api/v2/elitea_core/conversation/prompt_lib/406/5883",
        ),
        (
            "Failed to load resource: the server responded with a status of 500 ()",
            "http://localhost:5173/api/v2/artifacts/buckets/default/399",
        ),
        (
            "Failed to load resource: the server responded with a status of 500 ()",
            "http://localhost:5173/api/v2/notifications/notifications/prompt_lib/399",
        ),
        # A plain JS error carries no URL at all.
        ("TypeError: Cannot read properties of undefined", None),
    ],
    ids=["conversation-403", "artifacts-500", "notifications-500", "js-typeerror"],
)
def test_flow_and_unrelated_errors_are_never_dropped(spec, text, url):
    assert spec._is_known_background_noise(_rendered(text, url)) is False


def test_flow_console_errors_keeps_everything_but_the_two_signatures(spec):
    """End-to-end on the list helper the specs actually assert against."""
    genuine = _rendered(
        "Failed to load resource: the server responded with a status of 500 ()",
        KNOWN_403_SECRETS[1],
    )
    messages = [
        _rendered(*KNOWN_403_SECRETS),
        genuine,
        _rendered(*KNOWN_500_PROJECT_INFO),
        _rendered("TypeError: boom", "http://localhost:5173/app.js"),
    ]
    assert spec._flow_console_errors(messages) == [
        genuine,
        _rendered("TypeError: boom", "http://localhost:5173/app.js"),
    ]
