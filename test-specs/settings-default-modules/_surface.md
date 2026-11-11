# Surface digest: Settings > General > Default Modules (verified 2026-11-11, DEV)
- Route `/app/settings/project-general`. Sections (testids): `project-general-section`, `ai-configurations`, `default-modules-section`, `web-search-section` (separate admin card "Web Search / Uses the platform toolkit (...)", `web-search-settings-card`), `chat-configuration-section`.
- Default Modules: grid Module | Chats | Agents; rows from `MODULE_ORDER` in EliteaUI `DefaultModulesSettings.jsx` (image_generation, web_search, data_analysis, internal_mcp, skill_builder, project_context_builder, ask_user, planner, pyodide, swarm, lazy_tools_mode). Rows have NO testids; switches are bare `input[role=switch]` (2 per row; Agents shows an em dash when no agent field).
- Row description = `InternalToolsConstants` `infoTooltip.text`; no (i) icon in settings (the chat Modules panel has it).
- web_search row only if `platform_settings.tool_spend.web_search.available`.
- Autosave on blur: click switch then click neutral body area -> `PUT /api/v2/social/module_settings/{project_id}` 200. Persisted per user; default state Chats OFF. New chat inherits via `default_web_search_enabled` (Chats) / `default_agent_web_search_enabled` (Agents).
- Chat Modules panel: `plus-menu-button` -> click `internal-tools-menuitem` -> `modules-toggle-<key>`; web_search is the last toggle (11 total with it).
- Web-search tool call renders as `chat-answer-tool-chip` text "Web Search: web_search".
- Platform announcement dialog (`platform-banner-close`) blocks clicks: dismiss first. Storage state expires quickly (refresh `dev_storage_state.py`).
- Playwright MCP chrome binary missing in this sandbox; analysis done with scripted headless chromium probes via repo venv.
