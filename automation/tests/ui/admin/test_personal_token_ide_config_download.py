"""UI test — the two per-row IDE download icons generate a valid config file.

One parameterized test covering two TMS cases that run the identical four
steps against the identical row and differ only in data (which icon is
clicked, the resulting filename, and the content grammar):

Test cases: ELITEA-2289 (VSCode) · ELITEA-2290 (JetBrains)
AFS: test-specs/settings-personal-tokens/l3_ide-config-download-icons-vscode-jetbrains_ELITEA-2289-2290.md

Both icons call the same ``onIdeSettingsDownload(token, ide)`` handler
(``PersonalTokens.jsx:192-241``), which builds the file content as a string,
wraps it in a ``Blob`` and clicks a synthesized ``<a download>``. It is a
**pure client-side download — no request fires**, so ``expect_download()``
IS the wait; there is nothing to await on the network and no reason to sleep.

The test creates its own token via the real UI create flow and captures the
full token value from the generation dialog, because that dialog is the
ONLY place the product ever reveals it (``GET /api/v2/auth/token/`` returns
the token already masked). That captured value is ELITEA-2289's oracle for
"referencing the correct token" — a pre-existing row's real token is
unknowable, so no substitution could stand in for it here.

⚠️ SANCTIONED-RED, ELITEA-2289 param only — Known defect #1884: the generated
``settings.json`` embeds the MASKED token in ``eliteacode.authToken`` /
``eliteacode.LLMAuthToken``, so it cannot authenticate. The assertion states
the CORRECT expected behaviour (the full token) and is recorded as a soft
failure, per `.agents/testing.md` § Merge gate → sanctioned-RED. It flips
green when the product fix ships. The JetBrains param is unaffected — that
format carries no token field at all — and asserts hard throughout.

No substitution anywhere: every asserted value is produced by the product
from real session state, and the token oracle comes from the product's own
generation dialog.
"""

import json
import logging
import uuid
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

import allure
import pytest
from config import settings
from pages.create_personal_token_page import CreatePersonalTokenPage
from pages.personal_tokens_page import PersonalTokensPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

ROW_WAIT_TIMEOUT = 15_000
DOWNLOAD_TIMEOUT = 30_000

# The real JWT the generation dialog shows is ~226 characters; a mask is ~10.
# The guard only has to separate the two, not pin the exact length.
MIN_REAL_TOKEN_LENGTH = 100

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

EXPECTED_JETBRAINS_OPTIONS = [
    "displayType",
    "integrationName",
    "integrationUid",
    "llmCustomModelEnabled",
    "llmCustomModelName",
    "llmServerUrl",
    "projectId",
    "provider",
]


def expected_server_origin() -> str:
    """Return the configured backend origin (``scheme://netloc``).

    An INDEPENDENT oracle: derived from ``.env.test`` config, never from a
    second read of the page the download came from.
    """
    parsed = urlparse(settings.elitea_api_base)
    return f"{parsed.scheme}://{parsed.netloc}"


def assert_vscode_settings(parsed: dict, token_value: str, soft_failures: list[str]) -> None:
    """Assert the ELITEA-2289 (VSCode ``settings.json``) content contract."""
    assert sorted(parsed.keys()) == sorted(EXPECTED_VSCODE_KEYS), (
        f"Expected exactly the 12 eliteacode.* keys {sorted(EXPECTED_VSCODE_KEYS)}, "
        f"got {sorted(parsed.keys())}"
    )

    origin = expected_server_origin()
    assert parsed["eliteacode.providerServerURL"] == origin, (
        f"Expected eliteacode.providerServerURL to be the configured backend "
        f"origin {origin!r}, got {parsed['eliteacode.providerServerURL']!r}"
    )
    assert parsed["eliteacode.LLMServerUrl"] == parsed["eliteacode.providerServerURL"], (
        "Expected the legacy and current server-URL keys to carry the same value; "
        f"got providerServerURL={parsed['eliteacode.providerServerURL']!r} vs "
        f"LLMServerUrl={parsed['eliteacode.LLMServerUrl']!r}"
    )

    assert parsed["eliteacode.projectId"] == settings.elitea_project_id, (
        f"Expected eliteacode.projectId to be the configured project "
        f"{settings.elitea_project_id}, got {parsed['eliteacode.projectId']!r}"
    )

    assert parsed["eliteacode.modelName"], "Expected a non-empty eliteacode.modelName"
    assert parsed["eliteacode.LLMModelName"] == parsed["eliteacode.modelName"], (
        "Expected the legacy and current model-name keys to carry the same value; "
        f"got modelName={parsed['eliteacode.modelName']!r} vs "
        f"LLMModelName={parsed['eliteacode.LLMModelName']!r}"
    )
    assert parsed["eliteacode.integrationUid"], (
        "Expected a non-empty eliteacode.integrationUid in the row-level download "
        "(the eye-preview panel's empty value is defect #1885, a different surface)"
    )

    assert parsed["eliteacode.defaultViewMode"] == "split", (
        f"Expected eliteacode.defaultViewMode 'split', "
        f"got {parsed['eliteacode.defaultViewMode']!r}"
    )
    assert parsed["eliteacode.displayType"] == "split", (
        f"Expected eliteacode.displayType 'split', got {parsed['eliteacode.displayType']!r}"
    )
    assert parsed["eliteacode.verifySsl"] is False, (
        f"Expected eliteacode.verifySsl False, got {parsed['eliteacode.verifySsl']!r}"
    )
    assert parsed["eliteacode.debug"] is False, (
        f"Expected eliteacode.debug False, got {parsed['eliteacode.debug']!r}"
    )

    # Known defect: #1884 — the downloaded settings.json embeds the MASKED
    # token, so it cannot authenticate. The case's own expected result is
    # "referencing the correct token", so the CORRECT value is asserted here
    # (never the masked one, which would encode the bug as the contract) and
    # recorded as a soft failure per the project's soft_failures pattern.
    if parsed["eliteacode.authToken"] != token_value:
        soft_failures.append(
            "eliteacode.authToken does not carry the token the generation dialog "
            f"showed (expected the full {len(token_value)}-char value, got "
            f"{parsed['eliteacode.authToken']!r}) — Known defect: #1884"
        )
    if parsed["eliteacode.LLMAuthToken"] != token_value:
        soft_failures.append(
            "eliteacode.LLMAuthToken does not carry the token the generation dialog "
            f"showed (expected the full {len(token_value)}-char value, got "
            f"{parsed['eliteacode.LLMAuthToken']!r}) — Known defect: #1884"
        )


def assert_jetbrains_settings(root: ET.Element, token_value: str, soft_failures: list[str]) -> None:
    """Assert the ELITEA-2290 (JetBrains ``elitea.xml``) content contract."""
    assert root.tag == "project", f"Expected root element <project>, got <{root.tag}>"
    assert root.get("version") == "4", (
        f"Expected <project version=\"4\">, got version={root.get('version')!r}"
    )

    components = root.findall("component")
    assert len(components) == 1, f"Expected exactly one <component>, got {len(components)}"
    component = components[0]
    assert component.get("name") == "EliteASettings", (
        f"Expected <component name=\"EliteASettings\">, got name={component.get('name')!r}"
    )

    options = {opt.get("name"): opt.get("value") for opt in component.findall("option")}
    assert sorted(options.keys()) == sorted(EXPECTED_JETBRAINS_OPTIONS), (
        f"Expected exactly the 8 options {sorted(EXPECTED_JETBRAINS_OPTIONS)}, "
        f"got {sorted(options.keys())}"
    )

    origin = expected_server_origin()
    assert options["llmServerUrl"] == origin, (
        f"Expected llmServerUrl to be the configured backend origin {origin!r}, "
        f"got {options['llmServerUrl']!r}"
    )
    assert options["projectId"] == str(settings.elitea_project_id), (
        f"Expected projectId {str(settings.elitea_project_id)!r} (XML attribute "
        f"values are strings), got {options['projectId']!r}"
    )
    assert options["llmCustomModelName"], "Expected a non-empty llmCustomModelName"
    assert options["integrationUid"], "Expected a non-empty integrationUid"

    assert options["displayType"] == "SPLIT", (
        f"Expected displayType 'SPLIT', got {options['displayType']!r}"
    )
    assert options["llmCustomModelEnabled"] == "true", (
        f"Expected llmCustomModelEnabled 'true', got {options['llmCustomModelEnabled']!r}"
    )
    assert options["provider"] == "ELITEA_EYE", (
        f"Expected provider 'ELITEA_EYE', got {options['provider']!r}"
    )

    # `soft_failures` is unused on this param by design — the JetBrains format
    # carries no token field at all, so #1884 cannot reach it. The signature is
    # kept uniform so the parameterized caller stays branch-free.
    assert soft_failures is not None


class TestPersonalTokenIdeConfigDownload:
    """ELITEA-2289 / ELITEA-2290 — the per-row VSCode and JetBrains download
    icons generate a valid, non-empty IDE configuration file."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-personal-tokens/ELITEA-2289_vscode-download-icon-generates-a-downloadable-configuration.md",
        "onetest-ai Test Case link (ELITEA-2289 / ELITEA-2290)",
    )
    @pytest.mark.parametrize(
        "icon_testid,expected_filename,grammar",
        [
            pytest.param(
                "token-action-vscode-button",
                "settings.json",
                "json",
                id="ELITEA-2289-vscode",
            ),
            pytest.param(
                "token-action-jetbrains-button",
                "elitea.xml",
                "xml",
                id="ELITEA-2290-jetbrains",
            ),
        ],
    )
    def test_ide_download_icon_generates_config_file(
        self, page, tmp_path, icon_testid, expected_filename, grammar
    ):
        """Click a token row's IDE download icon and verify the downloaded
        file is non-empty and parses into valid configuration content
        referencing this session's server URL, project and model."""
        tokens_page = PersonalTokensPage(page)
        create_page = CreatePersonalTokenPage(page)
        console_errors = collect_console_errors(page)
        soft_failures: list[str] = []
        # Duplicate token names ARE legal on this surface (ELITEA-2288), so a
        # literal name could resolve more than one row and a leftover from a
        # failed run would inflate every count — always uuid-suffix it.
        token_name = f"autotest-token-{uuid.uuid4().hex[:8]}"

        try:
            with allure.step(
                "Setup — Create one token via the real UI create flow and capture "
                "the full token value from the generation dialog (the only place "
                "the product ever reveals it)"
            ):
                tokens_page.navigate()
                rows_before = tokens_page.token_row.count()
                tokens_page.click_add_button()
                create_page.wait_for_loaded()
                create_page.fill_name(token_name)
                create_response = create_page.click_generate()
                assert create_response.status == 200, (
                    f"Expected 200 from the token-create POST, got {create_response.status}"
                )
                token_value = create_page.get_dialog_token_value_text()
                # Guard: without it, a product change that masked the generation
                # dialog too would make ELITEA-2289's whole token assertion
                # vacuous while still passing.
                assert len(token_value) > MIN_REAL_TOKEN_LENGTH, (
                    f"Expected the generation dialog to show the REAL token "
                    f"(>{MIN_REAL_TOKEN_LENGTH} chars), got a {len(token_value)}-char "
                    f"value — a mask, not the token this case needs as its oracle"
                )
                create_page.close_dialog()
                # Assert the TOTAL row count first: the whole table unmounts
                # while the post-create refetch is in flight, so a bare
                # named-row read can pass vacuously during that window.
                expect(tokens_page.token_row).to_have_count(
                    rows_before + 1, timeout=ROW_WAIT_TIMEOUT
                )
                row = tokens_page.get_row_by_name(token_name)
                expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)

            with allure.step(
                "Step 1 — Verify Settings -> Personal Tokens shows the populated "
                "table with the created token row and the IDE download icon"
            ):
                assert tokens_page.page_title.text_content() == "Personal Tokens", (
                    f"Expected page title 'Personal Tokens', "
                    f"got {tokens_page.page_title.text_content()!r}"
                )
                assert tokens_page.token_row.count() >= 1, (
                    "Expected at least one token row (the populated branch)"
                )
                icon = tokens_page.get_row_action_icon(row, icon_testid)
                assert icon.count() == 1, (
                    f"The row's {icon_testid} is absent — the page is in the "
                    "showDownload == false branch (no model configuration_uid, or "
                    "the Public project), so this case cannot be exercised here"
                )

            with allure.step(
                f"Step 2 — Click the {icon_testid} icon in the Actions column of "
                "the token row"
            ):
                download = tokens_page.download_ide_settings(
                    row, icon_testid, timeout=DOWNLOAD_TIMEOUT
                )

            with allure.step("Step 3 — Verify a non-empty file is downloaded"):
                assert download.suggested_filename == expected_filename, (
                    f"Expected the downloaded file to be named {expected_filename!r}, "
                    f"got {download.suggested_filename!r}"
                )
                saved_path = tmp_path / expected_filename
                download.save_as(saved_path)
                assert saved_path.exists(), (
                    f"Expected the downloaded file to be saved at {saved_path}"
                )
                file_bytes = saved_path.stat().st_size
                assert file_bytes > 0, (
                    f"Expected a non-empty downloaded file, got {file_bytes} bytes"
                )

            with allure.step(
                "Step 4 — Verify the file parses and contains valid configuration "
                "content referencing the correct token, server URL, project and model"
            ):
                content = saved_path.read_text(encoding="utf-8")
                if grammar == "json":
                    # Parsing (not a substring check) is what "valid" means — a
                    # substring check passes on truncated or malformed output.
                    parsed = json.loads(content)
                    assert_vscode_settings(parsed, token_value, soft_failures)
                else:
                    root = ET.fromstring(content)
                    assert_jetbrains_settings(root, token_value, soft_failures)
                    # The JetBrains format carries no credential by design;
                    # pinning the absence turns that from "we happened not to
                    # include it" into an enforced invariant.
                    assert token_value not in content, (
                        "The full token value leaked into elitea.xml — the JetBrains "
                        "configuration format carries no credential by design"
                    )

            with allure.step("Step 5 — Verify no console errors across the flow"):
                assert not console_errors, f"Unexpected console errors: {console_errors}"
        finally:
            # Cleanup (not an AFS case step — mandatory, unwrapped, runs
            # regardless of outcome: this case creates a real, persistent token
            # in shared live project data).
            cleanup_row = tokens_page.get_row_by_name(token_name)
            if cleanup_row.count() > 0:
                tokens_page.get_row_action_icon(
                    cleanup_row.first, "token-action-delete-button"
                ).click()
                tokens_page.delete_confirm_dialog.wait_for(state="visible", timeout=10_000)
                tokens_page.fill_delete_confirm_name(token_name)
                tokens_page.confirm_delete()
                expect(tokens_page.get_row_by_name(token_name)).to_have_count(
                    0, timeout=ROW_WAIT_TIMEOUT
                )

        if soft_failures:
            # Sanctioned-RED (ELITEA-2289 param only) — every other assertion in
            # this case passed. See the module docstring and #1884.
            pytest.fail(
                "Known-defect soft failures were recorded (everything else in this "
                "case passed cleanly):\n" + "\n".join(soft_failures)
            )
