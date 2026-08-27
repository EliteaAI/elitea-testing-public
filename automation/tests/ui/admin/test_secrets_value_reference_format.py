"""UI test — Value column shows {{secret.name}} reference format when masked.

Read-only verification against the logged-in user's existing project secrets.
Every row is masked on load: the list GET returns `secret_name` (the reference
template), never the plaintext, and `SecretValueCell.jsx` renders it verbatim
until the row-level eye toggle fetches the real value (ELITEA-2343, a different
case). So the case's "when secret is masked" condition is the page's default
state — no setup is needed and the value cell is never clicked here.

The expected value is DERIVED from the name the product itself rendered
(`"{{secret." + name + "}}"`), so the assertion is fully deterministic while
every asserted value still comes from the system — the oracle is the product,
not a payload the test wrote.

No substitution of the system under test: no route interception, no injected
state, no fabricated response.

Test case: ELITEA-2342
AFS: test-specs/settings-secrets/l2_secrets-value-column-reference-format_ELITEA-2342.md

Known defect (EliteaAI/elitea-testing-public#1203): see the isolated soft
failure at the end of the flow.
"""

import logging

import allure
import pytest
from pages.secrets_page import SecretsPage
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p1, pytest.mark.regression, pytest.mark.new]

REFERENCE_PREFIX = "{{secret."
REFERENCE_SUFFIX = "}}"


def _is_known_defect_1203(text: str) -> bool:
    """True for the known, filed, isolated console error EliteaAI/
    elitea-testing-public#1203 ("Maximum update depth exceeded" on mount)."""
    return "Maximum update depth exceeded" in text


def _assert_reference_format(names: list[str], values: list[str], where: str) -> None:
    """Assert the per-row Value <-> Name correspondence and the masking invariant.

    Args:
        names: rendered `secret-name-cell` texts, in rendered order.
        values: rendered `secret-value-cell` texts, in rendered order.
        where: human-readable location, e.g. "page 1" — quoted in failures.
    """
    assert len(names) == len(values), (
        f"Expected one Value cell per Name cell on {where}: "
        f"{len(names)} names vs {len(values)} values"
    )
    assert names, f"Expected at least one row on {where} so the assertion is non-vacuous"

    mismatches = [
        (name, value)
        for name, value in zip(names, values, strict=True)
        if value != REFERENCE_PREFIX + name + REFERENCE_SUFFIX
    ]
    assert not mismatches, (
        f"Expected every row's Value cell on {where} to read exactly "
        f"'{{{{secret.<that row's name>}}}}'; mismatched (name, value) pairs: {mismatches}"
    )

    # The security-relevant half of "when the secret is masked": a regression
    # rendering the plaintext would have to coincidentally equal the template
    # to survive the correspondence check above.
    leaks = [
        (name, value)
        for name, value in zip(names, values, strict=True)
        if not (value.startswith(REFERENCE_PREFIX) and value.endswith(REFERENCE_SUFFIX))
        or value == name
    ]
    assert not leaks, (
        f"Expected every masked Value cell on {where} to be a '{{{{secret.…}}}}' "
        f"reference and never the bare name or a plaintext value; offenders: {leaks}"
    )


class TestSecretsValueReferenceFormat:
    """ELITEA-2342 — every masked row's Value column renders the reference
    template built from that row's own secret name."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/secrets/ELITEA-2342_value-column-shows-secret-name-reference-format-when-masked.md",
        "onetest-ai Test Case link",
    )
    def test_value_column_shows_secret_reference_format(self, page):
        secrets_page = SecretsPage(page)
        console_errors = collect_console_errors(page)
        soft_failures: list[str] = []

        with allure.step("Step 1 — Navigate to Settings -> Secrets"):
            secrets_page.navigate()
            row_count = secrets_page.secret_row.count()
            assert row_count >= 1, (
                "Case precondition — expected at least one secret row so the "
                f"per-row assertions are non-vacuous, got {row_count}"
            )

        with allure.step(
            "Steps 2-3 — Verify every rendered row's Value column shows the "
            "reference format {{secret.<name>}}, matching that row's own name exactly"
        ):
            names = secrets_page.get_row_names()
            values = secrets_page.get_row_values()
            assert len(names) == row_count, (
                f"Expected one name cell per row ({row_count}), got {len(names)}"
            )
            _assert_reference_format(names, values, "page 1")

        with allure.step(
            "Step 4 — Verify the same per-row correspondence holds on a second page "
            "of data (the case says 'each secret row', and re-slicing the list is "
            "where a row/value mapping bug would surface)"
        ):
            if secrets_page.next_page_button.is_enabled():
                secrets_page.click_next_page()
                page2_names = secrets_page.get_row_names()
                page2_values = secrets_page.get_row_values()
                assert set(page2_names).isdisjoint(set(names)), (
                    "Expected page 2 to render a different set of secrets than page 1; "
                    f"overlap: {sorted(set(page2_names) & set(names))}"
                )
                _assert_reference_format(page2_names, page2_values, "page 2")
            else:
                logger.info(
                    "Single-page dataset (%d rows) — the second-page check is not "
                    "applicable; page 1 already covers every existing row",
                    row_count,
                )

        with allure.step("Step 5 — Verify no unexpected console errors across the flow"):
            unexpected_errors = [e for e in console_errors if not _is_known_defect_1203(e)]
            assert not unexpected_errors, f"Unexpected console errors: {unexpected_errors}"

            known_defect_errors = [e for e in console_errors if _is_known_defect_1203(e)]
            if known_defect_errors:
                # Known defect: EliteaAI/elitea-testing-public#1203
                soft_failures.append(
                    "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1203: "
                    f"React 'Maximum update depth exceeded' console error(s) on "
                    f"/settings/secrets mount: {len(known_defect_errors)} occurrence(s)"
                )

        if soft_failures:
            pytest.fail(
                "Test flow completed and all functional assertions passed, but "
                "known-defect soft failures were recorded:\n" + "\n".join(soft_failures)
            )
