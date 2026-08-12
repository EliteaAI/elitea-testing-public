"""UI Test for Agent name field's 32-character limit (ELITEA-1900).

Verifies that the Name field on the Create Agent page enforces a
32-character maximum: typing more than 32 characters truncates the value
at exactly 32 (both via a single bulk `fill()` and via continued
keystroke-level typing past the boundary), no error state is shown while
the field sits exactly at the limit, and the Save button still becomes
enabled once Description is also filled.

Spec: test-specs/agents/l3_agent-name-character-limit-32_ELITEA-1900.md

Read-only / no test data: the test never clicks Save, so no agent is
created and nothing needs cleanup.

Markers:
    - ui: requires browser
    - agents: agent-related tests
    - p3: low priority (frontmatter priority is "low"/l3 — matches
      pytest.ini's p3 marker, same l3->p3 mapping used by the immediately
      adjacent sibling case ELITEA-1899's
      ``test_agent_icon_management.py``)
"""

import allure
import pytest
from pages.agent_form_page import AgentFormPage

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.new]

FORM_LOAD_TIMEOUT = 15000
MAX_NAME_LENGTH = 32  # EliteaUI src/common/constants.js


# Known defect #554 (already filed, unrelated) — an RTK-Query timing race in
# EliteaUI/src/api/toolkits.js's `toolkitTypes` endpoint fires before
# `useSelectedProjectId()` resolves, building the URL with an empty
# projectId segment (".../toolkits/prompt_lib/") which 404s. Intermittent
# (client-side race, not deterministic) and unrelated to the Name-field
# character-limit flow this filter is applied to — applied defensively
# (the Create Agent form page is within the same trigger condition #554
# documents as reproducible on "any page render"), matching the batch's
# own hardening-gate findings (elitea-testing-public#1277). SAME filter
# technique already established in test_credential_search_by_name.py /
# test_agent_publish_unpublish_version.py — matched on msg.location.url
# containing the toolkits endpoint path, NOT a blanket "any 404" filter,
# so an unrelated 404 from a genuinely different resource still surfaces
# as a real, unexpected failure.
def _is_known_554_toolkits_404(msg) -> bool:
    location_url = (msg.location or {}).get("url", "")
    return "404" in msg.text and "elitea_core/toolkits/prompt_lib/" in location_url


@pytest.mark.p3
@pytest.mark.regression
def test_agent_name_truncated_at_32_characters(page):
    """Name field truncates input to 32 chars, no error at the limit, Save
    enables once Description is also filled (ELITEA-1900).

    Read-only: no agent is created, edited, or deleted.
    """
    form_page = AgentFormPage(page)

    console_messages = []
    page.on(
        "console",
        lambda msg: console_messages.append(msg)
        if msg.type == "error" and not _is_known_554_toolkits_404(msg)
        else None,
    )

    with allure.step("Step 1 — Navigate to the Create Agent page"):
        form_page.navigate("/agents/create")
        form_page.wait_for_form_load(timeout=FORM_LOAD_TIMEOUT)
        assert form_page.name_input.is_visible(), "Name field should be visible"
        assert form_page.description_input.is_visible(), (
            "Description field should be visible"
        )
        assert form_page.get_name() == "", (
            "Name field should be empty on a fresh Create Agent form"
        )
        assert form_page.get_description() == "", (
            "Description field should be empty on a fresh Create Agent form"
        )
        assert not form_page.is_save_enabled(), (
            "Save button should be disabled on a fresh Create Agent form — "
            "control condition proving Step 5's later 'enabled' is a real "
            "state change"
        )

    with allure.step(
        "Step 2 — Type 80 characters into the Name field via a single "
        "bulk fill()"
    ):
        overflow_name = "A" * 80
        form_page.name_input.fill(overflow_name)

    with allure.step(
        "Step 3a — Verify the Name field contains exactly 32 characters "
        "after the bulk fill (no more than the limit was accepted)"
    ):
        truncated_value = form_page.get_name()
        assert len(truncated_value) == MAX_NAME_LENGTH, (
            f"Name field should be truncated to {MAX_NAME_LENGTH} chars, "
            f"got {len(truncated_value)} chars: {truncated_value!r}"
        )
        assert truncated_value == "A" * MAX_NAME_LENGTH, (
            f"Name field should contain exactly {MAX_NAME_LENGTH} 'A' "
            f"characters, got: {truncated_value!r}"
        )

    with allure.step(
        "Step 3b — Reset the field, type exactly 32 characters via real "
        "keystrokes, then attempt 5 more keystrokes past the boundary — "
        "verify the extra input is silently rejected (value stays at "
        "exactly 32 chars)"
    ):
        form_page.name_input.click()
        form_page.name_input.clear()
        form_page.name_input.press_sequentially("A" * MAX_NAME_LENGTH, delay=10)
        assert len(form_page.get_name()) == MAX_NAME_LENGTH, (
            "Name field should hold exactly 32 chars after typing exactly "
            "32 keystrokes"
        )

        form_page.name_input.press_sequentially("BBBBB", delay=10)
        value_after_overflow_keystrokes = form_page.get_name()
        assert len(value_after_overflow_keystrokes) == MAX_NAME_LENGTH, (
            "5 additional keystrokes past the 32-char boundary should be "
            f"silently rejected — expected length {MAX_NAME_LENGTH}, got "
            f"{len(value_after_overflow_keystrokes)}: "
            f"{value_after_overflow_keystrokes!r}"
        )
        assert value_after_overflow_keystrokes == "A" * MAX_NAME_LENGTH, (
            "Value should remain unchanged ('A' * 32) after the rejected "
            f"overflow keystrokes, got: {value_after_overflow_keystrokes!r}"
        )

    with allure.step(
        "Step 4 — Verify no error state is shown while the Name field "
        "sits exactly at the 32-character limit"
    ):
        assert not form_page.is_name_invalid(), (
            "Name field should NOT be flagged aria-invalid at the exact "
            "32-character limit — the limit is enforced by the native "
            "maxlength attribute, not a length-validation error"
        )

    with allure.step(
        "Step 5 — Fill the Description field and verify Save becomes "
        "enabled (Name at the 32-char limit, Description non-empty)"
    ):
        form_page.description_input.click()
        form_page.description_input.press_sequentially(
            "Filler description for ELITEA-1900", delay=10
        )
        form_page.wait_for_form_validation()
        assert form_page.is_save_enabled(), (
            "Save button should be enabled once Name (at the 32-char "
            "limit) and Description are both filled"
        )

    with allure.step(
        "Side-channel check — no console errors across the whole flow "
        "(navigate -> type 80 chars -> verify truncation/no-error -> "
        "fill description -> verify Save enabled)"
    ):
        assert not console_messages, (
            "Unexpected console errors during the name-character-limit "
            f"flow: {[m.text for m in console_messages]}"
        )
