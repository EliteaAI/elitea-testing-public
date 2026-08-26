"""UI test — Entry Point Node: Trigger Restricted When HITL/Printer/Interrupts Present.

TMS: ELITEA-2008
(test-specs/pipelines/l3_entry-point-trigger-restricted-interactive-nodes_ELITEA-2008.md)

Verifies the entry-point node's Trigger dropdown restricts the pipeline to the
Chat Message trigger whenever the pipeline's LAST-SAVED version contains a
Printer node, a HITL node, or a non-empty interrupt_before/interrupt_after
list — and that the restriction is keyed on the saved YAML, NOT the live
unsaved canvas (a restricting element added but not yet saved has NO effect on
the dropdown). Once saved, the restriction takes effect immediately (no reload
needed) and survives a reload. Removing all restricting elements + Save lifts
it again.

Since EliteaAI/EliteaUI@cb70a64e (EL-6128, on `main` 2026-08-24) the
restriction is expressed by GREYING THE OPTIONS OUT IN PLACE rather than
hiding them: `availableTriggerOptions` now maps Schedule/Webhook to
`{...opt, disabled: true}` instead of filtering them out. The option list is
therefore `[Chat Message, Schedule, Webhook]` in BOTH the restricted and the
unrestricted state, and the enabled/disabled split is the only observable that
discriminates between them — so every checkpoint below asserts that split, on
both sides of the restrict -> un-restrict cycle. (Asserting the option list
alone would leave a test that cannot fail.)

State is read as `aria-disabled` — MUI's own attribute; ABSENT, not "false",
on an enabled option. Filtering the existing `select-option-{value}` testid on
`aria-disabled` instead of a `data-*` attribute is a DECLARED IMPROVISATION
under .agents/role-overrides.md § Declared-improvisation protocol, canon-gap
card #1805: adding a `data-disabled` mirror would edit a shared component for
one case and would ship on `automation/testids` only, making this test green
on localhost and red on dev.elitea.ai — the exact promotion gap this repair
exists to close. See PipelineDetailPage.TRIGGER_OPTION_DISABLED.

No substitutions: every observable here is produced by the running system —
real pipeline via the `pipeline_with_llm_id` fixture, real node add/delete on
the ReactFlow canvas, real Save with its real response, real page reload, and
the option state read from the real rendered DOM.
"""

import logging

import allure
import pytest
from config import settings
from utils.console_errors import collect_console_errors

from tests.ui.pipeline_helpers import _navigate_to_canvas

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000

# Expected `{trigger_value: is_enabled}` maps, per
# PipelineDetailPage.get_trigger_option_states(). A value missing from the
# actual mapping means that option was not rendered at all, which fails the
# comparison the same way a wrong state does — so each assertion covers both
# "all three options are offered" and "these are the selectable ones".
ALL_THREE_ENABLED = {"chat_message": True, "schedule": True, "webhook": True}
CHAT_MESSAGE_ONLY_ENABLED = {"chat_message": True, "schedule": False, "webhook": False}


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2008_entry-point-trigger-restricted-interactive-nodes.md",
    "onetest-ai Test Case link",
)
def test_entry_point_trigger_restricted_interactive_nodes(page, pipeline_with_llm_id):
    """Chat-Message-only restriction gates on the SAVED version, for Printer/HITL/interrupts alike."""
    project_id = str(settings.elitea_project_id)
    console_errors = collect_console_errors(page)

    with allure.step(
        "Step 1 — Navigate to the fresh pipeline; verify baseline: all 3 trigger options present and ENABLED"
    ):
        pipeline_page = _navigate_to_canvas(page, pipeline_with_llm_id)
        llm_node_id = pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        baseline_states = pipeline_page.get_trigger_option_states(
            timeout=UI_ELEMENT_TIMEOUT, entry_point_node_id=llm_node_id
        )
        assert baseline_states == ALL_THREE_ENABLED, (
            f"Baseline (no restricting elements) should offer all 3 trigger types with all 3 "
            f"SELECTABLE, got {baseline_states!r}"
        )

    with allure.step('Step 2 — Add a Printer node (unconnected); verify it exists on canvas'):
        pipeline_page.add_node("Printer")
        printer_node_id = pipeline_page.wait_for_node_on_canvas("printer", timeout=UI_ELEMENT_TIMEOUT)
        assert printer_node_id in pipeline_page.get_node_ids(), (
            "Printer node should be present on the canvas after add_node"
        )

    with allure.step(
        "Step 3 — WITHOUT saving, open the Trigger dropdown; verify the restriction does NOT apply yet"
    ):
        # Load-bearing precondition finding (AFS Coverage Map row 4): the
        # restriction is keyed on the pipeline's last-SAVED YAML
        # (`version_details.instructions`), NOT the live unsaved ReactFlow
        # canvas — unchanged by EL-6128, re-confirmed live 2026-08-26. A
        # literal "add node -> assert restriction" would produce a false
        # negative here. Asserting the ENABLED state (not merely the option
        # list) is what keeps this step discriminating: post-EL-6128 the list
        # is identical restricted or not.
        pre_save_states = pipeline_page.get_trigger_option_states(
            timeout=UI_ELEMENT_TIMEOUT, entry_point_node_id=llm_node_id
        )
        assert pre_save_states == ALL_THREE_ENABLED, (
            "Restriction should NOT apply before Save — the unsaved Printer node on the live "
            f"canvas should leave all 3 trigger types selectable, got {pre_save_states!r}"
        )

    with allure.step("Step 4 — Save the pipeline"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_with_llm_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the updated pipeline version"

    with allure.step(
        "Step 5 — Open the Trigger dropdown again; verify Schedule + Webhook are DISABLED in place "
        "and Chat Message stays selectable, immediately (no reload needed) AND after a reload"
    ):
        post_save_states = pipeline_page.get_trigger_option_states(
            timeout=UI_ELEMENT_TIMEOUT, entry_point_node_id=llm_node_id
        )
        assert post_save_states == CHAT_MESSAGE_ONLY_ENABLED, (
            f"With the Printer node saved, all 3 options should still be listed but only Chat "
            f"Message selectable (Schedule + Webhook aria-disabled), got {post_save_states!r}"
        )

        canonical_url = page.url
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        post_reload_states = pipeline_page.get_trigger_option_states(
            timeout=UI_ELEMENT_TIMEOUT, entry_point_node_id=llm_node_id
        )
        assert post_reload_states == CHAT_MESSAGE_ONLY_ENABLED, (
            f"The disabled-in-place restriction should survive a reload, got {post_reload_states!r}"
        )

    with allure.step(
        "Step 6 — Remove Printer, add a HITL node instead; Save; verify the same restriction applies"
    ):
        pipeline_page.delete_node(printer_node_id)
        pipeline_page.add_node("Human-in-the-loop")
        hitl_node_id = pipeline_page.wait_for_node_on_canvas("hitl", timeout=UI_ELEMENT_TIMEOUT)
        assert hitl_node_id in pipeline_page.get_node_ids(), (
            "HITL node should be present on the canvas after add_node"
        )

        pipeline_page.save_and_wait_for_update(project_id, pipeline_with_llm_id, timeout=SAVE_RESPONSE_TIMEOUT)
        hitl_states = pipeline_page.get_trigger_option_states(
            timeout=UI_ELEMENT_TIMEOUT, entry_point_node_id=llm_node_id
        )
        assert hitl_states == CHAT_MESSAGE_ONLY_ENABLED, (
            f"With a saved HITL node present, Schedule + Webhook should be disabled and only Chat "
            f"Message selectable, got {hitl_states!r}"
        )

    with allure.step(
        "Step 7 — Remove HITL; add a second (non-entry-point) node and enable its "
        "'Interrupt before'; Save; verify the same restriction applies"
    ):
        pipeline_page.delete_node(hitl_node_id)
        # CommonInterruptSettings.jsx's "Interrupt before" toggle disables
        # only when the node IS the saved entry point (`entry_point === id`)
        # — a freshly-added Code node never is, so it's enabled regardless of
        # its own canvas connections. ("Interrupt after" was tried first but
        # is unusable here: the pipeline builder auto-wires a new node's
        # output to END, and that toggle disables whenever
        # `transition === END` — confirmed live during this implementation.)
        pipeline_page.add_node("Code")
        code_node_id = pipeline_page.wait_for_node_on_canvas("code", timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.toggle_node_interrupt_before(code_node_id, timeout=UI_ELEMENT_TIMEOUT)

        pipeline_page.save_and_wait_for_update(project_id, pipeline_with_llm_id, timeout=SAVE_RESPONSE_TIMEOUT)
        interrupt_states = pipeline_page.get_trigger_option_states(
            timeout=UI_ELEMENT_TIMEOUT, entry_point_node_id=llm_node_id
        )
        assert interrupt_states == CHAT_MESSAGE_ONLY_ENABLED, (
            f"With a saved non-empty interrupt list, Schedule + Webhook should be disabled and only "
            f"Chat Message selectable, got {interrupt_states!r}"
        )

    with allure.step(
        "Step 8 — Remove all HITL/Printer/interrupt configuration; Save; reload; "
        "verify all 3 trigger types are available AND ENABLED again"
    ):
        pipeline_page.toggle_node_interrupt_before(code_node_id, timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.delete_node(code_node_id)
        assert llm_node_id in pipeline_page.get_node_ids(), (
            "The original entry-point LLM node should still be present after cleanup"
        )

        pipeline_page.save_and_wait_for_update(project_id, pipeline_with_llm_id, timeout=SAVE_RESPONSE_TIMEOUT)

        canonical_url = page.url
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        restored_states = pipeline_page.get_trigger_option_states(
            timeout=UI_ELEMENT_TIMEOUT, entry_point_node_id=llm_node_id
        )
        # The ENABLED half is the whole discriminating content of this step:
        # post-EL-6128 a still-restricted pipeline lists the same 3 options.
        assert restored_states == ALL_THREE_ENABLED, (
            f"Removing every restricting element and saving should re-enable all 3 trigger types "
            f"(no option left aria-disabled), got {restored_states!r}"
        )

    assert not console_errors, (
        f"Exercising the trigger-restriction lifecycle should not introduce console errors: "
        f"{console_errors}"
    )
