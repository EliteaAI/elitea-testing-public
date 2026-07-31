"""UI Test for ELITEA-1866 — Create Artifact Bucket via Artifact Toolkit
Creation and Verify via List Files Tool.

Regression test: drives the full "New Toolkit" wizard through the
type-picker (search "art" -> filter to the sole "Artifact" card under
STORAGE), verifies every CONFIGURATION-form element (16 tool chips all
checkmarked, the MCP-availability checkbox, the Bucket field's info
tooltip), fills Name="my-artifact-toolkit"/Bucket="new-bucket" and Saves
(persisting BOTH a toolkit AND — as a server-side side effect of the SAME
create call — a bucket, confirmed at the network level: exactly one POST to
the toolkit-create endpoint, none to any bucket-create endpoint), then
exercises the toolkit-detail page's TEST SETTINGS panel end-to-end: selects
"List files", runs it against the just-created empty bucket, and verifies
the result. Finally confirms the new bucket is visible, searchable, and
shows the correct empty-bucket state in the Artifacts section.

Known findings (see AFS § Known Defects — neither blocking):
- [CLARIFICATION #669] the case's step-15 text says "click" the Bucket
  field's info icon; the live product (``InfoTooltip.jsx``, a plain MUI
  ``Tooltip``) only wires hover/focus — asserted via ``.hover()``, not
  ``.click()``, per the reverse-masking guard (live product is correct,
  case text is stale).
- [#636, pre-existing, root-cause lead only] ``ArtifactAPI.delete_bucket()``
  404s (path-segment URL shape, differs from the UI's own query-param
  shape) — NOT used for this test's bucket teardown; the UI dot-menu
  Delete flow is used instead (proven reliable, same as ELITEA-1817).

Test flow (39 case steps, folded where the case's own text splits one
observable across two steps — see AFS § Coverage Map for the full
step-by-step disposition):
1-2.   Navigate to Toolkits; verify the list is shown.
3-4.   Click "+ Toolkit"; verify the wizard opens (URL-based).
5-6.   Verify the type-search field and the 12 category filter tabs.
7-9.   Search "art"; verify exactly the "Artifact" card remains.
10.    Click the Artifact card; verify the config form opens.
11.    Verify the Name/Bucket fields are present.
12.    Verify all 16 tool chips are present AND checkmarked
       (`data-selected="true"` on every one, not just a count).
13.    Verify the MCP-availability checkbox is present and unchecked.
14.    Verify Save (disabled pre-dirty) and Cancel (enabled) are present.
15-16. Hover the Bucket field's info icon; verify the tooltip's exact
       bucket-naming-rules text.
17-19. Fill Name/Bucket; verify other fields stay at their defaults.
20-21. Click Save; verify navigation to the detail view + capture the new
       toolkit's numeric ID (needed by teardown) + verify the create POST
       is the ONLY mutating call (no separate bucket-create POST).
22-23. Verify the detail header shows the toolkit name; verify the URL
       reflects the new toolkit ID.
24.    Verify the Configuration/Indexes tabs are shown.
25.    Verify the TEST SETTINGS panel (model selector, Tool dropdown,
       welcome message).
26-28. Open the Tool dropdown; verify it lists all 16 tools including
       "List files"; select it.
29.    Verify the "List files" parameter panel (Bucket Name, Folder,
       Recursive, Include, Skip, RUN TOOL).
30-31. Click RUN TOOL; verify the result (`{'total': 0, 'rows': []}`).
32-36. Navigate to Artifacts; search "new"; verify "new-bucket" is listed.
37-39. Select "new-bucket"; verify the header + the empty-bucket state.

Cleanup: this case's own Preconditions mandate the EXACT literal names
"my-artifact-toolkit"/"new-bucket" (not randomized — see AFS § Test Data),
so collision-avoidance comes from idempotent pre-test cleanup PLUS
guaranteed post-test cleanup (a `try`/`finally`, since the test's core
subject is the CREATE path, not deletion — unlike ELITEA-1817, teardown
here is mandatory, not a fail-safe). Toolkit teardown uses
``ToolkitAPI.delete_toolkit()`` (proven reliable, 204). Bucket teardown
MUST use the UI dot-menu Delete flow, never ``ArtifactAPI.delete_bucket()``
(broken per #636 — see module docstring above).

AFS: test-specs/artifacts/l2_create-bucket-via-toolkit-verify-list-files_ELITEA-1866.md

Markers:
    - ui: requires browser
    - regression: regression test
    - toolkits: toolkit-creation-flow test
    - p1: high priority (matches case priority — AFS l2/"high")

Usage:
    cd automation
    pytest tests/ui/toolkits/test_toolkit_creation_create_bucket_verify_list_files.py -v
"""

import logging
import re

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from pages.toolkit_creation_page import ToolkitCreationPage
from pages.toolkit_detail_page import ToolkitDetailPage
from pages.toolkit_test_settings_page import ToolkitTestSettingsPage
from pages.toolkits_list_page import ToolkitsListPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.toolkits]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
TOOL_RUN_TIMEOUT = 15_000
DELETE_RESPONSE_TIMEOUT = 15_000

# The case's own literal Test Data — NOT placeholders (unlike sibling
# ELITEA-1808/1832/1839's generated names). The case's own Preconditions
# actively forbid randomizing these (see AFS § Test Data).
TOOLKIT_NAME = "my-artifact-toolkit"
BUCKET_NAME = "new-bucket"
SEARCH_TERM = "art"
TOOL_KEY = "list_files"

# Confirmed live (ELITEA-1866 exploration): the 16 tools an Artifact
# toolkit's TOOLS section renders, all selected by default.
EXPECTED_TOOL_COUNT = 16

# Live-confirmed exact tooltip text (whitespace-normalized — see
# ToolkitCreationPage.get_bucket_info_tooltip_text's docstring for why).
EXPECTED_TOOLTIP_TEXT = (
    "Name of the artifact bucket to use for file storage operations. "
    "The bucket name must: • Start with a lowercase letter "
    "• Contain only lowercase letters, numbers, and hyphens "
    "• Be unique within your project"
)

# Live-confirmed exact welcome message (TestTools.jsx's
# generateWelcomeMessage(isTestTools=True)).
EXPECTED_WELCOME_MESSAGE = (
    "Welcome! Select a tool from the Test Settings panel and click "
    "'RUN TOOL' to see the results here."
)

# Filed separately as github.com/EliteaAI/elitea-testing-public#656
# (MINOR, non-gating) — fires on every load of the type-picker screen,
# unrelated to this case's own pass/fail criteria. Exact filed signature
# only, so a genuinely new console error still fails this test.
KNOWN_NONGATING_CONSOLE_SIGNATURES = (
    'Each child in a list should have a unique "key" prop',
)


def _is_known_nongating_console_error(text: str) -> bool:
    return any(sig in text for sig in KNOWN_NONGATING_CONSOLE_SIGNATURES)


def _find_toolkit_id_by_name(toolkit_api, name: str):
    """Look up a toolkit's numeric ID by its EXACT name (never substring).

    Mirrors the same collision-avoidance discipline this AFS documents for
    bucket-name matching (`artifacts-bucket-row-new-bucket` vs. a
    substring-colliding `new-bucketautotest-buck1-...`) — the toolkit
    list-and-filter endpoint is a substring search too.
    """
    matches = toolkit_api.list_all_toolkits(params={"query": name})
    for t in matches:
        if t.get("name") == name:
            return t.get("id")
    return None


def _cleanup_stale_toolkit(toolkit_api) -> None:
    """Best-effort idempotent delete of any pre-existing TOOLKIT_NAME toolkit.

    Swallows all errors — a clean environment (the common case) is a no-op,
    not a failure (AFS § Test Data collision-avoidance design).
    """
    try:
        toolkit_id = _find_toolkit_id_by_name(toolkit_api, TOOLKIT_NAME)
        if toolkit_id is not None:
            toolkit_api.delete_toolkit(toolkit_id)
            logger.info("Cleaned up stale toolkit '%s' (id=%s)", TOOLKIT_NAME, toolkit_id)
    except Exception as exc:
        logger.warning("Toolkit cleanup for '%s' failed (continuing): %s", TOOLKIT_NAME, exc)


def _cleanup_stale_bucket(artifacts_page: ArtifactsPage) -> None:
    """Best-effort idempotent delete of any pre-existing BUCKET_NAME bucket.

    Uses the UI dot-menu Delete flow — NEVER ``ArtifactAPI.delete_bucket()``
    (broken per issue #636: its path-segment URL shape 404s; the UI's own
    call is query-param shaped and reliable — see this module's docstring
    and AFS § Cleanup / § Known Defects). Swallows all errors — a clean
    environment is the expected common case.
    """
    try:
        artifacts_page.navigate_to_artifacts()
        if artifacts_page.count_bucket_rows(BUCKET_NAME) == 0:
            return
        artifacts_page.open_bucket_menu(BUCKET_NAME, timeout=UI_ELEMENT_TIMEOUT)
        artifacts_page.click_bucket_menu_delete_item(timeout=UI_ELEMENT_TIMEOUT)
        artifacts_page.confirm_delete_bucket(timeout=DELETE_RESPONSE_TIMEOUT)
        artifacts_page.wait_for_bucket_removed_from_list(
            BUCKET_NAME, timeout=NAVIGATION_TIMEOUT,
        )
        logger.info("Cleaned up stale bucket '%s'", BUCKET_NAME)
    except Exception as exc:
        logger.warning("Bucket cleanup for '%s' failed (continuing): %s", BUCKET_NAME, exc)


@allure.epic("Toolkits")
@allure.feature("Toolkit Creation Wizard — Save Path (Artifact)")
class TestToolkitCreationCreateBucketVerifyListFiles:
    """ELITEA-1866 — Create an Artifact toolkit (which also creates a
    bucket), verify the TEST SETTINGS panel's List files tool, and confirm
    the new bucket in the Artifacts section.

    Idempotent pre-test cleanup PLUS guaranteed (`try`/`finally`) post-test
    cleanup for the case's own literal, non-randomized test data — see
    module docstring and AFS § Test Data / § Cleanup.
    """

    @pytest.mark.p1
    @allure.title(
        "Create an Artifact toolkit (creates a bucket as a side effect), "
        "run List files, verify the bucket in Artifacts"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1866_create-artifact-bucket-via-toolkit-verify-list-files.md",
        "onetest-ai Test Case link",
    )
    def test_create_artifact_toolkit_creates_bucket_verify_list_files(
        self, page, toolkit_api,
    ):
        """Create my-artifact-toolkit/new-bucket via the Save path, verify
        List files, verify the new bucket in Artifacts — with mandatory
        pre/post cleanup for the case's own literal test data.
        """
        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg)
            if msg.type == "error" and not _is_known_nongating_console_error(msg.text)
            else None,
        )

        toolkits_list = ToolkitsListPage(page)
        toolkit_creation = ToolkitCreationPage(page)
        toolkit_detail = ToolkitDetailPage(page)
        test_settings = ToolkitTestSettingsPage(page)
        artifacts_page = ArtifactsPage(page)

        with allure.step(
            "Precondition cleanup — idempotent best-effort delete of any "
            f"stale '{TOOLKIT_NAME}' toolkit / '{BUCKET_NAME}' bucket "
            "(this case's own literal Test Data — see AFS § Test Data)"
        ):
            _cleanup_stale_toolkit(toolkit_api)
            _cleanup_stale_bucket(artifacts_page)

        toolkit_id = None
        try:
            with allure.step("Step 1 — Navigate to the Toolkits section"):
                toolkits_list.navigate()

            with allure.step(
                "Step 2 — Verify the Toolkits list page is displayed "
                "showing existing toolkits"
            ):
                assert toolkits_list.count_visible_cards() > 0, (
                    "Toolkits list should show at least one existing "
                    "toolkit card"
                )

            with allure.step(
                "Steps 3-4 — Click '+ Toolkit'; verify the 'New Toolkit' "
                "wizard opens (URL-based — the 'Choose the toolkit type' "
                "heading carries no testid, and the URL already satisfies "
                "this step's own observable per the AFS)"
            ):
                toolkits_list.click_create_toolkit(timeout=NAVIGATION_TIMEOUT)
                assert "/toolkits/create" in page.url, (
                    f"Expected the wizard's type-picker URL, got: {page.url}"
                )

            with allure.step(
                "Step 5 — Verify the type-picker's search field is "
                "present with placeholder 'Search toolkits'"
            ):
                expect(toolkit_creation.type_search_input).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT,
                )
                assert (
                    toolkit_creation.type_search_input.get_attribute("placeholder")
                    == "Search toolkits"
                ), "Type-picker search field should have placeholder 'Search toolkits'"

            with allure.step(
                "Step 6 — Verify the category filter tabs are displayed "
                "(12 confirmed live)"
            ):
                assert toolkit_creation.count_category_tabs(
                    timeout=UI_ELEMENT_TIMEOUT
                ) == 12, "Expected all 12 category filter tabs to be visible"

            with allure.step(f"Step 7 — Type '{SEARCH_TERM}' in the search field"):
                toolkit_creation.search_toolkit_type(SEARCH_TERM)
                expect(toolkit_creation.type_search_input).to_have_value(
                    SEARCH_TERM, timeout=UI_ELEMENT_TIMEOUT,
                )

            with allure.step(
                "Steps 8-9 — Verify the toolkit list filters to show the "
                "'Artifact' card and to exclude non-matching types (the "
                "case's own text splits one observable across two steps)"
            ):
                # Two explicit halves instead of a total count: the Artifact card
                # IS shown, and a type that does NOT match the query is excluded.
                #
                # `count_type_cards() == 1` used to stand in for both, but the
                # product now ships a second "art"-matching type — "Elitea
                # Artifacts" (PLATFORM), supplied by the backend toolkit-type list
                # rather than EliteaUI source. Any absolute count is drift-prone:
                # it broke on the 2nd such type and would break again on a 3rd.
                artifact_card = toolkit_creation.get_type_card("artifact")
                expect(artifact_card).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(toolkit_creation.get_type_card("github")).to_have_count(
                    0, timeout=UI_ELEMENT_TIMEOUT,
                )

            with allure.step(
                "Step 10 — Click the 'Artifact' toolkit card (via its "
                "testid, never text-matching — a text-based locator "
                "resolves to a non-interactive ancestor and silently "
                "no-ops); verify the config form opens"
            ):
                artifact_card.click()
                assert "/toolkits/create/artifact" in page.url, (
                    f"Expected navigation to the Artifact config form, "
                    f"got: {page.url}"
                )
                expect(toolkit_creation.name_input).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT,
                )

            with allure.step(
                "Step 11 — Verify the CONFIGURATION section's Name and "
                "Bucket fields are present"
            ):
                bucket_field = toolkit_creation.get_field_locator("bucket")
                expect(bucket_field).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 12 — Verify the TOOLS section shows all 16 tools, "
                "EVERY ONE checkmarked (data-selected='true' on all 16, "
                "not just a count — Axis 2 addition, folds in the case's "
                "own 'with checkmarks' observable)"
            ):
                assert toolkit_creation.count_tool_chips(
                    timeout=UI_ELEMENT_TIMEOUT
                ) == EXPECTED_TOOL_COUNT, (
                    f"Expected {EXPECTED_TOOL_COUNT} tool chips in the "
                    "TOOLS section"
                )
                assert toolkit_creation.all_tool_chips_selected(), (
                    "Every tool chip should carry data-selected='true' "
                    "(checkmarked) by default"
                )

            with allure.step(
                "Step 13 — Verify the 'Make tools available by MCP' "
                "checkbox is present and unchecked by default"
            ):
                assert not toolkit_creation.is_checkbox_field_checked(
                    "available_by_mcp", timeout=UI_ELEMENT_TIMEOUT,
                ), "MCP-availability checkbox should be unchecked by default"

            with allure.step(
                "Step 14 — Verify Save (disabled pre-dirty) and Cancel "
                "(enabled) are both present"
            ):
                expect(toolkit_creation.save_button).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT,
                )
                assert toolkit_creation.save_button.is_disabled(), (
                    "Save should be disabled before any field is dirtied"
                )
                assert toolkit_creation.is_cancel_enabled(
                    timeout=UI_ELEMENT_TIMEOUT
                ), "Cancel button should be visible and enabled"

            with allure.step(
                "Step 15 — Hover (NOT click) the info icon next to the "
                "Bucket field — KNOWN CLARIFICATION #669: case text says "
                "'click', live product only wires hover/focus"
            ):
                toolkit_creation.hover_bucket_info_icon(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 16 — Verify the tooltip shows the exact bucket "
                "naming-rules text"
            ):
                tooltip_text = toolkit_creation.get_bucket_info_tooltip_text(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert tooltip_text == EXPECTED_TOOLTIP_TEXT, (
                    f"Expected tooltip text {EXPECTED_TOOLTIP_TEXT!r}, "
                    f"got {tooltip_text!r}"
                )

            with allure.step(f"Step 17 — Enter '{TOOLKIT_NAME}' into the Toolkit Name field"):
                toolkit_creation.fill_name(TOOLKIT_NAME)
                expect(toolkit_creation.name_input).to_have_value(
                    TOOLKIT_NAME, timeout=UI_ELEMENT_TIMEOUT,
                )

            with allure.step(f"Step 18 — Enter '{BUCKET_NAME}' into the Bucket field"):
                toolkit_creation.fill_field("bucket", BUCKET_NAME)
                expect(bucket_field).to_have_value(BUCKET_NAME, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 19 — Leave all other fields at their defaults — "
                "verify the MCP checkbox is still unchecked (unchanged by "
                "filling Name/Bucket)"
            ):
                assert not toolkit_creation.is_checkbox_field_checked(
                    "available_by_mcp", timeout=UI_ELEMENT_TIMEOUT,
                ), "MCP-availability checkbox should remain unchecked"

            with allure.step(
                "Side-channel check — no console errors across the "
                "type-picker + config-form flow so far (steps 1-19)"
            ):
                assert not console_errors, (
                    "Unexpected console errors before Save: "
                    f"{[m.text for m in console_errors]}"
                )

            # Capture mutating requests BEFORE clicking Save — the window
            # must cover the entire create-then-navigate flow (AFS §
            # Network Behavior / Axis 2: proves the toolkit-create POST is
            # the ONLY mutating call, no separate bucket-create POST).
            toolkit_create_requests = toolkits_list.capture_requests_matching(
                "elitea_core/tools", method="POST",
            )
            bucket_create_requests = toolkits_list.capture_requests_matching(
                "artifacts/buckets", method="POST",
            )

            with allure.step(
                "Steps 20-21 — Click Save; verify navigation to the "
                "toolkit-detail view and capture the new toolkit's "
                "numeric ID (needed for teardown)"
            ):
                toolkit_id = toolkit_creation.save_creation(timeout=NAVIGATION_TIMEOUT)
                assert re.search(rf"/toolkits/all/{toolkit_id}(\?|$)", page.url), (
                    f"Expected the URL to reflect the new toolkit's "
                    f"detail view, got: {page.url}"
                )

            with allure.step(
                "Step 22 — Verify the detail page header shows the "
                "toolkit name"
            ):
                # Auto-retrying assertion, not a bare visibility wait +
                # single text read: the header briefly shows a generic
                # "Edit Toolkit" placeholder before the toolkit's own data
                # finishes loading (confirmed live, implementer Phase 4
                # execution) — `expect(...).to_have_text()` polls until
                # the real name lands instead of racing that load.
                expect(toolkit_detail.toolkit_title).to_have_text(
                    TOOLKIT_NAME, timeout=NAVIGATION_TIMEOUT,
                )

            with allure.step(
                "Step 23 — Verify the URL updates to reflect the new "
                "toolkit (numeric ID + '?name=' query param)"
            ):
                page.wait_for_url(
                    re.compile(rf".*/toolkits/all/{toolkit_id}\?name={TOOLKIT_NAME}"),
                    timeout=NAVIGATION_TIMEOUT,
                )

            with allure.step(
                "Axis 2 — Verify the create call's network shape: exactly "
                "ONE POST to the toolkit-create endpoint (201), and NO "
                "separate POST to any bucket-create endpoint — proves the "
                "bucket is a server-side side effect of the SAME create "
                "call, per the case's own objective text"
            ):
                assert len(toolkit_create_requests) == 1, (
                    "Expected exactly one POST to the toolkit-create "
                    f"endpoint, captured: {toolkit_create_requests}"
                )
                assert toolkit_create_requests[0]["status"] == 201, (
                    "Toolkit-create POST should return 201, captured: "
                    f"{toolkit_create_requests[0]}"
                )
                assert not bucket_create_requests, (
                    "No separate POST should fire to a bucket-create "
                    f"endpoint, captured: {bucket_create_requests}"
                )

            with allure.step(
                "Step 24 — Verify the Configuration tab and the Indexes "
                "section are shown on the detail view"
            ):
                # EXPECTED-RESULT CHANGE (EliteaUI EL-5947): the case text says
                # "Configuration and Indexes TABS". Indexes is no longer a tab —
                # the redesign moved it INSIDE the Configuration tab as an
                # accordion, and the tab array's only other entry ('Test') ships
                # `display: 'none'` with empty content, so exactly one tab
                # renders. The observable the case cares about (both surfaces are
                # reachable on the detail view) is unchanged and asserted below;
                # only their shape moved. The TMS case text needs the same update.
                toolkit_detail.wait_for_config_surface(timeout=UI_ELEMENT_TIMEOUT)
                # The Configuration tab is ATTACHED and selected, but the strip
                # is not displayed (one real tab), so `to_be_visible()` would
                # never pass — assert attachment + selection instead.
                expect(toolkit_detail.configuration_tab).to_be_attached(
                    timeout=UI_ELEMENT_TIMEOUT,
                )
                expect(toolkit_detail.configuration_tab).to_have_attribute(
                    "aria-selected", "true", timeout=UI_ELEMENT_TIMEOUT,
                )
                # Indexes — now an accordion inside Configuration — IS visible.
                expect(toolkit_detail.indexes_accordion).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT,
                )

            with allure.step(
                "Step 25 — Verify the TEST SETTINGS panel is visible with "
                "model selector, Tool dropdown, and the welcome message"
            ):
                expect(test_settings.model_selector_button).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT,
                )
                model_name = test_settings.model_selector_name.text_content() or ""
                assert model_name.strip(), (
                    "Model selector should show a non-empty model name "
                    "(model-specific — not asserted on the exact value)"
                )
                expect(test_settings.tool_select).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT,
                )
                welcome_text = test_settings.get_welcome_message_text(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert EXPECTED_WELCOME_MESSAGE in welcome_text, (
                    f"Expected the welcome message {EXPECTED_WELCOME_MESSAGE!r} "
                    f"in the center panel, got: {welcome_text!r}"
                )

            with allure.step("Step 26 — Click the Tool dropdown"):
                test_settings.tool_select.click()

            with allure.step(
                f"Step 27 — Verify the tool list shows all "
                f"{EXPECTED_TOOL_COUNT} tools including 'List files'"
            ):
                options = test_settings.get_tool_options()
                expect(options).to_have_count(
                    EXPECTED_TOOL_COUNT, timeout=UI_ELEMENT_TIMEOUT,
                )
                expect(
                    test_settings.get_tool_option(TOOL_KEY)
                ).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 28 — Select 'List files' from the Tool dropdown"):
                test_settings.get_tool_option(TOOL_KEY).click()
                expect(test_settings.tool_select).to_contain_text(
                    "List files", timeout=UI_ELEMENT_TIMEOUT,
                )

            with allure.step(
                "Step 29 — Verify the 'List files' parameter panel shows "
                "Bucket Name, Folder, Recursive, Include, Skip, and RUN "
                "TOOL"
            ):
                for field_key in ("bucket_name", "folder", "recursive", "include", "skip"):
                    assert test_settings.is_param_field_visible(
                        field_key, timeout=UI_ELEMENT_TIMEOUT,
                    ), f"Expected the '{field_key}' parameter field to be visible"
                expect(test_settings.run_tool_button).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT,
                )

            with allure.step(
                "Step 30 — Click RUN TOOL, leaving all parameter fields "
                "at their default (empty) values, per the case's own "
                "literal step sequence"
            ):
                test_settings.run_tool(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 31 — Verify the tool runs and returns a result in "
                "the center panel — an empty result is the CORRECT "
                "outcome for a just-created, never-uploaded-to bucket"
            ):
                result_text = test_settings.wait_for_tool_result(timeout=TOOL_RUN_TIMEOUT)
                assert "list_files" in result_text, (
                    f"Expected the result to reference 'list_files', "
                    f"got: {result_text!r}"
                )
                assert "{'total': 0, 'rows': []}" in result_text, (
                    f"Expected an empty result for the just-created "
                    f"bucket, got: {result_text!r}"
                )

            with allure.step(
                "Side-channel check — no NEW console errors across the "
                "Save + TEST SETTINGS/RUN TOOL flow (steps 20-31)"
            ):
                assert not console_errors, (
                    "Unexpected console errors during Save/RUN TOOL: "
                    f"{[m.text for m in console_errors]}"
                )

            with allure.step("Step 32 — Navigate to the Artifacts section"):
                artifacts_page.navigate_to_artifacts()

            with allure.step("Step 33 — Click the search icon in the BUCKETS header"):
                artifacts_page.open_bucket_search(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 34 — Type 'new' into the bucket search field"):
                artifacts_page.search_buckets("new")
                expect(artifacts_page.bucket_search_input).to_have_value(
                    "new", timeout=UI_ELEMENT_TIMEOUT,
                )

            with allure.step(
                "Step 35 — Verify the bucket list filters and displays "
                "buckets containing 'new' — assert PRESENCE, never an "
                "exact row count (shared-env caveat: other suites' "
                "'new-bucket*'/'autotest-*' data accumulates over time)"
            ):
                assert artifacts_page.get_visible_bucket_count() >= 1, (
                    "Expected at least one bucket row after filtering to 'new'"
                )

            with allure.step("Step 36 — Verify 'new-bucket' is listed in the filtered results"):
                assert artifacts_page.count_bucket_rows(BUCKET_NAME) >= 1, (
                    f"Expected '{BUCKET_NAME}' to be present in the "
                    "filtered bucket list"
                )

            with allure.step("Step 37 — Click on 'new-bucket' to select it"):
                artifacts_page.click_bucket_row(BUCKET_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert f"bucket={BUCKET_NAME}" in page.url, (
                    f"Expected the URL to reflect the selected bucket, "
                    f"got: {page.url}"
                )

            with allure.step("Step 38 — Verify the main panel header displays 'new-bucket'"):
                expect(artifacts_page.breadcrumb_bucket_label).to_have_text(
                    BUCKET_NAME, timeout=UI_ELEMENT_TIMEOUT,
                )

            with allure.step(
                "Step 39 — Verify the main panel shows the empty-bucket "
                "state ('No files in this bucket' + 'Upload files' button)"
            ):
                expect(artifacts_page.empty_state_label).to_have_text(
                    "No files in this bucket", timeout=UI_ELEMENT_TIMEOUT,
                )
                expect(artifacts_page.upload_files_empty_state_button).to_have_text(
                    "Upload files", timeout=UI_ELEMENT_TIMEOUT,
                )

            with allure.step(
                "Side-channel check — no NEW console errors across the "
                "whole 39-step flow, idle"
            ):
                assert not console_errors, (
                    "Unexpected console errors across the full flow: "
                    f"{[m.text for m in console_errors]}"
                )
        finally:
            # Mandatory teardown (not a fail-safe): this case's core
            # subject is the CREATE path, so on a clean pass the toolkit
            # and bucket both still exist and MUST be deleted here —
            # unlike ELITEA-1817, where deletion IS the case's own subject
            # and teardown is a defensive fail-safe only.
            if toolkit_id is not None:
                try:
                    toolkit_api.delete_toolkit(toolkit_id)
                    logger.info("Teardown: deleted toolkit id=%s", toolkit_id)
                except Exception as exc:
                    logger.warning(
                        "Teardown: failed to delete toolkit id=%s: %s",
                        toolkit_id, exc,
                    )
            _cleanup_stale_bucket(artifacts_page)
