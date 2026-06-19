"""Toolkit configuration registry for parameterized tests.

Defines the ``ToolkitConfig`` and ``CredentialConfig`` dataclasses that
capture all per-toolkit differences (API payloads, UI form fields, test
expectations) and a ``TOOLKIT_CONFIGS`` registry mapping toolkit IDs to
their configurations.

Usage::

    from toolkit_configs import TOOLKIT_CONFIGS, ToolkitConfig

    cfg = TOOLKIT_CONFIGS["github"]
    print(cfg.display_name)      # "GitHub"
    print(cfg.credential.type)   # "github"
"""

import os
from dataclasses import dataclass, field

from config import settings


@dataclass
class CredentialConfig:
    """Configuration for creating a credential via API."""
    type: str                          # "github", "jira", "bitbucket", etc.
    env_token_var: str                 # e.g. "GITHUB_TOKEN", "JIRA_API_KEY"
    create_payload_fn: str             # name of factory function
    auth_fields: dict = field(default_factory=dict)  # extra fields like base_url


@dataclass
class ToolkitConfig:
    """Complete configuration for one toolkit type's test run."""
    # Identity
    toolkit_type: str                  # API type value: "github", "jira", etc.
    display_name: str                  # Human name: "GitHub", "Jira", etc.
    category: str                      # "Code Repositories", "Project Management", etc.
    url_slug: str                      # URL path segment: "github", "jira", etc.

    # Credential
    credential: CredentialConfig

    # Toolkit creation (API payload)
    settings_fn: str                   # factory function name for toolkit settings dict

    # UI form fields (for UI creation test)
    ui_card_text: str                  # Text to click on the toolkit card
    ui_form_fields: dict               # field_label -> value mapping for UI form fill

    # Test Settings panel
    test_tool_name: str                # tool to select in Test Settings, e.g. "List branches"
    test_tool_result_indicator: str    # text expected in result, e.g. "list_branches_in_repo"
    test_tool_result_content: str      # expected content, e.g. '"main"'

    # Chat integration
    chat_message: str                  # message to send in chat
    chat_response_keywords: list[str]  # keywords expected in AI response

    # Optional fields
    test_tool_params: dict = field(default_factory=dict)  # field_label -> value for tool params
    credential_check: dict = field(default_factory=dict)  # {url, auth_env_vars} for pre-validation
    extra_form_fields: dict = field(default_factory=dict)
    skip_reason: str = ""              # if set, pytest.skip() with this reason


TOOLKIT_CONFIGS = {
    "github": ToolkitConfig(
        toolkit_type="github",
        display_name="GitHub",
        category="Code Repositories",
        url_slug="github",
        credential=CredentialConfig(
            type="github",
            env_token_var="GIT_HUB_TOKEN",
            create_payload_fn="create_github_credential_payload",
            auth_fields={"base_url": "https://api.github.com"},
        ),
        settings_fn="github_toolkit_settings",
        ui_card_text="GitHub",
        ui_form_fields={
            "Repository": "EliteaAI/elitea-testing",
        },
        test_tool_name="List branches",
        test_tool_result_indicator="list_branches_in_repo",
        test_tool_result_content='"main"',
        chat_message="List branches in the repository",
        chat_response_keywords=["branch", "found", "repository"],
    ),

    "jira": ToolkitConfig(
        toolkit_type="jira",
        display_name="Jira",
        category="Project Management",
        url_slug="jira",
        credential=CredentialConfig(
            type="jira",
            env_token_var="JIRA_API_KEY",
            create_payload_fn="create_jira_credential_payload",
            auth_fields={"base_url": settings.jira_base_url},
        ),
        settings_fn="jira_toolkit_settings",
        ui_card_text="Jira",
        ui_form_fields={},
        test_tool_name="List projects",
        test_tool_result_indicator="list_projects",
        test_tool_result_content="project",
        chat_message="List all Jira projects",
        chat_response_keywords=["project", "jira"],
    ),

    "gitlab": ToolkitConfig(
        toolkit_type="gitlab",
        display_name="GitLab",
        category="Code Repositories",
        url_slug="gitlab",
        credential=CredentialConfig(
            type="gitlab",
            env_token_var="GITLAB_PRIVATE_TOKEN",
            create_payload_fn="create_gitlab_credential_payload",
            auth_fields={"url": settings.gitlab_url},
        ),
        settings_fn="gitlab_toolkit_settings",
        ui_card_text="GitLab",
        ui_form_fields={
            "Repository": settings.gitlab_repository,
        },
        test_tool_name="List branches",
        test_tool_result_indicator="list_branches_in_repo",
        test_tool_result_content="do-not-delete-test-branch",
        chat_message="List branches in the repository",
        chat_response_keywords=["branch", "repository"],
    ),

    "bitbucket": ToolkitConfig(
        toolkit_type="bitbucket",
        display_name="Bitbucket",
        category="Code Repositories",
        url_slug="bitbucket",
        credential=CredentialConfig(
            type="bitbucket",
            env_token_var="BITBUCKET_TOKEN",
            create_payload_fn="create_bitbucket_credential_payload",
            auth_fields={"url": "https://api.bitbucket.org"},
        ),
        settings_fn="bitbucket_toolkit_settings",
        ui_card_text="Bitbucket",
        ui_form_fields={
            "Project": "elitea-automation",
            "Repository": "automation",
        },
        test_tool_name="List branches",
        test_tool_result_indicator="list_branches_in_repo",
        test_tool_result_content='"master"',  # Bitbucket default branch is often "master"
        credential_check={
            "url": "https://api.bitbucket.org/2.0/user",
            "auth_type": "basic",
            "username_env": "BITBUCKET_USERNAME",
            "password_env": "BITBUCKET_TOKEN",
        },
        chat_message="List branches in the repository",
        chat_response_keywords=["branch", "repository"],
    ),

    "confluence": ToolkitConfig(
        toolkit_type="confluence",
        display_name="Confluence",
        category="Documentation",
        url_slug="confluence",
        credential=CredentialConfig(
            type="confluence",
            env_token_var="CONFLUENCE_API_KEY",
            create_payload_fn="create_confluence_credential_payload",
            auth_fields={"base_url": "https://your-instance.atlassian.net/wiki"},
        ),
        settings_fn="confluence_toolkit_settings",
        ui_card_text="Confluence",
        ui_form_fields={
            "Space": "ELITEATEST",
        },
        test_tool_name="List pages",
        test_tool_result_indicator="list_pages_with_label",
        test_tool_result_content="page",
        test_tool_params={"Label": "test"},
        chat_message="Use the list_pages_with_label tool to list pages with label 'test' in Confluence",
        chat_response_keywords=["page", "list", "label"],
    ),
}
