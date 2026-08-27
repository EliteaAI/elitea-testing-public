"""UI test — Settings → Secrets surfaces an error state when the secrets-list
request fails at the transport level, and recovers cleanly once the connection
is restored.

Read-only case (`.agents/testing.md` § Test data strategy): nothing is created,
edited or deleted. Only the transport of one GET is interrupted, and only for
the duration of steps 1-2.

Test case: ELITEA-2349
AFS: test-specs/settings-secrets/l3_secrets-error-state-on-network-failure_ELITEA-2349.md

Fidelity — declared substitution (`.agents/testing.md` § Fidelity policy)
------------------------------------------------------------------------
`page.route(..., route.abort("failed"))` cuts the TRANSPORT of the secrets-list
GET. This is **case-authorised**: the case's own step 1 reads "Navigate to
Settings → Secrets **on a throttled or offline connection**" — the offline
condition IS the case's stated precondition, not a convenience.

Nothing the case observes is fabricated. `abort()` authors no response body; it
produces a genuine RTK-Query `FETCH_ERROR`, exactly as a dropped connection
would, and every asserted value — the toast, its severity, the page shell, the
recovered rows — is produced by the product. Steps 3-4 run with the route
UNROUTED, so the recovery half asserts against a live `200` and the backend's
own payload with zero interception in play.

Known defect — deliberately NOT pinned
--------------------------------------
The toast's text is currently the bare string "Unknown error": `SecretsContent.jsx`
calls the shared `buildErrorMessage` (`src/common/utils.jsx:146-184`), which has
no `FETCH_ERROR` branch and falls through to `undefined`. Filed as
EliteaAI/elitea-testing-public#1910. This test asserts the SHAPE the case
actually specifies — an error-severity toast, non-empty text, no raw stack
trace — and deliberately does not assert the literal string, which would encode
the defect as the expected contract and go red the day the product improves it.

Console errors are deliberately NOT asserted: `/settings/secrets` fires the
known, filed, OPEN #1203 render-loop burst on every mount (59 errors measured
live in the failure state). That defect already has soft-asserted coverage in
`test_secrets_page_layout.py` (ELITEA-2330); re-asserting it here would make
this spec a permanent duplicate red. See the AFS § Deliberately NOT asserted.

Markers:
    - ui: requires browser
    - admin: settings/admin surface
    - p2: priority (per AFS metadata: l3 — case frontmatter `priority: medium`)
    - regression
"""

import logging

import allure
import pytest
from pages.secrets_page import SecretsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

SECRETS_LIST_GLOB = "**/secrets/secrets/default/**"
EXPECTED_TITLE = "Secrets"
ERROR_SEVERITY = "error"
DEFAULT_PAGE_SIZE = 10
UI_ELEMENT_TIMEOUT = 10_000
RECOVERY_TIMEOUT = 20_000

#: Markers that would betray a raw stack trace / unhandled exception leaking
#: into user-facing text. The case's step 2 criterion is explicitly "not a
#: blank page or raw stack trace", so this is the case's own bar made
#: mechanical rather than a stylistic preference.
STACK_TRACE_MARKERS = ("TypeError", "Uncaught", "at Object.", ".jsx:", ".js:", "\n    at ")


def _stack_markers_in(text: str) -> list[str]:
    """Stack-trace markers present in *text* (empty list == clean)."""
    return [m for m in STACK_TRACE_MARKERS if m in text]


class TestSecretsErrorStateOnNetworkFailure:
    """ELITEA-2349 — with the connection down the Secrets page renders its
    shell plus a user-facing error toast (no blank page, no stack trace); once
    the connection is restored a reload loads the list from the live API."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/secrets/ELITEA-2349_secrets-page-shows-error-state-on-network-failure.md",
        "onetest-ai Test Case link",
    )
    def test_secrets_error_state_on_network_failure_and_recovery(self, page):
        secrets_page = SecretsPage(page)

        with allure.step(
            "Step 1 — Navigate to Settings -> Secrets on a downed connection: "
            "the page shell renders (not a blank page)"
        ):
            # Case-authorised simulation of the case's own precondition
            # ("on a throttled or offline connection"). abort() cuts the
            # transport only — no response body is authored.
            page.route(SECRETS_LIST_GLOB, lambda route: route.abort("failed"))
            secrets_page.navigate_expecting_no_rows()

            expect(secrets_page.page_title).to_be_visible()
            expect(secrets_page.page_title).to_have_text(EXPECTED_TITLE)
            expect(secrets_page.add_button).to_be_visible()
            # The list could not load, so the table must be empty — this makes
            # the step-4 recovery assertion a real transition, not a no-op.
            expect(secrets_page.secret_row).to_have_count(0)

        with allure.step(
            "Step 2 — Verify a user-friendly error message is shown "
            "(not a blank page, not a raw stack trace)"
        ):
            error_toast = page.locator(
                secrets_page.TOAST_ALERT_SEVERITY.format(ERROR_SEVERITY)
            )
            # Severity asserted by ATTRIBUTE FILTER on the stable toast testid:
            # the product classified this as an error, not info/warning.
            expect(error_toast).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            expect(secrets_page.toast_message).to_be_visible()
            message = secrets_page.toast_message.inner_text().strip()
            assert message, (
                "Case step 2 — an error message must be SHOWN; the toast "
                "rendered with empty text"
            )

            # "not a raw stack trace" — asserted on the toast text AND on the
            # whole page body, because a crash could leak the trace anywhere.
            toast_markers = _stack_markers_in(message)
            assert not toast_markers, (
                f"Case step 2 — the error message must not be a raw stack trace, "
                f"found {toast_markers} in {message!r}"
            )
            # Scoped to the Settings content pane (a real app testid): a React
            # error boundary would render its trace there, and the pane is
            # exactly what the case means by "the page".
            pane_text = secrets_page.settings_content.inner_text()
            pane_markers = _stack_markers_in(pane_text)
            assert not pane_markers, (
                f"Case step 2 — no raw stack trace may reach the user, found "
                f"{pane_markers} in the rendered Settings content pane"
            )
            logger.info("Failure-state toast message rendered: %r", message)
            allure.attach(
                message, "toast message (failure state)", allure.attachment_type.TEXT
            )

        with allure.step(
            "Step 3 — Restore the connection and reload: the secrets-list request "
            "fires and is answered by the backend"
        ):
            page.unroute(SECRETS_LIST_GLOB)
            with page.expect_response(
                secrets_page._is_secrets_list_response, timeout=RECOVERY_TIMEOUT
            ) as response_info:
                page.reload(wait_until="domcontentloaded")
            response = response_info.value

            assert response.status == 200, (
                f"Case step 3 — after restoring the connection the secrets-list "
                f"request must succeed, got HTTP {response.status}"
            )
            api_secrets = response.json()
            assert isinstance(api_secrets, list) and api_secrets, (
                "Case precondition — the project must hold at least one secret so "
                f"step 4 is non-vacuous, API returned {api_secrets!r}"
            )
            logger.info("Recovery: list returned %d secrets", len(api_secrets))

        with allure.step(
            "Step 4 — Verify the page recovers and the secrets list loads correctly"
        ):
            # Relational, not literal: the expected row count is derived from
            # the LIVE payload capped at the product's default page size, so
            # adding a secret cannot break this test.
            expected_rows = min(len(api_secrets), DEFAULT_PAGE_SIZE)
            expect(secrets_page.secret_row).to_have_count(
                expected_rows, timeout=RECOVERY_TIMEOUT
            )

            api_names = {s["name"] for s in api_secrets}
            rendered_names = [
                name.strip()
                for name in secrets_page.secret_row.locator(
                    secrets_page.SECRET_NAME_CELL_SELECTOR
                ).all_inner_texts()
            ]
            assert rendered_names, "Recovered table rendered no name cells"
            unknown = [n for n in rendered_names if n not in api_names]
            assert not unknown, (
                "Case step 4 — every rendered row must come from the live API "
                f"response (stale rows would also satisfy a bare count check); "
                f"{unknown} are absent from the {len(api_names)} names the backend returned"
            )

            # Recovery clears the failure state rather than stacking on it.
            expect(secrets_page.toast_alert).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
