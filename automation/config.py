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
from typing import Optional

from pydantic import field_validator
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
    # Team project ID for multi-user tests (bucket permissions, sharing)
    # Team projects have "Manage permissions" feature, unlike private projects
    elitea_team_project_id: Optional[int] = 0

    # A project in which the acting test user genuinely holds the `admin`
    # role (ELITEA-2245/2247). Elitea roles are PROJECT-scoped, so switching
    # the sidebar selector to this project puts the app in a real,
    # product-computed admin state -- no injected permissions, no stub.
    # Verified live 2026-08-30 from the product's own
    # `GET /admin/users/prompt_lib/{id}` + `GET /auth/permissions/prompt_lib/{id}`:
    # 400 ("UI Testing") -> role `admin`, 360 permissions (8 `*secret*`);
    # 399 ("Private") -> `editor`+`viewer`, 299; 471 -> `viewer`, 158.
    # Deliberately a DISTINCT key from `users_team_project_id` /
    # `ai_providers_seeded_project_id` (same default, different precondition)
    # for the reason those two already state about each other: conflating
    # preconditions that merely share a value today silently breaks whichever
    # one moves first.
    elitea_admin_project_id: int = 400

    @field_validator('elitea_admin_project_id', mode='before')
    @classmethod
    def parse_admin_project_id(cls, v):
        """Handle empty string from CI environment variables."""
        if v is None or v == "":
            return 400
        return int(v)

    @field_validator('elitea_project_id', mode='before')
    @classmethod
    def parse_project_id(cls, v):
        """Parse project ID from string or int, allowing empty string to default to 0."""
        if v is None or v == "":
            return 0
        return int(v)

    @field_validator('elitea_team_project_id', mode='before')
    @classmethod
    def parse_team_project_id(cls, v):
        """Handle empty string from CI environment variables."""
        if v == '' or v is None:
            return 0
        return int(v)
    # URL prefix for the React app routes.  On deployed environments (DEV/STAGE/NEXT)
    # the React Router has basename="/app", so all routes are under /app.
    # On localhost the Vite dev server has no basename, so the prefix is empty.
    # Default is "" (empty) — all environments must set APP_PREFIX explicitly:
    #   APP_PREFIX=       for localhost
    #   APP_PREFIX=/app   for deployed envs (DEV/STAGE/NEXT)
    app_prefix: str = ""

    @property
    def app_base_url(self) -> str:
        """Base URL for page-object navigation (includes app prefix).

        Page objects call ``navigate("/skills/all")`` and this property
        provides the correct base so the final URL is correct on both
        localhost (no prefix) and deployed environments (/app prefix).
        """
        return f"{self.elitea_url.rstrip('/')}{self.app_prefix}"

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

    # Secondary user for multi-user tests (bucket permissions, sharing, etc.)
    # This user should exist in the Team project with limited/no admin rights
    test_user_b_email: str = ""
    test_user_b_password: str = ""

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
    git_repo: str = "EliteaAI/elitea-testing-public"
    github_repo: str = "EliteaAI/elitea-testing-public"

    # ------------------------------------------------------------------
    # MCP (ELITEA-1954)
    # ------------------------------------------------------------------
    # The environment's pre-existing "Remote Github" MCP toolkit id — reused
    # read-only by mcp_pipeline_with_toolkits (its cached tool list renders
    # client-side without a live OAuth reconnection). NOT discoverable via
    # ToolkitAPI.list_all_toolkits(): that endpoint returns an empty list on
    # this environment regardless of auth method (confirmed both via cookie
    # and Bearer session during ELITEA-1954 implementer Phase 2 exploration)
    # — a real API/environment quirk, not a test bug. Override via env if the
    # environment's Remote Github toolkit id ever changes.
    remote_github_mcp_toolkit_id: int = 3

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
    confluence_space: str = ""

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
    # Settings -> Users page test data (ELITEA-2292)
    # ------------------------------------------------------------------
    # A TEAM (non-private) project the acting test user belongs to, confirmed
    # live to carry existing users — Settings -> Users is hidden/redirected
    # away for a PRIVATE project (see admin_users_page.py module docstring).
    # Deliberately a DISTINCT key from the existing (currently unused by any
    # test) ELITEA_TEAM_PROJECT_ID=471 — that value is "Elitea Testing Team",
    # a different project already relied on (as a locally-hardcoded constant)
    # by several chat/toolkit tests; conflating the two would silently break
    # this precondition or misrepresent that one. Default "400" ("UI Testing")
    # preserves current behaviour when the key is unset.
    users_team_project_id: str = "400"

    # ------------------------------------------------------------------
    # Settings -> AI Providers, Vector Storage section (ELITEA-2399/2400/2401)
    # ------------------------------------------------------------------
    # A project that already carries >=1 Vector Storage (pgvector)
    # configuration. This is a HARD precondition, not a convenience:
    # `CredentialsControls.jsx`'s `isLastInSection` disables the delete
    # control while a protected section holds one item, and Vector Storage --
    # unlike Embedding -- has no SHARED configurations to pad the count. So a
    # project going 0 -> 1 can never go back through the UI, and a spec that
    # created the first one would leave permanent residue in a shared project.
    # The acting user's default project (399, "Private") has ZERO vector
    # storages; 400 ("UI Testing") carries the deliberate permanent seed
    # `Autotest PGVector Seed` the analyst established for these cases
    # (test-specs/settings-ai-providers/_surface.md). Confirmed live
    # 2026-08-29 from the product's own
    # `GET /configurations/models/{id}?section=vectorstorage`: 399 -> total 0,
    # 400 -> total 1. Distinct key from `users_team_project_id` (same default,
    # different precondition) for the reason stated above it.
    ai_providers_seeded_project_id: str = "400"

    # ------------------------------------------------------------------
    # Public project id (ELITEA-2051)
    # ------------------------------------------------------------------
    # The "Public" project id, used ONLY as the path segment of the
    # projects-list endpoint's check_public_role probe:
    #   GET /projects/project/default/{public_project_id}?check_public_role=true
    # This mirrors EliteaUI's own VITE_PUBLIC_PROJECT_ID (see
    # ../EliteaUI/src/api/project.js + src/common/constants.js), which is 1 on
    # the DEV backend — confirmed live 2026-08-26 from the UI's own request.
    # Config-driven so a deployed env with a different public project id needs
    # no code change; no .env.test key or CI secret is required today.
    public_project_id: int = 1

    # ------------------------------------------------------------------
    # Default LLM settings for API-created agents / pipelines
    # Using gpt-5.2 as cheap default model for cost efficiency in tests
    # model_project_id=1 matches UI-created agents (0 may cause issues)
    # ------------------------------------------------------------------
    default_model_name: str = "gpt-5.2"
    default_model_project_id: int = 1

    # ------------------------------------------------------------------
    # Rate limiting (Cloudflare bypass)
    # ------------------------------------------------------------------
    cf_ext_rate: str = ""

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

