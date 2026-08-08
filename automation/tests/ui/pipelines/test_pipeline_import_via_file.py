"""UI test — Pipeline Import via File: export / delete / import round trip.

TMS: ELITEA-2012
(test-specs/pipelines/l2_pipeline-import-via-file_ELITEA-2012.md)

Creates a pipeline (name/description/chat starter/LLM node) via UI, exports
it via the three-dot menu (downloads a ``.pipeline.md`` Markdown file — the
case text's "JSON file" wording is stale, see CLARIFICATION #1334), deletes
the original, then re-imports the exported file via the Pipelines
dashboard's Import button. Verifies the imported pipeline gets a NEW unique
id, its name/description/chat starter/step limit/node structure match the
original exactly, and it executes successfully via the embedded chat.

No product defect found — the round trip works end-to-end. One case-text
clarification (not a defect): Step 2 says "JSON file downloads"; the live
product always exports Markdown with YAML frontmatter
(EliteaAI/elitea-testing-public#1334).

AFS amendment (this PR, Phase 2 technique note — case step 5): the "Import
parameters" preview dialog's Type/Description/Chat-starters/Step-limit
fields (rendered by the shared ``IWModalEntityCard``/
``IWModalEntityCardWrapper`` components, also used by Agent/Skill import)
carry NO ``data-testid`` at this call site — the wrapper supports a
``subtitleTestId`` prop but ``IWModalEntityCard.jsx`` doesn't wire it, and
the Description/Chat-starters/Step-limit ``Typography`` nodes carry no
testid at all (confirmed via source read). Per the AFS's own "zero
additional testid work needed" scoping (Concrete Handles / Automation
Hints) and the suite's established pattern for this shared dialog
(``test_import_agent_valid_md_file.py``, ELITEA-1901), the preview step
(Step 5) asserts only what's testid-backed — dialog rendering + Main entity
name — and defers full config-equivalence verification to Step 7's
post-import detail page + API readback, which is also the more durable
check per the AFS's own Automation Hints (API readback preferred over DOM).
"""

import logging
import tempfile
import uuid
from pathlib import Path
from urllib.parse import urlparse

import allure
import pytest
import yaml
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage
from pages.pipelines_list_page import PipelinesListPage

logger = logging.getLogger("elitea.tests.pipelines")

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000
IMPORT_TIMEOUT = 15_000
EXECUTION_TIMEOUT = 90_000
STABLE_DURATION_MS = 3_000

# Known, pre-existing, unrelated React dev-mode DOM-nesting warning that
# fires on every successful "Import Complete" dialog render (AFS § Known
# Defects, already tracked at EliteaAI/elitea-testing-public#570) — not
# specific to this case. Filtered out of the zero-console-errors assertion
# rather than asserted against, mirroring
# test_import_agent_valid_md_file.py's ``_KNOWN_NONBLOCKING_CONSOLE_SUBSTRING``.
_KNOWN_NONBLOCKING_CONSOLE_SUBSTRING = "validateDOMNesting"

_DESC_MARKER = "ELITEA_2012_DESC_MARKER"
_SYSTEM_VALUE = "You are a helpful assistant for import/export testing. ELITEA_2012_SYSTEM_MARKER"


def _slug_chars(text: str) -> str:
    """Lowercase, alnum-only projection of *text*, for loose filename matching
    without depending on the export handler's exact slugify algorithm."""
    return "".join(ch for ch in text.lower() if ch.isalnum())


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2012_pipeline-import-via-file.md",
    "onetest-ai Test Case link",
)
@pytest.mark.p2
def test_pipeline_import_via_file(page, pipeline_api):
    """Export a pipeline, delete the original, import the file back, verify the round trip."""
    unique_suffix = uuid.uuid4().hex[:8]
    pipeline_name = f"autotest_imp_{unique_suffix}"
    pipeline_description = (
        f"Pipeline import round trip for ELITEA-2012. {_DESC_MARKER} must appear verbatim."
    )
    chat_starter = "What can this pipeline do?"

    project_id = str(settings.elitea_project_id)
    list_page = PipelinesListPage(page)
    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 1 (not inside it) so the zero-console-errors
    # assertion genuinely covers the FULL flow, mirroring
    # test_import_agent_valid_md_file.py's registration point.
    console_errors = []
    page.on(
        "console",
        lambda msg: console_errors.append(msg) if msg.type == "error" else None,
    )

    original_pipeline_id = None
    imported_pipeline_id = None
    original_yaml = None
    original_llm_node = None
    original_step_limit = None
    download_path = None

    try:
        with allure.step(
            "Step 1 — Create a pipeline with name, description, chat starter, "
            "and an LLM node (System filled, Task=Variable/input); Save"
        ):
            list_page.navigate()
            list_page.click_create_pipeline()

            pipeline_page.name_input.click()
            pipeline_page.name_input.press_sequentially(pipeline_name, delay=20)
            assert pipeline_page.get_name() == pipeline_name

            pipeline_page.description_input.click()
            pipeline_page.description_input.press_sequentially(pipeline_description, delay=20)
            assert pipeline_page.get_description() == pipeline_description

            pipeline_page.add_conversation_starter(chat_starter)
            assert pipeline_page.get_conversation_starter_value(0) == chat_starter

            create_response = pipeline_page.save_and_wait_for_creation(
                project_id, timeout=FORM_SAVE_TIMEOUT
            )
            original_pipeline_id = create_response["id"]
            pipeline_page.wait_for_detail_page_load()
            pipeline_page.wait_for_canvas()

            pipeline_page.add_node("LLM")
            node_id = pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
            assert node_id, "LLM node should be present on the canvas with a non-empty data-id"

            pipeline_page.fill_llm_node_section_value("system", _SYSTEM_VALUE)
            assert pipeline_page.get_llm_node_section_value("system") == _SYSTEM_VALUE

            pipeline_page.select_llm_node_section_type("task", "Variable", timeout=UI_ELEMENT_TIMEOUT)
            pipeline_page.select_llm_node_section_variable_value(
                "task", "input", timeout=UI_ELEMENT_TIMEOUT
            )
            assert pipeline_page.get_llm_node_section_variable_value("task") == "input"

            update_response = pipeline_page.save_and_wait_for_update(
                project_id, original_pipeline_id, timeout=FORM_SAVE_TIMEOUT
            )
            assert update_response is not None, "Save should return the persisted pipeline version"
            assert pipeline_page.get_pipeline_id() == str(original_pipeline_id), (
                "Pipeline ID display should match the created pipeline's id"
            )
            assert not console_errors, f"Pipeline creation should not introduce console errors: {console_errors}"

            # Capture server-truth config for the post-import comparison
            # (Step 7) BEFORE the original is deleted (Step 3).
            original_server = pipeline_api.get_pipeline(original_pipeline_id)
            original_yaml = yaml.safe_load(original_server["version_details"]["instructions"])
            original_step_limit = pipeline_page.get_step_limit()

            # Independent, absolute proof of the canvas node wiring this step
            # created — not just a value later diffed against the import
            # (Step 7). A single-LLM-node pipeline's default (unedited)
            # transition is the literal "END" (see
            # test_pipeline_yaml_flow_sync.py / test_pipeline_edge_deletion.py /
            # test_pipeline_yaml_editor_invalid_syntax.py for the same
            # baseline, confirmed live).
            original_llm_node = next(n for n in original_yaml["nodes"] if n["type"] == "llm")
            assert original_llm_node["transition"] == "END", (
                "Newly created LLM node should wire to END by default (no "
                f"downstream node added), got: {original_llm_node['transition']!r}"
            )

        with allure.step(
            "Step 2 — Export the pipeline via the three-dot menu; verify a "
            "'.pipeline.md' Markdown file downloads (CLARIFICATION #1334 — "
            "case text says JSON, live product exports Markdown)"
        ):
            download = pipeline_page.export_pipeline_via_menu_and_download(timeout=UI_ELEMENT_TIMEOUT)
            assert download.suggested_filename.endswith(".pipeline.md"), (
                "Export should download a '.pipeline.md' Markdown file (not JSON — "
                f"CLARIFICATION #1334), got: {download.suggested_filename!r}"
            )
            assert _slug_chars(pipeline_name) in _slug_chars(download.suggested_filename), (
                "Downloaded filename should embed the pipeline's (slugified) name, "
                f"got: {download.suggested_filename!r}"
            )

            download_path = Path(tempfile.gettempdir()) / download.suggested_filename
            download.save_as(download_path)
            assert download_path.exists() and download_path.stat().st_size > 0, (
                "Downloaded export file should exist and be non-empty"
            )

            raw_content = download_path.read_text(encoding="utf-8")
            parts = raw_content.split("---", 2)
            assert len(parts) == 3, (
                f"Expected YAML frontmatter delimited by '---', got: {raw_content[:200]!r}"
            )
            frontmatter = yaml.safe_load(parts[1])
            assert frontmatter.get("name") == pipeline_name, "Exported frontmatter name should match"
            assert frontmatter.get("description") == pipeline_description, (
                "Exported frontmatter description should match"
            )
            assert frontmatter.get("agent_type") == "pipeline", (
                f"Exported frontmatter agent_type should be 'pipeline', got: "
                f"{frontmatter.get('agent_type')!r}"
            )
            assert frontmatter.get("conversation_starters") == [chat_starter], (
                "Exported frontmatter conversation_starters should match, got: "
                f"{frontmatter.get('conversation_starters')!r}"
            )

        with allure.step(
            "Step 3 — Delete the original pipeline via the three-dot menu; verify "
            "the DELETE response, the auto-redirect to /pipelines/all, and that "
            "the pipeline no longer appears in the dashboard"
        ):
            with page.expect_response(
                lambda r: (
                    f"/application/prompt_lib/{project_id}/{original_pipeline_id}" in r.url
                    and r.request.method == "DELETE"
                ),
                timeout=NAVIGATION_TIMEOUT,
            ) as delete_response_info:
                pipeline_page.delete_pipeline_via_menu(timeout=NAVIGATION_TIMEOUT)
            assert delete_response_info.value.status in (200, 202, 204), (
                f"Delete should return 2xx/204, got: {delete_response_info.value.status}"
            )

            page.wait_for_url(
                lambda url: urlparse(url).path.rstrip("/").endswith("/pipelines/all"),
                timeout=NAVIGATION_TIMEOUT,
            )
            assert pipeline_name not in list_page.get_card_names(timeout=UI_ELEMENT_TIMEOUT), (
                f"'{pipeline_name}' should no longer appear on the dashboard after deletion"
            )

        with allure.step(
            'Step 4 — Navigate to the Pipelines dashboard; verify "Import" is '
            "available in the toolbar"
        ):
            list_page.navigate()
            assert list_page.import_button.is_visible(), (
                "Import button should be visible in the Pipelines dashboard toolbar"
            )

        with allure.step(
            "Step 5 — Upload the exported file via the file chooser; verify the "
            "'Import parameters' preview dialog renders with the original "
            "pipeline's name (see module docstring for the preview-dialog "
            "AFS amendment)"
        ):
            list_page.import_pipeline(str(download_path), timeout=IMPORT_TIMEOUT)
            assert list_page.import_preview_name.is_visible(), (
                "Import dialog should preview the Main entity (Pipeline) name"
            )
            assert list_page.import_preview_name.text_content() == pipeline_name, (
                "Import dialog's Main-entity name preview should show the "
                "exported pipeline's name verbatim"
            )

        with allure.step(
            "Step 6 — Confirm the import; verify the Import Complete dialog "
            "lists the new pipeline; click 'Got it'; verify a NEW unique "
            "pipeline ID"
        ):
            list_page.confirm_pipeline_import(timeout=IMPORT_TIMEOUT)
            assert pipeline_name in list_page.import_complete_pipelines_list.text_content(), (
                "Import Complete dialog's Pipelines list should include the "
                "imported pipeline's name"
            )

            imported_pipeline_id = list_page.confirm_import_complete(timeout=NAVIGATION_TIMEOUT)
            pipeline_page.wait_for_detail_page_load()
            assert imported_pipeline_id != original_pipeline_id, (
                "Imported pipeline should get a NEW id, got the same id "
                f"({imported_pipeline_id}) as the original"
            )

        with allure.step(
            "Step 7 — Verify name, description, chat starter, step limit, and "
            "node structure are preserved (API readback for node structure, "
            "per AFS Automation Hints)"
        ):
            assert pipeline_page.get_name() == pipeline_name, "Imported pipeline's Name should match"
            imported_description = pipeline_page.get_description()
            assert _DESC_MARKER in imported_description, (
                f"Imported Description should contain the planted marker "
                f"{_DESC_MARKER!r} verbatim, got: {imported_description!r}"
            )
            assert imported_description == pipeline_description, (
                "Imported pipeline's Description should match the original verbatim"
            )
            assert pipeline_page.get_conversation_starter_value(0) == chat_starter, (
                "Imported pipeline's Chat starter should match the original"
            )
            assert pipeline_page.get_step_limit() == original_step_limit, (
                "Imported pipeline's Step limit should match the original"
            )

            imported_server = pipeline_api.get_pipeline(imported_pipeline_id)
            imported_yaml = yaml.safe_load(imported_server["version_details"]["instructions"])
            assert imported_yaml.get("entry_point") == original_yaml.get("entry_point"), (
                "Imported pipeline's entry_point should match the original"
            )
            # original_llm_node was extracted + independently asserted in Step 1
            imported_llm_node = next(n for n in imported_yaml["nodes"] if n["type"] == "llm")
            assert imported_llm_node["id"] == original_llm_node["id"], (
                "Imported LLM node id/label should match the original"
            )
            assert imported_llm_node["transition"] == original_llm_node["transition"], (
                "Imported LLM node's transition (wiring to END) should match the original"
            )
            assert imported_llm_node["input_mapping"]["system"]["value"] == _SYSTEM_VALUE, (
                "Imported LLM node's SYSTEM value should match the original verbatim"
            )
            assert imported_llm_node["input_mapping"]["task"] == {"type": "variable", "value": "input"}, (
                "Imported LLM node's TASK Type/Value should match the original "
                f"(Type=Variable, Value=input), got: "
                f"{imported_llm_node['input_mapping']['task']!r}"
            )

        with allure.step(
            "Step 8 — Verify the imported pipeline can be executed: send a chat "
            "message and confirm a real (non-error) AI response"
        ):
            initial_count = pipeline_page.get_embedded_chat_message_count()
            pipeline_page.send_message_in_embedded_chat("Hello", timeout=UI_ELEMENT_TIMEOUT)
            pipeline_page.wait_for_embedded_chat_response(
                initial_count=initial_count,
                stable_duration_ms=STABLE_DURATION_MS,
                timeout=EXECUTION_TIMEOUT,
            )
            response = pipeline_page.get_embedded_chat_last_message()
            assert len(response.strip()) > 3, f"Expected a substantive AI response, got: {response!r}"
            assert "unexpected error" not in response.lower(), (
                f"Response should not contain an error, got: {response}"
            )

        # Axis 2 addition (AFS) — zero (unfiltered) console errors across the
        # entire create -> export -> delete -> import -> verify -> execute flow.
        real_console_errors = [
            m.text for m in console_errors
            if _KNOWN_NONBLOCKING_CONSOLE_SUBSTRING not in m.text
        ]
        assert not real_console_errors, (
            "Expected no (unfiltered) console errors across the import round "
            f"trip, got: {real_console_errors!r}"
        )
    finally:
        with allure.step("Cleanup — delete original (if still present) and imported pipelines via API"):
            if original_pipeline_id is not None:
                try:
                    pipeline_api.delete_pipeline(original_pipeline_id)
                    logger.info("Cleanup: deleted original pipeline id=%s", original_pipeline_id)
                except Exception as exc:
                    logger.debug(
                        "Cleanup: original pipeline id=%s already gone (expected — "
                        "deleted in Step 3): %s", original_pipeline_id, exc,
                    )
            if imported_pipeline_id is not None:
                try:
                    pipeline_api.delete_pipeline(imported_pipeline_id)
                    logger.info("Cleanup: deleted imported pipeline id=%s", imported_pipeline_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete imported pipeline id=%s: %s",
                        imported_pipeline_id, exc,
                    )
