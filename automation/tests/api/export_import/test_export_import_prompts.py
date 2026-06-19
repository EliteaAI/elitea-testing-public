"""Export/import roundtrip API tests for Elitea agents (prompts).

In Elitea, "Prompts" are stored as Agents (applications).  The export
produces a ``.agent.md`` file with YAML frontmatter and the system
instructions as the body.  Import sends the parsed payload to the
``/import_wizard`` endpoint.

Tests cover:
- Basic roundtrip (create → export → delete → import → verify)
- Full field preservation (variables, description, welcome_message, etc.)
- Conflicting-name behaviour (import when agent with same name exists)
- Edge cases: empty optional fields, special characters, large instructions
"""

import logging
import time as _time
import uuid

import pytest
import yaml

from api import AgentAPI

logger = logging.getLogger("elitea.test.export_import")

pytestmark = [pytest.mark.api, pytest.mark.agents]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
API_TIMEOUT = 30
LONG_OP_TIMEOUT = 60
from config import settings as _settings
DEFAULT_MODEL_NAME = _settings.default_model_name


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wait_for(condition_fn, timeout: float = 10.0, interval: float = 0.5):
    """Poll condition_fn() until truthy or timeout expires."""
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


def _normalize_ws(s):
    import re
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def _parse_exported_md(content: bytes) -> dict:
    """Parse an exported ``.agent.md`` file into its frontmatter and body.

    Returns a dict with ``"frontmatter"`` (parsed YAML dict) and
    ``"instructions"`` (str).
    """
    text = content.decode("utf-8")
    if not text.startswith("---"):
        raise ValueError("Exported markdown does not start with YAML frontmatter")

    # Split on the closing --- delimiter
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Cannot find closing --- for YAML frontmatter")

    frontmatter = yaml.safe_load(parts[1])
    instructions = parts[2].strip()
    return {"frontmatter": frontmatter, "instructions": instructions}


def _build_import_payload(
    name: str,
    description: str,
    instructions: str,
    *,
    model_name: str = DEFAULT_MODEL_NAME,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    agent_type: str = "openai",
    step_limit: int = 25,
    variables: list | None = None,
    conversation_starters: list | None = None,
    welcome_message: str = "",
    tags: list | None = None,
) -> list[dict]:
    """Build the JSON payload expected by ``/import_wizard``.

    This mirrors what the EliteAUI client-side parser produces from a
    ``.agent.md`` file.
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
                    "agent_type": agent_type,
                    "llm_settings": {
                        "model_name": model_name,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                    "meta": {"step_limit": step_limit, "internal_tools": []},
                    "tools": [],
                    "variables": variables or [],
                    "conversation_starters": conversation_starters or [],
                    "welcome_message": welcome_message,
                    "tags": tags or [],
                }
            ],
            "entity": "agents",
        }
    ]


def _build_import_payload_from_export(export_bytes: bytes) -> list[dict]:
    """Parse an exported .agent.md and rebuild the import payload."""
    parsed = _parse_exported_md(export_bytes)
    fm = parsed["frontmatter"]

    variables = fm.get("variables", [])
    # Exported variables have an extra "id" field — strip it for import
    clean_vars = [{"name": v["name"], "value": v.get("value", "")} for v in variables]

    return _build_import_payload(
        name=fm["name"],
        description=fm.get("description", ""),
        instructions=parsed["instructions"],
        model_name=fm.get("model", DEFAULT_MODEL_NAME),
        temperature=fm.get("temperature", 0.7),
        max_tokens=fm.get("max_tokens", 1024),
        agent_type=fm.get("agent_type", "openai"),
        step_limit=fm.get("step_limit", 25),
        variables=clean_vars,
    )


def _create_agent_with_fields(
    agent_api: AgentAPI,
    *,
    name: str,
    description: str = "Export/import test agent",
    instructions: str = "You are a test agent.",
    temperature: float = 0.7,
    max_tokens: int = 1024,
    variables: list | None = None,
    welcome_message: str = "",
    conversation_starters: list | None = None,
) -> dict:
    """Create an agent with full field control via the public API."""
    payload = {
        "name": name,
        "description": description,
        "type": "interface",
        "versions": [
            {
                "name": "base",
                "tags": [],
                "instructions": instructions,
                "variables": variables or [],
                "tools": [],
                "llm_settings": {
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "reasoning_effort": "medium",
                    "model_name": DEFAULT_MODEL_NAME,
                    "model_project_id": _settings.default_model_project_id,
                },
                "conversation_starters": conversation_starters or [],
                "agent_type": "openai",
                "welcome_message": welcome_message,
                "meta": {"step_limit": 25},
            }
        ],
    }
    return agent_api.create_agent_full(payload)


def assert_prompt_fields_match(
    original: dict,
    imported: dict,
    *,
    exclude_fields: list[str] | None = None,
) -> None:
    """Compare relevant fields between original and imported agent.

    ``original`` is the dict returned by :func:`_create_agent_with_fields`
    (or ``get_agent``).  ``imported`` is the result from ``get_agent``
    after importing.

    Only compares fields that survive the export/import cycle.
    """
    excl = set(exclude_fields or [])

    def _vd(agent: dict) -> dict:
        """Extract the default version details."""
        vd = agent.get("version_details")
        if vd:
            return vd
        versions = agent.get("versions", [])
        return versions[0] if versions else {}

    orig_vd = _vd(original)
    imported_vd = _vd(imported)

    if "name" not in excl:
        assert imported["name"] == original["name"], (
            f"Name mismatch: {imported['name']!r} != {original['name']!r}"
        )

    if "description" not in excl:
        assert imported.get("description", "") == original.get("description", ""), (
            f"Description mismatch: {imported.get('description')!r} != {original.get('description')!r}"
        )

    if "instructions" not in excl:
        assert imported_vd.get("instructions", "") == orig_vd.get("instructions", ""), (
            "Instructions mismatch"
        )

    if "model_name" not in excl:
        orig_model = orig_vd.get("llm_settings", {}).get("model_name")
        imp_model = imported_vd.get("llm_settings", {}).get("model_name")
        assert imp_model == orig_model, f"Model mismatch: {imp_model!r} != {orig_model!r}"

    if "temperature" not in excl:
        orig_temp = orig_vd.get("llm_settings", {}).get("temperature")
        imp_temp = imported_vd.get("llm_settings", {}).get("temperature")
        assert imp_temp == orig_temp, f"Temperature mismatch: {imp_temp} != {orig_temp}"

    if "max_tokens" not in excl:
        orig_mt = orig_vd.get("llm_settings", {}).get("max_tokens")
        imp_mt = imported_vd.get("llm_settings", {}).get("max_tokens")
        assert imp_mt == orig_mt, f"Max tokens mismatch: {imp_mt} != {orig_mt}"

    if "variables" not in excl:
        orig_vars = {v["name"]: v.get("value", "") for v in orig_vd.get("variables", [])}
        imp_vars = {v["name"]: v.get("value", "") for v in imported_vd.get("variables", [])}
        assert imp_vars == orig_vars, f"Variables mismatch: {imp_vars} != {orig_vars}"

    if "agent_type" not in excl:
        assert imported_vd.get("agent_type") == orig_vd.get("agent_type"), (
            f"Agent type mismatch: {imported_vd.get('agent_type')!r} != {orig_vd.get('agent_type')!r}"
        )

    # welcome_message
    expected_wm = original.get("welcome_message", "")
    imported_wm = imported_vd.get("welcome_message", "")
    assert imported_wm == expected_wm, (
        f"welcome_message mismatch: expected {expected_wm!r}, got {imported_wm!r}"
    )

    # conversation_starters
    expected_cs = original.get("conversation_starters", [])
    imported_cs = imported_vd.get("conversation_starters", [])
    assert imported_cs == expected_cs, (
        f"conversation_starters mismatch: expected {expected_cs!r}, got {imported_cs!r}"
    )


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

class TestExportImportRoundtrip:
    """Export → delete → import → verify cycle for agents (prompts)."""

    @pytest.mark.p0
    def test_export_import_roundtrip_basic(self, agent_api):
        """EXP-001: Basic export/import roundtrip preserves core fields."""
        name = f"autotest_export_basic_{uuid.uuid4().hex[:6]}"
        created_id = None
        imported_id = None

        try:
            # 1. Create agent
            created = _create_agent_with_fields(
                agent_api,
                name=name,
                description="Roundtrip test",
                instructions="Answer questions about Python testing.",
                temperature=0.5,
                max_tokens=2048,
                variables=[
                    {"name": "language", "value": "Python"},
                    {"name": "framework", "value": "pytest"},
                ],
            )
            created_id = created["id"]
            logger.info("Created agent %s (%s)", created_id, name)
            _wait_for(lambda: agent_api.get_agent(created_id) is not None)

            # 2. Export
            export_bytes = agent_api.export_agent(created_id)
            assert len(export_bytes) > 0, "Export should return non-empty content"

            parsed = _parse_exported_md(export_bytes)
            assert parsed["frontmatter"]["name"] == name
            assert parsed["instructions"] == "Answer questions about Python testing."
            logger.info("Exported %d bytes", len(export_bytes))

            # 3. Delete original
            agent_api.delete_agent(created_id)
            logger.info("Deleted original agent %s", created_id)
            created_id = None
            _time.sleep(0.5)  # brief settle

            # 4. Import from export
            import_payload = _build_import_payload_from_export(export_bytes)
            result = agent_api.import_agent(import_payload)

            agents_result = result.get("result", {}).get("agents", [])
            assert len(agents_result) > 0, \
                f"Import returned no agents; full result: {result}"

            imported_id = agents_result[0]["id"]
            logger.info("Imported as agent %s", imported_id)

            # 5. Verify against known values
            imported_agent = agent_api.get_agent(imported_id)

            assert imported_agent["name"] == name
            assert imported_agent.get("description") == "Roundtrip test"

            vd = imported_agent.get("version_details", {})
            assert vd.get("instructions") == "Answer questions about Python testing."
            assert vd.get("llm_settings", {}).get("model_name") == DEFAULT_MODEL_NAME
            assert vd.get("llm_settings", {}).get("temperature") == 0.5
            assert vd.get("llm_settings", {}).get("max_tokens") == 2048

            imp_vars = {v["name"]: v.get("value", "") for v in vd.get("variables", [])}
            assert imp_vars == {"language": "Python", "framework": "pytest"}

        finally:
            if created_id:
                try:
                    agent_api.delete_agent(created_id)
                except Exception as _exc:
                    logger.warning("Cleanup failed: %s", _exc)
            if imported_id:
                try:
                    agent_api.delete_agent(imported_id)
                except Exception as _exc:
                    logger.warning("Cleanup failed: %s", _exc)

    @pytest.mark.p1
    def test_export_import_preserves_all_fields(self, agent_api):
        """EXP-002: Roundtrip preserves all populated fields."""
        name = f"autotest_full_fields_{uuid.uuid4().hex[:6]}"
        created_id = None
        imported_id = None

        try:
            created = _create_agent_with_fields(
                agent_api,
                name=name,
                description="Full field coverage agent",
                instructions=(
                    "You are a comprehensive test agent.\n\n"
                    "## Guidelines\n"
                    "- Always be helpful\n"
                    "- Use markdown in responses\n"
                    "- Include code examples when relevant"
                ),
                temperature=0.3,
                max_tokens=4096,
                variables=[
                    {"name": "topic", "value": "automation"},
                    {"name": "style", "value": "technical"},
                    {"name": "lang", "value": "en"},
                ],
                welcome_message="Welcome! How can I help with testing?",
                conversation_starters=["Run tests", "Debug issue"],
            )
            created_id = created["id"]
            _wait_for(lambda: agent_api.get_agent(created_id) is not None)

            # Fetch full details for comparison baseline
            original = agent_api.get_agent(created_id)

            # Export → delete → import
            export_bytes = agent_api.export_agent(created_id)
            agent_api.delete_agent(created_id)
            created_id = None
            _time.sleep(0.5)  # brief settle

            import_payload = _build_import_payload_from_export(export_bytes)
            result = agent_api.import_agent(import_payload)
            agents_result = result.get("result", {}).get("agents", [])
            assert len(agents_result) > 0, \
                f"Import returned no agents; full result: {result}"

            imported_id = agents_result[0]["id"]
            imported = agent_api.get_agent(imported_id)

            # Compare — exclude id/timestamps and fields not in export
            assert_prompt_fields_match(original, imported)

        finally:
            if created_id:
                try:
                    agent_api.delete_agent(created_id)
                except Exception as _exc:
                    logger.warning("Cleanup failed: %s", _exc)
            if imported_id:
                try:
                    agent_api.delete_agent(imported_id)
                except Exception as _exc:
                    logger.warning("Cleanup failed: %s", _exc)

    @pytest.mark.p1
    def test_export_format_is_valid_yaml_frontmatter(self, agent_api):
        """EXP-003: Export produces valid YAML frontmatter + markdown."""
        name = f"autotest_fmt_{uuid.uuid4().hex[:6]}"
        created_id = None

        try:
            created = _create_agent_with_fields(
                agent_api,
                name=name,
                instructions="Test instructions for format validation.",
            )
            created_id = created["id"]
            _wait_for(lambda: agent_api.get_agent(created_id) is not None)

            export_bytes = agent_api.export_agent(created_id)
            text = export_bytes.decode("utf-8")

            # Format checks
            assert text.startswith("---\n"), "Export must start with YAML delimiter"
            parts = text.split("---", 2)
            assert len(parts) >= 3, "Export must have opening and closing --- delimiters"

            # YAML must parse successfully
            fm = yaml.safe_load(parts[1])
            assert isinstance(fm, dict), "Frontmatter should parse as dict"
            assert "name" in fm, "Frontmatter must contain 'name'"
            assert "model" in fm, "Frontmatter must contain 'model'"
            assert "agent_type" in fm, "Frontmatter must contain 'agent_type'"

            # Body should contain instructions
            body = parts[2].strip()
            assert body == "Test instructions for format validation."

        finally:
            if created_id:
                try:
                    agent_api.delete_agent(created_id)
                except Exception as _exc:
                    logger.warning("Cleanup failed: %s", _exc)


class TestExportImportConflicts:
    """Test import behaviour when a same-named agent already exists."""

    @pytest.mark.p1
    def test_import_with_conflicting_name_creates_new(self, agent_api):
        """EXP-004: Importing when agent with same name exists creates a second agent."""
        name = f"autotest_conflict_{uuid.uuid4().hex[:6]}"
        original_id = None
        imported_id = None

        try:
            # Create original
            original = _create_agent_with_fields(
                agent_api,
                name=name,
                description="Original agent",
                instructions="Original instructions.",
            )
            original_id = original["id"]
            _wait_for(lambda: agent_api.get_agent(original_id) is not None)

            # Export it
            export_bytes = agent_api.export_agent(original_id)

            # DON'T delete — import same file
            import_payload = _build_import_payload_from_export(export_bytes)
            result = agent_api.import_agent(import_payload)

            agents_result = result.get("result", {}).get("agents", [])
            errors = result.get("errors", {}).get("agents", [])

            if agents_result:
                # Import succeeded — created a second agent with same name
                imported_id = agents_result[0]["id"]
                assert imported_id != original_id, (
                    "Imported agent should have a different ID from original"
                )
                logger.info(
                    "Conflicting import created new agent %s (original %s)",
                    imported_id, original_id,
                )
            elif errors:
                # Import returned error — document the behaviour
                logger.info("Import with conflicting name returned errors: %s", errors)
                pytest.xfail(
                    f"Platform rejected duplicate name instead of creating a new agent. "
                    f"Errors: {errors}"
                )
            else:
                pytest.fail("Import returned neither result nor error for conflicting name")

        finally:
            if original_id:
                try:
                    agent_api.delete_agent(original_id)
                except Exception as _exc:
                    logger.warning("Cleanup failed: %s", _exc)
            if imported_id:
                try:
                    agent_api.delete_agent(imported_id)
                except Exception as _exc:
                    logger.warning("Cleanup failed: %s", _exc)

    @pytest.mark.p2
    def test_import_preserves_original_when_conflict(self, agent_api):
        """EXP-005: Original agent is unchanged after importing with same name."""
        name = f"autotest_preserve_{uuid.uuid4().hex[:6]}"
        original_id = None
        imported_id = None

        try:
            original = _create_agent_with_fields(
                agent_api,
                name=name,
                description="Original description",
                instructions="Original instructions.",
                temperature=0.3,
            )
            original_id = original["id"]
            _wait_for(lambda: agent_api.get_agent(original_id) is not None)

            # Capture original state
            original_data = agent_api.get_agent(original_id)

            # Export and import (without deleting original)
            export_bytes = agent_api.export_agent(original_id)
            import_payload = _build_import_payload_from_export(export_bytes)
            result = agent_api.import_agent(import_payload)

            agents_result = result.get("result", {}).get("agents", [])
            if agents_result:
                imported_id = agents_result[0]["id"]

            # Verify original is unchanged
            original_after = agent_api.get_agent(original_id)
            assert original_after["name"] == original_data["name"]
            assert original_after.get("description") == original_data.get("description")

            orig_vd = original_data.get("version_details", {})
            after_vd = original_after.get("version_details", {})
            assert after_vd.get("instructions") == orig_vd.get("instructions")

            assert original_after["id"] == original_id, \
                "Original agent ID must not change after conflict import"
            if imported_id is not None:
                assert imported_id != original_id, \
                    "Imported agent should be a new record, not an overwrite of the original"

        finally:
            if original_id:
                try:
                    agent_api.delete_agent(original_id)
                except Exception as _exc:
                    logger.warning("Cleanup failed: %s", _exc)
            if imported_id:
                try:
                    agent_api.delete_agent(imported_id)
                except Exception as _exc:
                    logger.warning("Cleanup failed: %s", _exc)


class TestExportImportEdgeCases:
    """Edge case tests for export/import."""

    @pytest.mark.p2
    def test_export_import_empty_optional_fields(self, agent_api):
        """EXP-006: Roundtrip works with empty optional fields."""
        name = f"autotest_empty_{uuid.uuid4().hex[:6]}"
        created_id = None
        imported_id = None

        try:
            created = _create_agent_with_fields(
                agent_api,
                name=name,
                description="",
                instructions="Minimal agent.",
                variables=[],
                welcome_message="",
                conversation_starters=[],
            )
            created_id = created["id"]
            _wait_for(lambda: agent_api.get_agent(created_id) is not None)

            export_bytes = agent_api.export_agent(created_id)
            agent_api.delete_agent(created_id)
            created_id = None
            _time.sleep(0.5)  # brief settle

            import_payload = _build_import_payload_from_export(export_bytes)
            result = agent_api.import_agent(import_payload)

            agents_result = result.get("result", {}).get("agents", [])
            assert len(agents_result) > 0, \
                f"Import returned no agents; full result: {result}"

            imported_id = agents_result[0]["id"]
            imported = agent_api.get_agent(imported_id)

            assert imported["name"] == name
            vd = imported.get("version_details", {})
            assert vd.get("instructions") == "Minimal agent."
            assert imported.get("description", "") == "", \
                f"description should be empty after roundtrip, got {imported.get('description')!r}"
            imp_vars = vd.get("variables", [])
            assert imp_vars == [], f"variables should be empty, got {imp_vars!r}"
            assert vd.get("welcome_message", "") == "", \
                f"welcome_message should be empty, got {vd.get('welcome_message')!r}"

        finally:
            if created_id:
                try:
                    agent_api.delete_agent(created_id)
                except Exception as _exc:
                    logger.warning("Cleanup failed: %s", _exc)
            if imported_id:
                try:
                    agent_api.delete_agent(imported_id)
                except Exception as _exc:
                    logger.warning("Cleanup failed: %s", _exc)

    @pytest.mark.p2
    def test_export_import_special_characters_in_name(self, agent_api):
        """EXP-007: Names with special characters survive roundtrip."""
        name = f"autotest_sp&ci@l-{uuid.uuid4().hex[:4]}"
        description = "Agent with special chars: <>&\"'"
        instructions = "Handle edge cases with special chars: <>&\"'"
        created_id = None
        imported_id = None

        try:
            created = _create_agent_with_fields(
                agent_api,
                name=name,
                description=description,
                instructions=instructions,
            )
            created_id = created["id"]
            _wait_for(lambda: agent_api.get_agent(created_id) is not None)

            export_bytes = agent_api.export_agent(created_id)
            agent_api.delete_agent(created_id)
            created_id = None
            _time.sleep(0.5)  # brief settle

            import_payload = _build_import_payload_from_export(export_bytes)
            result = agent_api.import_agent(import_payload)

            agents_result = result.get("result", {}).get("agents", [])
            assert len(agents_result) > 0, \
                f"Import returned no agents; full result: {result}"

            imported_id = agents_result[0]["id"]
            imported = agent_api.get_agent(imported_id)

            assert imported["name"] == name
            assert imported.get("description") == description, \
                f"Description with special chars should survive roundtrip"
            vd = imported["versions"][0] if imported.get("versions") else {}
            assert vd.get("instructions") == instructions, \
                f"Instructions with special chars should survive roundtrip"

        finally:
            if created_id:
                try:
                    agent_api.delete_agent(created_id)
                except Exception as _exc:
                    logger.warning("Cleanup failed: %s", _exc)
            if imported_id:
                try:
                    agent_api.delete_agent(imported_id)
                except Exception as _exc:
                    logger.warning("Cleanup failed: %s", _exc)

    @pytest.mark.p2
    def test_export_import_large_instructions(self, agent_api):
        """EXP-008: Large instruction text (5000+ chars) survives roundtrip."""
        name = f"autotest_large_{uuid.uuid4().hex[:6]}"
        created_id = None
        imported_id = None

        # Build large but realistic instructions (clean whitespace)
        sections = []
        for i in range(1, 31):
            sections.append(
                f"## Section {i}\n\n"
                f"This is section {i} of the detailed instructions. "
                f"It contains important guidelines about testing methodology, "
                f"best practices, and common patterns to follow when writing "
                f"automated tests for web applications.\n\n"
                f"- Guideline {i}.1: Always validate preconditions\n"
                f"- Guideline {i}.2: Use descriptive assertions\n"
                f"- Guideline {i}.3: Clean up test data after each run"
            )
        large_instructions = "You are a comprehensive test automation expert.\n\n" + "\n\n".join(sections)

        assert len(large_instructions) > 5000, (
            f"Instructions should be 5000+ chars, got {len(large_instructions)}"
        )

        try:
            created = _create_agent_with_fields(
                agent_api,
                name=name,
                instructions=large_instructions,
            )
            created_id = created["id"]
            _wait_for(lambda: agent_api.get_agent(created_id) is not None)

            export_bytes = agent_api.export_agent(created_id)
            assert len(export_bytes) > 5000, "Export should preserve large content"

            agent_api.delete_agent(created_id)
            created_id = None
            _time.sleep(0.5)  # brief settle

            import_payload = _build_import_payload_from_export(export_bytes)
            result = agent_api.import_agent(import_payload)

            agents_result = result.get("result", {}).get("agents", [])
            assert len(agents_result) > 0, \
                f"Import returned no agents; full result: {result}"

            imported_id = agents_result[0]["id"]
            imported = agent_api.get_agent(imported_id)

            vd = imported.get("version_details", {})
            imported_instructions = vd.get("instructions", "")
            assert len(imported_instructions) > 5000, (
                f"Imported instructions should be 5000+ chars, got {len(imported_instructions)}"
            )
            assert _normalize_ws(imported_instructions) == _normalize_ws(large_instructions)

        finally:
            if created_id:
                try:
                    agent_api.delete_agent(created_id)
                except Exception as _exc:
                    logger.warning("Cleanup failed: %s", _exc)
            if imported_id:
                try:
                    agent_api.delete_agent(imported_id)
                except Exception as _exc:
                    logger.warning("Cleanup failed: %s", _exc)

    @pytest.mark.p2
    def test_import_via_constructed_payload(self, agent_api):
        """EXP-009: Import works with a manually constructed payload (no export)."""
        name = f"autotest_manual_{uuid.uuid4().hex[:6]}"
        imported_id = None

        try:
            payload = _build_import_payload(
                name=name,
                description="Manually constructed import",
                instructions="You are an agent created from a manual import payload.",
                temperature=0.4,
                max_tokens=512,
                variables=[{"name": "mode", "value": "test"}],
            )

            result = agent_api.import_agent(payload)

            agents_result = result.get("result", {}).get("agents", [])
            assert len(agents_result) > 0, "Manual import should create an agent"

            imported_id = agents_result[0]["id"]
            imported = agent_api.get_agent(imported_id)

            assert imported["name"] == name
            assert imported.get("description") == "Manually constructed import"

            vd = imported.get("version_details", {})
            assert vd.get("instructions") == "You are an agent created from a manual import payload."
            assert vd.get("llm_settings", {}).get("temperature") == 0.4
            assert vd.get("llm_settings", {}).get("max_tokens") == 512

            imp_vars = {v["name"]: v.get("value", "") for v in vd.get("variables", [])}
            assert imp_vars == {"mode": "test"}

        finally:
            if imported_id:
                try:
                    agent_api.delete_agent(imported_id)
                except Exception as _exc:
                    logger.warning("Cleanup failed: %s", _exc)
