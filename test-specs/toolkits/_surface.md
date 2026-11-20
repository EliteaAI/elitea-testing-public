# Toolkits — Test Toolkit surface digest (handle cache; verify as used)

- Reach: `toolkit_api.create_artifact_toolkit(name, desc, bucket)` -> `ToolkitDetailPage.navigate_to_toolkit(id)` -> `wait_for_config_surface` -> `open_test_surface()` (route `/toolkits/*/{id}/test`) -> `ToolkitTestSettingsPage.get_tool_chip("List files").click()` -> `run_tool()` -> `wait_for_tool_result(90000)`. Verified 2026-11-20 (ELITEA-4758), ~25s.
- Result card toolbar: `chat-copy-markdown-button` / `chat-copy-text-button` (aria-labels Copy markdown / Copy text), inside `chat-message-list`; hover tooltip `role=tooltip`; click toast `toast-message` ("Markdown copied to clipboard." / "Text copied to clipboard."), `toast-alert` data-severity=info. Same handles as agent/skill/pipeline test panels.
- Test panel testids present: toolkit-test-tool-select(-combobox), toolkit-test-param-*, toolkit-test-run-tool-button.
- Playwright MCP chrome missing in sandbox; probe via pytest scratch spec (delete afterwards).
