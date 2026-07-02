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
- invalid_jira_credential: Jira credential with invalid/expired token
- jira_toolkit_with_invalid_credential: Jira toolkit using invalid credential
- invalid_github_credential: GitHub credential with invalid token
- github_toolkit_with_invalid_credential: GitHub toolkit using invalid credential
"""
import logging
import time

import pytest

from api import ArtifactAPI, ConversationAPI, AgentAPI, PipelineAPI, CredentialAPI, ToolkitAPI
from config import settings

logger = logging.getLogger("elitea.automation.fixtures.data")

# Branch used to configure the GitHub toolkit and to verify toolkit responses.
_GITHUB_BRANCH = "main"


@pytest.fixture
def conversation_id(conversation_api: ConversationAPI, request):
    """Create a fresh conversation before the test and delete it afterwards.

    The conversation is created via the API with a unique name based on
    the test function name. This ensures complete isolation between tests.

    Yields the conversation ID as a string so tests can navigate to
    ``/app/chat/{conversation_id}`` or use it with the API.

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
    ``/app/agents/all/{agent_id}`` or use it with the API.

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
    ``/app/pipelines/all/{pipeline_id}`` or use it with the API.

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

    yield {"id": toolkit["id"], "name": name, "bucket_name": bucket_name}

    try:
        toolkit_api.delete_toolkit(toolkit["id"])
        logger.info("Deleted artifact toolkit %s", toolkit["id"])
    except Exception as exc:
        logger.warning("Failed to delete artifact toolkit %s: %s", toolkit["id"], exc)


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
