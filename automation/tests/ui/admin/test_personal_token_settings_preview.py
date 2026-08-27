"""UI test — the eye icon opens the IDE configuration preview panel.

Test case: ELITEA-2291
AFS: test-specs/settings-personal-tokens/l3_eye-icon-ide-settings-preview-panel_ELITEA-2291.md

The eye icon (``token-action-preview-button``) opens an in-page ``react-split``
pane, NOT a route change and NOT a modal (``PersonalTokens.jsx:133-141``): the
URL stays ``/settings/tokens`` and the tokens table stays mounted beside it.
The pane's close is animated THEN unmounted — sizes go to ``[100, 0]``, then a
50 ms ``setTimeout`` removes it — so every disappearance assertion here uses an
auto-retrying expectation, never an immediate read and never a sleep.

Read-only: runs against an existing token row, creates nothing and needs no
cleanup.

⚠️ SANCTIONED-RED — Known defect #1885: the previewed VSCode config always
shows ``"eliteacode.integrationUid": ""`` because ``SettingsPreview.jsx``
dereferences ``modelData.integration_uid`` while the model object carries
``configuration_uid`` (``|| ''`` swallows the ``undefined``, so nothing reaches
the console). The row-level VSCode download writes the real value for the same
token/project/model. Step 7 asserts the CORRECT expected behaviour — a
non-empty ``integrationUid`` — recorded as a soft failure per the project's
``soft_failures`` + trailing ``pytest.fail()`` pattern and
`.agents/testing.md` § Merge gate → sanctioned-RED. It flips green when the
product fix ships. Every other assertion in this spec is hard.

#1884 (the panel's ``eliteacode.authToken`` is the masked token, not a usable
one) is deliberately NOT asserted here: this spec reads an arbitrary
pre-existing row whose real token is unknowable, so any assertion would be
vacuous. That defect is owned and soft-asserted by ELITEA-2289's spec, which
creates its own token and therefore has the real value in scope.

No substitution anywhere: every asserted value is rendered live by the app
from real session state.
"""

import json
import logging
from urllib.parse import urlparse

import allure
import pytest
from config import settings
from pages.personal_tokens_page import PersonalTokensPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

EXPECTED_VSCODE_KEYS = [
    "eliteacode.providerServerURL",
    "eliteacode.LLMServerUrl",
    "eliteacode.modelName",
    "eliteacode.LLMModelName",
    "eliteacode.authToken",
    "eliteacode.LLMAuthToken",
    "eliteacode.projectId",
    "eliteacode.integrationUid",
    "eliteacode.defaultViewMode",
    "eliteacode.verifySsl",
    "eliteacode.displayType",
    "eliteacode.debug",
]

# The panel title's separator is U+2022 BULLET with a single space either side
# (`canvasTitle`, SettingsPreview.jsx) — kept as a named constant so the exact
# character is stated once and cannot be mistaken for a hyphen or middle dot.
TITLE_SEPARATOR = " • "


class TestPersonalTokenSettingsPreview:
    """ELITEA-2291 — the eye icon opens the IDE configuration preview panel
    with correct content, and the panel closes cleanly."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-personal-tokens/ELITEA-2291_eye-icon-opens-ide-configuration-preview-panel-with-correct.md",
        "onetest-ai Test Case link",
    )
    def test_eye_icon_opens_ide_settings_preview_panel(self, page):
        """Open a token row's Settings Preview pane; verify its title, IDE
        dropdown, copy/download buttons and JSON body; then close it and
        verify it unmounts leaving the table intact."""
        tokens_page = PersonalTokensPage(page)
        console_errors = collect_console_errors(page)
        soft_failures: list[str] = []

        with allure.step(
            "Step 1 — Navigate to Settings -> Personal Tokens (with at least one token)"
        ):
            tokens_page.navigate()
            assert tokens_page.page_title.text_content() == "Personal Tokens", (
                f"Expected page title 'Personal Tokens', "
                f"got {tokens_page.page_title.text_content()!r}"
            )
            row_count_before = tokens_page.token_row.count()
            assert row_count_before >= 1, (
                "Expected at least one token row (the populated branch)"
            )
            row = tokens_page.token_row.first
            preview_icon = tokens_page.get_row_action_icon(
                row, "token-action-preview-button"
            )
            # Precondition guard, not a case step: showDownload is a PAGE-level
            # boolean (`!!model.configuration_uid && selectedProjectId !==
            # PUBLIC_PROJECT_ID`). When false the eye icon does not render at
            # all and the case would fail as an opaque locator timeout.
            assert preview_icon.count() == 1, (
                "The first row's eye (preview) icon is absent — the page is in the "
                "showDownload == false branch (no model configuration_uid, or the "
                "Public project), so this case cannot be exercised here"
            )
            row_name = (tokens_page.get_row_name_cell(row).text_content() or "").strip()
            assert row_name, "Expected the first row's name cell to be non-empty"

        with allure.step("Step 2 — Click the eye icon in the token row's Actions column"):
            tokens_page.open_settings_preview(row)
            expect(tokens_page.settings_preview_panel).to_be_visible()
            # It is a pane, not a route: without this the test would still pass
            # if the product regressed to navigating away.
            assert page.url.split("?")[0].rstrip("/").endswith("/settings/tokens"), (
                f"Expected to stay on /settings/tokens (the preview is an in-page "
                f"split pane, not a route change), got {page.url!r}"
            )

        with allure.step(
            'Step 3 — Verify the side panel title reads "[token name] • VSCode Settings"'
        ):
            expected_title = f"{row_name}{TITLE_SEPARATOR}VSCode Settings"
            expect(tokens_page.settings_preview_title).to_have_text(expected_title)

        with allure.step(
            "Step 4 — Verify the IDE type dropdown is shown in the panel header"
        ):
            expect(tokens_page.settings_preview_ide_select_combobox).to_be_visible()
            expect(tokens_page.settings_preview_ide_select_combobox).to_have_text("VSCode")

        with allure.step(
            "Step 5 — Verify a copy icon button and a download icon button are "
            "present in the panel header"
        ):
            expect(tokens_page.settings_preview_copy_button).to_be_visible()
            expect(tokens_page.settings_preview_copy_button).to_be_enabled()
            expect(tokens_page.settings_preview_download_button).to_be_visible()
            expect(tokens_page.settings_preview_download_button).to_be_enabled()

        with allure.step("Step 6 — Verify the panel shows a JSON configuration"):
            body = tokens_page.get_settings_preview_body()
            # Parsing IS the "shows a JSON configuration" assertion — a substring
            # check would pass on malformed JSON.
            parsed = json.loads(body)
            assert sorted(parsed.keys()) == sorted(EXPECTED_VSCODE_KEYS), (
                f"Expected exactly the 12 eliteacode.* keys "
                f"{sorted(EXPECTED_VSCODE_KEYS)}, got {sorted(parsed.keys())}"
            )
            assert parsed["eliteacode.projectId"] == settings.elitea_project_id, (
                f"Expected eliteacode.projectId to be the configured project "
                f"{settings.elitea_project_id}, got {parsed['eliteacode.projectId']!r}"
            )
            parsed_api_base = urlparse(settings.elitea_api_base)
            expected_origin = f"{parsed_api_base.scheme}://{parsed_api_base.netloc}"
            assert parsed["eliteacode.providerServerURL"] == expected_origin, (
                f"Expected eliteacode.providerServerURL to be the configured backend "
                f"origin {expected_origin!r}, got "
                f"{parsed['eliteacode.providerServerURL']!r}"
            )
            assert parsed["eliteacode.LLMServerUrl"] == parsed["eliteacode.providerServerURL"], (
                "Expected the legacy and current server-URL keys to carry the same "
                f"value; got providerServerURL="
                f"{parsed['eliteacode.providerServerURL']!r} vs LLMServerUrl="
                f"{parsed['eliteacode.LLMServerUrl']!r}"
            )

        with allure.step(
            "Step 7 — Verify no field shows 'undefined' or a null value unexpectedly"
        ):
            null_valued = [key for key, value in parsed.items() if value is None]
            assert not null_valued, (
                f"Expected no null values in the previewed configuration, got null "
                f"for {null_valued}"
            )
            assert "undefined" not in body, (
                "The literal token 'undefined' appears in the previewed configuration"
            )
            assert parsed["eliteacode.modelName"], (
                "Expected a non-empty eliteacode.modelName"
            )
            assert parsed["eliteacode.LLMModelName"] == parsed["eliteacode.modelName"], (
                "Expected the legacy and current model-name keys to carry the same "
                f"value; got modelName={parsed['eliteacode.modelName']!r} vs "
                f"LLMModelName={parsed['eliteacode.LLMModelName']!r}"
            )
            # Known defect: #1885 — SettingsPreview reads modelData.integration_uid
            # while the model object carries configuration_uid, so the preview
            # always shows "". The row-level VSCode download writes the real value
            # for the same token/project/model, which is why the CORRECT expected
            # behaviour is asserted here rather than the buggy "".
            if not parsed["eliteacode.integrationUid"]:
                soft_failures.append(
                    "eliteacode.integrationUid is empty in the Settings Preview "
                    "(the row-level VSCode download writes the real configuration_uid "
                    "for the same token) — Known defect: #1885"
                )

        with allure.step("Step 8 — Close the panel and verify it closes cleanly"):
            tokens_page.close_settings_preview()
            expect(tokens_page.settings_preview_panel).to_have_count(0)
            # "Closes cleanly" is satisfiable by a width-0 pane that never
            # unmounted; asserting the editor is gone is what makes it mean
            # something.
            expect(tokens_page.settings_preview_content).to_have_count(0)
            # The pane manipulates the table's own react-split container sizes,
            # so a bad close could leave the table collapsed.
            expect(tokens_page.token_row).to_have_count(row_count_before)
            expect(tokens_page.get_row_name_cell(tokens_page.token_row.first)).to_have_text(
                row_name
            )

        with allure.step("Step 9 — Verify no console errors across the flow"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"

        if soft_failures:
            # Sanctioned-RED — every other assertion in this case passed.
            # See the module docstring and #1885.
            pytest.fail(
                "Known-defect soft failures were recorded (everything else in this "
                "case passed cleanly):\n" + "\n".join(soft_failures)
            )
