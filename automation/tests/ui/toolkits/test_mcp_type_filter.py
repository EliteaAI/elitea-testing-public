"""UI test — MCP list page "Types" filter (Remote).

TMS: ELITEA-1942 (test-specs/mcp/l1_mcp-dashboard-filter-by-type-remote_ELITEA-1942.md)

Verifies the MCP dashboard's right-hand "Types" panel (shared
``Categories.jsx``): both type chips render, selecting **Remote** applies a
server-side filter (URL ``?tags[]=Remote`` + the panel's own "Clear all"
affordance), only Remote-badged MCPs are listed, no Local-badged card leaks
through, and re-clicking the chip restores the exact unfiltered list captured
in step 1.

Environment clarification (AFS § Preconditions, question
github.com/EliteaAI/elitea-testing-public#1738): the case's precondition
"both Local and Remote MCPs exist" does NOT hold and cannot be made to hold
here — ``GET /toolkit_types/prompt_lib/{project}?mcp=true`` returns
``{"rows": ["mcp"], "total": 1}`` and ``/mcps/create`` offers a single type
card, so no Local MCP can be found or created. Step 5 is therefore automated
in its honest, test-enforced form — *no rendered card carries a ``Local``
badge while the Remote filter is active* (an absence assertion that turns red
the day a Local MCP exists and leaks through), not as "ADO/FileSystem/
PlaywrightMCP disappeared".

Known defect not exercised here (EliteaAI/elitea-testing-public#1737, OPEN):
the **Local** chip applies visibly but does not filter. It does not affect
this case — the Remote path is correct — and the Local absence assertion
above must never be "fixed" by clicking the Local chip.

No substitutions: every asserted value (card names, badge texts, URL,
Clear-all presence) is produced by the live product against whatever MCPs the
shared DEV project holds; the baseline is captured at run time, never
hardcoded.
"""

import logging
import uuid
from urllib.parse import unquote

import allure
import pytest
from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage
from pages.mcp_list_page import McpListPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p1, pytest.mark.regression]

REMOTE_TYPE = "Remote"
LOCAL_TYPE = "Local"


def _seed_mcp_via_ui(page) -> int:
    """Create a minimal Remote MCP through the UI create flow; return its id.

    Called only when the project is genuinely empty (see
    :meth:`McpListPage.has_any_mcp`) — read-only-by-default (Hard Rule 10)
    otherwise reuses whatever MCPs already exist. Same seed-if-empty guard as
    ``test_mcp_view_toggle.py`` (ELITEA-1944), which the AFS names as the
    established pattern for this precondition.
    """
    form = McpFormPage(page)
    # McpListPage.has_any_mcp() already left the page on /mcps/create.
    form.select_remote_mcp_type()
    form.fill_name(f"autotest_mcp_typefilter_{uuid.uuid4().hex[:6]}")
    form.fill_url("https://mcp.example.com/sse")
    save_response = form.save_and_wait_for_created(str(settings.elitea_project_id))
    return save_response["id"]


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1942_mcp-dashboard-filter-by-type-remote-only.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_dashboard_filter_by_type_remote(page, toolkit_api: ToolkitAPI):
    """The Remote type filter shows only Remote MCPs; deselecting restores all."""
    list_page = McpListPage(page)
    seeded_mcp_id: int | None = None

    # Side-channel check (AFS § Expected Results): the whole filter flow is
    # console-error-clean live. Warnings are NOT collected — /mcps/all carries
    # the pre-existing #291 "missing key" dev warning via the shared
    # ToolkitTypeSelector render path (see test_mcp_search_by_name.py), which
    # this case's assertion must not be masked by nor falsely fail on.
    console_errors: list[str] = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

    try:
        # Precondition (AFS § Preconditions): at least one MCP must exist —
        # with zero MCPs /mcps/all redirects to /mcps/create and the Types
        # panel never renders. Not a case step.
        if not list_page.has_any_mcp():
            seeded_mcp_id = _seed_mcp_via_ui(page)
            logger.info("Seeded MCP toolkit %s — project had zero MCPs", seeded_mcp_id)

        with allure.step(
            "Step 1 — Navigate to the MCP list page: it loads and shows the unfiltered MCP list"
        ):
            list_page.navigate()
            list_page.wait_for_type_panel(REMOTE_TYPE)
            baseline_names = list_page.get_card_names()
            baseline_count = len(baseline_names)
            assert baseline_count >= 1, (
                "Expected at least one MCP card on a fresh unfiltered list load, got none"
            )
            # No filter may be active on a clean load — otherwise step 3's
            # Clear-all assertion could be satisfied by a leftover filter
            # (AFS Axis 2).
            assert not list_page.is_type_filter_active(), (
                "A fresh /mcps/all load must carry no active type filter, but the Types panel "
                "is already rendering its 'Clear all' control"
            )
            logger.info("Unfiltered baseline: %s MCP(s) — %s", baseline_count, baseline_names)

        with allure.step(
            'Step 2 — Verify the "Types" filter area shows both the Local and Remote chips'
        ):
            # The panel title text carries no testid; the two chips (which do)
            # are the testid-only equivalent of the case's "Types label and
            # filter buttons Local and Remote are visible" (AFS step 2).
            assert list_page.type_filter_chip(LOCAL_TYPE).first.is_visible(), (
                "The Types panel must render a 'Local' filter chip"
            )
            assert list_page.type_filter_chip(REMOTE_TYPE).first.is_visible(), (
                "The Types panel must render a 'Remote' filter chip"
            )

        with allure.step('Step 3 — Click the "Remote" chip: the filter is applied'):
            response = list_page.click_type_filter(REMOTE_TYPE)
            assert response.status == 200, (
                f"Filtered MCP list query failed: HTTP {response.status} for {response.url}"
            )
            assert f"tags[]={REMOTE_TYPE}" in unquote(page.url), (
                f"Selecting the Remote chip must push ?tags[]={REMOTE_TYPE} into the URL, "
                f"got {page.url}"
            )
            # The product's own "a filter is active" signal — the panel
            # renders Clear all only while >=1 chip is selected.
            assert list_page.is_type_filter_active(), (
                "The Types panel must render its 'Clear all' control while the Remote filter "
                "is applied"
            )

        with allure.step(
            'Step 4 — Verify only MCPs carrying a "Remote" type badge are displayed'
        ):
            filtered_names = list_page.get_card_names()
            badges = list_page.get_visible_type_badges()
            assert set(badges) == {REMOTE_TYPE}, (
                f"Every rendered card must carry a {REMOTE_TYPE!r} type badge while the Remote "
                f"filter is active, got badges {badges}"
            )
            # Pairing the counts closes the hole where a card renders no badge
            # at all — set(badges) == {"Remote"} alone would still pass (AFS Axis 2).
            assert len(badges) == len(filtered_names), (
                f"Every visible card must be badged: {len(filtered_names)} card(s) rendered but "
                f"{len(badges)} type badge(s) — {filtered_names} vs {badges}"
            )
            # In this environment every MCP is Remote, so the Remote filter is
            # a no-op on the result set — compared against the CAPTURED
            # baseline, never a literal (the DEV project is shared and churns).
            assert filtered_names == baseline_names, (
                f"The Remote filter must retain every Remote MCP; expected {baseline_names}, "
                f"got {filtered_names}"
            )

        with allure.step("Step 5 — Verify Local MCPs are hidden (no Local-badged card renders)"):
            # CLARIFICATION (AFS step 5 / question #1738): vacuous in this
            # environment — no Local MCP exists or can be created here. Kept
            # as a real absence assertion so it turns red the day one exists
            # and leaks through the Remote filter.
            assert badges.count(LOCAL_TYPE) == 0, (
                f"No card may carry a {LOCAL_TYPE!r} badge while the Remote filter is active, "
                f"got badges {badges}"
            )

        with allure.step('Step 6 — Click the "Remote" chip again: the filter is deactivated'):
            response = list_page.remove_type_filter(REMOTE_TYPE)
            assert response.status == 200, (
                f"Unfiltered MCP list query failed: HTTP {response.status} for {response.url}"
            )
            assert "tags[]=" not in unquote(page.url), (
                f"Deselecting the Remote chip must drop the tags[] query param, got {page.url}"
            )
            assert not list_page.is_type_filter_active(), (
                "The Types panel must unmount its 'Clear all' control once no chip is selected"
            )

        with allure.step("Step 7 — Verify all MCPs reappear (the step-1 baseline is restored)"):
            restored_names = list_page.get_card_names()
            assert restored_names == baseline_names, (
                f"Removing the Remote filter must restore the unfiltered list captured in "
                f"step 1; expected {baseline_names}, got {restored_names}"
            )

        with allure.step("Side-channel check — no console errors across the filter flow"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"

    finally:
        # Not a case step — cleanup for the MCP seeded above when the project
        # was empty (AFS § Cleanup: the case itself is read-only and creates
        # nothing; pre-existing MCPs are reused and never touched).
        if seeded_mcp_id is not None:
            try:
                toolkit_api.delete_toolkit(seeded_mcp_id)
            except Exception:
                logger.warning(
                    "Failed to delete seeded MCP toolkit id=%s during cleanup",
                    seeded_mcp_id,
                    exc_info=True,
                )
