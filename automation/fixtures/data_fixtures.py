"""Test data fixtures that create and cleanup test entities.

These fixtures use the API clients to create fresh test data for each test,
ensuring complete isolation between tests. Each fixture follows the pattern:
1. Create entity with unique name (based on test name)
2. Yield entity ID (or data dict) to test
3. Delete entity in teardown (even if test fails)

All fixtures are function-scoped, meaning each test gets a fresh entity.

Fixtures:
- conversation_id: Fresh conversation per test
- agent_id: Fresh agent per test
- pipeline_id: Fresh empty pipeline per test
- pipeline_with_llm_id: Fresh executable pipeline with LLM node
- github_credential: GitHub API credential (skipped if GITHUB_TOKEN unset)
- github_toolkit: GitHub toolkit attached to a fresh credential
- github_toolkit_with_selected_tools: GitHub toolkit with settings.selected_tools
  set (required for the pipeline Toolkit node's Tool select to render)
- github_relevant_agents: GitHub-relevant Agent pair (selected/not_selected)
- github_relevant_skills: GitHub-relevant Skill pair (selected/not_selected)
- invalid_jira_credential: Jira credential with invalid/expired token
- jira_toolkit_with_invalid_credential: Jira toolkit using invalid credential
- invalid_github_credential: GitHub credential with invalid token
- github_toolkit_with_invalid_credential: GitHub toolkit using invalid credential
"""
import logging
import time

import pytest
from api import AgentAPI, APIClient, ArtifactAPI, ConversationAPI, CredentialAPI, PipelineAPI, SkillAPI, ToolkitAPI
from config import settings
from pages.guardrails_admin_page import GuardrailsAdminPage
from playwright.sync_api import Browser

logger = logging.getLogger("elitea.automation.fixtures.data")

# Branch used to configure the GitHub toolkit and to verify toolkit responses.
_GITHUB_BRANCH = "main"


@pytest.fixture
def conversation_id(conversation_api: ConversationAPI, request):
    """Create a fresh conversation before the test and delete it afterwards.

    The conversation is created via the API with a unique name based on
    the test function name. This ensures complete isolation between tests.

    Yields the conversation ID as a string so tests can navigate to
    ``/chat/{conversation_id}`` or use it with the API.

    Args:
        conversation_api: ConversationAPI client (from api_fixtures)
        request: Pytest request object (provides test metadata)

    Yields:
        str: Numeric conversation ID as string

    Example:
        def test_send_message(page, conversation_id):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)
            chat.send_message("Hello")
            # conversation is automatically deleted after test
    """
    name = f"autotest_{request.node.name}"[:32]  # API enforces 32-char max
    conv = conversation_api.create_conversation(name)
    conv_id = conv["id"]
    logger.info("Created conversation %s (%s) for %s", conv_id, name, request.node.name)

    yield str(conv_id)

    # Cleanup: delete conversation even if test fails
    try:
        conversation_api.delete_conversation(conv_id)
        logger.info("Deleted conversation %s", conv_id)
    except Exception as exc:
        logger.warning("Failed to delete conversation %s: %s", conv_id, exc)


@pytest.fixture
def agent_id(agent_api: AgentAPI, request):
    """Create a fresh agent before the test and delete it afterwards.

    The agent is created via the API with:
    - Unique name based on test function name
    - Basic description
    - Default instructions

    Yields the agent ID as an integer so tests can navigate to
    ``/agents/all/{agent_id}`` or use it with the API.

    Args:
        agent_api: AgentAPI client (from api_fixtures)
        request: Pytest request object (provides test metadata)

    Yields:
        int: Numeric agent ID

    Example:
        def test_agent_detail(page, agent_id):
            detail_page = AgentDetailPage(page)
            detail_page.navigate(agent_id)
            # agent is automatically deleted after test
    """
    name = f"autotest_{request.node.name}"[:32]  # API enforces 32-char max
    description = f"Auto-created for test {request.node.name}"
    agent = agent_api.create_agent(name, description, instructions="You are a test agent.")
    aid = agent["id"]
    logger.info("Created agent %s (%s) for %s", aid, name, request.node.name)

    yield aid

    # Cleanup: delete agent even if test fails
    try:
        agent_api.delete_agent(aid)
        logger.info("Deleted agent %s", aid)
    except Exception as exc:
        logger.warning("Failed to delete agent %s: %s", aid, exc)


@pytest.fixture
def pipeline_id(pipeline_api: PipelineAPI, request):
    """Create a fresh empty pipeline before the test and delete it afterwards.

    The pipeline is created via the API with a unique name based on the
    test function name. The pipeline starts empty (no nodes or connections).

    Yields the numeric pipeline ID so tests can navigate to
    ``/pipelines/all/{pipeline_id}`` or use it with the API.

    Args:
        pipeline_api: PipelineAPI client (from api_fixtures)
        request: Pytest request object (provides test metadata)

    Yields:
        int: Numeric pipeline ID

    Example:
        def test_pipeline_editor(page, pipeline_id):
            editor = PipelineEditorPage(page)
            editor.navigate(pipeline_id)
            editor.add_node("llm")
            # pipeline is automatically deleted after test
    """
    name = f"autotest_{request.node.name}"[:32]  # API enforces 32-char max
    description = f"Auto-created for test {request.node.name}"
    pipeline = pipeline_api.create_pipeline(name, description)
    pid = pipeline["id"]
    logger.info("Created pipeline %s (%s) for %s", pid, name, request.node.name)

    yield pid

    # Cleanup: delete pipeline even if test fails
    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete pipeline %s: %s", pid, exc)


@pytest.fixture
def pipeline_with_llm_id(pipeline_api: PipelineAPI, request):
    """Create a pipeline with a single LLM node connected to END.

    This pipeline can actually execute — it receives a user message via
    the LLM node and produces a response. Useful for testing pipeline
    execution, chat integration, and end-to-end flows.

    The pipeline structure:
    - START node
    - LLM node (connected to START)
    - END node (connected to LLM)

    Yields the numeric pipeline ID so tests can execute or navigate to it.

    Args:
        pipeline_api: PipelineAPI client (from api_fixtures)
        request: Pytest request object (provides test metadata)

    Yields:
        int: Numeric pipeline ID

    Example:
        def test_pipeline_execution(page, pipeline_with_llm_id):
            chat = ChatPage(page)
            chat.navigate_to_pipeline_chat(pipeline_with_llm_id)
            chat.send_message("Hello")
            chat.wait_for_ai_response()
            # pipeline is automatically deleted after test
    """
    name = f"autotest_{request.node.name}"[:32]  # Truncate to 32 chars
    description = f"Auto-created LLM pipeline for test {request.node.name}"
    pipeline = pipeline_api.create_pipeline_with_llm_node(name, description)
    pid = pipeline["id"]
    logger.info("Created LLM pipeline %s (%s) for %s", pid, name, request.node.name)

    yield pid

    # Cleanup: delete pipeline even if test fails
    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted LLM pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete LLM pipeline %s: %s", pid, exc)


@pytest.fixture
def github_credential(credential_api: CredentialAPI, request):
    """Create a GitHub API credential and yield its metadata.

    Skips the test if ``GITHUB_TOKEN`` is not set in the environment
    (loaded from ``.env.test``).

    Yields a dict with ``id`` and ``elitea_title`` keys.
    Deletes the credential in teardown even if the test fails.

    Args:
        credential_api: CredentialAPI client (from api_fixtures)
        request: Pytest request object (provides test metadata)

    Yields:
        dict: ``{"id": int, "elitea_title": str}``
    """
    if not settings.git_hub_token:
        pytest.skip("GIT_HUB_TOKEN not set in .env.test")

    name = f"autotest_gh_cred_{request.node.name}"[:32]
    cred = credential_api.create_github_credential(
        display_name=name,
        base_url=settings.github_base_url,
        token=settings.git_hub_token,
    )
    logger.info("Created GitHub credential %s (%s) for %s", cred["id"], name, request.node.name)

    yield {"id": cred["id"], "elitea_title": cred["elitea_title"]}

    try:
        credential_api.delete_credential(cred["id"])
        logger.info("Deleted GitHub credential %s", cred["id"])
    except Exception as exc:
        logger.warning("Failed to delete credential %s during teardown: %s", cred["id"], exc)


@pytest.fixture
def github_toolkit(github_credential: dict, toolkit_api: ToolkitAPI, request):
    """Create a GitHub toolkit linked to a fresh credential.

    Depends on ``github_credential`` — both are cleaned up after the test.
    The toolkit is configured against ``_GITHUB_REPO`` / ``_GITHUB_BRANCH``.

    Yields a dict with ``id``, ``name``, and ``branch`` keys so tests can
    assert that the known branch appears in toolkit responses without needing
    to import module-level constants.

    Args:
        github_credential: GitHub credential fixture (provides elitea_title)
        toolkit_api: ToolkitAPI client (from api_fixtures)
        request: Pytest request object (provides test metadata)

    Yields:
        dict: ``{"id": int, "name": str, "branch": str}``
    """
    name = f"autotest_gh_toolkit_{request.node.name}"[:32]
    toolkit = toolkit_api.create_github_toolkit(
        name=name,
        description=f"Auto-created for test {request.node.name}",
        credential_elitea_title=github_credential["elitea_title"],
        repository=settings.git_repo,
        active_branch=_GITHUB_BRANCH,
        base_branch=_GITHUB_BRANCH,
    )
    logger.info("Created GitHub toolkit %s (%s) for %s", toolkit["id"], name, request.node.name)

    yield {"id": toolkit["id"], "name": name, "branch": _GITHUB_BRANCH}

    try:
        toolkit_api.delete_toolkit(toolkit["id"])
        logger.info("Deleted GitHub toolkit %s", toolkit["id"])
    except Exception as exc:
        logger.warning("Failed to delete toolkit %s during teardown: %s", toolkit["id"], exc)


@pytest.fixture
def github_toolkit_with_selected_tools(github_credential: dict, toolkit_api: ToolkitAPI, request):
    """Create a GitHub toolkit with ``settings.selected_tools`` explicitly set.

    Sibling of :func:`github_toolkit` — that fixture does NOT set
    ``selected_tools``, which is fine for toolkit-attach/agent flows but is a
    load-bearing gap for the pipeline Toolkit node (ELITEA-2010 AFS §
    Preconditions / Automation Hints): a toolkit with no ``selected_tools``
    renders a Toolkit node with no Tool select at all (0 options, absent
    from the DOM, confirmed live) — the node's Tool dropdown reads the
    toolkit's own ``settings.selected_tools``, not a dynamic "discover all
    tools" call. This fixture selects ``search_issues`` (1 required param —
    SEARCH QUERY — plus 2 optional — MAX COUNT / REPO NAME), matching the
    AFS's Test Data.

    Depends on ``github_credential`` — both are cleaned up after the test.

    Yields a dict with ``id``, ``name``, and ``branch`` keys — same shape as
    :func:`github_toolkit`.

    Args:
        github_credential: GitHub credential fixture (provides elitea_title)
        toolkit_api: ToolkitAPI client (from api_fixtures)
        request: Pytest request object (provides test metadata)

    Yields:
        dict: ``{"id": int, "name": str, "branch": str}``
    """
    name = f"autotest_gh_tk_tools_{request.node.name}"[:32]
    toolkit = toolkit_api.create_github_toolkit(
        name=name,
        description=f"Auto-created for test {request.node.name}",
        credential_elitea_title=github_credential["elitea_title"],
        repository=settings.git_repo,
        active_branch=_GITHUB_BRANCH,
        base_branch=_GITHUB_BRANCH,
        selected_tools=["search_issues"],
    )
    logger.info(
        "Created GitHub toolkit %s (%s, selected_tools=['search_issues']) for %s",
        toolkit["id"], name, request.node.name,
    )

    yield {"id": toolkit["id"], "name": name, "branch": _GITHUB_BRANCH}

    try:
        toolkit_api.delete_toolkit(toolkit["id"])
        logger.info("Deleted GitHub toolkit %s", toolkit["id"])
    except Exception as exc:
        logger.warning("Failed to delete toolkit %s during teardown: %s", toolkit["id"], exc)


# ---------------------------------------------------------------------------
# GitHub-relevant Agent pair for ELITEA-1909 ("Build with AI" suggested-Agent
# precondition)
# ---------------------------------------------------------------------------

def _build_with_ai_agent_payload(name: str, description: str) -> dict:
    """Payload for a minimal Agent used purely as a "Build with AI"
    suggestion-engine candidate (never opened/edited by the test itself).

    Uses ``AgentAPI.create_agent_full()`` rather than the ``create_agent()``
    convenience method's default ``llm_settings`` (which pairs
    ``temperature`` with ``reasoning_effort``) — that combination is
    rejected with a 400 by this project's current default model. See the
    ELITEA-1909 AFS's Known Defects/Gaps #3.
    """
    return {
        "name": name,
        "description": description,
        "type": "interface",
        "versions": [
            {
                "name": "base",
                "tags": [],
                "instructions": description,
                "variables": [],
                "tools": [],
                "llm_settings": {
                    "max_tokens": -1,
                    "model_name": settings.default_model_name,
                    "model_project_id": settings.default_model_project_id,
                },
                "conversation_starters": [],
                "agent_type": "openai",
                "welcome_message": "",
                "meta": {"step_limit": 25},
            }
        ],
    }


@pytest.fixture
def github_relevant_agents(agent_api: AgentAPI, request):
    """Create two pre-existing, GitHub-relevant Agents so "Build with AI"'s
    suggestion engine has real candidates to surface as ``suggested_agents``
    — the engine only suggests Agents already configured in the project,
    filtered by semantic relevance to the submitted prompt (see ELITEA-1909
    AFS Preconditions — the case's own preconditions never state this).

    Yields a dict with ``selected`` and ``not_selected`` sub-dicts, each
    ``{"id": int, "name": str, "description": str}`` — the caller's test
    prompt must name both agents by their exact ``name`` for the
    suggestion engine's relevance match to pick them up (see AFS
    Automation Hints: fixture descriptions and the test prompt are
    co-maintained in the same test module for this reason).

    Both agents are deleted in teardown even if the test fails.
    """
    # Distinctive, collision-resistant naming (AFS Automation Hints): a
    # short numeric suffix rather than the full (often >32-char) test node
    # name, which the API's 32-char name limit can't accommodate anyway.
    suffix = str(int(time.time() * 1000))[-6:]
    selected_name = f"autotest GH Issue Bot {suffix}"[:32]
    not_selected_name = f"autotest GH PR Reviewer {suffix}"[:32]
    selected_description = "Agent that manages GitHub issues and pull requests for a repository."
    not_selected_description = "Agent that reviews GitHub pull requests and posts review comments."

    selected = agent_api.create_agent_full(
        _build_with_ai_agent_payload(selected_name, selected_description)
    )
    not_selected = agent_api.create_agent_full(
        _build_with_ai_agent_payload(not_selected_name, not_selected_description)
    )
    logger.info(
        "Created GitHub-relevant agent pair %s (%s) / %s (%s) for %s",
        selected["id"], selected_name, not_selected["id"], not_selected_name,
        request.node.name,
    )

    yield {
        "selected": {
            "id": selected["id"], "name": selected_name, "description": selected_description,
        },
        "not_selected": {
            "id": not_selected["id"], "name": not_selected_name, "description": not_selected_description,
        },
    }

    for agent in (selected, not_selected):
        try:
            agent_api.delete_agent(agent["id"])
            logger.info("Deleted GitHub-relevant agent %s", agent["id"])
        except Exception as exc:
            logger.warning("Failed to delete agent %s during teardown: %s", agent["id"], exc)


# ---------------------------------------------------------------------------
# GitHub-relevant Skill pair for ELITEA-1911 ("Build with AI" suggested-Skill
# precondition — same shape as github_relevant_agents above)
# ---------------------------------------------------------------------------


@pytest.fixture
def github_relevant_skills(skill_api: SkillAPI, request):
    """Create two pre-existing, GitHub-relevant Skills so "Build with AI"'s
    suggestion engine has real candidates to surface as ``suggested_skills``
    — the engine only suggests Skills already configured in the project,
    filtered by semantic relevance to the submitted prompt (see ELITEA-1911
    AFS Preconditions — same inventory-gating mechanism ``github_relevant_agents``
    already documents for Toolkits/Agents).

    Yields a dict with ``selected`` and ``not_selected`` sub-dicts, each
    ``{"id": int, "name": str, "description": str}`` — the caller's test
    prompt must name both skills by their exact ``name`` for the suggestion
    engine's relevance match to pick them up (mirrors
    ``github_relevant_agents``'s Automation Hints).

    Skill names are constrained (live-confirmed via the Skills UI form's
    validation message, see ``SkillAPI.create_skill()``) to lowercase
    letters, digits, and hyphens, max 32 characters, no leading/trailing
    hyphen — the generated names respect this.

    Both skills are deleted in teardown even if the test fails.
    """
    suffix = str(int(time.time() * 1000))[-6:]
    selected_name = f"autotest-gh-changelog-{suffix}"[:32]
    not_selected_name = f"autotest-gh-issue-label-{suffix}"[:32]
    selected_description = (
        "Skill that writes GitHub repository changelog entries from merged pull requests."
    )
    not_selected_description = (
        "Skill that reads GitHub issues and applies priority/severity labels automatically."
    )
    selected_instructions = (
        "You are a skill that reads merged GitHub pull requests and writes concise "
        "changelog entries summarizing the changes."
    )
    not_selected_instructions = (
        "You are a skill that reads incoming GitHub issues and applies priority and "
        "severity labels based on their content."
    )

    selected = skill_api.create_skill(selected_name, selected_description, selected_instructions)
    not_selected = skill_api.create_skill(
        not_selected_name, not_selected_description, not_selected_instructions
    )
    logger.info(
        "Created GitHub-relevant skill pair %s (%s) / %s (%s) for %s",
        selected["id"], selected_name, not_selected["id"], not_selected_name,
        request.node.name,
    )

    yield {
        "selected": {
            "id": selected["id"], "name": selected_name, "description": selected_description,
        },
        "not_selected": {
            "id": not_selected["id"], "name": not_selected_name, "description": not_selected_description,
        },
    }

    for skill in (selected, not_selected):
        try:
            skill_api.delete_skill(skill["id"])
            logger.info("Deleted GitHub-relevant skill %s", skill["id"])
        except Exception as exc:
            logger.warning("Failed to delete skill %s during teardown: %s", skill["id"], exc)


# ---------------------------------------------------------------------------
# Artifact bucket + toolkit fixtures for ELITEA-1327
# ---------------------------------------------------------------------------


@pytest.fixture
def artifact_bucket(artifact_api: ArtifactAPI, request):
    """Create a fresh artifact bucket before the test and delete it afterwards.

    The bucket is created with a unique name based on the test function name
    and a millisecond timestamp to guarantee uniqueness across parallel or
    repeated runs.

    Yields a dict with ``name`` and ``id`` keys.

    Args:
        artifact_api: ArtifactAPI client (from api_fixtures)
        request: Pytest request object (provides test metadata)

    Yields:
        dict: ``{"name": str, "id": str}``

    Example:
        def test_bucket_files(page, artifact_bucket):
            bucket_name = artifact_bucket["name"]
            # bucket is automatically deleted after test
    """
    ts = str(int(time.time() * 1000))[-6:]  # last 6 digits for brevity
    # Bucket names: lowercase, hyphens only, max ~63 chars
    raw = f"autotest-{request.node.name}"
    safe = raw.lower().replace("_", "-").replace("[", "").replace("]", "")[:40]
    name = f"{safe}-{ts}"

    bucket = artifact_api.create_bucket(name)
    logger.info("Created artifact bucket '%s' (id=%s) for %s", name, bucket.get("id"), request.node.name)

    yield {"name": name, "id": bucket.get("id", name)}

    try:
        artifact_api.delete_bucket(name)
        logger.info("Deleted artifact bucket '%s'", name)
    except Exception as exc:
        logger.warning("Failed to delete artifact bucket '%s': %s", name, exc)


@pytest.fixture
def artifact_toolkit(artifact_bucket: dict, toolkit_api: ToolkitAPI, request):
    """Create an Artifact toolkit connected to a fresh bucket.

    Depends on ``artifact_bucket`` — both are cleaned up after the test.

    Yields a dict with ``id``, ``name``, and ``bucket_name`` keys so tests
    can attach the toolkit to an agent by name and verify bucket contents.

    Args:
        artifact_bucket: Artifact bucket fixture (provides bucket name)
        toolkit_api: ToolkitAPI client (from api_fixtures)
        request: Pytest request object (provides test metadata)

    Yields:
        dict: ``{"id": int, "name": str, "bucket_name": str}``

    Example:
        def test_agent_creates_files(page, agent_id, artifact_toolkit):
            toolkit_name = artifact_toolkit["name"]
            bucket_name = artifact_toolkit["bucket_name"]
            # attach toolkit to agent via UI, then run assertions
    """
    ts = str(int(time.time()))
    raw = f"autotest-art-{request.node.name}"
    name = raw[:28] + f"-{ts[-4:]}"   # keep total ≤ 32 chars (API limit)

    bucket_name = artifact_bucket["name"]
    toolkit = toolkit_api.create_artifact_toolkit(
        name=name,
        description=f"Auto-created artifact toolkit for {request.node.name}",
        bucket_name=bucket_name,
    )
    logger.info(
        "Created artifact toolkit %s ('%s') → bucket '%s' for %s",
        toolkit["id"], name, bucket_name, request.node.name,
    )

    yield {
        "id": toolkit["id"],
        "name": name,
        "bucket_name": bucket_name,
        "project_id": int(toolkit_api.project_id),  # ELITEA-2203: slash-mention menu-item testids need it
    }

    try:
        toolkit_api.delete_toolkit(toolkit["id"])
        logger.info("Deleted artifact toolkit %s", toolkit["id"])
    except Exception as exc:
        logger.warning("Failed to delete artifact toolkit %s: %s", toolkit["id"], exc)


# ELITEA-2204's exact, narrow selected_tools list -- NOT create_artifact_toolkit()'s
# hardcoded 16-tool list, which would make the case's "exactly 4 tools, in this
# order" assertion false against the live default (AFS § Test Data).
_FOUR_TOOL_SELECTED_TOOLS = ["index_data", "list_indexes", "search_index", "stepback_search_index"]


@pytest.fixture
def artifact_toolkit_four_tools(artifact_bucket: dict, toolkit_api: ToolkitAPI, request):
    """Create an Artifact toolkit with EXACTLY 4 ``selected_tools`` (ELITEA-2204).

    ``artifact_toolkit`` (above) reuses ``create_artifact_toolkit()``, whose
    factory hardcodes a 16-tool ``selected_tools`` list -- unusable for a case
    that asserts the slash-mention tools list shows exactly 4, in configuration
    order. This fixture calls ``toolkit_api.create_toolkit()`` directly with
    the narrower list instead, keeping the same
    ``pgvector_configuration``/``embedding_model``/``bucket`` shape
    ``create_artifact_toolkit()`` already uses.

    Depends on ``artifact_bucket`` -- both are cleaned up after the test.

    Yields:
        dict: ``{"id": int, "name": str, "bucket_name": str, "project_id": int}``
    """
    ts = str(int(time.time()))
    raw = f"autotest-art4-{request.node.name}"
    name = raw[:28] + f"-{ts[-4:]}"  # keep total ≤ 32 chars (API limit)

    bucket_name = artifact_bucket["name"]
    toolkit = toolkit_api.create_toolkit(
        name=name,
        description=f"Auto-created 4-tool artifact toolkit for {request.node.name}",
        toolkit_type="artifact",
        settings={
            "pgvector_configuration": None,
            "embedding_model": "text-embedding-3-small",
            "bucket": bucket_name,
            "selected_tools": _FOUR_TOOL_SELECTED_TOOLS,
        },
    )
    logger.info(
        "Created 4-tool artifact toolkit %s ('%s') → bucket '%s' for %s",
        toolkit["id"], name, bucket_name, request.node.name,
    )

    yield {
        "id": toolkit["id"],
        "name": name,
        "bucket_name": bucket_name,
        "project_id": int(toolkit_api.project_id),
    }

    try:
        toolkit_api.delete_toolkit(toolkit["id"])
        logger.info("Deleted 4-tool artifact toolkit %s", toolkit["id"])
    except Exception as exc:
        logger.warning("Failed to delete 4-tool artifact toolkit %s: %s", toolkit["id"], exc)


# ---------------------------------------------------------------------------
# HITL sensitive-action fixtures for ELITEA-2211..2214 (direct toolkit call)
# ---------------------------------------------------------------------------


@pytest.fixture
def artifact_seeded_file(artifact_toolkit: dict, artifact_api: ArtifactAPI, request):
    """Seed one real file into ``artifact_toolkit``'s bucket.

    Gives Authorize/Block something genuine to act on so the backend-verified
    execution/non-execution checks (ELITEA-2212/2213/2214 — "assert via
    ArtifactAPI, not just a UI-only signal") have ground truth to compare
    against: Authorize should make this file disappear, Block should leave
    it in place. No separate teardown — the ``artifact_bucket`` fixture
    (a dependency of ``artifact_toolkit``) deletes the whole bucket.

    Yields:
        str: the file's key (relative path) inside the bucket.
    """
    bucket_name = artifact_toolkit["bucket_name"]
    file_key = f"autotest-hitl-{request.node.name}"[:60] + ".txt"
    artifact_api.upload_file(bucket_name, file_key, b"hitl automation seed file")
    logger.info("Seeded file '%s' in bucket '%s' for %s", file_key, bucket_name, request.node.name)
    return file_key


@pytest.fixture(scope="module")
def sensitive_delete_file_toolkit(browser: Browser, auth_state):
    """Mark ``artifact``/``delete_file`` sensitive for the whole test module.

    Sensitivity is toolkit-TYPE scoped
    (``GuardrailsAdminPage.add_sensitive_tool("artifact", "delete_file")``),
    not per-toolkit-instance, so marking/removing it ONCE per module (rather
    than once per test) avoids redundant admin round-trips across
    ELITEA-2211..2214's four cases, per those AFS's own Cleanup section —
    same pattern ``test_guardrails_live_reload.py``'s
    ``TestSensitiveToolLiveReload`` already established.

    Module scope means this fixture's setup/teardown run ONCE for whichever
    single test module requests it, even though it is centrally defined here
    (fixture location rule — ``.claude/rules/api-patterns.md``).
    """
    ctx = browser.new_context(
        storage_state=auth_state, viewport={"width": 1920, "height": 1080}
    )
    ctx.set_default_timeout(15000)
    ctx.set_default_navigation_timeout(30000)
    page = ctx.new_page()

    guardrails = GuardrailsAdminPage(page)
    guardrails.navigate_to_guardrails()
    guardrails.add_sensitive_tool("artifact", "delete_file")
    guardrails.save_configuration()
    logger.info("Marked artifact/delete_file sensitive for the module")

    yield

    try:
        guardrails.remove_sensitive_tool("delete_file")
        guardrails.save_configuration()
        logger.info("Removed artifact/delete_file from the sensitive list")
    except Exception as exc:
        logger.warning("Failed to remove sensitive tool 'delete_file' during teardown: %s", exc)
    finally:
        page.close()
        ctx.close()


# ---------------------------------------------------------------------------
# Invalid credential fixtures for testing bug #4906
# ---------------------------------------------------------------------------


@pytest.fixture
def invalid_jira_credential(credential_api: CredentialAPI, request):
    """Create a Jira credential with invalid/expired token.

    Uses a deliberately invalid API key to simulate expired credentials.
    The credential is created successfully, but authentication will fail
    when the toolkit tries to use it.

    Used for testing bug #4906 fix - warning messages for invalid credentials.

    Yields:
        dict: {"id": int, "elitea_title": str}
    """
    ts = str(int(time.time() * 1000))
    name = f"InvalidJira_{request.node.name}"[:32]

    payload = {
        "type": "jira",
        "elitea_title": f"invalid_jira_{ts}",
        "label": name,
        "data": {
            "base_url": settings.jira_base_url,
            "api_key": "invalid_expired_token_12345",
            "username": settings.jira_username or "test@example.com",
        },
        "shared": False,
    }

    cred = credential_api.create_credential(payload)
    logger.info("Created invalid Jira credential %s (%s)", cred["id"], name)

    yield {"id": cred["id"], "elitea_title": cred["elitea_title"]}

    try:
        credential_api.delete_credential(cred["id"])
        logger.info("Deleted invalid Jira credential %s", cred["id"])
    except Exception as exc:
        logger.warning("Failed to delete credential %s: %s", cred["id"], exc)


@pytest.fixture
def jira_toolkit_with_invalid_credential(
    invalid_jira_credential: dict,
    toolkit_api: ToolkitAPI,
    request,
):
    """Create a Jira toolkit that uses the invalid credential.

    The toolkit is created successfully, but when opened in UI,
    it should show an authentication warning.

    Used for testing bug #4906 fix.

    Yields:
        dict: {"id": int, "name": str}
    """
    ts = str(int(time.time()))
    name = f"InvalidJiraToolkit_{ts}"[:32]

    toolkit = toolkit_api.create_toolkit(
        name=name,
        description="Toolkit with invalid credentials for testing",
        toolkit_type="jira",
        settings={
            "jira_configuration": {
                "elitea_title": invalid_jira_credential["elitea_title"],
                "private": True,
            },
            "cloud": True,
            "limit": 5,
            "api_version": "Auto",
            "verify_ssl": True,
        },
    )
    logger.info("Created Jira toolkit with invalid credential: %s (%s)", toolkit["id"], name)

    yield {"id": toolkit["id"], "name": name}

    try:
        toolkit_api.delete_toolkit(toolkit["id"])
        logger.info("Deleted toolkit %s", toolkit["id"])
    except Exception as exc:
        logger.warning("Failed to delete toolkit %s: %s", toolkit["id"], exc)


@pytest.fixture
def invalid_github_credential(credential_api: CredentialAPI, request):
    """Create a GitHub credential with invalid token.

    Used for testing bug #4906 fix across different toolkit types.

    Yields:
        dict: {"id": int, "elitea_title": str}
    """
    ts = str(int(time.time() * 1000))
    name = f"InvalidGitHub_{request.node.name}"[:32]

    payload = {
        "type": "github",
        "elitea_title": f"invalid_github_{ts}",
        "label": name,
        "data": {
            "base_url": "https://api.github.com",
            "access_token": "ghp_invalidtoken123456789012345678901234",
        },
        "shared": False,
    }

    cred = credential_api.create_credential(payload)
    logger.info("Created invalid GitHub credential %s", cred["id"])

    yield {"id": cred["id"], "elitea_title": cred["elitea_title"]}

    try:
        credential_api.delete_credential(cred["id"])
        logger.info("Deleted invalid GitHub credential %s", cred["id"])
    except Exception as exc:
        logger.warning("Failed to delete credential %s: %s", cred["id"], exc)


@pytest.fixture
def github_toolkit_with_invalid_credential(
    invalid_github_credential: dict,
    toolkit_api: ToolkitAPI,
    request,
):
    """Create a GitHub toolkit with invalid credentials.

    Used for testing bug #4906 fix across different toolkit types.

    Yields:
        dict: {"id": int, "name": str}
    """
    ts = str(int(time.time()))
    name = f"InvalidGHToolkit_{ts}"[:32]

    toolkit = toolkit_api.create_toolkit(
        name=name,
        description="GitHub toolkit with invalid credentials",
        toolkit_type="github",
        settings={
            "github_configuration": {
                "elitea_title": invalid_github_credential["elitea_title"],
                "private": True,
            },
            "repository": "owner/repo",
            "active_branch": "main",
            "base_branch": "main",
        },
    )
    logger.info("Created GitHub toolkit with invalid credential: %s", toolkit["id"])

    yield {"id": toolkit["id"], "name": name}

    try:
        toolkit_api.delete_toolkit(toolkit["id"])
        logger.info("Deleted toolkit %s", toolkit["id"])
    except Exception as exc:
        logger.warning("Failed to delete toolkit %s: %s", toolkit["id"], exc)


# ---------------------------------------------------------------------------
# MCP toolkit + pipeline fixtures for ELITEA-1954
# ---------------------------------------------------------------------------

# Public, auth-free MCP endpoint used to provision a throwaway MCP toolkit
# with a real, non-empty tool list (3 tools: read_wiki_structure,
# read_wiki_contents, ask_question). Picked over the environment's
# pre-existing placeholder-URL MCPs (which return zero tools) and over
# "Remote Github" (whose live OAuth session is disconnected, though its
# CACHED tool list still renders) — see
# test-specs/pipelines/l2_mcp-node-change-toolkit-and-tool_ELITEA-1954.md
# § Test Data for the full rationale.
_MCP_DEEPWIKI_URL = "https://mcp.deepwiki.com/mcp"

# The environment's pre-existing "Remote Github" MCP toolkit — reused (not
# created/deleted by this fixture) because its cached tool list renders
# client-side without a live OAuth reconnection (ELITEA-1954 AFS § Test Data).
_REMOTE_GITHUB_TOOLKIT_NAME = "Remote Github"
_REMOTE_GITHUB_TOOLKIT_YAML_NAME = "RemoteGithub"
_REMOTE_GITHUB_TOOL = "search_repositories"


@pytest.fixture
def mcp_toolkit_with_tools(toolkit_api: ToolkitAPI, request):
    """Create a throwaway Remote MCP toolkit with a real, working tool list.

    Probes the public, auth-free ``mcp.deepwiki.com`` endpoint via
    ``ToolkitAPI.sync_mcp_tools`` (the same call the UI's "Load Tools"
    button makes) and bakes the result into the toolkit's
    ``settings.selected_tools`` / ``settings.available_mcp_tools`` at
    creation time, so a pipeline MCP node attached to this toolkit shows a
    real, non-empty Tool dropdown — a plain ``create_toolkit(type="mcp")``
    without a synced tool list does NOT populate the Tool dropdown (see
    ``ToolkitAPI.create_remote_mcp_toolkit`` docstring).

    Yields:
        dict: ``{"id": int, "name": str, "toolkit_name": str, "tools": list[str]}``
    """
    name = f"autotest_mcp_{request.node.name}"[:32]
    tools = toolkit_api.sync_mcp_tools(_MCP_DEEPWIKI_URL)
    assert tools, f"mcp_sync_tools returned no tools for {_MCP_DEEPWIKI_URL!r} — endpoint may be down"

    toolkit = toolkit_api.create_remote_mcp_toolkit(
        name=name,
        description=f"Auto-created MCP for test {request.node.name}",
        url=_MCP_DEEPWIKI_URL,
        tools=tools,
    )
    logger.info(
        "Created MCP toolkit %s (%s) with %d tools for %s",
        toolkit["id"], name, len(tools), request.node.name,
    )

    yield {
        "id": toolkit["id"],
        "name": name,
        "toolkit_name": toolkit.get("toolkit_name", name),
        "tools": [t["name"] for t in tools],
        "project_id": int(toolkit_api.project_id),  # ELITEA-2203: slash-mention menu-item testids need it
    }

    try:
        toolkit_api.delete_toolkit(toolkit["id"])
        logger.info("Deleted MCP toolkit %s", toolkit["id"])
    except Exception as exc:
        logger.warning("Failed to delete MCP toolkit %s: %s", toolkit["id"], exc)


@pytest.fixture
def mcp_pipeline_with_toolkits(
    mcp_toolkit_with_tools: dict, toolkit_api: ToolkitAPI, pipeline_api: PipelineAPI, request
):
    """Create a pipeline with an MCP node pre-configured with a Toolkit + Tool.

    Satisfies the ELITEA-1954 precondition: a pipeline with an MCP node
    already configured (Toolkit=``RemoteGithub``, Tool=``search_repositories``),
    with >=2 MCP toolkits attached in the pipeline's TOOLS section — both
    with real, non-empty tool lists (the environment's pre-existing
    "Remote Github" MCP, reused read-only, plus the fresh
    ``mcp_toolkit_with_tools`` fixture).

    Yields:
        dict: ``{"id": int, "name": str, "node_id": str, "toolkit_name": str,
        "tool": str, "other_toolkit_name": str, "other_tools": list[str]}``
        — the "other" fields describe the toolkit/tools the test switches TO.
    """
    # NOTE: not discovered via toolkit_api.list_all_toolkits() by name — that
    # listing endpoint returns an empty list on this environment regardless
    # of auth method (confirmed during ELITEA-1954 implementer Phase 2
    # exploration; a real API/environment quirk). The toolkit id is a fixed,
    # pre-existing environment resource instead (config.py
    # `remote_github_mcp_toolkit_id`, overridable via env).
    remote_github = toolkit_api.get_toolkit(settings.remote_github_mcp_toolkit_id)
    assert remote_github.get("name") == _REMOTE_GITHUB_TOOLKIT_NAME, (
        f"Environment precondition mismatch: toolkit id {settings.remote_github_mcp_toolkit_id} "
        f"is {remote_github.get('name')!r}, expected {_REMOTE_GITHUB_TOOLKIT_NAME!r} — "
        f"update `remote_github_mcp_toolkit_id` in config.py / .env.test if the environment's "
        f"Remote Github MCP toolkit id has changed."
    )
    assert _REMOTE_GITHUB_TOOL in (remote_github.get("settings", {}).get("selected_tools") or []), (
        f"{_REMOTE_GITHUB_TOOLKIT_NAME!r} toolkit no longer exposes tool {_REMOTE_GITHUB_TOOL!r} — "
        f"pick a different initial tool for the fixture's precondition node"
    )

    deepwiki_full = toolkit_api.get_toolkit(mcp_toolkit_with_tools["id"])

    name = f"autotest_pl_{request.node.name}"[:32]
    node_id = "MCP 1"
    pipeline = pipeline_api.create_pipeline_with_mcp_node(
        name=name,
        description=f"Auto-created MCP pipeline for test {request.node.name}",
        tools=[remote_github, deepwiki_full],
        toolkit_name=_REMOTE_GITHUB_TOOLKIT_YAML_NAME,
        tool=_REMOTE_GITHUB_TOOL,
        node_id=node_id,
    )
    pid = pipeline["id"]
    logger.info("Created MCP pipeline %s (%s) for %s", pid, name, request.node.name)

    yield {
        "id": pid,
        "name": name,
        "node_id": node_id,
        "toolkit_name": _REMOTE_GITHUB_TOOLKIT_YAML_NAME,
        "tool": _REMOTE_GITHUB_TOOL,
        "other_toolkit_name": mcp_toolkit_with_tools["toolkit_name"],
        "other_tools": mcp_toolkit_with_tools["tools"],
    }

    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted MCP pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete MCP pipeline %s: %s", pid, exc)


_HITL_RUNTIME_PRINTER_OUTPUT = "Final: pipeline approved"


def build_hitl_runtime_nodes(hitl_message: str) -> list[dict]:
    """Build the LLM 1 -> HITL 1 -> Printer 1 -> END node list for ELITEA-2015.

    HITL routes: APPROVE -> Printer 1, REJECT -> END (the case's stated
    precondition). Exposed as a plain function (not a fixture) so a test
    needing MORE THAN ONE independent instance — e.g. a fresh pipeline per
    Approve/Reject variant, per the AFS's Test isolation note — can call it
    directly via ``pipeline_api`` instead of duplicating the YAML.

    ``LLM 1``'s task is a real, non-empty fixed value (the analyst's
    exploration pipeline had an empty task, which is incidental to the
    precondition, not required by the case — see the AFS Test Data note) so
    the Reject-path evidence stays legible.

    Args:
        hitl_message: The HITL node's fixed user_message value.

    Returns:
        list[dict]: Node definitions for ``PipelineAPI.create_pipeline_with_nodes``.
    """
    return [
        {
            "id": "LLM 1",
            "type": "llm",
            "input": [],
            "input_mapping": {
                "chat_history": {"type": "fixed", "value": []},
                "system": {"type": "fixed", "value": ""},
                "task": {"type": "fixed", "value": "Say hello in one short sentence."},
            },
            "output": ["messages"],
            "structured_output": False,
            "transition": "HITL 1",
        },
        {
            "id": "HITL 1",
            "type": "hitl",
            "user_message": {"type": "fixed", "value": hitl_message},
            "input": [],
            "routes": {"approve": "Printer 1", "reject": "END"},
        },
        {
            "id": "Printer 1",
            "type": "printer",
            "input_mapping": {
                "printer": {"type": "fixed", "value": _HITL_RUNTIME_PRINTER_OUTPUT},
            },
            "transition": "END",
        },
    ]


@pytest.fixture
def hitl_runtime_pipeline(pipeline_api: PipelineAPI, request):
    """Create a pipeline LLM 1 -> HITL 1 -> Printer 1 -> END with HITL routes
    configured (APPROVE -> Printer 1, REJECT -> END).

    Satisfies the ELITEA-2015 precondition (see :func:`build_hitl_runtime_nodes`).

    Yields:
        dict: ``{"id": int, "hitl_message": str, "printer_output": str}``
    """
    name = f"autotest_hitl_{request.node.name}"[:32]
    hitl_message = "Please review this response"
    pipeline = pipeline_api.create_pipeline_with_nodes(
        name=name,
        description=f"Auto-created HITL runtime pipeline for test {request.node.name}",
        entry_point="LLM 1",
        nodes=build_hitl_runtime_nodes(hitl_message),
    )
    pid = pipeline["id"]
    logger.info("Created HITL runtime pipeline %s (%s) for %s", pid, name, request.node.name)

    yield {"id": pid, "hitl_message": hitl_message, "printer_output": _HITL_RUNTIME_PRINTER_OUTPUT}

    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted HITL runtime pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete HITL runtime pipeline %s: %s", pid, exc)


def _llm_node_dict(transition: str) -> dict:
    """Build the LLM 1 node dict shared by the canvas node/edge CRUD fixtures
    below (ELITEA-2018/2031/2032) — same shape confirmed live in the AFS
    exploration sessions for all three cases.

    Args:
        transition: The node's ``transition`` target (e.g. ``"Code 1"``,
            ``"Printer 1"``, ``"END"``).
    """
    return {
        "id": "LLM 1",
        "type": "llm",
        "input": [],
        "input_mapping": {
            "chat_history": {"type": "fixed", "value": []},
            "system": {"type": "fixed", "value": ""},
            "task": {"type": "fixed", "value": "hi"},
        },
        "output": ["messages"],
        "structured_output": False,
        "transition": transition,
    }


def build_delete_node_pipeline_nodes() -> list[dict]:
    """LLM 1 -> Code 1 -> END node list for ELITEA-2018 (Pipeline Canvas —
    Delete Node). Confirmed live (2026-08-03): produces exactly 3 nodes /
    2 edges on first canvas load, no manual UI wiring needed.
    """
    return [
        _llm_node_dict(transition="Code 1"),
        {
            "id": "Code 1",
            "type": "code",
            "input": [],
            "output": [],
            "code": "print('hi')",
            "transition": "END",
        },
    ]


@pytest.fixture
def pipeline_llm_code_end(pipeline_api: PipelineAPI, request):
    """Create a pipeline ``LLM 1 -> Code 1 -> END`` (3 nodes, 2 edges) before
    the test and delete it afterwards. Satisfies the ELITEA-2018 precondition
    (see :func:`build_delete_node_pipeline_nodes`).

    Yields:
        int: Numeric pipeline ID.
    """
    name = f"autotest_delnode_{request.node.name}"[:32]
    pipeline = pipeline_api.create_pipeline_with_nodes(
        name=name,
        description=f"Auto-created delete-node pipeline for test {request.node.name}",
        entry_point="LLM 1",
        nodes=build_delete_node_pipeline_nodes(),
    )
    pid = pipeline["id"]
    logger.info("Created delete-node pipeline %s (%s) for %s", pid, name, request.node.name)

    yield pid

    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted delete-node pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete delete-node pipeline %s: %s", pid, exc)


def _printer_node_dict(transition: str) -> dict:
    """Build the Printer 1 node dict shared by the edge-creation/-deletion
    fixtures below (ELITEA-2031/2032).

    Args:
        transition: The node's ``transition`` target (e.g. ``"END"``).
    """
    return {
        "id": "Printer 1",
        "type": "printer",
        "input_mapping": {"printer": {"type": "fixed", "value": "done"}},
        "transition": transition,
    }


def build_llm_printer_nodes(llm_transition: str) -> list[dict]:
    """Build an ``LLM 1`` + ``Printer 1`` node pair, parametrized on where
    ``LLM 1`` transitions to. Shared by the ELITEA-2031 (edge creation) and
    ELITEA-2032 (edge deletion) fixtures below — same node pair, differing
    only in whether LLM 1 already points at Printer 1.

    Args:
        llm_transition: ``LLM 1``'s ``transition`` value — ``"END"`` seeds
            two independently-terminating nodes (ELITEA-2031, so the edge
            under test doesn't pre-exist); ``"Printer 1"`` seeds the edge
            directly (ELITEA-2032, so the edge under test already exists).

    Returns:
        list[dict]: ``[LLM 1, Printer 1]`` node definitions.
    """
    return [
        _llm_node_dict(transition=llm_transition),
        _printer_node_dict(transition="END"),
    ]


@pytest.fixture
def pipeline_llm_printer_disconnected(pipeline_api: PipelineAPI, request):
    """Create a pipeline with ``LLM 1`` and ``Printer 1``, each independently
    ``transition: END`` (NOT connected to each other) before the test, and
    delete it afterwards. Satisfies the ELITEA-2031 precondition — omitting
    ``transition`` on both nodes entirely auto-defaults ``LLM 1`` to
    ``transition: Printer 1`` (the next node in the YAML list), which would
    pre-create the very edge this case tests the creation of; both must
    explicitly point at END.

    Yields:
        int: Numeric pipeline ID.
    """
    name = f"autotest_edgecreate_{request.node.name}"[:32]
    pipeline = pipeline_api.create_pipeline_with_nodes(
        name=name,
        description=f"Auto-created edge-creation pipeline for test {request.node.name}",
        entry_point="LLM 1",
        nodes=build_llm_printer_nodes(llm_transition="END"),
    )
    pid = pipeline["id"]
    logger.info("Created edge-creation pipeline %s (%s) for %s", pid, name, request.node.name)

    yield pid

    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted edge-creation pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete edge-creation pipeline %s: %s", pid, exc)


@pytest.fixture
def pipeline_llm_printer_connected(pipeline_api: PipelineAPI, request):
    """Create a pipeline ``LLM 1 -> Printer 1 -> END`` (the edge under test
    already exists) before the test, and delete it afterwards. Satisfies the
    ELITEA-2032 precondition.

    Yields:
        int: Numeric pipeline ID.
    """
    name = f"autotest_edgedelete_{request.node.name}"[:32]
    pipeline = pipeline_api.create_pipeline_with_nodes(
        name=name,
        description=f"Auto-created edge-deletion pipeline for test {request.node.name}",
        entry_point="LLM 1",
        nodes=build_llm_printer_nodes(llm_transition="Printer 1"),
    )
    pid = pipeline["id"]
    logger.info("Created edge-deletion pipeline %s (%s) for %s", pid, name, request.node.name)

    yield pid

    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted edge-deletion pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete edge-deletion pipeline %s: %s", pid, exc)


def _delete_project_context(client: APIClient) -> None:
    """Best-effort DELETE of the active project's Project Context.

    Tolerates HTTP 404 (``{"error": "Project context not found"}`` —
    confirmed live) — "already clean" is a pass, not a failure. Any other
    non-2xx status is re-raised so a real API problem is not swallowed.
    """
    path = f"/elitea_core/project_context/prompt_lib/{client.project_id}/project-context"
    resp = client.delete(path)
    if resp.status_code == 404:
        logger.info("Project Context already absent for project %s (404 — clean)", client.project_id)
        return
    resp.raise_for_status()
    logger.info("Deleted Project Context for project %s", client.project_id)


@pytest.fixture
def clean_project_context(api: APIClient):
    """Ensure the active project has no Project Context before AND after the test.

    Deletes via the API (tolerating 404 — "already clean" is a pass) both
    before the test runs (clean precondition for the empty-state "Create"
    flow) and after it finishes (teardown, restores the empty-state
    precondition for the next run) — ELITEA-2272.

    No corresponding "id" is yielded: this fixture's only job is the
    delete-before/delete-after bracket, not creating an entity.
    """
    _delete_project_context(api)

    yield

    try:
        _delete_project_context(api)
    except Exception as exc:
        logger.warning("Failed to delete Project Context in teardown: %s", exc)
