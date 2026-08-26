"""Unit tests pinning the console-noise filter scope of the ELITEA-1966 /
ELITEA-1973 credentials specs.

Regression coverage for the PR round-1 review finding
(`.agents/memory/qa-engineer/credentials_console_noise_filters_518_554_are_stale_closed.md`):
both specs had copied forward a `_is_known_518_warning()` filter whose
docstring claimed elitea-testing-public#518 was "already-filed, OPEN".
#518 is CLOSED (COMPLETED 2026-08-11, NOT REPRODUCIBLE after 22 attempts)
and its signature is a React error-boundary crash of `<CredentialsList>` —
the very component both cases render and assert against. Keeping that
filter meant a genuine crash regression would have shipped green.

These tests pin the fix from both sides:

1. Neither spec module may expose a `_is_known_518_warning` symbol again —
   a copy-forward from a neighbouring spec fails here first.
2. The one filter that stays (#554, closed as a local-UI/test-client
   artifact) must remain pinned to its own `.../toolkits/prompt_lib` URL
   shape, so it can never swallow a `<CredentialsList>` crash, a generic
   404, or an unrelated console error.
"""

import pytest

from tests.ui.toolkits import test_credential_filter_by_type, test_credential_view_toggle

SPEC_MODULES = (test_credential_filter_by_type, test_credential_view_toggle)

#: The exact #518 crash signatures the removed filter used to swallow.
_REFETCH_TEXT = "Cannot refetch a query that has not been started yet"
_ERROR_BOUNDARY_TEXT = (
    "The above error occurred in the <CredentialsList> component:\n"
    "    at CredentialsList\n    at Suspense\n    at Route"
)


class _FakeConsoleMessage:
    """Minimal stand-in for Playwright's `ConsoleMessage` — the two
    attributes the filters read."""

    def __init__(self, text: str, url: str | None = None, msg_type: str = "error"):
        self.text = text
        self.type = msg_type
        self.location = {"url": url} if url else None


@pytest.mark.parametrize("module", SPEC_MODULES, ids=lambda m: m.__name__.rsplit(".", 1)[-1])
def test_spec_does_not_reintroduce_the_518_filter(module):
    """#518 is CLOSED as NOT REPRODUCIBLE and its signature is a crash of
    the component under test — a filter for it is masking, not noise."""
    assert not hasattr(module, "_is_known_518_warning"), (
        f"{module.__name__} re-introduced _is_known_518_warning(); "
        "elitea-testing-public#518 is CLOSED (NOT REPRODUCIBLE) and its "
        "signature is a <CredentialsList> error-boundary crash — filtering "
        "it would hide a real regression of the component under test."
    )


@pytest.mark.parametrize("module", SPEC_MODULES, ids=lambda m: m.__name__.rsplit(".", 1)[-1])
@pytest.mark.parametrize(
    "text",
    [_REFETCH_TEXT, _ERROR_BOUNDARY_TEXT],
    ids=["refetch-not-started", "credentialslist-error-boundary"],
)
def test_retained_554_filter_never_swallows_a_credentialslist_crash(module, text):
    """The surviving #554 filter must let every #518-shaped crash through,
    whatever URL it is reported from."""
    assert module._is_known_554_warning(_FakeConsoleMessage(text)) is False
    assert (
        module._is_known_554_warning(
            _FakeConsoleMessage(text, url="http://localhost:5173/elitea_core/toolkits/prompt_lib/")
        )
        is False
    )


@pytest.mark.parametrize("module", SPEC_MODULES, ids=lambda m: m.__name__.rsplit(".", 1)[-1])
def test_retained_554_filter_stays_pinned_to_its_own_url_shape(module):
    """It matches the empty-projectId toolkit-types 404 and nothing else —
    not a blanket 404 ignore."""
    matched = _FakeConsoleMessage(
        "Failed to load resource: the server responded with a status of 404 ()",
        url="http://localhost:5173/elitea_core/toolkits/prompt_lib/",
    )
    assert module._is_known_554_warning(matched) is True

    other_404 = _FakeConsoleMessage(
        "Failed to load resource: the server responded with a status of 404 ()",
        url="http://localhost:5173/elitea_core/credentials/prompt_lib/471",
    )
    assert module._is_known_554_warning(other_404) is False

    unrelated = _FakeConsoleMessage("TypeError: Cannot read properties of undefined")
    assert module._is_known_554_warning(unrelated) is False
