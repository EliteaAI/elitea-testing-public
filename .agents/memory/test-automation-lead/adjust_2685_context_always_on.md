# ELITEA-2377 / #2685 — Context Management always-on (EL-6898)
Class A drift: DEV removed `context-management-toggle` + `max-context-tokens-input` (EliteaUI 7242d9c3). Fixed wait_for_page_load + Step 2 precondition. ELITEA-2374 and chat/test_context_management.py still red for the same drift — need their own adjust cards.
Host note: no automation/.env.test here → APP_PREFIX defaults "" → 404s; export APP_PREFIX=/app for gate runs. Playwright MCP chrome not installed; probe DEV with python playwright + storage state.
