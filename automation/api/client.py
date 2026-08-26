"""Base API client for the Elitea platform.

Provides a thin wrapper around ``requests`` with authentication headers
and convenience methods for all HTTP verbs.

Usage::

    client = APIClient()
    resp = client.get("/v1/prompts")
    resp = client.post("/v1/agents", json={"name": "my-agent"})
"""

import logging
from typing import Optional
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import settings

logger = logging.getLogger("elitea.api")


def _default_llm_settings(model_name: str = None) -> dict:
    """Return default LLM settings for agent/pipeline creation.

    Args:
        model_name: Optional model name override. Uses settings.default_model_name if not provided.

    Returns:
        dict with max_tokens, temperature, reasoning_effort, model_name, model_project_id

    Note:
        Settings match UI-created agent defaults:
        - temperature: null (not 0.6) - lets the model use its default
        - reasoning_effort: "medium" (not "none") - matches UI default
        - model_project_id: 1 (not 0) - 0 may cause conversation creation issues
    """
    return {
        "max_tokens": -1,
        "temperature": None,  # Match UI default (null)
        "reasoning_effort": "medium",  # Match UI default
        "model_name": model_name or settings.default_model_name,
        "model_project_id": settings.default_model_project_id,
    }


def _create_retry_session() -> requests.Session:
    """Create a requests Session with retry on 429 (rate limit).

    Retries up to 3 times with exponential backoff starting at 5 seconds:
    - 1st retry after ~5s
    - 2nd retry after ~10s
    - 3rd retry after ~20s

    If settings.cf_ext_rate is set, adds cf-ext-rate header to bypass Cloudflare rate limits.
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=5,
        status_forcelist=[429],
        allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        raise_on_status=False,  # Let _raise_for_status handle errors
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    if settings.cf_ext_rate:
        session.headers["cf-ext-rate"] = settings.cf_ext_rate
        logger.debug("cf-ext-rate header configured")

    return session


def _get_source_ip(resp: requests.Response) -> Optional[str]:
    """Extract source IP from the socket used for the request."""
    try:
        sock = resp.raw._connection.sock
        if sock:
            return sock.getsockname()[0]
    except Exception:
        pass
    return None


def _raise_for_status(resp: requests.Response) -> None:
    """Raise HTTPError with the response body, headers, and source IP included.

    Replaces bare ``resp.raise_for_status()`` calls so that test failures
    show the API's error payload (validation message, field errors, etc.)
    instead of just the HTTP status code.

    For 429 errors, includes Cloudflare Ray ID, source IP, and other debug headers.
    """
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        try:
            body = resp.json()
        except Exception:
            body = resp.text

        # Put headers BEFORE body so they're visible (body can be huge HTML and gets truncated)
        error_msg = f"{exc} — headers: {dict(resp.headers)} — body: {body}"

        raise requests.HTTPError(error_msg, response=resp) from exc


class APIClient:
    """HTTP client with Elitea auth baked in.

    Configuration is read from environment variables by default and can be
    overridden via constructor arguments.

    Attributes:
        base_url: Root URL for API requests (e.g. ``https://nexus.elitea.ai/api``).
        api_token: Bearer token used in the ``Authorization`` header.
        project_id: Default project/workspace identifier.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_token: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.elitea_api_base).rstrip("/")
        self.api_token = api_token or settings.elitea_api_token
        self.project_id = project_id or str(settings.elitea_project_id)

        # Base headers for all requests
        self._auth_header = {"Authorization": f"Bearer {self.api_token}"}
        logger.debug("APIClient initialised — base_url=%s", self.base_url)

    def _headers_for_method(self, method: str) -> dict[str, str]:
        """Return appropriate headers for the HTTP method.
        
        Content-Type is only sent for POST/PUT/PATCH (requests with body).
        Sending it on GET/DELETE causes 400 from the server.
        """
        headers = dict(self._auth_header)
        if method.upper() in ("POST", "PUT", "PATCH"):
            headers["Content-Type"] = "application/json"
        return headers

    @property
    def headers(self) -> dict[str, str]:
        """Return a copy of the default request headers (with Content-Type)."""
        return {**self._auth_header, "Content-Type": "application/json"}

    # --- HTTP verbs ---

    def get(self, path: str, **kwargs) -> requests.Response:
        """Send a GET request.

        Args:
            path: URL path appended to ``base_url``.
            **kwargs: Forwarded to ``requests.get``.
        """
        url = f"{self.base_url}{path}"
        logger.debug("GET %s", url)
        return requests.get(url, headers=self._headers_for_method("GET"), **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        """Send a POST request.

        Args:
            path: URL path appended to ``base_url``.
            **kwargs: Forwarded to ``requests.post``.
        """
        url = f"{self.base_url}{path}"
        logger.debug("POST %s", url)
        return requests.post(url, headers=self._headers_for_method("POST"), **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        """Send a PUT request.

        Args:
            path: URL path appended to ``base_url``.
            **kwargs: Forwarded to ``requests.put``.
        """
        url = f"{self.base_url}{path}"
        logger.debug("PUT %s", url)
        return requests.put(url, headers=self._headers_for_method("PUT"), **kwargs)

    def patch(self, path: str, **kwargs) -> requests.Response:
        """Send a PATCH request.

        Args:
            path: URL path appended to ``base_url``.
            **kwargs: Forwarded to ``requests.patch``.
        """
        url = f"{self.base_url}{path}"
        logger.debug("PATCH %s", url)
        return requests.patch(url, headers=self._headers_for_method("PATCH"), **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        """Send a DELETE request.

        Args:
            path: URL path appended to ``base_url``.
            **kwargs: Forwarded to ``requests.delete``.
        """
        url = f"{self.base_url}{path}"
        logger.debug("DELETE %s", url)
        return requests.delete(url, headers=self._headers_for_method("DELETE"), **kwargs)

    def close(self):
        """No-op — APIClient uses module-level requests, not a session."""
        pass


class ProjectAPI:
    """Read the acting user's project memberships (ELITEA-2051).

    Hits the SAME endpoint the UI's own project selector uses
    (``../EliteaUI/src/api/project.js``)::

        GET /projects/project/default/{public_project_id}?check_public_role=true

    — verified live 2026-08-26 against ``localhost:5173``'s own network trace.
    The ``public_project_id`` path segment mirrors EliteaUI's
    ``VITE_PUBLIC_PROJECT_ID`` and comes from ``settings.public_project_id``.

    Authentication mirrors :class:`PipelineAPI` exactly (browser session
    cookies, Bearer-token fallback) so the API identity is the same one the
    browser under test is acting as — a test that resolves projects here and
    then drives the UI must see the same membership list the UI sees.

    Args:
        browser_cookies: List of cookie dicts from ``BrowserContext.cookies()``.
        base_url: API root (defaults to ``ELITEA_API_BASE`` env var).
    """

    def __init__(
        self,
        browser_cookies: list[dict],
        base_url: str | None = None,
    ):
        self.base_url = (base_url or settings.elitea_api_base).rstrip("/")

        self._session = _create_retry_session()
        for c in browser_cookies:
            self._session.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))
        if not browser_cookies and settings.elitea_api_token:
            self._session.headers.update({"Authorization": f"Bearer {settings.elitea_api_token}"})

        logger.debug("ProjectAPI initialised — base_url=%s", self.base_url)

    def _projects_url(self) -> str:
        return (
            f"{self.base_url}/projects/project/default/"
            f"{settings.public_project_id}"
        )

    def list_projects(self) -> list[dict]:
        """Return the acting user's project memberships.

        Each entry carries at least ``id``, ``name`` and ``owner_id``.
        """
        url = self._projects_url()
        logger.debug("LIST projects %s", url)
        resp = self._session.get(url, params={"check_public_role": "true"})
        _raise_for_status(resp)
        return resp.json()

    def close(self):
        """Close the underlying HTTP session."""
        self._session.close()


class ConversationAPI:
    """Manage chat conversations via the Elitea API.

    Uses Keycloak session cookies (from browser auth state) rather than
    Bearer tokens, because the conversation endpoints require cookie-based
    authentication.

    The ``Content-Type`` header is only sent on requests with a JSON body
    (POST/PUT/PATCH).  Sending it on GET/DELETE causes a 400 from the server.

    Args:
        browser_cookies: List of cookie dicts from ``BrowserContext.cookies()``.
        base_url: API root (defaults to ``ELITEA_API_BASE`` env var).
        project_id: Project identifier (defaults to ``ELITEA_PROJECT_ID``).
    """

    def __init__(
        self,
        browser_cookies: list[dict],
        base_url: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.elitea_api_base).rstrip("/")
        self.project_id = project_id or str(settings.elitea_project_id)

        self._session = _create_retry_session()
        for c in browser_cookies:
            self._session.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))
        if not browser_cookies and settings.elitea_api_token:
            self._session.headers.update({"Authorization": f"Bearer {settings.elitea_api_token}"})

        logger.debug("ConversationAPI initialised — base_url=%s", self.base_url)

    def _conversations_url(self, conversation_id: Optional[int] = None) -> str:
        base = f"{self.base_url}/elitea_core/conversations/prompt_lib/{self.project_id}"
        if conversation_id is not None:
            return f"{base}/{conversation_id}"
        return base

    def list_conversations(self) -> dict:
        """Return ``{"total": int, "rows": [...]}``.

        Raises ``requests.HTTPError`` on non-2xx status.
        """
        url = self._conversations_url()
        logger.debug("LIST conversations %s", url)
        resp = self._session.get(url)
        _raise_for_status(resp)
        return resp.json()

    def create_conversation(self, name: str) -> dict:
        """Create a new conversation and return its JSON representation.

        Args:
            name: Display name for the conversation.
        """
        url = self._conversations_url()
        logger.debug("CREATE conversation %s name=%s", url, name)
        resp = self._session.post(url, json={"name": name})
        _raise_for_status(resp)
        return resp.json()

    def get_conversation(self, conversation_id: int) -> dict:
        """Fetch a single conversation by *conversation_id*.

        Note: the GET endpoint uses the **singular** path segment
        ``/conversation/`` (not ``/conversations/``).
        """
        resp = self.get_conversation_raw(conversation_id)
        _raise_for_status(resp)
        return resp.json()

    def get_conversation_raw(self, conversation_id: int) -> requests.Response:
        """Return the raw ``Response`` for a single-conversation GET.

        Unlike :meth:`get_conversation`, does NOT raise on non-2xx — callers
        assert status/headers/body themselves. Used by error-path and
        content-type tests that must inspect the response without a raised
        ``HTTPError`` short-circuiting the check.
        """
        url = (
            f"{self.base_url}/elitea_core/conversation/prompt_lib"
            f"/{self.project_id}/{conversation_id}"
        )
        logger.debug("GET conversation (raw) %s", url)
        return self._session.get(url)

    def delete_conversation(self, conversation_id: int) -> None:
        """Delete a conversation.  Returns ``None`` on success (HTTP 204).

        Note: Uses singular /conversation/ endpoint (not /conversations/).
        """
        # Use singular endpoint for delete
        url = (
            f"{self.base_url}/elitea_core/conversation/prompt_lib"
            f"/{self.project_id}/{conversation_id}"
        )
        logger.debug("DELETE conversation %s", url)
        resp = self._session.delete(url)
        _raise_for_status(resp)

    def close(self):
        """Close the underlying HTTP session."""
        self._session.close()

    def rename_conversation(self, conversation_id: int, new_name: str) -> dict:
        """Rename a conversation via PUT on the singular ``/conversation/`` endpoint.

        Args:
            conversation_id: Numeric conversation ID.
            new_name: New name (3–50 characters).

        Returns:
            Updated conversation JSON.
        """
        url = (
            f"{self.base_url}/elitea_core/conversation/prompt_lib"
            f"/{self.project_id}/{conversation_id}"
        )
        logger.debug("RENAME conversation %s -> %s", url, new_name)
        resp = self._session.put(
            url,
            json={"name": new_name},
            headers={"Content-Type": "application/json"},
        )
        _raise_for_status(resp)
        return resp.json()

    def create_folder(self, name: str) -> dict:
        """Create a chat folder and return its JSON representation.

        ELITEA-2098 addition: no ``FolderAPI`` client exists yet — folder
        endpoints share the conversations project scope, so they live here
        alongside ``rename_conversation``/``delete_conversation`` per the
        "extend, don't duplicate" abstraction-layer rule.

        Args:
            name: Folder display name.

        Returns:
            Folder JSON (``id``, ``name``, ``owner_id``, ``position``, ``meta``).
            The server fills ``owner_id`` from the auth session — the
            ``FolderCreate`` OpenAPI schema lists it as required, but it is
            NOT sent in the request body (same pattern already relied on for
            ``author_id`` on conversation create).
        """
        url = f"{self.base_url}/elitea_core/folder/prompt_lib/{self.project_id}"
        logger.debug("CREATE folder %s name=%s", url, name)
        resp = self._session.post(
            url, json={"name": name}, headers={"Content-Type": "application/json"},
        )
        _raise_for_status(resp)
        return resp.json()

    def delete_folder(self, folder_id: int) -> None:
        """Delete a folder. Returns ``None`` on success (HTTP 204).

        Args:
            folder_id: Numeric folder ID.
        """
        url = f"{self.base_url}/elitea_core/folder/prompt_lib/{self.project_id}/{folder_id}"
        logger.debug("DELETE folder %s", url)
        resp = self._session.delete(url)
        _raise_for_status(resp)

    def move_conversation_to_folder(self, conversation_id: int, folder_id: int) -> dict:
        """Move a conversation into *folder_id* via PUT ``folder_id`` on the
        singular ``/conversation/`` endpoint (same endpoint as
        :meth:`rename_conversation`, different field).

        Args:
            conversation_id: Numeric conversation ID.
            folder_id: Numeric folder ID to move the conversation into.

        Returns:
            Updated conversation JSON.
        """
        url = (
            f"{self.base_url}/elitea_core/conversation/prompt_lib"
            f"/{self.project_id}/{conversation_id}"
        )
        logger.debug("MOVE conversation %s -> folder %s", url, folder_id)
        resp = self._session.put(
            url,
            json={"folder_id": folder_id},
            headers={"Content-Type": "application/json"},
        )
        _raise_for_status(resp)
        return resp.json()


class AgentAPI:
    """Manage agents (applications) via the Elitea API.

    Uses Keycloak session cookies (from browser auth state) like
    :class:`ConversationAPI`.

    The API entity is called ``application`` internally.  The list endpoint
    uses the **plural** path ``/applications/`` while the single-resource
    endpoints use **singular** ``/application/``.

    Args:
        browser_cookies: List of cookie dicts from ``BrowserContext.cookies()``.
        base_url: API root (defaults to ``ELITEA_API_BASE`` env var).
        project_id: Project identifier (defaults to ``ELITEA_PROJECT_ID``).
    """

    def __init__(
        self,
        browser_cookies: list[dict],
        base_url: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.elitea_api_base).rstrip("/")
        self.project_id = project_id or str(settings.elitea_project_id)

        self._session = _create_retry_session()
        for c in browser_cookies:
            self._session.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))
        if not browser_cookies and settings.elitea_api_token:
            self._session.headers.update({"Authorization": f"Bearer {settings.elitea_api_token}"})

        logger.debug("AgentAPI initialised — base_url=%s", self.base_url)

    def _applications_url(self) -> str:
        return f"{self.base_url}/elitea_core/applications/prompt_lib/{self.project_id}"

    def _application_url(self, agent_id: int) -> str:
        return f"{self.base_url}/elitea_core/application/prompt_lib/{self.project_id}/{agent_id}"

    def list_agents(self) -> dict:
        """Return agent list from ``/applications/`` with ``agents_type=classic``."""
        url = self._applications_url()
        params = {
            "agents_type": "classic",
            "sort_by": "created_at",
            "sort_order": "desc",
            "query": "",
            "limit": 50,
            "offset": 0,
        }
        logger.debug("LIST agents %s", url)
        resp = self._session.get(url, params=params)
        _raise_for_status(resp)
        return resp.json()

    def create_agent(self, name: str, description: str, instructions: str = "") -> dict:
        """Create a new agent and return its JSON representation.

        The API requires a ``versions`` array with LLM settings and a
        ``type`` field set to ``"interface"``.

        Args:
            name: Agent display name.
            description: Short description (required by the API).
            instructions: System prompt / guidelines for the agent.
        """
        url = self._applications_url()
        payload = {
            "name": name,
            "description": description,
            "type": "interface",
            "versions": [
                {
                    "name": "base",
                    "tags": [],
                    "instructions": instructions,
                    "variables": [],
                    "tools": [],
                    "llm_settings": _default_llm_settings(),
                    "conversation_starters": [],
                    "agent_type": "openai",
                    "welcome_message": "",
                    "meta": {"step_limit": 25},
                }
            ],
        }
        logger.debug("CREATE agent %s name=%s", url, name)
        resp = self._session.post(url, json=payload)
        _raise_for_status(resp)
        return resp.json()

    def create_agent_full(self, payload: dict) -> dict:
        """Create an agent using a raw payload dict.

        Allows tests to pass a fully-constructed payload (including all version
        fields, variables, welcome_message, conversation_starters, etc.)
        without the constraints of the ``create_agent`` convenience method.

        Args:
            payload: Complete agent creation payload. Must include at minimum
                     ``name``, ``description``, ``type``, and ``versions``.

        Returns:
            Created agent JSON (same structure as ``create_agent``).
        """
        url = self._applications_url()
        logger.debug("CREATE agent (full payload) %s name=%s", url, payload.get("name"))
        resp = self._session.post(url, json=payload)
        _raise_for_status(resp)
        return resp.json()

    def get_agent(self, agent_id: int) -> dict:
        """Fetch a single agent by *agent_id*.

        Uses the **singular** ``/application/`` path segment.
        """
        url = self._application_url(agent_id)
        logger.debug("GET agent %s", url)
        resp = self._session.get(url)
        _raise_for_status(resp)
        return resp.json()

    def update_agent(self, agent_id: int, **kwargs) -> dict:
        """Update an agent.  Keyword arguments become the JSON body fields.

        Args:
            agent_id: The numeric agent ID.
            **kwargs: Fields to update (e.g. ``name``, ``description``).
        """
        url = self._application_url(agent_id)
        logger.debug("UPDATE agent %s payload=%s", url, kwargs)
        resp = self._session.put(url, json=kwargs)
        _raise_for_status(resp)
        return resp.json()

    def delete_agent(self, agent_id: int) -> None:
        """Delete an agent."""
        url = self._application_url(agent_id)
        logger.debug("DELETE agent %s", url)
        resp = self._session.delete(url)
        _raise_for_status(resp)

    def unpublish_version(self, version_id: int) -> None:
        """Unpublish a Published version, reverting its status to Draft.

        Added for ELITEA-1892's publish/unpublish cycle test — a
        Published version has no dedicated delete endpoint (per the AFS,
        "no delete-version UI/API, only whole-agent delete"), and
        ``delete_agent()`` itself 400s with "Cannot delete application
        with published or embedded versions. Unpublish first." while any
        version on the agent is still Published. Cleanup paths that create
        Published versions (directly or via a failed mid-test run) must
        call this before ``delete_agent()`` to avoid leaking an
        undeletable agent.

        Args:
            version_id: The numeric id of the PUBLISHED version to revert
                (not the agent id — matches ``{versionId}`` in the UI's own
                ``POST .../unpublish/prompt_lib/{project}/{versionId}`` call).
        """
        url = f"{self.base_url}/elitea_core/unpublish/prompt_lib/{self.project_id}/{version_id}"
        logger.debug("UNPUBLISH version %s", url)
        resp = self._session.post(url)
        _raise_for_status(resp)

    def export_agent(self, agent_id: int, fmt: str = "md") -> bytes:
        """Export an agent as markdown.

        Args:
            agent_id: The numeric agent ID.
            fmt: Export format (default ``"md"``).

        Returns:
            Raw file content (bytes).
        """
        url = (
            f"{self.base_url}/elitea_core/export_import/prompt_lib"
            f"/{self.project_id}/{agent_id}?format={fmt}"
        )
        logger.debug("EXPORT agent %s", url)
        resp = self._session.get(url)
        _raise_for_status(resp)
        return resp.content

    def import_agent(self, payload: list[dict]) -> dict:
        """Import one or more agents from a parsed markdown payload.

        The payload is a JSON array of agent dicts as produced by the
        EliteAUI client-side markdown parser.  Each dict must include
        ``name``, ``description``, ``versions``, ``entity``, and
        ``import_uuid``.

        Args:
            payload: List of import dicts (see test code for structure).

        Returns:
            Dict with ``result`` (created entities) and ``errors``.
        """
        url = (
            f"{self.base_url}/elitea_core/import_wizard/prompt_lib"
            f"/{self.project_id}"
        )
        logger.debug("IMPORT agent %s", url)
        resp = self._session.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        _raise_for_status(resp)
        return resp.json()

    def close(self):
        """Close the underlying HTTP session."""
        self._session.close()


class PipelineAPI:
    """Manage pipelines via the Elitea API.

    Pipelines share the ``application`` API endpoints with agents.
    The only difference is the ``agents_type=pipeline`` query parameter
    for listing, and ``agent_type='pipeline'`` in the version payload.

    Uses Keycloak session cookies (from browser auth state) like
    :class:`ConversationAPI`.

    Args:
        browser_cookies: List of cookie dicts from ``BrowserContext.cookies()``.
        base_url: API root (defaults to ``ELITEA_API_BASE`` env var).
        project_id: Project identifier (defaults to ``ELITEA_PROJECT_ID``).
    """

    def __init__(
        self,
        browser_cookies: list[dict],
        base_url: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.elitea_api_base).rstrip("/")
        self.project_id = project_id or str(settings.elitea_project_id)

        self._session = _create_retry_session()
        for c in browser_cookies:
            self._session.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))
        if not browser_cookies and settings.elitea_api_token:
            self._session.headers.update({"Authorization": f"Bearer {settings.elitea_api_token}"})

        logger.debug("PipelineAPI initialised — base_url=%s", self.base_url)

    def _applications_url(self) -> str:
        return f"{self.base_url}/elitea_core/applications/prompt_lib/{self.project_id}"

    def _application_url(self, pipeline_id: int) -> str:
        return f"{self.base_url}/elitea_core/application/prompt_lib/{self.project_id}/{pipeline_id}"

    def list_pipelines(self) -> dict:
        """Return pipeline list from ``/applications/`` with ``agents_type=pipeline``."""
        url = self._applications_url()
        params = {
            "agents_type": "pipeline",
            "sort_by": "created_at",
            "sort_order": "desc",
            "query": "",
            "limit": 50,
            "offset": 0,
        }
        logger.debug("LIST pipelines %s", url)
        resp = self._session.get(url, params=params)
        _raise_for_status(resp)
        return resp.json()

    def create_pipeline(self, name: str, description: str, instructions: str = "") -> dict:
        """Create a new pipeline and return its JSON representation.

        The API requires a ``versions`` array with ``agent_type='pipeline'``
        and ``pipeline_settings`` to distinguish from agents.

        Args:
            name: Pipeline display name.
            description: Short description (required by the API).
            instructions: YAML pipeline definition (optional for empty pipeline).
        """
        url = self._applications_url()
        payload = {
            "name": name,
            "description": description,
            "type": "interface",
            "versions": [
                {
                    "name": "base",
                    "tags": [],
                    "instructions": instructions,
                    "variables": [],
                    "tools": [],
                    "llm_settings": _default_llm_settings(),
                    "conversation_starters": [],
                    "agent_type": "pipeline",
                    "welcome_message": "",
                    "pipeline_settings": {
                        "nodes": [],
                        "edges": [],
                        "orientation": "vertical",
                        "layout_version": "1.0",
                    },
                    "meta": {"step_limit": 25},
                }
            ],
        }
        logger.debug("CREATE pipeline %s name=%s", url, name)
        resp = self._session.post(url, json=payload)
        _raise_for_status(resp)
        return resp.json()

    def get_pipeline(self, pipeline_id: int) -> dict:
        """Fetch a single pipeline by *pipeline_id*.

        Uses the **singular** ``/application/`` path segment.
        """
        url = self._application_url(pipeline_id)
        logger.debug("GET pipeline %s", url)
        resp = self._session.get(url)
        _raise_for_status(resp)
        return resp.json()

    def update_pipeline(self, pipeline_id: int, **kwargs) -> dict:
        """Update a pipeline.  Keyword arguments become the JSON body fields.

        Args:
            pipeline_id: The numeric pipeline ID.
            **kwargs: Fields to update (e.g. ``name``, ``description``).
        """
        url = self._application_url(pipeline_id)
        logger.debug("UPDATE pipeline %s payload=%s", url, kwargs)
        resp = self._session.put(url, json=kwargs)
        _raise_for_status(resp)
        return resp.json()

    def delete_pipeline(self, pipeline_id: int) -> None:
        """Delete a pipeline."""
        url = self._application_url(pipeline_id)
        logger.debug("DELETE pipeline %s", url)
        resp = self._session.delete(url)
        _raise_for_status(resp)

    def create_pipeline_with_llm_node(
        self,
        name: str,
        description: str,
        *,
        model_name: str = "",
    ) -> dict:
        """Create a pipeline with a single LLM node connected to END.

        This produces a pipeline that can actually execute — the LLM node
        receives the user message and produces a response.

        The pipeline definition is stored as YAML in the ``instructions``
        field, not in ``pipeline_settings`` (which only stores visual
        canvas layout metadata).

        Args:
            name: Pipeline display name.
            description: Short description.
            model_name: LLM model to use in the node (defaults to
                        ``settings.default_model_name``).

        Returns:
            The created pipeline JSON.
        """
        if not model_name:
            model_name = settings.default_model_name
        # Pipeline execution definition is YAML in the instructions field
        instructions_yaml = (
            "entry_point: LLM 1\n"
            "nodes:\n"
            "  - id: LLM 1\n"
            "    type: llm\n"
            "    input: []\n"
            "    input_mapping:\n"
            "      chat_history:\n"
            "        type: fixed\n"
            "        value: []\n"
            "      system:\n"
            "        type: fixed\n"
            "        value: ''\n"
            "      task:\n"
            "        type: fixed\n"
            "        value: ''\n"
            "    output: []\n"
            "    structured_output: false\n"
            "    transition: END\n"
        )

        url = self._applications_url()
        payload = {
            "name": name,
            "description": description,
            "type": "interface",
            "versions": [
                {
                    "name": "base",
                    "tags": [],
                    "instructions": instructions_yaml,
                    "variables": [],
                    "tools": [],
                    "llm_settings": _default_llm_settings(model_name),
                    "conversation_starters": [],
                    "agent_type": "pipeline",
                    "welcome_message": "",
                    "pipeline_settings": {
                        "nodes": [],
                        "edges": [],
                        "orientation": "vertical",
                        "layout_version": "1.0",
                    },
                    "meta": {"step_limit": 25},
                }
            ],
        }
        logger.debug("CREATE pipeline with LLM node %s name=%s", url, name)
        resp = self._session.post(url, json=payload)
        _raise_for_status(resp)
        return resp.json()

    def create_pipeline_with_nodes(
        self,
        name: str,
        description: str,
        entry_point: str,
        nodes: list[dict],
    ) -> dict:
        """Create a pipeline with custom nodes.

        Args:
            name: Pipeline display name.
            description: Short description.
            entry_point: ID of the entry-point node (e.g. ``"LLM 1"``).
            nodes: List of node dicts with keys ``id``, ``type``,
                   ``input``, ``output``, ``transition``, etc.

        Returns:
            Created pipeline JSON.
        """
        import yaml as _yaml

        instructions_yaml = _yaml.dump(
            {"entry_point": entry_point, "nodes": nodes},
            default_flow_style=False,
            allow_unicode=True,
        )

        url = self._applications_url()
        payload = {
            "name": name,
            "description": description,
            "type": "interface",
            "versions": [
                {
                    "name": "base",
                    "tags": [],
                    "instructions": instructions_yaml,
                    "variables": [],
                    "tools": [],
                    "llm_settings": _default_llm_settings(),
                    "conversation_starters": [],
                    "agent_type": "pipeline",
                    "welcome_message": "",
                    "pipeline_settings": {
                        "nodes": [],
                        "edges": [],
                        "orientation": "vertical",
                        "layout_version": "1.0",
                    },
                    "meta": {"step_limit": 25},
                }
            ],
        }
        logger.debug("CREATE pipeline with custom nodes %s name=%s", url, name)
        resp = self._session.post(url, json=payload)
        _raise_for_status(resp)
        return resp.json()

    def create_pipeline_with_mcp_node(
        self,
        name: str,
        description: str,
        tools: list[dict],
        *,
        toolkit_name: str,
        tool: str,
        input_mapping: Optional[dict] = None,
        node_id: str = "MCP 1",
    ) -> dict:
        """Create a pipeline with a single MCP node pre-configured with a Toolkit + Tool.

        Used to seed the precondition for ELITEA-1954 (MCP node Toolkit/Tool
        switching): a pipeline with an MCP node already configured, and
        >=2 MCP toolkits attached in the pipeline's TOOLS section — without
        needing to drive the UI to attach toolkits or configure the node.

        Args:
            name: Pipeline display name.
            description: Short description.
            tools: Full toolkit JSON objects (as returned by
                ``ToolkitAPI.get_toolkit`` / ``create_remote_mcp_toolkit``)
                to attach in the pipeline's TOOLS section. The MCP node's
                Toolkit dropdown lists exactly these (``ToolSelect.jsx``
                reads ``version_details.tools``) — a bare ``{"id": ...}``
                reference is rejected by the API (confirmed empirically:
                400 "Missing 'settings'"), so full objects are required.
            toolkit_name: The node's initial ``toolkit_name`` YAML field —
                must match one of ``tools``' cleaned display names (spaces/
                punctuation stripped; see EliteaUI's ``cleanString`` /
                ``genToolkitName`` — e.g. toolkit "Remote Github" ->
                ``toolkit_name: RemoteGithub``).
            tool: The node's initial ``tool`` YAML field (a tool name from
                the ``toolkit_name`` toolkit's ``settings.selected_tools``).
            input_mapping: Optional initial ``input_mapping`` dict for the
                node (defaults to empty — the initial tool/toolkit pairing
                only needs to exist for the test's Step 3 "read current
                values"; it does not need a fully valid mapping since the
                test immediately switches Toolkit/Tool away from it).
            node_id: The node's YAML id (also the entry point).

        Returns:
            Created pipeline JSON (same shape as ``create_pipeline_with_nodes``).
        """
        import yaml as _yaml

        node = {
            "id": node_id,
            "type": "mcp",
            "toolkit_name": toolkit_name,
            "tool": tool,
            "input": ["input"],
            "output": ["messages"],
            "input_mapping": input_mapping or {},
            "structured_output": False,
            "transition": "END",
        }
        instructions_yaml = _yaml.dump(
            {"entry_point": node_id, "nodes": [node]},
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

        url = self._applications_url()
        payload = {
            "name": name,
            "description": description,
            "type": "interface",
            "versions": [
                {
                    "name": "base",
                    "tags": [],
                    "instructions": instructions_yaml,
                    "variables": [],
                    "tools": tools,
                    "llm_settings": _default_llm_settings(),
                    "conversation_starters": [],
                    "agent_type": "pipeline",
                    "welcome_message": "",
                    "pipeline_settings": {
                        "nodes": [],
                        "edges": [],
                        "orientation": "vertical",
                        "layout_version": "1.0",
                    },
                    "meta": {"step_limit": 25},
                }
            ],
        }
        logger.debug("CREATE pipeline with MCP node %s name=%s", url, name)
        resp = self._session.post(url, json=payload)
        _raise_for_status(resp)
        return resp.json()

    def export_pipeline(self, pipeline_id: int, fmt: str = "md") -> bytes:
        """Export a pipeline as markdown.

        Uses the same ``/export_import/`` endpoint as agents — pipelines
        and agents share the ``application`` backend.

        Args:
            pipeline_id: The numeric pipeline ID.
            fmt: Export format (default ``"md"``).

        Returns:
            Raw file content (bytes).
        """
        url = (
            f"{self.base_url}/elitea_core/export_import/prompt_lib"
            f"/{self.project_id}/{pipeline_id}?format={fmt}"
        )
        logger.debug("EXPORT pipeline %s", url)
        resp = self._session.get(url)
        _raise_for_status(resp)
        return resp.content

    def import_pipeline(self, payload: list[dict]) -> dict:
        """Import one or more pipelines from a parsed markdown payload.

        The payload is a JSON array of pipeline dicts, similar to the
        agent import but with ``entity: "pipelines"`` and pipeline-specific
        version fields (``agent_type: "pipeline"``, ``pipeline_settings``).

        Args:
            payload: List of import dicts.

        Returns:
            Dict with ``result`` (created entities) and ``errors``.
        """
        url = (
            f"{self.base_url}/elitea_core/import_wizard/prompt_lib"
            f"/{self.project_id}"
        )
        logger.debug("IMPORT pipeline %s", url)
        resp = self._session.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        _raise_for_status(resp)
        return resp.json()

    def close(self):
        """Close the underlying HTTP session."""
        self._session.close()


class CredentialAPI:
    """Manage credentials via the Elitea API.

    Uses Keycloak session cookies (from browser auth state) like
    :class:`ConversationAPI`.

    Args:
        browser_cookies: List of cookie dicts from ``BrowserContext.cookies()``.
        base_url: API root (defaults to ``ELITEA_API_BASE`` env var).
        project_id: Project identifier (defaults to ``ELITEA_PROJECT_ID``).
    """

    def __init__(
        self,
        browser_cookies: list[dict],
        base_url: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.elitea_api_base).rstrip("/")
        self.project_id = project_id or str(settings.elitea_project_id)

        self._session = _create_retry_session()
        for c in browser_cookies:
            self._session.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))
        if not browser_cookies and settings.elitea_api_token:
            self._session.headers.update({"Authorization": f"Bearer {settings.elitea_api_token}"})

        logger.debug("CredentialAPI initialised — base_url=%s", self.base_url)

    def _credentials_url(self, credential_id: Optional[int] = None) -> str:
        """Build URL for credentials API (uses /configurations endpoint)."""
        if credential_id is not None:
            return f"{self.base_url}/configurations/configuration/{self.project_id}/{credential_id}"
        return f"{self.base_url}/configurations/configurations/{self.project_id}"

    def list_credentials(self, params: Optional[dict] = None) -> dict:
        """Return credential list (single page, default limit=20).
        
        Args:
            params: Optional query parameters (e.g., {'section': 'ai_credentials'})
        
        Returns:
            Dict with keys: 'total', 'items', 'offset', 'limit'
        """
        url = self._credentials_url()
        logger.info("LIST credentials URL=%s project_id=%s params=%s", url, self.project_id, params)
        resp = self._session.get(url, params=params or {})
        logger.info("Response status=%d body=%s", resp.status_code, resp.text[:500])
        _raise_for_status(resp)
        return resp.json()
    
    def list_all_credentials(self, params: Optional[dict] = None) -> list[dict]:
        """Return ALL credentials by fetching all pages.
        
        API returns paginated results (default limit=20). This method fetches
        all pages and returns a flat list of credential dicts.
        
        Args:
            params: Optional query parameters (e.g., {'section': 'ai_credentials'})
        
        Returns:
            List of credential dicts (each with 'id', 'label', 'type', etc.)
        """
        all_items = []
        offset = 0
        limit = 100  # Fetch 100 per page (larger batches = fewer requests)
        
        while True:
            page_params = dict(params or {})
            page_params.update({"offset": offset, "limit": limit})
            
            resp = self.list_credentials(params=page_params)
            items = resp.get("items", [])
            total = resp.get("total", 0)
            
            all_items.extend(items)
            logger.debug("Fetched credentials page: offset=%d limit=%d got=%d total=%d",
                        offset, limit, len(items), total)
            
            # Stop if we've fetched everything
            if len(all_items) >= total or len(items) < limit:
                break
            
            offset += limit
        
        logger.info("list_all_credentials: fetched %d credentials", len(all_items))
        return all_items

    def list_credential_types(self) -> list[str]:
        """Return the credential type keys present in the project.

        Reads ``GET /configurations/types/{project_id}`` — the SAME endpoint
        that backs the credentials list page's right-hand TYPES filter panel,
        so it is the honest oracle for "which type chips should the panel
        render" (ELITEA-1966). Returns only types for which at least one
        credential exists, e.g. ``["github", "jira", "s3_api_credentials"]``.
        """
        url = f"{self.base_url}/configurations/types/{self.project_id}"
        logger.debug("LIST credential types %s", url)
        resp = self._session.get(url)
        _raise_for_status(resp)
        return resp.json().get("rows", [])

    def create_github_credential(
        self, display_name: str, base_url: str, token: str, elitea_title: Optional[str] = None
    ) -> dict:
        """Create a GitHub credential and return its JSON representation.

        Args:
            display_name: Human-readable name for the credential.
            base_url: GitHub API base URL (e.g. ``https://api.github.com``).
            token: GitHub personal access token.
            elitea_title: Optional unique identifier (auto-generated with timestamp if not provided).

        Returns:
            Dict with ``id``, ``elitea_title``, ``label`` (display name), etc.
        """
        import time
        url = self._credentials_url()
        # Auto-generate unique elitea_title if not provided
        if not elitea_title:
            timestamp = str(int(time.time() * 1000))  # millisecond precision
            safe_name = display_name.replace(' ', '_').replace('-', '_').lower()[:30]
            title = f"github_{safe_name}_{timestamp}"
        else:
            title = elitea_title
        
        payload = {
            "type": "github",
            "elitea_title": title,
            "label": display_name,
            "data": {
                "base_url": base_url,
                "access_token": token,
            },
            "shared": False,
        }
        logger.debug("CREATE github credential %s name=%s title=%s", url, display_name, title)
        resp = self._session.post(
            url, json=payload, headers={"Content-Type": "application/json"}
        )
        if not resp.ok:
            logger.error(
                "Failed to create credential: status=%s body=%s",
                resp.status_code,
                resp.text[:500],
            )
        _raise_for_status(resp)
        return resp.json()

    def create_jira_credential(
        self, display_name: str, base_url: str, username: str, api_key: str, elitea_title: Optional[str] = None
    ) -> dict:
        """Create a JIRA credential and return its JSON representation.

        Args:
            display_name: Human-readable name for the credential.
            base_url: JIRA base URL (e.g. ``https://your-domain.atlassian.net``).
            username: JIRA username (email).
            api_key: JIRA API key/token.
            elitea_title: Optional unique identifier (auto-generated with timestamp if not provided).

        Returns:
            Dict with ``id``, ``elitea_title``, ``label`` (display name), etc.
        """
        import time
        url = self._credentials_url()
        # Auto-generate unique elitea_title if not provided
        if not elitea_title:
            timestamp = str(int(time.time() * 1000))  # millisecond precision
            safe_name = display_name.replace(' ', '_').replace('-', '_').lower()[:30]
            title = f"jira_{safe_name}_{timestamp}"
        else:
            title = elitea_title

        payload = {
            "type": "jira",
            "elitea_title": title,
            "label": display_name,
            "data": {
                "base_url": base_url,
                "username": username,
                "api_key": api_key,
            },
            "shared": False,
        }
        logger.debug("CREATE jira credential %s name=%s title=%s", url, display_name, title)
        resp = self._session.post(
            url, json=payload, headers={"Content-Type": "application/json"}
        )
        if not resp.ok:
            logger.error(
                "Failed to create credential: status=%s body=%s",
                resp.status_code,
                resp.text[:500],
            )
        _raise_for_status(resp)
        return resp.json()

    def create_credential(self, payload: dict) -> dict:
        """Create a credential of any type using a raw payload dict.

        The payload must include: type, elitea_title, label, data, shared.
        """
        url = self._credentials_url()
        resp = self._session.post(
            url, json=payload, headers={"Content-Type": "application/json"}
        )
        _raise_for_status(resp)
        return resp.json()

    def delete_credential(self, credential_id: int) -> None:
        """Delete a credential."""
        url = self._credentials_url(credential_id)
        logger.debug("DELETE credential %s", url)
        resp = self._session.delete(url)
        _raise_for_status(resp)

    def update_credential(self, credential_id: int, payload: dict) -> dict:
        """Update an existing credential.

        Args:
            credential_id: ID of the credential to update.
            payload: Full credential payload (type, elitea_title, label, data, shared).

        Returns:
            Updated credential dict.
        """
        url = self._credentials_url(credential_id)
        logger.debug("PUT credential %s", url)
        resp = self._session.put(
            url, json=payload, headers={"Content-Type": "application/json"}
        )
        _raise_for_status(resp)
        return resp.json()

    def close(self):
        """Close the underlying HTTP session."""
        self._session.close()


class ArtifactAPI:
    """Manage artifact buckets via the Elitea API.

    Uses Keycloak session cookies (from browser auth state) like
    :class:`ConversationAPI`.

    Args:
        browser_cookies: List of cookie dicts from ``BrowserContext.cookies()``.
        base_url: API root (defaults to ``ELITEA_API_BASE`` env var).
        project_id: Project identifier (defaults to ``ELITEA_PROJECT_ID``).
    """

    def __init__(
        self,
        browser_cookies: list[dict],
        base_url: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.elitea_api_base).rstrip("/")
        self.project_id = project_id or str(settings.elitea_project_id)

        self._session = _create_retry_session()
        for c in browser_cookies:
            self._session.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))
        if not browser_cookies and settings.elitea_api_token:
            self._session.headers.update({"Authorization": f"Bearer {settings.elitea_api_token}"})

        logger.debug("ArtifactAPI initialised — base_url=%s", self.base_url)

    def _buckets_url(self, bucket_name: Optional[str] = None) -> str:
        base = f"{self.base_url}/artifacts/buckets/default/{self.project_id}"
        if bucket_name:
            return f"{base}/{bucket_name}"
        return base

    def create_bucket(
        self,
        name: str,
        expiration_measure: str = "years",
        expiration_value: int = 1,
    ) -> dict:
        """Create a new artifact bucket.

        Args:
            name: Bucket name (must be unique within the project).
            expiration_measure: Retention period unit (default ``"years"``).
            expiration_value: Retention period quantity (default ``1``).

        Returns:
            Dict with ``message``, ``id``, and ``name`` keys.
        """
        url = self._buckets_url()
        payload = {
            "name": name,
            "expiration_measure": expiration_measure,
            "expiration_value": expiration_value,
        }
        logger.debug("CREATE bucket %s name=%s", url, name)
        resp = self._session.post(url, json=payload, headers={"Content-Type": "application/json"})
        _raise_for_status(resp)
        return resp.json()

    def delete_bucket(self, bucket_name: str) -> None:
        """Delete an artifact bucket and all its contents.

        Tries the bucket-name URL first, then falls back to the bucket-ID
        format (``p--{project_id}.{bucket_name}``) which some deployments
        require.

        Args:
            bucket_name: Name of the bucket to delete.
        """
        url = self._buckets_url(bucket_name)
        logger.debug("DELETE bucket %s", url)
        resp = self._session.delete(url)
        if resp.status_code == 404:
            # Try with the compound bucket-ID format
            bucket_id = f"p--{self.project_id}.{bucket_name}"
            url_id = self._buckets_url(bucket_id)
            logger.debug("DELETE bucket 404 — retrying with id format %s", url_id)
            resp = self._session.delete(url_id)
        _raise_for_status(resp)

    def set_bucket_pinned(self, bucket_name: str, is_pinned: bool) -> None:
        """Set (or clear) a bucket's "pinned to top" flag.

        Mirrors the UI's own pin mutation exactly — ``PATCH
        /artifacts/buckets/default/{project_id}?name={bucket}`` with body
        ``{"is_pinned": <bool>}`` (``EliteaUI/src/api/artifacts.js``'s
        ``updateBucketPin``). Note the QUERY-string bucket form: the
        path-segment form used by :meth:`delete_bucket` is not what this
        endpoint accepts.

        Added for the ELITEA-1820/1821 pin/unpin tests' TEARDOWN — a leaked
        *pinned* bucket would sit at the top of every project member's
        bucket list forever (bucket deletion itself is unreliable, see
        ``#636``), so those tests clear the flag before deleting. It is
        cleanup, never an observable: both tests pin and unpin through the
        UI, which is what they verify.

        Args:
            bucket_name: Name of the bucket to pin/unpin.
            is_pinned: ``True`` to pin to top, ``False`` to unpin.
        """
        url = f"{self._buckets_url()}?name={quote(bucket_name)}"
        logger.debug("PATCH bucket pin %s is_pinned=%s", url, is_pinned)
        resp = self._session.patch(
            url,
            json={"is_pinned": is_pinned},
            headers={"Content-Type": "application/json"},
        )
        _raise_for_status(resp)

    def list_bucket_files(self, bucket_name: str) -> list[str]:
        """List all file keys in a bucket via the S3 listing API.

        Uses the ``/artifacts/s3/{bucket_name}?project_id=...&format=json``
        endpoint (note: no ``/api/v2/`` prefix — this is a direct S3 proxy).
        Returns the ``contents[].key`` values, which are full relative paths
        (e.g. ``"output/a.txt"``).

        Args:
            bucket_name: Name of the bucket to list.

        Returns:
            List of file key strings relative to the bucket root.
        """
        # The S3 listing endpoint sits at the root, not under /api/v2/
        elitea_root = self.base_url.split("/api/")[0]
        url = (
            f"{elitea_root}/artifacts/s3/{bucket_name}"
            f"?project_id={self.project_id}&format=json"
        )
        logger.debug("LIST bucket files %s", url)
        resp = self._session.get(url)
        _raise_for_status(resp)
        data = resp.json()
        # Response: {"name": "...", "contents": [{"key": "file1.txt", ...}, ...]}
        if isinstance(data, list):
            return data
        contents = data.get("contents", [])
        return [item["key"] for item in contents if "key" in item]

    def get_file(self, bucket_name: str, file_key: str) -> bytes:
        """Fetch the raw content of a file from a bucket.

        Uses the ``/api/v2/artifacts/artifact/default/{project_id}/{bucket}/{key}``
        endpoint — the same URL the browser downloads from when clicking
        "Download" in the Artifacts UI.

        Args:
            bucket_name: Name of the bucket.
            file_key: Full key of the file (e.g. ``"output/a.txt"``).

        Returns:
            Raw bytes of the file content.

        Raises:
            requests.HTTPError: If the file does not exist or cannot be fetched.
        """
        url = (
            f"{self.base_url}/artifacts/artifact/default"
            f"/{self.project_id}/{bucket_name}/{file_key}"
        )
        logger.debug("GET file %s", url)
        resp = self._session.get(url)
        _raise_for_status(resp)
        return resp.content

    def upload_file(
        self,
        bucket_name: str,
        file_key: str,
        content: bytes,
        content_type: Optional[str] = None,
    ) -> None:
        """Upload raw bytes to a bucket via the S3 proxy endpoint.

        Uses the same ``PUT /artifacts/s3/{bucket_name}/{file_key}?project_id=...``
        endpoint the browser itself calls when uploading through the Artifacts
        UI (confirmed live via network capture). Seeds precondition files fast,
        independent of the browser — no ``/api/v2/`` prefix, same direct S3
        proxy root as :meth:`list_bucket_files`.

        Args:
            bucket_name: Name of the target bucket (must already exist).
            file_key: Full relative key/path for the file (e.g. ``"sample.txt"``
                or ``"output/a.txt"``).
            content: Raw file bytes to upload.
            content_type: Optional ``Content-Type`` header value. Omitted when
                not given (S3 proxy accepts uploads without it).

        Raises:
            requests.HTTPError: If the upload fails.
        """
        elitea_root = self.base_url.split("/api/")[0]
        url = (
            f"{elitea_root}/artifacts/s3/{bucket_name}/{file_key}"
            f"?project_id={self.project_id}"
        )
        headers = {"Content-Type": content_type} if content_type else {}
        logger.debug("PUT upload file %s (%d bytes)", url, len(content))
        resp = self._session.put(url, data=content, headers=headers)
        _raise_for_status(resp)

    def get_file_metadata(self, bucket_name: str, file_key: str) -> Optional[dict]:
        """Fetch a single file's full metadata from the bucket's S3 JSON listing.

        Unlike :meth:`list_bucket_files` (which returns only key strings, and
        is left unchanged so its existing shape/callers are unaffected), this
        returns the full per-file dict from the ``contents[]`` array —
        including ``lastModified``, which has no UI-visible equivalent
        anywhere in the Artifacts file table (Name / Type / Size / Actions
        columns only — confirmed via full-table snapshot during ELITEA-1832
        exploration).

        Args:
            bucket_name: Name of the bucket.
            file_key: Full key of the file to look up (e.g. ``"sample.txt"``).

        Returns:
            Dict with ``key``, ``lastModified``, ``etag``, ``size``,
            ``storageClass`` keys, or ``None`` if the file is not present in
            the listing.
        """
        elitea_root = self.base_url.split("/api/")[0]
        url = (
            f"{elitea_root}/artifacts/s3/{bucket_name}"
            f"?project_id={self.project_id}&format=json"
        )
        logger.debug("GET file metadata %s (key=%s)", url, file_key)
        resp = self._session.get(url)
        _raise_for_status(resp)
        data = resp.json()
        contents = data.get("contents", []) if isinstance(data, dict) else []
        for item in contents:
            if item.get("key") == file_key:
                return item
        return None

    def close(self):
        """Close the underlying HTTP session."""
        self._session.close()

    # -------------------------------------------------------------------------
    # Permission enforcement test helpers (return response, don't raise)
    # -------------------------------------------------------------------------

    def get_file_raw(self, bucket_name: str, file_key: str) -> "requests.Response":
        """GET a file without raising on error status — for permission testing.

        Args:
            bucket_name: Name of the bucket.
            file_key: Full key of the file.

        Returns:
            Raw requests.Response object (check .status_code).
        """
        url = (
            f"{self.base_url}/artifacts/artifact/default"
            f"/{self.project_id}/{bucket_name}/{file_key}"
        )
        logger.debug("GET file (raw) %s", url)
        return self._session.get(url)

    def upload_file_raw(
        self,
        bucket_name: str,
        filename: str,
        content: bytes,
    ) -> "requests.Response":
        """POST (upload) a file without raising on error — for permission testing.

        Args:
            bucket_name: Name of the bucket.
            filename: Name for the uploaded file.
            content: File content as bytes.

        Returns:
            Raw requests.Response object (check .status_code).
        """
        url = f"{self.base_url}/artifacts/artifacts/default/{self.project_id}/{bucket_name}"
        files = {"file": (filename, content)}
        logger.debug("POST file (raw) %s filename=%s", url, filename)
        return self._session.post(url, files=files)

    def delete_file_raw(self, bucket_name: str, filename: str) -> "requests.Response":
        """DELETE a file without raising on error — for permission testing.

        Args:
            bucket_name: Name of the bucket.
            filename: Name of the file to delete.

        Returns:
            Raw requests.Response object (check .status_code).
        """
        url = f"{self.base_url}/artifacts/artifact/default/{self.project_id}/{bucket_name}"
        params = {"filename": filename}
        logger.debug("DELETE file (raw) %s filename=%s", url, filename)
        return self._session.delete(url, params=params)

    def bucket_exists(self, bucket_name: str) -> bool:
        """Check if a bucket exists by attempting to list its files.

        Args:
            bucket_name: Name of the bucket to check.

        Returns:
            True if bucket exists, False otherwise.
        """
        try:
            self.list_bucket_files(bucket_name)
            return True
        except Exception:
            return False


class SkillAPI:
    """Manage skills via the Elitea API.

    Uses Keycloak session cookies (from browser auth state) like
    :class:`ConversationAPI`.

    The API entity is ``skill``.  The list endpoint uses the **plural**
    path ``/skills/`` while single-resource endpoints use **singular**
    ``/skill/``.

    Args:
        browser_cookies: List of cookie dicts from ``BrowserContext.cookies()``.
        base_url: API root (defaults to ``ELITEA_API_BASE`` env var).
        project_id: Project identifier (defaults to ``ELITEA_PROJECT_ID``).
    """

    def __init__(
        self,
        browser_cookies: list[dict],
        base_url: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.elitea_api_base).rstrip("/")
        self.project_id = project_id or str(settings.elitea_project_id)

        self._session = requests.Session()
        for c in browser_cookies:
            self._session.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))
        if not browser_cookies and settings.elitea_api_token:
            self._session.headers.update({"Authorization": f"Bearer {settings.elitea_api_token}"})

        logger.debug("SkillAPI initialised — base_url=%s", self.base_url)

    def _skills_url(self) -> str:
        return f"{self.base_url}/elitea_core/skills/prompt_lib/{self.project_id}"

    def _skill_url(self, skill_id: int) -> str:
        return f"{self.base_url}/elitea_core/skill/prompt_lib/{self.project_id}/{skill_id}"

    def list_skills(self, limit: int = 500) -> dict:
        """Return skill list from ``/skills/``.

        Args:
            limit: Maximum number of skills to return. Defaults to 500 to
                avoid silent misses in shared environments with many skills.
        """
        url = self._skills_url()
        params = {
            "sort_by": "created_at",
            "sort_order": "desc",
            "query": "",
            "limit": limit,
            "offset": 0,
        }
        logger.debug("LIST skills %s", url)
        resp = self._session.get(url, params=params)
        _raise_for_status(resp)
        return resp.json()

    def create_skill(self, name: str, description: str, instructions: str) -> dict:
        """Create a new skill and return its JSON representation.

        Mirrors ``AgentAPI.create_agent_full()``'s "raw payload" convenience
        pattern, scoped to the fields the Skill create endpoint actually
        needs. Payload shape confirmed source-side against EliteaUI's
        ``skillsApi.js`` (``skillCreate`` mutation): ``{name, description,
        versions: [{name: "base", instructions}]}`` — ``"base"`` is
        ``LATEST_VERSION_NAME`` (``entities/version/lib/constants``). Added
        for ELITEA-1911 (the AFS's own exploration created its fixture
        Skills via the live UI form, flagging this convenience method as
        the missing piece — see the AFS's Automation Hints).

        Args:
            name: Skill name. The UI form constrains this to lowercase
                letters, digits, and hyphens, max 32 characters, no leading
                or trailing hyphen (live-confirmed client-side validation
                message) — callers should pre-validate names against that
                format to avoid surprises if the API enforces it too.
            description: Skill description (required by the API).
            instructions: The "base" version's instructions text.
        """
        url = self._skills_url()
        payload = {
            "name": name,
            "description": description,
            "versions": [{"name": "base", "instructions": instructions}],
        }
        logger.debug("CREATE skill %s name=%s", url, name)
        resp = self._session.post(url, json=payload)
        _raise_for_status(resp)
        return resp.json()

    def get_skill(self, skill_id: int) -> dict:
        """Fetch a single skill by *skill_id*.

        Uses the **singular** ``/skill/`` path segment. Added for
        ELITEA-2602/ELITEA-2603 (Fork verification) — the source of truth
        for field/tags/icon/lineage assertions instead of re-deriving them
        from the DOM (mirrors ``AgentAPI.get_agent()``/
        ``PipelineAPI.get_pipeline()``).

        Args:
            skill_id: The numeric skill ID.
        """
        url = self._skill_url(skill_id)
        logger.debug("GET skill %s", url)
        resp = self._session.get(url)
        _raise_for_status(resp)
        return resp.json()

    def delete_skill(self, skill_id: int) -> None:
        """Delete a skill by ID.

        Args:
            skill_id: The numeric skill ID.
        """
        url = self._skill_url(skill_id)
        logger.debug("DELETE skill %s", url)
        resp = self._session.delete(url)
        _raise_for_status(resp)

    def close(self):
        """Close the underlying HTTP session."""
        self._session.close()


class ToolkitAPI:
    """Manage toolkits via the Elitea API.

    Uses Keycloak session cookies (from browser auth state) like
    :class:`ConversationAPI`.

    Args:
        browser_cookies: List of cookie dicts from ``BrowserContext.cookies()``.
        base_url: API root (defaults to ``ELITEA_API_BASE`` env var).
        project_id: Project identifier (defaults to ``ELITEA_PROJECT_ID``).
    """

    def __init__(
        self,
        browser_cookies: list[dict],
        base_url: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.elitea_api_base).rstrip("/")
        self.project_id = project_id or str(settings.elitea_project_id)

        self._session = _create_retry_session()
        for c in browser_cookies:
            self._session.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))
        if not browser_cookies and settings.elitea_api_token:
            self._session.headers.update({"Authorization": f"Bearer {settings.elitea_api_token}"})

        logger.debug("ToolkitAPI initialised — base_url=%s", self.base_url)

    def _toolkits_url(self, toolkit_id: Optional[int] = None) -> str:
        """Build URL for toolkits API."""
        if toolkit_id is not None:
            return f"{self.base_url}/elitea_core/tool/prompt_lib/{self.project_id}/{toolkit_id}"
        return f"{self.base_url}/elitea_core/tools/prompt_lib/{self.project_id}"

    def list_toolkits(self, params: Optional[dict] = None) -> dict:
        """Return toolkit list (single page).

        Args:
            params: Optional query parameters (e.g., {'toolkit_type': 'github'})

        Returns:
            API response — either a list or a dict with ``"rows"`` key.
        """
        url = self._toolkits_url()
        logger.debug("LIST toolkits %s params=%s", url, params)
        resp = self._session.get(url, params=params or {})
        _raise_for_status(resp)
        return resp.json()

    def list_all_toolkits(self, params: Optional[dict] = None) -> list[dict]:
        """Return ALL toolkits as a flat list.

        Handles both response shapes: plain list and ``{"rows": [...], "total": N}``.
        Paginates automatically when the response includes ``"total"``.

        Args:
            params: Optional query parameters (e.g., {'toolkit_type': 'github'})

        Returns:
            List of toolkit dicts, each with at least ``"id"`` and ``"name"``.
        """
        all_items: list[dict] = []
        offset = 0
        limit = 100

        while True:
            page_params = dict(params or {})
            page_params.update({"offset": offset, "limit": limit})
            data = self.list_toolkits(params=page_params)

            if isinstance(data, list):
                # API returned a plain list — no pagination info available
                all_items.extend(data)
                break

            rows = data.get("rows", [])
            total = data.get("total", len(rows))
            all_items.extend(rows)

            logger.debug(
                "Fetched toolkits page: offset=%d limit=%d got=%d total=%d",
                offset, limit, len(rows), total,
            )

            if len(all_items) >= total or len(rows) < limit:
                break
            offset += limit

        logger.info("list_all_toolkits: fetched %d toolkits", len(all_items))
        return all_items

    def create_github_toolkit(
        self,
        name: str,
        description: str,
        credential_elitea_title: str,
        repository: str,
        active_branch: str,
        base_branch: str,
        selected_tools: list[str] | None = None,
    ) -> dict:
        """Create a GitHub toolkit and return its JSON representation.

        Args:
            name: Toolkit display name.
            description: Short description.
            credential_elitea_title: The ``elitea_title`` of the credential to use.
            repository: GitHub repository in ``owner/repo`` format.
            active_branch: Branch for toolkit operations.
            base_branch: Base branch for comparisons (e.g. ``main``).
            selected_tools: Optional explicit tool-name list for
                ``settings.selected_tools``. Omitted (``None``) reproduces the
                original behavior — no key in ``settings`` at all. This is
                load-bearing for the pipeline Toolkit node (ELITEA-2010): a
                toolkit created WITHOUT ``selected_tools`` renders a Toolkit
                node with no Tool select at all (0 options, absent from the
                DOM) — confirmed live during ELITEA-2010 exploration; the
                Toolkit node's Tool dropdown is driven by the toolkit's own
                ``settings.selected_tools``, not a dynamic "discover all
                tools" call.

        Returns:
            Dict with ``id`` and other toolkit fields.
        """
        url = self._toolkits_url()
        settings: dict = {
            "github_configuration": {
                "elitea_title": credential_elitea_title,
                "private": False,
            },
            "repository": repository,
            "active_branch": active_branch,
            "base_branch": base_branch,
        }
        if selected_tools is not None:
            settings["selected_tools"] = selected_tools
        payload = {
            "type": "github",
            "name": name,
            "description": description,
            "settings": settings,
        }
        logger.debug("CREATE github toolkit %s name=%s", url, name)
        resp = self._session.post(
            url, json=payload, headers={"Content-Type": "application/json"}
        )
        if not resp.ok:
            logger.error(
                "Failed to create toolkit: status=%s body=%s",
                resp.status_code,
                resp.text[:500],
            )
        _raise_for_status(resp)
        return resp.json()

    def create_toolkit(self, name: str, description: str, toolkit_type: str,
                       settings: dict) -> dict:
        """Create a toolkit of any type using a settings dict.

        Args:
            name: Toolkit display name.
            description: Short description.
            toolkit_type: API type value (e.g. "github", "jira").
            settings: Type-specific settings dict (include "selected_tools" list for tools).
        """
        url = self._toolkits_url()
        payload = {
            "type": toolkit_type,
            "name": name,
            "description": description,
            "settings": settings,
        }
        logger.debug(f"Creating toolkit with payload: {payload}")
        resp = self._session.post(
            url, json=payload, headers={"Content-Type": "application/json"}
        )
        if not resp.ok:
            logger.error(f"Failed to create toolkit. Status: {resp.status_code}, Response: {resp.text}")
        _raise_for_status(resp)
        return resp.json()

    def create_artifact_toolkit(self, name: str, description: str, bucket_name: str) -> dict:
        """Create an Artifact (storage) toolkit pointing to a specific bucket.

        Args:
            name: Toolkit display name.
            description: Short description.
            bucket_name: Name of the artifact bucket to connect to.

        Returns:
            Dict with ``id`` and other toolkit fields.
        """
        url = self._toolkits_url()
        payload = {
            "type": "artifact",
            "name": name,
            "description": description,
            "settings": {
                "pgvector_configuration": None,
                "embedding_model": "text-embedding-3-small",
                "bucket": bucket_name,
                "selected_tools": [
                    "index_data", "list_indexes", "search_index",
                    "stepback_search_index", "stepback_summary_index", "remove_index",
                    "list_files", "create_file", "read_file", "get_file_metadata",
                    "delete_file", "append_data", "create_new_bucket",
                    "read_multiple_files", "grep_file", "edit_file",
                ],
            },
        }
        logger.debug("CREATE artifact toolkit %s name=%s bucket=%s", url, name, bucket_name)
        resp = self._session.post(url, json=payload, headers={"Content-Type": "application/json"})
        if not resp.ok:
            logger.error(
                "Failed to create artifact toolkit: status=%s body=%s",
                resp.status_code, resp.text[:500],
            )
        _raise_for_status(resp)
        return resp.json()

    def delete_toolkit(self, toolkit_id: int) -> None:
        """Delete a toolkit."""
        url = self._toolkits_url(toolkit_id)
        logger.debug("DELETE toolkit %s", url)
        resp = self._session.delete(url)
        _raise_for_status(resp)

    def get_toolkit(self, toolkit_id: int) -> dict:
        """Fetch a single toolkit's full JSON representation.

        Used to re-embed an existing toolkit (e.g. the environment's
        pre-existing ``Remote Github`` MCP, id 3) as a full object in a
        pipeline version's ``tools`` list — the create/update endpoint
        requires the full toolkit dict (``type`` + ``settings``), not a
        bare ``{"id": ...}`` reference (confirmed empirically: a bare
        reference 400s with "Missing 'settings'").
        """
        url = self._toolkits_url(toolkit_id)
        logger.debug("GET toolkit %s", url)
        resp = self._session.get(url)
        _raise_for_status(resp)
        return resp.json()

    def sync_mcp_tools(self, url: str, timeout: int = 60, ssl_verify: bool = True) -> list[dict]:
        """Probe a remote MCP server and return its live tool list.

        Hits the same ``mcp_sync_tools`` endpoint the UI's "Load Tools"
        button calls (``EliteaUI/src/api/toolkits.js``). Returns the raw
        tool list — each item shaped ``{"name", "description", "inputSchema"}``
        — for ``create_remote_mcp_toolkit`` to convert into the toolkit's
        ``available_mcp_tools`` schema.

        Args:
            url: The MCP server's URL (e.g. ``https://mcp.deepwiki.com/mcp``).
            timeout: Seconds to wait for the MCP handshake.
            ssl_verify: Whether to verify the server's TLS certificate.

        Returns:
            List of tool dicts as reported by the MCP server.

        Raises:
            RuntimeError: If the sync call reports failure (bad URL, MCP
                server unreachable, auth required, etc.).
        """
        sync_url = (
            f"{self.base_url}/elitea_core/mcp_sync_tools/prompt_lib/{self.project_id}"
            f"?await_response=true"
        )
        payload = {"url": url, "timeout": timeout, "ssl_verify": ssl_verify}
        logger.debug("POST mcp_sync_tools %s url=%s", sync_url, url)
        resp = self._session.post(
            sync_url, json=payload, headers={"Content-Type": "application/json"}
        )
        _raise_for_status(resp)
        result = resp.json().get("result", {})
        if not result.get("success"):
            raise RuntimeError(f"mcp_sync_tools failed for {url!r}: {result}")
        return result.get("tools", [])

    def create_remote_mcp_toolkit(self, name: str, description: str, url: str, tools: list[dict]) -> dict:
        """Create a Remote MCP toolkit with a real, working tool list.

        Unlike a bare toolkit create, this populates ``settings.selected_tools``
        and ``settings.available_mcp_tools`` from an already-synced tool list
        (see ``sync_mcp_tools``) — the pipeline MCP node's Toolkit/Tool
        dropdowns resolve tool names and parameter schemas straight from
        these fields client-side (``useFunctionInputMapping``: MCP toolkits
        carry their schemas synchronously in ``settings.available_mcp_tools``,
        no live reconnection needed at pipeline-load time — confirmed via
        ELITEA-1954 exploration; this is why a plain
        ``create_toolkit(type="mcp", ...)`` without a synced tool list
        produces a toolkit whose pipeline-node Tool dropdown never
        populates).

        Args:
            name: Toolkit display name.
            description: Short description.
            url: The MCP server URL.
            tools: Raw tool list from ``sync_mcp_tools(url)``.

        Returns:
            The created toolkit's JSON representation.
        """
        available_mcp_tools = [
            {
                "label": tool["name"],
                "value": tool["name"],
                "args_schema": tool.get("inputSchema", {}),
                "description": tool.get("description", ""),
            }
            for tool in tools
        ]
        toolkit_settings = {
            "url": url,
            "headers": {},
            "client_id": "",
            "client_secret": "",
            "scopes": [],
            "timeout": "300",
            "cache_ttl": "300",
            "enable_caching": True,
            "ssl_verify": True,
            "selected_tools": [tool["name"] for tool in tools],
            "available_mcp_tools": available_mcp_tools,
        }
        return self.create_toolkit(
            name=name, description=description, toolkit_type="mcp", settings=toolkit_settings
        )

    def close(self):
        """Close the underlying HTTP session."""
        self._session.close()
