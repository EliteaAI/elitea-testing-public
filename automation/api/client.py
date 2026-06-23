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

import requests

from config import settings

logger = logging.getLogger("elitea.api")


def _raise_for_status(resp: requests.Response) -> None:
    """Raise HTTPError with the response body included in the message.

    Replaces bare ``resp.raise_for_status()`` calls so that test failures
    show the API's error payload (validation message, field errors, etc.)
    instead of just the HTTP status code.
    """
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        raise requests.HTTPError(
            f"{exc} — body: {body}",
            response=resp,
        ) from exc


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

        self._session = requests.Session()
        for c in browser_cookies:
            self._session.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))

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
        url = (
            f"{self.base_url}/elitea_core/conversation/prompt_lib"
            f"/{self.project_id}/{conversation_id}"
        )
        logger.debug("GET conversation %s", url)
        resp = self._session.get(url)
        _raise_for_status(resp)
        return resp.json()

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

        self._session = requests.Session()
        for c in browser_cookies:
            self._session.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))

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
                    "llm_settings": {
                        "max_tokens": -1,
                        "temperature": 0.6,
                        "reasoning_effort": "medium",
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

        self._session = requests.Session()
        for c in browser_cookies:
            self._session.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))

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
                    "llm_settings": {
                        "max_tokens": -1,
                        "temperature": 0.6,
                        "reasoning_effort": "medium",
                        "model_name": settings.default_model_name,
                        "model_project_id": settings.default_model_project_id,
                    },
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
                    "llm_settings": {
                        "max_tokens": -1,
                        "temperature": 0.6,
                        "reasoning_effort": "medium",
                        "model_name": model_name,
                        "model_project_id": settings.default_model_project_id,
                    },
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
                    "llm_settings": {
                        "max_tokens": -1,
                        "temperature": 0.6,
                        "reasoning_effort": "medium",
                        "model_name": settings.default_model_name,
                        "model_project_id": settings.default_model_project_id,
                    },
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

        self._session = requests.Session()
        for c in browser_cookies:
            self._session.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))

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

        self._session = requests.Session()
        for c in browser_cookies:
            self._session.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))

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
    ) -> dict:
        """Create a GitHub toolkit and return its JSON representation.

        Args:
            name: Toolkit display name.
            description: Short description.
            credential_elitea_title: The ``elitea_title`` of the credential to use.
            repository: GitHub repository in ``owner/repo`` format.
            active_branch: Branch for toolkit operations.
            base_branch: Base branch for comparisons (e.g. ``main``).

        Returns:
            Dict with ``id`` and other toolkit fields.
        """
        url = self._toolkits_url()
        payload = {
            "type": "github",
            "name": name,
            "description": description,
            "settings": {
                "github_configuration": {
                    "elitea_title": credential_elitea_title,
                    "private": False,
                },
                "repository": repository,
                "active_branch": active_branch,
                "base_branch": base_branch,
            },
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
            settings: Type-specific settings dict.
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

    def delete_toolkit(self, toolkit_id: int) -> None:
        """Delete a toolkit."""
        url = self._toolkits_url(toolkit_id)
        logger.debug("DELETE toolkit %s", url)
        resp = self._session.delete(url)
        _raise_for_status(resp)

    def close(self):
        """Close the underlying HTTP session."""
        self._session.close()
