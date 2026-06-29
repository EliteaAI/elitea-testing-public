"""Centralised settings for the Elitea test automation suite.

Loads from ``automation/.env.test`` using pydantic-settings.  The source
priority is:
  1. ``init`` values (hardcoded overrides — never used in practice)
  2. ``.env.test`` file  ← authoritative for local test runs
  3. System environment variables  ← allow CI to override if needed

This means ``.env.test`` wins over any stale system env vars, which prevents
the common failure mode where an expired token in the shell environment
silently overrides the value in the file.

Usage::

    from config import settings

    token = settings.github_token
    url   = settings.elitea_url
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_ENV_FILE = Path(__file__).parent / ".env.test"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",          # tolerate any extra keys (future-proofing)
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    elitea_url: str = ""
    elitea_api_base: str = ""
    elitea_api_token: str = ""
    elitea_project_id: int = 0

    @property
    def elitea_auth_url(self) -> str:
        """URL for authentication.

        If elitea_url is localhost, extracts auth URL from elitea_api_base.
        This allows testing UI on localhost while authenticating against dev/stage.
        """
        if "localhost" in self.elitea_url or "127.0.0.1" in self.elitea_url:
            # Extract base URL from API base (e.g., https://dev.elitea.ai/api/v2 -> https://dev.elitea.ai)
            if self.elitea_api_base:
                from urllib.parse import urlparse
                parsed = urlparse(self.elitea_api_base)
                return f"{parsed.scheme}://{parsed.netloc}"
        return self.elitea_url

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------
    test_user_email: str = ""
    test_user_password: str = ""

    # ------------------------------------------------------------------
    # Browser
    # ------------------------------------------------------------------
    headless: bool = False
    # Window position for headed mode: "x,y" (e.g., "1920,0" for second monitor)
    # Leave empty to use default (opens on active monitor)
    browser_window_position: str = ""
    # Playwright traces: set PLAYWRIGHT_TRACES=true to enable.
    # Off by default; safe to enable locally for debugging failures.
    playwright_traces: bool = False

    # ------------------------------------------------------------------
    # GitHub toolkit
    # ------------------------------------------------------------------
    git_hub_token: str = ""
    github_base_url: str = "https://api.github.com"
    git_repo: str = "EliteaAI/elitea-testing"
    github_repo: str = "EliteaAI/elitea-testing"

    # ------------------------------------------------------------------
    # Jira toolkit
    # ------------------------------------------------------------------
    jira_base_url: str = ""
    jira_username: str = ""
    jira_api_key: str = ""

    # ------------------------------------------------------------------
    # GitLab toolkit
    # ------------------------------------------------------------------
    gitlab_url: str = ""
    gitlab_private_token: str = ""
    gitlab_repository: str = ""
    gitlab_base_branch: str = "main"

    # ------------------------------------------------------------------
    # Bitbucket toolkit
    # ------------------------------------------------------------------
    bitbucket_token: str = ""
    bitbucket_url: str = "https://api.bitbucket.org"
    bitbucket_username: str = ""
    bitbucket_project: str = ""
    bitbucket_repository: str = ""

    # ------------------------------------------------------------------
    # Azure DevOps toolkit
    # ------------------------------------------------------------------
    ado_token: str = ""
    ado_repository_id: str = ""
    ado_organization_url: str = ""
    ado_project: str = ""
    ado_org: str = ""

    # ------------------------------------------------------------------
    # Confluence toolkit
    # ------------------------------------------------------------------
    confluence_base_url: str = ""
    confluence_username: str = ""
    confluence_api_key: str = ""
    confluence_space: str = "ELITEATEST"

    # ------------------------------------------------------------------
    # Xray toolkit
    # ------------------------------------------------------------------
    xray_base_url: str = "https://eu.xray.cloud.getxray.app/"
    xray_client_id: str = ""
    xray_client_secret: str = ""

    # ------------------------------------------------------------------
    # Zephyr toolkit
    # ------------------------------------------------------------------
    zephyr_api_key: str = ""
    zephyr_essential_base_url: str = "https://prod-api.zephyr4jiracloud.com/v2"
    zephyr_esentials_key: str = ""

    # ------------------------------------------------------------------
    # Postman toolkit
    # ------------------------------------------------------------------
    postman_base_url: str = "https://api.getpostman.com"
    postman_workspace_id: str = ""
    postman_api_key: str = ""

    # ------------------------------------------------------------------
    # Default LLM settings for API-created agents / pipelines
    # ------------------------------------------------------------------
    default_model_name: str = ""
    default_model_project_id: int = 0

    # ------------------------------------------------------------------
    # Source priority: .env.test beats system env vars
    # ------------------------------------------------------------------
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        # dotenv_settings (the .env.test file) is placed before env_settings
        # (system environment) so the file always takes precedence.
        return (init_settings, dotenv_settings, env_settings, file_secret_settings)


settings = Settings()

