"""Local conftest for unit tests.

Overrides the session-level autouse cleanup fixtures from the root conftest
so that unit tests run without requiring Keycloak authentication or any
browser/API infrastructure.
"""
import pytest


@pytest.fixture(scope="session", autouse=True)
def cleanup_autotest_pipelines_at_end():
    """No-op override: unit tests don't need API cleanup."""
    yield


@pytest.fixture(scope="session", autouse=True)
def cleanup_leaked_credentials():
    """No-op override: unit tests don't need API cleanup."""
    yield


@pytest.fixture(scope="session", autouse=True)
def cleanup_leaked_toolkits_at_end():
    """No-op override: unit tests don't need API cleanup."""
    yield


@pytest.fixture(scope="session", autouse=True)
def cleanup_autotest_agents_at_end():
    """No-op override: unit tests don't need API cleanup."""
    yield


@pytest.fixture(scope="session", autouse=True)
def cleanup_all_conversations_at_end():
    """No-op override: unit tests don't need API cleanup."""
    yield
