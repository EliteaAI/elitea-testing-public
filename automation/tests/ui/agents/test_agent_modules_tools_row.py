"""+ Toolkit / + MCP / + Agent / + Pipeline still work next to + Modules, and a
tool add leaves module states unchanged (ELITEA-4793).

Adding/removing a tool persists immediately (Save/Discard stay disabled), so the
case's "click Save" is asserted as persistence after reload (AFS clarification 1).

Spec: test-specs/agents/l0_tools-row-quick-add-buttons-still-work-with-modules_ELITEA-4793.md
"""

import allure
import pytest
from pages.agent_detail_page import AgentDetailPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.agents]

TIMEOUT = 10_000


def _module_states(detail: AgentDetailPage) -> dict[str, bool]:
    return {key: detail.module_is_on(key) for key in detail.module_menu_item_keys()}


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
    "agents/modules/ELITEA-4793_tools-row-quick-add-buttons-work-next-to-modules-button.md",
    "onetest-ai Test Case link",
)
@pytest.mark.tms("ELITEA-4793")
@pytest.mark.p0
@pytest.mark.regression
def test_tools_row_quick_add_buttons_work_next_to_modules(page, agent_id, artifact_toolkit):
    detail = AgentDetailPage(page)
    detail.navigate(agent_id)
    detail.dismiss_platform_release_banner_if_present()
    detail.ensure_toolkits_section_visible()
    toolkit_name = artifact_toolkit["name"]

    buttons = {
        "Step 1 — + Toolkit": detail.add_toolkit_button,
        "Step 2 — + MCP": detail.add_mcp_button,
        "Step 3 — + Agent": detail.add_agent_button,
        "Step 4 — + Pipeline": detail.add_pipeline_button,
    }
    for step, button in buttons.items():
        with allure.step(f"{step} opens its picker and click-outside closes it"):
            detail.open_tools_row_picker(button, timeout=TIMEOUT)
            expect(detail.toolkit_search_input).to_be_visible(timeout=TIMEOUT)
            detail.dismiss_tools_row_picker(timeout=TIMEOUT)
            expect(detail.toolkit_search_input).to_have_count(0, timeout=TIMEOUT)

    with allure.step("Step 5 — + Toolkit with the Modules menu open closes the menu and opens the picker"):
        detail.open_modules_menu(timeout=TIMEOUT)
        before = _module_states(detail)
        assert before, "Modules menu listed no modules"
        detail.add_toolkit_button.click()
        expect(detail.modules_menu).to_be_hidden(timeout=TIMEOUT)
        expect(detail.toolkit_search_input).to_be_visible(timeout=TIMEOUT)
        detail.dismiss_tools_row_picker(timeout=TIMEOUT)

    with allure.step("Step 6 — Attach the toolkit: card appears and persists (Save stays disabled)"):
        detail.add_toolkit(toolkit_name)
        card = detail.toolkit_card.filter(has_text=toolkit_name)
        expect(card).to_have_count(1, timeout=TIMEOUT)
        expect(detail.save_button).to_be_disabled(timeout=TIMEOUT)
        expect(detail.discard_button).to_be_disabled(timeout=TIMEOUT)
        page.reload()
        detail.wait_for_page_load()
        detail.ensure_toolkits_section_visible()
        expect(detail.toolkit_card.filter(has_text=toolkit_name)).to_have_count(1, timeout=TIMEOUT)

    with allure.step("Step 7 — Module states are the same as recorded in step 5"):
        detail.open_modules_menu(timeout=TIMEOUT)
        assert _module_states(detail) == before
        page.keyboard.press("Escape")
        expect(detail.modules_menu).to_be_hidden(timeout=TIMEOUT)

    with allure.step("Step 8 — Remove the toolkit: card gone and stays gone after reload"):
        detail.remove_toolkit(toolkit_name)
        expect(detail.toolkit_card.filter(has_text=toolkit_name)).to_have_count(0, timeout=TIMEOUT)
        expect(detail.save_button).to_be_disabled(timeout=TIMEOUT)
        page.reload()
        detail.wait_for_page_load()
        detail.ensure_toolkits_section_visible()
        expect(detail.toolkit_card.filter(has_text=toolkit_name)).to_have_count(0, timeout=TIMEOUT)
