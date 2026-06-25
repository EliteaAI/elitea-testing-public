"""Export/import roundtrip API tests for Elitea pipelines.

Pipelines share the ``application`` backend with agents.  The export
produces a ``.agent.md`` file whose YAML frontmatter embeds the pipeline
definition (``entry_point``, ``nodes``) rather than placing instructions
in the body (which remains empty for pipelines).

The import wizard uses ``entity: "agents"`` for both agents and pipelines
— the ``agent_type: "pipeline"`` field inside the version payload is what
distinguishes them.

Tests cover:
- Basic roundtrip (create → export → delete → import → verify)
- Full field preservation (multiple node types, connections, all metadata)
- Conflicting-name behaviour (import when pipeline with same name exists)
- Edge cases: empty description, special characters, complex topology,
  all node types
"""

import logging
import time as _time
import uuid

import pytest
import yaml

from api import PipelineAPI
from config import settings
import allure

logger = logging.getLogger("elitea.test.export_import_pipelines")

pytestmark = [pytest.mark.api, pytest.mark.pipelines]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
API_TIMEOUT = 30       # seconds for API calls
LONG_OP_TIMEOUT = 60   # seconds for import/export operations


# ---------------------------------------------------------------------------
# Retry helper
# ---------------------------------------------------------------------------

def _wait_for(condition_fn, timeout: float = 10.0, interval: float = 0.5):
    """Poll condition_fn() until it returns truthy or timeout expires.

    Args:
        condition_fn: Zero-argument callable; returns truthy when condition met.
        timeout: Maximum seconds to wait.
        interval: Seconds between polls.

    Raises:
        TimeoutError: If condition_fn never returns truthy within timeout.
    """
    deadline = _time.monotonic() + timeout
    last_exc = None
    while _time.monotonic() < deadline:
        try:
            result = condition_fn()
            if result:
                return result
        except Exception as exc:
            last_exc = exc
        _time.sleep(interval)
    raise TimeoutError(
        f"Condition not met within {timeout}s"
        + (f": {last_exc}" if last_exc else "")
    )


# ---------------------------------------------------------------------------
# Pipeline YAML instruction builders
# ---------------------------------------------------------------------------

def _llm_node(node_id: str, transition: str = "END") -> dict:
    """Build a single LLM node definition."""
    return {
        "id": node_id,
        "type": "llm",
        "input": [],
        "input_mapping": {
            "chat_history": {"type": "fixed", "value": []},
            "system": {"type": "fixed", "value": ""},
            "task": {"type": "fixed", "value": ""},
        },
        "output": [],
        "structured_output": False,
        "transition": transition,
    }


def _decision_node(node_id: str, transitions: dict) -> dict:
    """Build a Decision node with condition-based transitions."""
    return {
        "id": node_id,
        "type": "decision",
        "input": [],
        "input_mapping": {
            "condition": {"type": "fixed", "value": "True"},
        },
        "output": [],
        "transitions": transitions,
    }


def _printer_node(node_id: str, transition: str = "END") -> dict:
    """Build a Printer node."""
    return {
        "id": node_id,
        "type": "printer",
        "input": [],
        "input_mapping": {
            "text": {"type": "fixed", "value": "output"},
        },
        "output": [],
        "transition": transition,
    }


def _router_node(node_id: str, routes: list[dict]) -> dict:
    """Build a Router node with routing rules."""
    return {
        "id": node_id,
        "type": "router",
        "input": [],
        "input_mapping": {
            "task": {"type": "fixed", "value": ""},
        },
        "output": [],
        "routes": routes,
    }


def _code_node(node_id: str, transition: str = "END") -> dict:
    """Build a Code node."""
    return {
        "id": node_id,
        "type": "code",
        "input": [],
        "input_mapping": {
            "code": {"type": "fixed", "value": "result = 'hello'"},
        },
        "output": [],
        "transition": transition,
    }


def _build_instructions_yaml(entry_point: str, nodes: list[dict]) -> str:
    """Build the YAML instructions string from entry_point + nodes."""
    data = {"entry_point": entry_point, "nodes": nodes}
    return yaml.dump(data, default_flow_style=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_exported_md(content: bytes) -> dict:
    """Parse an exported pipeline ``.agent.md`` file.

    For pipelines, the YAML frontmatter contains the pipeline definition
    (``entry_point``, ``nodes``) as top-level keys.  The body after the
    closing ``---`` is empty.

    Returns a dict with ``"frontmatter"`` (parsed YAML dict) and
    ``"body"`` (str, typically empty for pipelines).
    """
    text = content.decode("utf-8")
    if not text.startswith("---"):
        raise ValueError("Exported markdown does not start with YAML frontmatter")

    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Cannot find closing --- for YAML frontmatter")

    frontmatter = yaml.safe_load(parts[1])
    body = parts[2].strip()
    return {"frontmatter": frontmatter, "body": body}


def _reconstruct_instructions(fm: dict) -> str:
    """Reconstruct the pipeline YAML instructions from frontmatter.

    The export embeds ``entry_point`` and ``nodes`` as top-level keys in
    the YAML frontmatter.  We reconstruct the ``instructions`` field that
    the API stores internally.
    """
    nodes = fm.get("nodes", [])
    entry_point = fm.get("entry_point", "")
    if not nodes and not entry_point:
        return ""
    data = {}
    if entry_point:
        data["entry_point"] = entry_point
    if nodes:
        data["nodes"] = nodes
    return yaml.dump(data, default_flow_style=False)


def _build_import_payload(
    name: str,
    description: str,
    instructions: str,
    *,
    model_name: str = settings.default_model_name,
    temperature: float = 0.6,
    max_tokens: int = -1,
    step_limit: int = 25,
    variables: list | None = None,
) -> list[dict]:
    """Build the JSON payload for ``/import_wizard``.

    Uses ``entity: "agents"`` because both agents and pipelines share the
    same import handler.  The ``agent_type: "pipeline"`` inside the
    version is what makes it a pipeline.
    """
    return [
        {
            "name": name,
            "description": description,
            "original_exported": True,
            "import_uuid": str(uuid.uuid4()),
            "versions": [
                {
                    "name": "base",
                    "import_version_uuid": str(uuid.uuid4()),
                    "instructions": instructions,
                    "agent_type": "pipeline",
                    "llm_settings": {
                        "model_name": model_name,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                    "meta": {"step_limit": step_limit, "internal_tools": []},
                    "tools": [],
                    "variables": variables or [],
                    "conversation_starters": [],
                    "welcome_message": "",
                    "tags": [],
                    "pipeline_settings": {
                        "nodes": [],
                        "edges": [],
                        "orientation": "vertical",
                        "layout_version": "1.0",
                    },
                }
            ],
            "entity": "agents",
        }
    ]


def _build_import_payload_from_export(export_bytes: bytes) -> list[dict]:
    """Parse an exported pipeline .md and rebuild the import payload."""
    parsed = _parse_exported_md(export_bytes)
    fm = parsed["frontmatter"]
    instructions = _reconstruct_instructions(fm)

    variables = fm.get("variables", [])
    clean_vars = [{"name": v["name"], "value": v.get("value", "")} for v in variables]

    return _build_import_payload(
        name=fm["name"],
        description=fm.get("description", ""),
        instructions=instructions,
        model_name=fm.get("model", settings.default_model_name),
        temperature=fm.get("temperature", 0.6),
        max_tokens=fm.get("max_tokens", -1),
        step_limit=fm.get("step_limit", 25),
        variables=clean_vars,
    )


def _create_pipeline_with_nodes(
    pipeline_api: PipelineAPI,
    *,
    name: str,
    description: str = "Export/import test pipeline",
    entry_point: str = "LLM 1",
    nodes: list[dict] | None = None,
    temperature: float = 0.6,
    max_tokens: int = -1,
    variables: list | None = None,
) -> dict:
    """Create a pipeline with custom nodes via the public API."""
    if nodes is None:
        nodes = [_llm_node("LLM 1")]

    return pipeline_api.create_pipeline_with_nodes(
        name=name,
        description=description,
        entry_point=entry_point,
        nodes=nodes,
    )


def assert_pipeline_fields_match(
    original: dict,
    imported: dict,
    *,
    exclude_fields: list[str] | None = None,
) -> None:
    """Compare relevant fields between original and imported pipeline.

    Compares name, description, agent_type, model settings, and the
    pipeline instructions (entry_point + nodes).  Skips fields that
    don't survive the export/import cycle (id, timestamps, etc.).
    """
    excl = set(exclude_fields or [])

    def _vd(pipeline: dict) -> dict:
        vd = pipeline.get("version_details")
        if vd:
            return vd
        versions = pipeline.get("versions", [])
        return versions[0] if versions else {}

    orig_vd = _vd(original)
    imp_vd = _vd(imported)

    if "name" not in excl:
        assert imported["name"] == original["name"], (
            f"Name mismatch: {imported['name']!r} != {original['name']!r}"
        )

    if "description" not in excl:
        assert imported.get("description", "") == original.get("description", ""), (
            f"Description mismatch: {imported.get('description')!r} != {original.get('description')!r}"
        )

    if "agent_type" not in excl:
        assert imp_vd.get("agent_type") == "pipeline", (
            f"Agent type should be 'pipeline', got {imp_vd.get('agent_type')!r}"
        )

    if "model_name" not in excl:
        orig_model = orig_vd.get("llm_settings", {}).get("model_name")
        imp_model = imp_vd.get("llm_settings", {}).get("model_name")
        assert imp_model == orig_model, f"Model mismatch: {imp_model!r} != {orig_model!r}"

    if "temperature" not in excl:
        orig_temp = orig_vd.get("llm_settings", {}).get("temperature")
        imp_temp = imp_vd.get("llm_settings", {}).get("temperature")
        assert imp_temp == orig_temp, f"Temperature mismatch: {imp_temp} != {orig_temp}"

    if "instructions" not in excl:
        orig_instr = orig_vd.get("instructions", "")
        imp_instr = imp_vd.get("instructions", "")
        # Parse both as YAML and compare structurally
        orig_parsed = yaml.safe_load(orig_instr) if orig_instr else {}
        imp_parsed = yaml.safe_load(imp_instr) if imp_instr else {}
        assert imp_parsed == orig_parsed, (
            f"Instructions (pipeline definition) mismatch:\n"
            f"  Original: {orig_parsed}\n"
            f"  Imported: {imp_parsed}"
        )

    if "variables" not in excl:
        orig_vars = {v["name"]: v.get("value", "") for v in orig_vd.get("variables", [])}
        imp_vars = {v["name"]: v.get("value", "") for v in imp_vd.get("variables", [])}
        assert imp_vars == orig_vars, f"Variables mismatch: {imp_vars} != {orig_vars}"


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------

class TestPipelineExportImportRoundtrip:
    """Export → delete → import → verify cycle for pipelines."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0861_pipeline-export-and-import.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    def test_pipeline_export_import_roundtrip_basic(self, pipeline_api):
        """PEXP-001: Basic roundtrip preserves pipeline with LLM node."""
        name = f"autotest_pexp_basic_{uuid.uuid4().hex[:6]}"
        created_id = None
        imported_id = None

        try:
            # 1. Create pipeline with a single LLM node
            created = _create_pipeline_with_nodes(
                pipeline_api,
                name=name,
                description="Roundtrip test pipeline",
                entry_point="LLM 1",
                nodes=[_llm_node("LLM 1")],
            )
            created_id = created["id"]
            logger.info("Created pipeline %s (%s)", created_id, name)
            _wait_for(lambda: pipeline_api.get_pipeline(created_id) is not None)

            # 2. Export
            export_bytes = pipeline_api.export_pipeline(created_id)
            assert len(export_bytes) > 0, "Export should return non-empty content"

            parsed = _parse_exported_md(export_bytes)
            assert parsed["frontmatter"]["name"] == name
            assert parsed["frontmatter"].get("agent_type") == "pipeline"
            assert parsed["frontmatter"].get("entry_point") == "LLM 1"
            assert len(parsed["frontmatter"].get("nodes", [])) == 1
            logger.info("Exported %d bytes", len(export_bytes))

            # 3. Delete original
            pipeline_api.delete_pipeline(created_id)
            logger.info("Deleted original pipeline %s", created_id)
            created_id = None
            _time.sleep(0.5)  # brief settle — no polling endpoint for delete confirmation

            # 4. Import from export
            import_payload = _build_import_payload_from_export(export_bytes)
            result = pipeline_api.import_pipeline(import_payload)

            errors = result.get("errors", {})
            agents_errors = errors.get("agents", []) if isinstance(errors, dict) else []
            assert not agents_errors, f"Import returned errors: {agents_errors}"

            agents_result = result.get("result", {}).get("agents", [])
            assert len(agents_result) > 0, f"Import returned no pipelines; full result: {result}"

            imported_id = agents_result[0]["id"]
            logger.info("Imported as pipeline %s", imported_id)

            # 5. Verify
            imported_pipeline = pipeline_api.get_pipeline(imported_id)

            assert imported_pipeline["name"] == name
            assert imported_pipeline.get("description") == "Roundtrip test pipeline"

            vd = imported_pipeline.get("version_details", {})
            assert vd.get("agent_type") == "pipeline"
            assert vd.get("llm_settings", {}).get("model_name") == settings.default_model_name

            # Verify pipeline definition
            instr = yaml.safe_load(vd.get("instructions", ""))
            assert instr.get("entry_point") == "LLM 1"
            assert len(instr.get("nodes", [])) == 1
            assert instr["nodes"][0]["type"] == "llm"

        finally:
            if created_id:
                try:
                    pipeline_api.delete_pipeline(created_id)
                except Exception as _exc:
                    import logging as _log
                    _log.getLogger(__name__).warning("Cleanup failed: %s", _exc)
            if imported_id:
                try:
                    pipeline_api.delete_pipeline(imported_id)
                except Exception as _exc:
                    import logging as _log
                    _log.getLogger(__name__).warning("Cleanup failed: %s", _exc)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0861_pipeline-export-and-import.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_pipeline_export_import_preserves_all_fields(self, pipeline_api):
        """PEXP-002: Roundtrip preserves all fields including multiple nodes."""
        name = f"autotest_pexp_full_{uuid.uuid4().hex[:6]}"
        created_id = None
        imported_id = None

        try:
            nodes = [
                _llm_node("LLM 1", transition="Printer 1"),
                _printer_node("Printer 1"),
            ]

            created = _create_pipeline_with_nodes(
                pipeline_api,
                name=name,
                description="Full field coverage pipeline",
                entry_point="LLM 1",
                nodes=nodes,
                temperature=0.3,
                max_tokens=4096,
            )
            created_id = created["id"]
            _wait_for(lambda: pipeline_api.get_pipeline(created_id) is not None)

            original = pipeline_api.get_pipeline(created_id)

            # Export → delete → import
            export_bytes = pipeline_api.export_pipeline(created_id)
            pipeline_api.delete_pipeline(created_id)
            created_id = None
            _time.sleep(0.5)  # brief settle — no polling endpoint for delete confirmation

            import_payload = _build_import_payload_from_export(export_bytes)
            result = pipeline_api.import_pipeline(import_payload)

            errors = result.get("errors", {})
            agents_errors = errors.get("agents", []) if isinstance(errors, dict) else []
            assert not agents_errors, f"Import returned errors: {agents_errors}"

            agents_result = result.get("result", {}).get("agents", [])
            assert len(agents_result) > 0, f"Import returned no pipelines; full result: {result}"

            imported_id = agents_result[0]["id"]
            imported = pipeline_api.get_pipeline(imported_id)

            assert_pipeline_fields_match(original, imported)

        finally:
            if created_id:
                try:
                    pipeline_api.delete_pipeline(created_id)
                except Exception as _exc:
                    import logging as _log
                    _log.getLogger(__name__).warning("Cleanup failed: %s", _exc)
            if imported_id:
                try:
                    pipeline_api.delete_pipeline(imported_id)
                except Exception as _exc:
                    import logging as _log
                    _log.getLogger(__name__).warning("Cleanup failed: %s", _exc)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0861_pipeline-export-and-import.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_pipeline_export_format_is_valid_yaml(self, pipeline_api):
        """PEXP-003: Export produces valid YAML frontmatter with pipeline keys."""
        name = f"autotest_pexp_fmt_{uuid.uuid4().hex[:6]}"
        created_id = None

        try:
            created = _create_pipeline_with_nodes(
                pipeline_api,
                name=name,
                entry_point="LLM 1",
                nodes=[_llm_node("LLM 1")],
            )
            created_id = created["id"]
            _wait_for(lambda: pipeline_api.get_pipeline(created_id) is not None)

            export_bytes = pipeline_api.export_pipeline(created_id)
            text = export_bytes.decode("utf-8")

            # Format checks
            assert text.startswith("---\n"), "Export must start with YAML delimiter"
            parts = text.split("---", 2)
            assert len(parts) >= 3, "Export must have opening and closing --- delimiters"

            fm = yaml.safe_load(parts[1])
            assert isinstance(fm, dict), "Frontmatter should parse as dict"
            assert "name" in fm, "Frontmatter must contain 'name'"
            assert "agent_type" in fm, "Frontmatter must contain 'agent_type'"
            assert fm["agent_type"] == "pipeline"
            assert "entry_point" in fm, "Frontmatter must contain 'entry_point'"
            assert "nodes" in fm, "Frontmatter must contain 'nodes'"

            # Body should be empty for pipelines
            body = parts[2].strip()
            assert body == "", f"Pipeline body should be empty, got: {body!r}"

        finally:
            if created_id:
                try:
                    pipeline_api.delete_pipeline(created_id)
                except Exception as _exc:
                    import logging as _log
                    _log.getLogger(__name__).warning("Cleanup failed: %s", _exc)


class TestPipelineExportImportConflicts:
    """Test import behaviour when a same-named pipeline already exists."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0861_pipeline-export-and-import.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_pipeline_import_with_conflicting_name(self, pipeline_api):
        """PEXP-004: Importing when pipeline with same name exists creates second one."""
        name = f"autotest_pexp_conflict_{uuid.uuid4().hex[:6]}"
        original_id = None
        imported_id = None

        try:
            original = _create_pipeline_with_nodes(
                pipeline_api,
                name=name,
                description="Original pipeline",
                entry_point="LLM 1",
                nodes=[_llm_node("LLM 1")],
            )
            original_id = original["id"]
            _wait_for(lambda: pipeline_api.get_pipeline(original_id) is not None)

            # Export it
            export_bytes = pipeline_api.export_pipeline(original_id)

            # DON'T delete — import same file
            import_payload = _build_import_payload_from_export(export_bytes)
            result = pipeline_api.import_pipeline(import_payload)

            agents_result = result.get("result", {}).get("agents", [])
            errors = result.get("errors", {}).get("agents", [])

            if agents_result:
                imported_id = agents_result[0]["id"]
                assert imported_id != original_id, (
                    "Imported pipeline should have a different ID from original"
                )
                logger.info(
                    "Conflicting import created new pipeline %s (original %s)",
                    imported_id, original_id,
                )
            elif errors:
                pytest.xfail(f"Platform rejected duplicate name with errors: {errors}")
            else:
                pytest.fail("Import returned neither result nor error for conflicting name")

        finally:
            if original_id:
                try:
                    pipeline_api.delete_pipeline(original_id)
                except Exception as _exc:
                    import logging as _log
                    _log.getLogger(__name__).warning("Cleanup failed: %s", _exc)
            if imported_id:
                try:
                    pipeline_api.delete_pipeline(imported_id)
                except Exception as _exc:
                    import logging as _log
                    _log.getLogger(__name__).warning("Cleanup failed: %s", _exc)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0861_pipeline-export-and-import.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    def test_pipeline_import_preserves_original_when_conflict(self, pipeline_api):
        """PEXP-005: Original pipeline is unchanged after importing with same name."""
        name = f"autotest_pexp_preserve_{uuid.uuid4().hex[:6]}"
        original_id = None
        imported_id = None

        try:
            original = _create_pipeline_with_nodes(
                pipeline_api,
                name=name,
                description="Original description",
                entry_point="LLM 1",
                nodes=[_llm_node("LLM 1")],
                temperature=0.3,
            )
            original_id = original["id"]
            _wait_for(lambda: pipeline_api.get_pipeline(original_id) is not None)

            # Capture original state
            original_data = pipeline_api.get_pipeline(original_id)

            # Export and import (without deleting original)
            export_bytes = pipeline_api.export_pipeline(original_id)
            import_payload = _build_import_payload_from_export(export_bytes)
            result = pipeline_api.import_pipeline(import_payload)

            errors = result.get("errors", {})
            agents_errors = errors.get("agents", []) if isinstance(errors, dict) else []
            assert not agents_errors, f"Import returned errors: {agents_errors}"

            agents_result = result.get("result", {}).get("agents", [])
            if agents_result:
                imported_id = agents_result[0]["id"]

            # Verify original is unchanged
            original_after = pipeline_api.get_pipeline(original_id)
            assert original_after["name"] == original_data["name"]
            assert original_after.get("description") == original_data.get("description")

            orig_vd = original_data.get("version_details", {})
            after_vd = original_after.get("version_details", {})
            assert after_vd.get("instructions") == orig_vd.get("instructions")
            assert after_vd.get("agent_type") == "pipeline"

        finally:
            if original_id:
                try:
                    pipeline_api.delete_pipeline(original_id)
                except Exception as _exc:
                    import logging as _log
                    _log.getLogger(__name__).warning("Cleanup failed: %s", _exc)
            if imported_id:
                try:
                    pipeline_api.delete_pipeline(imported_id)
                except Exception as _exc:
                    import logging as _log
                    _log.getLogger(__name__).warning("Cleanup failed: %s", _exc)


class TestPipelineExportImportEdgeCases:
    """Edge case tests for pipeline export/import."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0861_pipeline-export-and-import.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    def test_pipeline_export_import_empty_description(self, pipeline_api):
        """PEXP-006: Roundtrip works with empty description."""
        name = f"autotest_pexp_empty_{uuid.uuid4().hex[:6]}"
        created_id = None
        imported_id = None

        try:
            created = _create_pipeline_with_nodes(
                pipeline_api,
                name=name,
                description="",
                entry_point="LLM 1",
                nodes=[_llm_node("LLM 1")],
            )
            created_id = created["id"]
            _wait_for(lambda: pipeline_api.get_pipeline(created_id) is not None)

            export_bytes = pipeline_api.export_pipeline(created_id)
            pipeline_api.delete_pipeline(created_id)
            created_id = None
            _time.sleep(0.5)  # brief settle — no polling endpoint for delete confirmation

            import_payload = _build_import_payload_from_export(export_bytes)
            result = pipeline_api.import_pipeline(import_payload)

            errors = result.get("errors", {})
            agents_errors = errors.get("agents", []) if isinstance(errors, dict) else []
            assert not agents_errors, f"Import returned errors: {agents_errors}"

            agents_result = result.get("result", {}).get("agents", [])
            assert len(agents_result) > 0, f"Import returned no pipelines; full result: {result}"

            imported_id = agents_result[0]["id"]
            imported = pipeline_api.get_pipeline(imported_id)

            assert imported["name"] == name
            assert imported.get("description", "") == "", \
                f"Description should be empty after roundtrip, got {imported.get('description')!r}"
            vd = imported.get("version_details", {})
            assert vd.get("agent_type") == "pipeline"

        finally:
            if created_id:
                try:
                    pipeline_api.delete_pipeline(created_id)
                except Exception as _exc:
                    import logging as _log
                    _log.getLogger(__name__).warning("Cleanup failed: %s", _exc)
            if imported_id:
                try:
                    pipeline_api.delete_pipeline(imported_id)
                except Exception as _exc:
                    import logging as _log
                    _log.getLogger(__name__).warning("Cleanup failed: %s", _exc)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0861_pipeline-export-and-import.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    def test_pipeline_export_import_special_characters_in_name(self, pipeline_api):
        """PEXP-007: Names with special characters survive roundtrip."""
        name = f"autotest_p&p@-{uuid.uuid4().hex[:4]}"
        description = "Pipeline with special chars: <>&\"'"
        created_id = None
        imported_id = None

        try:
            created = _create_pipeline_with_nodes(
                pipeline_api,
                name=name,
                description=description,
                entry_point="LLM 1",
                nodes=[_llm_node("LLM 1")],
            )
            created_id = created["id"]
            _wait_for(lambda: pipeline_api.get_pipeline(created_id) is not None)

            export_bytes = pipeline_api.export_pipeline(created_id)
            pipeline_api.delete_pipeline(created_id)
            created_id = None
            _time.sleep(0.5)  # brief settle — no polling endpoint for delete confirmation

            import_payload = _build_import_payload_from_export(export_bytes)
            result = pipeline_api.import_pipeline(import_payload)

            errors = result.get("errors", {})
            agents_errors = errors.get("agents", []) if isinstance(errors, dict) else []
            assert not agents_errors, f"Import returned errors: {agents_errors}"

            agents_result = result.get("result", {}).get("agents", [])
            assert len(agents_result) > 0, f"Import returned no pipelines; full result: {result}"

            imported_id = agents_result[0]["id"]
            imported = pipeline_api.get_pipeline(imported_id)

            assert imported["name"] == name
            assert imported.get("description") == description, \
                f"Description with special chars should survive roundtrip"

        finally:
            if created_id:
                try:
                    pipeline_api.delete_pipeline(created_id)
                except Exception as _exc:
                    import logging as _log
                    _log.getLogger(__name__).warning("Cleanup failed: %s", _exc)
            if imported_id:
                try:
                    pipeline_api.delete_pipeline(imported_id)
                except Exception as _exc:
                    import logging as _log
                    _log.getLogger(__name__).warning("Cleanup failed: %s", _exc)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0861_pipeline-export-and-import.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_pipeline_export_import_complex_topology(self, pipeline_api):
        """PEXP-008: Complex pipeline with branching topology survives roundtrip."""
        name = f"autotest_pexp_complex_{uuid.uuid4().hex[:6]}"
        created_id = None
        imported_id = None

        try:
            # Build a complex topology: LLM → Decision → (LLM2 or Printer) → END
            nodes = [
                _llm_node("LLM 1", transition="Decision 1"),
                _decision_node("Decision 1", transitions={
                    "true": "LLM 2",
                    "false": "Printer 1",
                }),
                _llm_node("LLM 2"),
                _printer_node("Printer 1"),
            ]

            created = _create_pipeline_with_nodes(
                pipeline_api,
                name=name,
                description="Complex topology pipeline",
                entry_point="LLM 1",
                nodes=nodes,
            )
            created_id = created["id"]
            _wait_for(lambda: pipeline_api.get_pipeline(created_id) is not None)

            original = pipeline_api.get_pipeline(created_id)

            # Export → delete → import
            export_bytes = pipeline_api.export_pipeline(created_id)
            pipeline_api.delete_pipeline(created_id)
            created_id = None
            _time.sleep(0.5)  # brief settle — no polling endpoint for delete confirmation

            import_payload = _build_import_payload_from_export(export_bytes)
            result = pipeline_api.import_pipeline(import_payload)

            errors = result.get("errors", {})
            agents_errors = errors.get("agents", []) if isinstance(errors, dict) else []
            assert not agents_errors, f"Import returned errors: {agents_errors}"

            agents_result = result.get("result", {}).get("agents", [])
            assert len(agents_result) > 0, f"Import returned no pipelines; full result: {result}"

            imported_id = agents_result[0]["id"]
            imported = pipeline_api.get_pipeline(imported_id)

            # Verify all 4 nodes survived
            vd = imported.get("version_details", {})
            instr = yaml.safe_load(vd.get("instructions", ""))
            assert instr.get("entry_point") == "LLM 1"

            imported_nodes = instr.get("nodes", [])
            assert len(imported_nodes) == 4, (
                f"Expected 4 nodes, got {len(imported_nodes)}"
            )

            node_ids = {n["id"] for n in imported_nodes}
            assert node_ids == {"LLM 1", "Decision 1", "LLM 2", "Printer 1"}

            node_types = {n["id"]: n["type"] for n in imported_nodes}
            assert node_types["LLM 1"] == "llm"
            assert node_types["Decision 1"] == "decision"
            assert node_types["LLM 2"] == "llm"
            assert node_types["Printer 1"] == "printer"

            # Verify structural comparison
            assert_pipeline_fields_match(original, imported)

        finally:
            if created_id:
                try:
                    pipeline_api.delete_pipeline(created_id)
                except Exception as _exc:
                    import logging as _log
                    _log.getLogger(__name__).warning("Cleanup failed: %s", _exc)
            if imported_id:
                try:
                    pipeline_api.delete_pipeline(imported_id)
                except Exception as _exc:
                    import logging as _log
                    _log.getLogger(__name__).warning("Cleanup failed: %s", _exc)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0861_pipeline-export-and-import.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_pipeline_export_import_all_node_types(self, pipeline_api):
        """PEXP-009: Pipeline with all available node types survives roundtrip."""
        name = f"autotest_pexp_allnodes_{uuid.uuid4().hex[:6]}"
        created_id = None
        imported_id = None

        try:
            # Build a pipeline using LLM, Code, Decision, Printer, Router
            nodes = [
                _llm_node("LLM 1", transition="Code 1"),
                _code_node("Code 1", transition="Decision 1"),
                _decision_node("Decision 1", transitions={
                    "true": "Router 1",
                    "false": "Printer 1",
                }),
                _router_node("Router 1", routes=[
                    {"condition": "default", "transition": "Printer 1"},
                ]),
                _printer_node("Printer 1"),
            ]

            created = _create_pipeline_with_nodes(
                pipeline_api,
                name=name,
                description="All node types pipeline",
                entry_point="LLM 1",
                nodes=nodes,
            )
            created_id = created["id"]
            _wait_for(lambda: pipeline_api.get_pipeline(created_id) is not None)

            original = pipeline_api.get_pipeline(created_id)

            # Export → delete → import
            export_bytes = pipeline_api.export_pipeline(created_id)
            pipeline_api.delete_pipeline(created_id)
            created_id = None
            _time.sleep(0.5)  # brief settle — no polling endpoint for delete confirmation

            import_payload = _build_import_payload_from_export(export_bytes)
            result = pipeline_api.import_pipeline(import_payload)

            errors = result.get("errors", {})
            agents_errors = errors.get("agents", []) if isinstance(errors, dict) else []
            assert not agents_errors, f"Import returned errors: {agents_errors}"

            agents_result = result.get("result", {}).get("agents", [])
            assert len(agents_result) > 0, f"Import returned no pipelines; full result: {result}"

            imported_id = agents_result[0]["id"]
            imported = pipeline_api.get_pipeline(imported_id)

            # Verify all 5 node types survived
            vd = imported.get("version_details", {})
            instr = yaml.safe_load(vd.get("instructions", ""))
            imported_nodes = instr.get("nodes", [])

            assert len(imported_nodes) == 5, (
                f"Expected 5 nodes, got {len(imported_nodes)}"
            )

            type_set = {n["type"] for n in imported_nodes}
            assert type_set == {"llm", "code", "decision", "router", "printer"}, (
                f"Expected all 5 node types, got {type_set}"
            )

            assert_pipeline_fields_match(original, imported)

        finally:
            if created_id:
                try:
                    pipeline_api.delete_pipeline(created_id)
                except Exception as _exc:
                    import logging as _log
                    _log.getLogger(__name__).warning("Cleanup failed: %s", _exc)
            if imported_id:
                try:
                    pipeline_api.delete_pipeline(imported_id)
                except Exception as _exc:
                    import logging as _log
                    _log.getLogger(__name__).warning("Cleanup failed: %s", _exc)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0861_pipeline-export-and-import.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    def test_pipeline_import_via_constructed_payload(self, pipeline_api):
        """PEXP-010: Import works with a manually constructed payload (no export)."""
        name = f"autotest_pexp_manual_{uuid.uuid4().hex[:6]}"
        imported_id = None

        try:
            instructions = _build_instructions_yaml(
                "LLM 1",
                [_llm_node("LLM 1", transition="Printer 1"), _printer_node("Printer 1")],
            )

            payload = _build_import_payload(
                name=name,
                description="Manually constructed pipeline import",
                instructions=instructions,
                temperature=0.4,
                max_tokens=2048,
            )

            result = pipeline_api.import_pipeline(payload)

            errors = result.get("errors", {})
            agents_errors = errors.get("agents", []) if isinstance(errors, dict) else []
            assert not agents_errors, f"Import returned errors: {agents_errors}"

            agents_result = result.get("result", {}).get("agents", [])
            assert len(agents_result) > 0, "Manual import should create a pipeline"

            imported_id = agents_result[0]["id"]
            imported = pipeline_api.get_pipeline(imported_id)

            assert imported["name"] == name
            assert imported.get("description") == "Manually constructed pipeline import"

            vd = imported.get("version_details", {})
            assert vd.get("agent_type") == "pipeline"
            assert vd.get("llm_settings", {}).get("temperature") == 0.4
            assert vd.get("llm_settings", {}).get("max_tokens") == 2048

            instr = yaml.safe_load(vd.get("instructions", ""))
            assert instr.get("entry_point") == "LLM 1"
            assert len(instr.get("nodes", [])) == 2

        finally:
            if imported_id:
                try:
                    pipeline_api.delete_pipeline(imported_id)
                except Exception as _exc:
                    import logging as _log
                    _log.getLogger(__name__).warning("Cleanup failed: %s", _exc)
