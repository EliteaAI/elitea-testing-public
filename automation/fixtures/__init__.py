"""Fixture modules for Elitea test automation.

Fixtures are organized by responsibility (Single Responsibility Principle):

- session_fixtures: Browser, authentication, test run metadata (session scope)
- api_fixtures: API clients for different services (session/function scope)
- data_fixtures: Test data factories — conversation_id, agent_id, github_toolkit, etc.
                 (function scope). All entity creation/teardown belongs here.
- cleanup_fixtures: Bulk cleanup hooks and teardown logic (session scope, autouse)

## Rule: No fixtures in test files

All fixtures must live in this fixtures/ directory and be registered in conftest.py.
Test files contain only test functions and test-local constants (timeouts, etc.).

Rationale: fixtures defined inside test files cannot be shared across test modules
and violate single responsibility — a test file should only contain test logic.

All fixtures are imported in the main conftest.py so pytest can discover them.
"""
