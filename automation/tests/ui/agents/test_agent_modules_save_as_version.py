"""Save As Version keeps module changes on the new version; the base version is
unchanged (ELITEA-4792).

Baseline-relative: a fresh agent's module states are recorded live and two
modules are flipped relative to that record (nothing hardcoded ON/OFF).
The ``agent_id`` fixture deletes the agent (and its versions) at teardown.

Spec: test-specs/agents/l0_save-as-version-keeps-module-changes-base-unchanged_ELITEA-4792.md
"""

import allure
import pytest
from pages.agent_detail_page import AgentDetailPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.agents]

TIMEOUT = 10_000
VERSION_NAME = "modules-reg-v2"
# Toggle without a warning dialog and keep the menu open (verified live).
MODULE_A = "pyodide"
MODULE_B = "web_search"
# Rows that need special handling (warning dialog / (i) icon at row centre).
AVOID = {"code_mode", "attachments"}


def _snapshot_modules(detail: AgentDetailPage) -> dict[str, bool]:
    """Open the Modules menu, read every module's switch, close the menu."""
    detail.open_modules_menu(timeout=TIMEOUT)
    states = {key: detail.module_is_on(key) for key in detail.module_menu_item_keys()}
    detail.page.keyboard.press("Escape")
    expect(detail.modules_menu).to_be_hidden(timeout=TIMEOUT)
    return states


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
    "agents/modules/ELITEA-4792_save-as-version-keeps-module-changes-base-version-unchanged.md",
    "onetest-ai Test Case link",
)
@pytest.mark.tms("ELITEA-4792")
@pytest.mark.p0
@pytest.mark.regression
def test_save_as_version_keeps_module_changes_and_base_unchanged(page, agent_id):
    detail = AgentDetailPage(page)
    detail.navigate(agent_id)
    detail.dismiss_platform_release_banner_if_present()

    with allure.step("Step 1 — Record every module state on the base version"):
        base = _snapshot_modules(detail)
        assert base, "Modules menu listed no modules"
        assert MODULE_A in base, f"{MODULE_A} missing from modules: {sorted(base)}"
        module_b = MODULE_B
        if module_b not in base:
            module_b = next(k for k in reversed(list(base)) if k not in AVOID | {MODULE_A})
        base_version = detail.get_version_selector_value()

    changed = {MODULE_A: not base[MODULE_A], module_b: not base[module_b]}

    with allure.step("Step 2 — Switch two modules to the opposite state"):
        detail.open_modules_menu(timeout=TIMEOUT)
        for key in changed:
            detail.toggle_module(key, timeout=TIMEOUT)
        for key, want in changed.items():
            assert detail.module_is_on(key) == want, f"{key} did not switch to {want}"
        page.keyboard.press("Escape")
        expect(detail.modules_menu).to_be_hidden(timeout=TIMEOUT)

    with allure.step(f"Step 3 — Save As Version '{VERSION_NAME}' creates and opens the new version"):
        url_before = page.url
        detail.save_as_version(VERSION_NAME, timeout=TIMEOUT)
        assert detail.get_version_selector_value() == VERSION_NAME
        assert page.url != url_before, "URL did not move to the new version"

    expected_v2 = {**base, **changed}
    with allure.step("Step 4 — New version shows the two changed states; the others match base"):
        v2 = _snapshot_modules(detail)
        assert v2 == expected_v2, {k: (base.get(k), v2.get(k)) for k in set(base) | set(v2) if base.get(k) != v2.get(k)}

    with allure.step("Step 5 — Base version still shows the originally recorded states"):
        detail.open_version_selector(timeout=TIMEOUT)
        detail.select_version_by_name(base_version, timeout=TIMEOUT)
        assert detail.get_version_selector_value() == base_version
        assert _snapshot_modules(detail) == base

    with allure.step("Step 6 — Switching back to the new version still shows the changes"):
        detail.open_version_selector(timeout=TIMEOUT)
        detail.select_version_by_name(VERSION_NAME, timeout=TIMEOUT)
        assert detail.get_version_selector_value() == VERSION_NAME
        assert _snapshot_modules(detail) == expected_v2
