"""Export Agent with no nested dependencies — exported .md has correct
frontmatter and no leaked credentials (ELITEA-1894).

Creates a GitHub credential + toolkit (via the existing ``github_credential``
/ ``github_toolkit`` API fixtures) and an Agent with no attached Skills and
no nested sub-Agent, attaches the toolkit to the Agent, triggers "Export"
from the agent-actions overflow menu (VERSION group), downloads the
resulting ``.agent.md`` file, and asserts its raw content directly:

1. The YAML frontmatter contains the required fields (name, description,
   model settings) with NO ``skills:`` key present at all (since none are
   attached) — the structural inverse of ELITEA-1794's export shape.
2. The markdown body below the frontmatter contains the Agent's own
   instructions verbatim (via a planted unique marker string).
3. The toolkit's ``github_configuration`` block contains only a credential
   *reference* (``elitea_title``) — the raw GitHub access token value is
   never present anywhere in the file (byte-level grep against the actual
   live secret value, not a heuristic).

No product defect found.

Spec: test-specs/skills/l3_export-agent-no-nested-dependencies_ELITEA-1894.md
"""

import logging
import tempfile
import uuid
from pathlib import Path

import allure
import pytest
import yaml

from config import settings
from pages.agent_detail_page import AgentDetailPage
from pages.agent_form_page import AgentFormPage
from pages.agents_list_page import AgentsListPage

pytestmark = [pytest.mark.ui, pytest.mark.skills]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000

logger = logging.getLogger("elitea.tests.skills")

MARKER = "ELITEA_1894_INSTR_MARKER"

# Credential-shaped substrings that must never appear in the exported file,
# regardless of key name — the case's core security claim is that the
# export mechanism dereferences-by-name rather than embedding the secret.
_CREDENTIAL_SHAPED_SUBSTRINGS = (
    "access_token",
    "api_key",
    "secret",
    "password",
    "ghp_",
    "github_pat_",
)


class TestExportAgentNoNestedDependencies:
    """Export Agent with no nested dependencies (ELITEA-1894, l3)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1894_export-agent-no-nested-dependencies-produces-md-file.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_export_agent_no_nested_dependencies(
        self, page, agent_api, github_credential, github_toolkit,
    ):
        """Create an Agent with no attached Skills/sub-Agents but with an
        external GitHub toolkit attached, export it via the actions overflow
        menu, and verify the downloaded file's raw content: correct
        frontmatter, no ``skills:`` key, instructions embedded verbatim, and
        no leaked credential value anywhere in the file.

        Steps (AFS
        test-specs/skills/l3_export-agent-no-nested-dependencies_ELITEA-1894.md):
        1. Create an Agent via UI (no Skills/sub-Agents attached).
        2. Attach the pre-created GitHub toolkit to the Agent (case
           precondition — "no nested dependencies" + a real credential to
           prove non-leakage against).
        3. Confirm the Agent detail view shows the toolkit attached and no
           Skills (already satisfied by step 2).
        4. Confirm the version dropdown shows the default `base` version
           selected (single-version agent — see AFS § Blocked Steps).
        5. Open the agent-actions overflow menu; click "Export" (VERSION
           group); verify a file download is initiated.
        6. Verify the downloaded file has a `.md`-suffixed name.
        7. Read the downloaded file's raw content; verify the YAML
           frontmatter (name, description, model settings) has NO
           `skills:` key, and the instructions body is embedded verbatim.
        8. Verify the file does NOT contain the raw GitHub token value nor
           any credential-shaped substring — only the toolkit's non-secret
           `elitea_title` reference.
        """
        unique_suffix = uuid.uuid4().hex[:8]
        # Agent name field enforces MAX_NAME_LENGTH=32 chars (silently
        # truncates via input maxLength) — same cap documented in
        # ELITEA-1794/1789/1792.
        agent_name = f"el-1894-agent-{unique_suffix}"
        agent_description = "Agent for ELITEA-1894 export no-nested-dependency check."
        # Shorter than the AFS's "used in this run" wording (implementer
        # Phase 2 technique adjustment, not a scope change): the shared
        # AgentFormPage.fill_form() types the instructions field via
        # press_sequentially(delay=80ms/char) against a 10s default action
        # timeout, so a ~180-char string times out. The marker-verbatim
        # requirement is unaffected — only the surrounding prose is shorter.
        agent_instructions = (
            f"Test agent for export verification, no nested deps. {MARKER} "
            "must appear verbatim."
        )

        agent_id = None
        download_path = None

        try:
            with allure.step("Step 1 — Create an Agent via UI"):
                list_page = AgentsListPage(page)
                list_page.navigate_to_create()

                form_page = AgentFormPage(page)
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=agent_name,
                    description=agent_description,
                    instructions=agent_instructions,
                )
                form_page.wait_for_form_validation()
                assert form_page.is_save_enabled(), (
                    "Save should be enabled after filling all required agent fields"
                )
                form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

                detail_page = AgentDetailPage(page)
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                detail_page.verify_on_detail_page()
                agent_id = int(detail_page.get_agent_id())
                logger.info("Created agent %r with id=%d", agent_name, agent_id)

            with allure.step(
                "Step 2 — Attach the pre-created GitHub toolkit to the "
                "Agent (case precondition: agent with no nested Skill/"
                "Agent dependencies but with an external toolkit attached)"
            ):
                console_messages = []
                page.on(
                    "console",
                    lambda msg: console_messages.append(msg) if msg.type == "error" else None,
                )

                detail_page.add_toolkit(github_toolkit["name"], timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.is_toolkit_attached(
                    github_toolkit["name"], timeout=UI_ELEMENT_TIMEOUT
                ), (
                    f"Toolkit card for '{github_toolkit['name']}' should render "
                    "after attaching"
                )

            with allure.step(
                "Step 3 — Confirm the Agent detail view shows the toolkit "
                "attached and no Skills (already satisfied by Step 2)"
            ):
                detail_page.verify_on_detail_page(expected_agent_id=agent_id)
                assert "0/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should show 0 skills attached — no nested "
                    "Skill dependency for this case"
                )

            # Step 4 (case step 2, "select the version to export from the
            # version dropdown"): per AFS Blocked Steps, the dropdown has no
            # dedicated testid yet (out of this case's scope to add — the
            # testid-only locator policy forbids a raw role/CSS locator in
            # the spec). A freshly created agent has exactly one ("base")
            # version selected by default, so the export in Step 5 below
            # necessarily exercises that default selection; the exported
            # frontmatter's content (asserted in Step 7) is the durable
            # proof that the correct (only) version was exported. Accepted
            # per the AFS's judgment call (a) — single-version
            # default-selection proof satisfies case step 2.

            with allure.step(
                "Step 5 — Open the agent-actions overflow menu; click "
                "'Export' (VERSION group); verify a file download is "
                "initiated"
            ):
                download = detail_page.export_agent_via_menu(timeout=UI_ELEMENT_TIMEOUT)
                assert download.suggested_filename, (
                    "Export should trigger a file download with a suggested filename"
                )
                assert not console_messages, (
                    "Expected no console errors during the toolkit-attach/export/"
                    f"download flow, got: {[m.text for m in console_messages]}"
                )

            with allure.step(
                "Step 6 — Verify the downloaded file has a .md-suffixed name"
            ):
                assert download.suggested_filename.endswith(".md"), (
                    f"Expected a .md download, got: {download.suggested_filename!r}"
                )
                # Playwright's internal download path doesn't preserve the
                # suggested filename/extension — save_as() to a path that
                # keeps the real ".md" extension (mirrors ELITEA-1794).
                download_path = Path(tempfile.gettempdir()) / download.suggested_filename
                download.save_as(download_path)
                assert download_path.exists() and download_path.stat().st_size > 0, (
                    "Downloaded export file should exist and be non-empty"
                )

            with allure.step(
                "Step 7 — Read the downloaded file's raw content; verify "
                "YAML frontmatter (name, description, model settings) has "
                "NO 'skills:' key, and the instructions body is embedded "
                "verbatim"
            ):
                raw_content = download_path.read_text(encoding="utf-8")
                parts = raw_content.split("---", 2)
                assert len(parts) == 3, (
                    "Expected YAML frontmatter delimited by '---', got "
                    f"structure: {raw_content[:200]!r}"
                )
                frontmatter = yaml.safe_load(parts[1])
                agent_body = parts[2].strip()

                assert frontmatter.get("name") == agent_name, (
                    f"Exported frontmatter name mismatch: {frontmatter.get('name')!r} "
                    f"!= {agent_name!r}"
                )
                assert frontmatter.get("description") == agent_description, (
                    "Exported frontmatter description should match the Agent"
                )
                for required_key in (
                    "model", "temperature", "max_tokens", "agent_type", "step_limit",
                ):
                    assert required_key in frontmatter, (
                        f"Exported frontmatter should contain '{required_key}', "
                        f"got keys: {sorted(frontmatter.keys())}"
                    )

                assert "skills" not in frontmatter, (
                    "Exported frontmatter should have NO 'skills:' key — this "
                    "Agent has no attached Skills, distinguishing this export "
                    f"shape from ELITEA-1794's; got: {frontmatter.get('skills')!r}"
                )

                # This is the case's core claim and the strongest evidence:
                # the marker substring can only appear if the FULL
                # instructions text is embedded, not a bare reference.
                assert MARKER in agent_body, (
                    f"Exported markdown body should contain the planted marker "
                    f"{MARKER!r} verbatim, got: {agent_body!r}"
                )
                assert agent_body == agent_instructions, (
                    "Exported markdown body should match the Agent's own "
                    "instructions verbatim"
                )

                toolkits = frontmatter.get("toolkits")
                assert isinstance(toolkits, list) and len(toolkits) == 1, (
                    f"Expected exactly one attached toolkit in the exported "
                    f"'toolkits:' list, got: {toolkits!r}"
                )
                exported_toolkit = toolkits[0]
                github_config = exported_toolkit.get("settings", {}).get(
                    "github_configuration", {}
                )
                assert github_config.get("elitea_title") == github_credential[
                    "elitea_title"
                ], (
                    "Exported toolkit's github_configuration should reference "
                    "the credential by its elitea_title, got: "
                    f"{github_config.get('elitea_title')!r}"
                )

            with allure.step(
                "Step 8 — Verify the file does NOT contain the raw GitHub "
                "token value nor any credential-shaped substring (the "
                "case's core security assertion)"
            ):
                raw_bytes = download_path.read_bytes()
                token_value = settings.git_hub_token
                assert token_value, (
                    "GIT_HUB_TOKEN must be set for this assertion to be "
                    "meaningful (github_toolkit fixture should have already "
                    "skipped otherwise)"
                )
                assert token_value.encode("utf-8") not in raw_bytes, (
                    "Exported file must NOT contain the raw GitHub access "
                    "token value anywhere in its bytes"
                )
                for shaped_substring in _CREDENTIAL_SHAPED_SUBSTRINGS:
                    assert shaped_substring not in raw_content, (
                        f"Exported file must NOT contain the credential-shaped "
                        f"substring {shaped_substring!r} — got a match, "
                        "indicating a possible credential leak or leak-shaped "
                        "key name"
                    )

        finally:
            # Cleanup per AFS: delete the agent (has the attached-toolkit
            # dependency); the toolkit/credential are cleaned up by their
            # own fixtures' teardown (github_toolkit -> github_credential).
            if agent_id is not None:
                try:
                    agent_api.delete_agent(agent_id)
                    logger.info("Cleanup: deleted agent id=%d", agent_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete agent id=%s: %s", agent_id, exc
                    )
            if download_path is not None:
                try:
                    download_path.unlink(missing_ok=True)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to remove downloaded file %s: %s",
                        download_path, exc,
                    )
