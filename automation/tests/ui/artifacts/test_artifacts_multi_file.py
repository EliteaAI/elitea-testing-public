"""UI Test for ELITEA-1327 — Agent Multi-File Artifact Downloads.

Regression test: verifies that *all* files created by an agent in a single
run are visible in the artifact bucket and individually downloadable via the UI.
Covers both files written at the bucket root and files written under a
sub-path prefix in the same agent run.

Test flow:
1. Creates a fresh artifact bucket (via API).
2. Creates an artifact toolkit pointing to that bucket (via API).
3. Creates a fresh agent (via API).
4. Attaches the toolkit to the agent via UI and saves.
5. Sends a single prompt asking the agent to create files at the bucket root
   AND under an 'output/' sub-path.
6. Verifies all 6 file cards appear in the agent's chat response bubble.
7. Verifies all root-level files are visible in the bucket UI.
8. Navigates into the 'output/' sub-folder and verifies all sub-path files
   are visible in the UI.
9. Downloads one root-level file and one sub-path file via the UI and
   verifies non-empty content (spot-check of the download mechanism).
9. Cleans up: agent, toolkit, and bucket are deleted on teardown.

Markers:
    - ui: requires browser
    - regression: regression test
    - p0: critical priority (data-loss regression)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_multi_file.py -v
    pytest tests/ui/artifacts/ -v -m p0
"""

import logging

import allure
import pytest

from pages.agent_detail_page import AgentDetailPage
from pages.agent_page import AgentPage
from pages.artifacts_page import ArtifactsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000     # buttons, panels, form fields
NAVIGATION_TIMEOUT = 15_000     # SPA route transitions
FORM_SAVE_TIMEOUT = 15_000      # agent save + network settle
AGENT_RUN_TIMEOUT = 180_000     # agent may call multiple tools to create files
FILE_APPEAR_TIMEOUT = 30_000    # bucket re-load after agent run

# ---------------------------------------------------------------------------
# Test data — single combined prompt
# ---------------------------------------------------------------------------

# Ask the agent to create files in both the root AND a sub-path in one run.
_PROMPT = (
    "Create and save 6 files using the Artifact toolkit in a single action: "
    "report1.txt with content 'Report 1 content', "
    "report2.txt with content 'Report 2 content', "
    "report3.txt with content 'Report 3 content' at the root level, "
    "and output/a.txt with content 'Content A', "
    "output/b.txt with content 'Content B', "
    "output/c.txt with content 'Content C' under the 'output/' sub-path."
)

# Root-level files (checked at bucket root)
_ROOT_FILES = ["report1.txt", "report2.txt", "report3.txt"]

# Sub-path files — full keys for bucket navigation, base names for UI checks
_SUB_FOLDER = "output"
_SUB_PATH_FILES = ["output/a.txt", "output/b.txt", "output/c.txt"]

# All file names expected as artifact cards in the chat response (base names only)
_ALL_EXPECTED_CARD_NAMES = _ROOT_FILES + [f.split("/")[-1] for f in _SUB_PATH_FILES]


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


@allure.epic("Artifacts")
@allure.feature("Multi-file Download")
class TestArtifactMultiFileDownload:
    """ELITEA-1327 — All agent-created files are visible and accessible.

    A single agent run creates files at the bucket root AND under a sub-path.
    The test verifies that all files (root and sub-path) are visible in the
    UI and downloadable — covering the regression where only the last-written
    file survived when an agent called the toolkit multiple times in one turn.
    """

    @pytest.mark.p0
    @allure.title("Agent creates files at root and in subfolder — all visible and accessible")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/artifacts/artifacts-toolkit-multi-file/ELITEA-1327_verify-all-files-downloadable-when-agent-creates-multiple-files.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/elitea_issues/issues/5313", "Github issue link")
    def test_agent_creates_files_at_root_and_in_subfolder(
        self,
        page,
        agent_id: int,
        artifact_toolkit: dict,
    ):
        """Agent creates files at root and under a sub-path — all visible and accessible.

        ELITEA-1327 regression: when an agent creates N files in a single tool call,
        all N files must be downloadable via the UI.  Before the fix, only the last
        file written would be persisted; all earlier files were silently lost.
        """
        toolkit_name: str = artifact_toolkit["name"]
        bucket_name: str = artifact_toolkit["bucket_name"]

        # ------------------------------------------------------------------
        # Step 1 — Attach the artifact toolkit to the agent via UI and save
        # ------------------------------------------------------------------
        with allure.step("Step 1 — Attach the artifact toolkit to the agent via UI and save"):
            agent_page = AgentPage(page)
            agent_page.navigate_to_agent(agent_id)
            agent_page.wait_for_agent_detail()
            agent_page.add_toolkit(toolkit_name)
            assert agent_page.is_toolkit_attached(toolkit_name), (
                f"Toolkit '{toolkit_name}' should appear in the agent's Toolkits section"
            )
            agent_page.save_and_wait(timeout=FORM_SAVE_TIMEOUT)
            logger.info("Attached toolkit '%s' to agent %d and saved", toolkit_name, agent_id)

        # ------------------------------------------------------------------
        # Step 2 — Send the combined multi-file prompt via embedded chat
        # ------------------------------------------------------------------
        with allure.step("Step 2 — Send the combined multi-file prompt via embedded chat"):
            detail_page = AgentDetailPage(page)
            initial_msg_count = detail_page.get_chat_message_count()
            logger.info(
                "Sending multi-file prompt to agent %d (initial messages: %d)",
                agent_id, initial_msg_count,
            )
            detail_page.send_chat_message(_PROMPT)

        # ------------------------------------------------------------------
        # Step 3 — Wait for the agent to finish creating the files
        # ------------------------------------------------------------------
        with allure.step("Step 3 — Wait for the agent to finish creating the files"):
            detail_page.wait_for_chat_response(
                initial_count=initial_msg_count,
                stable_duration_ms=5000,
                timeout=AGENT_RUN_TIMEOUT,
            )
            last_response = detail_page.get_last_chat_message()
            logger.info("Agent response (truncated): %.200s", last_response)

            assert any(
                kw in last_response.lower()
                for kw in ("saved", "created", "written", "success", "file")
            ), (
                f"Agent response did not confirm file creation. "
                f"Response: {last_response!r}"
            )

        # ------------------------------------------------------------------
        # Step 3b — Verify all 6 file cards are visible in the chat response
        # The Artifact toolkit renders a card chip for every file it creates,
        # directly inside the agent's answer bubble.
        # ------------------------------------------------------------------
        with allure.step("Step 3b — Verify all 6 artifact file cards visible in chat response"):
            card_names = detail_page.get_chat_artifact_file_names(timeout=UI_ELEMENT_TIMEOUT)
            missing_cards = [f for f in _ALL_EXPECTED_CARD_NAMES if f not in card_names]
            assert not missing_cards, (
                f"Artifact file cards missing from chat response: {missing_cards}. "
                f"Cards found: {card_names}. "
                f"ELITEA-1327: all {len(_ALL_EXPECTED_CARD_NAMES)} files must appear as "
                f"cards in the agent response immediately after creation."
            )
            logger.info("All %d artifact file cards visible in chat response: %s",
                        len(card_names), card_names)

        # ------------------------------------------------------------------
        # Step 4 — Navigate to bucket root; verify root-level files
        # ------------------------------------------------------------------
        with allure.step("Step 4 — Navigate to bucket root; verify root-level files"):
            artifacts_page = ArtifactsPage(page)
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)

            missing_root = [
                f for f in _ROOT_FILES
                if not artifacts_page.file_exists(f, timeout=FILE_APPEAR_TIMEOUT)
            ]
            assert not missing_root, (
                f"Root-level files NOT visible in bucket '{bucket_name}': {missing_root}. "
                f"ELITEA-1327: files may be lost when an agent creates multiple files "
                f"in a single tool call."
            )
            logger.info("Root files visible in bucket UI: %s", _ROOT_FILES)

        # ------------------------------------------------------------------
        # Step 5 — Navigate into 'output/' sub-folder; verify all sub-path files
        # ------------------------------------------------------------------
        with allure.step("Step 5 — Navigate into 'output/' sub-folder; verify sub-path files"):
            artifacts_page.navigate_into_folder(_SUB_FOLDER, timeout=UI_ELEMENT_TIMEOUT)

            sub_names = [key.split("/")[-1] for key in _SUB_PATH_FILES]
            missing_sub = [
                f for f in sub_names
                if not artifacts_page.file_exists(f, timeout=FILE_APPEAR_TIMEOUT)
            ]
            assert not missing_sub, (
                f"Sub-path files NOT visible in bucket '{bucket_name}/{_SUB_FOLDER}/': {missing_sub}. "
                f"ELITEA-1327: files may be lost when an agent creates multiple files "
                f"in a single tool call."
            )
            logger.info("Sub-path files visible in bucket UI: %s", sub_names)

        # ------------------------------------------------------------------
        # Step 6 — Download one root file and one sub-path file via UI
        # ------------------------------------------------------------------
        with allure.step("Step 6 — Download 1 root file and 1 sub-path file via UI"):
            # 6a — one root-level file (navigate back to bucket root first)
            with allure.step(f"Step 6a — Download root file: {_ROOT_FILES[0]}"):
                artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
                download = artifacts_page.download_file(_ROOT_FILES[0], timeout=UI_ELEMENT_TIMEOUT)
                path = download.path()
                size = path.stat().st_size if path else 0
                assert size > 0, f"Downloaded root file '{_ROOT_FILES[0]}' is empty"
                logger.info("Root file '%s' downloaded (%d bytes)", _ROOT_FILES[0], size)

            # 6b — one sub-path file (navigate into 'output/' via left-panel tree)
            sub_sample = _SUB_PATH_FILES[0].split("/")[-1]  # "a.txt"
            with allure.step(f"Step 6b — Download sub-path file: {sub_sample}"):
                artifacts_page.navigate_into_folder(_SUB_FOLDER, timeout=UI_ELEMENT_TIMEOUT)
                download = artifacts_page.download_file(sub_sample, timeout=UI_ELEMENT_TIMEOUT)
                path = download.path()
                size = path.stat().st_size if path else 0
                assert size > 0, f"Downloaded sub-path file '{sub_sample}' is empty"
                logger.info("Sub-path file '%s' downloaded (%d bytes)", sub_sample, size)
