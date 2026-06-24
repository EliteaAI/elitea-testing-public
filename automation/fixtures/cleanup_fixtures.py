"""Cleanup fixtures that run at session end to remove leaked test data.

These fixtures run automatically after all tests complete (autouse=True)
to ensure no test data is left behind, even if tests crash or fail before
their teardown runs.

All cleanup fixtures follow the pattern:
1. yield (let tests run first)
2. List all entities matching test name pattern
3. Delete each entity, logging successes and failures
4. Report final cleanup statistics

Fixtures:
- cleanup_autotest_pipelines_at_end: Delete autotest_ pipelines
- cleanup_leaked_credentials: Delete ALL credentials (aggressive cleanup)
- cleanup_autotest_agents_at_end: Delete autotest_ agents
- cleanup_all_conversations_at_end: Delete ALL conversations (aggressive cleanup)

Note: Some cleanups are aggressive (delete ALL) because the test environment
is ephemeral and should start fresh each session.

Note: Cleanup is skipped when running against localhost because browser cookies
are not available for API authentication. Tests should clean up their own data.
"""
import logging

import pytest

# Import API client types for type hints
from api import AgentAPI, ConversationAPI, CredentialAPI, PipelineAPI, ToolkitAPI
from config import settings

logger = logging.getLogger("elitea.automation.fixtures.cleanup")


def _is_localhost() -> bool:
    """Check if running against localhost (no API auth available)."""
    url = settings.elitea_url or ""
    return "localhost" in url or "127.0.0.1" in url


@pytest.fixture(scope="session", autouse=True)
def cleanup_autotest_pipelines_at_end(pipeline_api: PipelineAPI):
    """Delete all autotest_ pipelines at the end of the test session.

    Catches pipelines created outside the pipeline_id fixture or leaked
    by test failures. Only deletes pipelines with names starting with
    "autotest_" to avoid touching production data.

    Args:
        pipeline_api: PipelineAPI client (from api_fixtures)

    Note:
        Runs automatically after all tests (autouse=True).
        Failures are logged but don't fail the test session.
        Skipped when running against localhost (no API auth).
    """
    yield  # Let all tests run first

    if _is_localhost():
        logger.info("Pipeline cleanup: skipped (localhost mode)")
        return

    try:
        data = pipeline_api.list_pipelines()
        rows = data.get("rows", [])
        autotest_pipelines = [p for p in rows if p.get("name", "").startswith("autotest_")]
        count = len(autotest_pipelines)

        if count == 0:
            logger.info("Pipeline cleanup: 0 autotest pipelines remaining")
            return

        logger.info("Pipeline cleanup: deleting %d autotest pipeline(s)...", count)
        deleted = 0
        for pipeline in autotest_pipelines:
            try:
                pipeline_api.delete_pipeline(pipeline["id"])
                deleted += 1
            except Exception as exc:
                logger.warning("  Failed to delete pipeline %s: %s", pipeline["id"], exc)

        logger.info("Pipeline cleanup complete: deleted %d/%d pipelines", deleted, count)

    except Exception as exc:
        logger.error("Pipeline cleanup failed: %s", exc)


@pytest.fixture(scope="session", autouse=True)
def cleanup_leaked_credentials(_browser_cookies):
    """Session-level safety net: delete ALL credentials after test run.

    AGGRESSIVE CLEANUP: Deletes every credential in the test environment,
    not just autotest_ prefixed ones. This is appropriate because:
    - Test environment is ephemeral
    - Credentials shouldn't persist across sessions
    - UI can auto-create credentials during navigation

    Catches credentials leaked by:
    - Failed tests (fixture cleanup skipped)
    - UI auto-creation during navigation
    - Interrupted test runs

    Two-layer cleanup pattern:
    1. Per-test: create → use → delete (in test's fixture)
    2. Session: catch everything at the end (this fixture)

    Args:
        _browser_cookies: Browser cookies for API authentication

    Note:
        Creates a fresh CredentialAPI instance for cleanup to ensure
        it has its own connection pool separate from test execution.
    """
    yield  # Let all tests run first

    if _is_localhost():
        logger.info("Credential cleanup: skipped (localhost mode)")
        return

    # Final cleanup: delete everything (fetch ALL pages)
    api = CredentialAPI(browser_cookies=_browser_cookies)
    try:
        items = api.list_all_credentials()

        if items:
            logger.warning(
                "Session cleanup: Found %d leaked credentials, deleting all...",
                len(items)
            )
            for c in items:
                try:
                    api.delete_credential(c["id"])
                except Exception as e:
                    logger.error("Failed to delete credential %s: %s", c.get("id"), e)
        else:
            logger.info("Session cleanup: No leaked credentials found")
    finally:
        api.close()


@pytest.fixture(scope="session", autouse=True)
def cleanup_leaked_toolkits_at_end(_browser_cookies):
    """Session-level safety net: delete ALL toolkits after test run.

    AGGRESSIVE CLEANUP: Deletes every toolkit in the test environment.
    Toolkit tests create many toolkits that can outlive their per-test fixtures
    on failure or interruption.

    Args:
        _browser_cookies: Browser cookies for API authentication

    Note:
        Creates a fresh ToolkitAPI instance for cleanup to ensure
        it has its own connection pool separate from test execution.
    """
    yield  # Let all tests run first

    if _is_localhost():
        logger.info("Toolkit cleanup: skipped (localhost mode)")
        return

    api = ToolkitAPI(browser_cookies=_browser_cookies)
    try:
        items = api.list_all_toolkits()

        if items:
            logger.warning(
                "Session cleanup: Found %d leaked toolkit(s), deleting all...",
                len(items)
            )
            for t in items:
                try:
                    api.delete_toolkit(t["id"])
                except Exception as e:
                    logger.error("Failed to delete toolkit %s: %s", t.get("id"), e)
        else:
            logger.info("Session cleanup: No leaked toolkits found")
    finally:
        api.close()


@pytest.fixture(scope="session", autouse=True)
def cleanup_autotest_agents_at_end(agent_api: AgentAPI):
    """Delete all autotest_ agents at the end of the test session.

    Catches agents created outside the agent_id fixture or leaked by
    test failures. Only deletes agents with names starting with
    "autotest_" to avoid touching production data.

    Args:
        agent_api: AgentAPI client (from api_fixtures)

    Note:
        Runs automatically after all tests (autouse=True).
        Failures are logged but don't fail the test session.
        Skipped when running against localhost (no API auth).
    """
    yield  # Let all tests run first

    if _is_localhost():
        logger.info("Agent cleanup: skipped (localhost mode)")
        return

    try:
        data = agent_api.list_agents()
        rows = data.get("rows", [])
        autotest_agents = [a for a in rows if a.get("name", "").startswith("autotest_")]
        count = len(autotest_agents)

        if count == 0:
            logger.info("Agent cleanup: 0 autotest agents remaining")
            return

        logger.info("Agent cleanup: deleting %d autotest agent(s)...", count)
        deleted = 0
        for agent in autotest_agents:
            try:
                agent_api.delete_agent(agent["id"])
                deleted += 1
            except Exception as exc:
                logger.warning("  Failed to delete agent %s: %s", agent["id"], exc)

        logger.info("Agent cleanup complete: deleted %d/%d agents", deleted, count)

    except Exception as exc:
        logger.error("Agent cleanup failed: %s", exc)


@pytest.fixture(scope="session", autouse=True)
def cleanup_all_conversations_at_end(conversation_api: ConversationAPI):
    """Delete ALL conversations at the end of the test session.

    AGGRESSIVE CLEANUP: Deletes every conversation in the test environment,
    not just autotest_ prefixed ones. This is appropriate because:
    - Test environment is ephemeral
    - Conversations shouldn't persist across sessions
    - UI can auto-create conversations during navigation

    Catches conversations created outside of the conversation_id fixture
    (e.g., by UI auto-creation, parallel sessions, or leaked test data).

    Args:
        conversation_api: ConversationAPI client (from api_fixtures)

    Note:
        Runs automatically after all tests (autouse=True).
        Failures are logged but don't fail the test session.
        Skipped when running against localhost (no API auth).
    """
    yield  # Let all tests run first

    if _is_localhost():
        logger.info("Conversation cleanup: skipped (localhost mode)")
        return

    # Teardown: delete everything
    try:
        data = conversation_api.list_conversations()
        conversations = data.get("rows", [])
        count = len(conversations)

        if count == 0:
            logger.info("Session cleanup: 0 conversations remaining")
            return

        logger.info("Session cleanup: deleting %d conversation(s)...", count)
        deleted = 0
        for conv in conversations:
            conv_id = conv["id"]
            conv_name = conv.get("name", "(no name)")
            try:
                conversation_api.delete_conversation(conv_id)
                deleted += 1
                logger.debug("  Deleted conversation %s (%s)", conv_id, conv_name)
            except Exception as exc:
                logger.warning("  Failed to delete %s: %s", conv_id, exc)

        logger.info("Session cleanup complete: deleted %d/%d conversations", deleted, count)

    except Exception as exc:
        logger.error("Session cleanup failed: %s", exc)
