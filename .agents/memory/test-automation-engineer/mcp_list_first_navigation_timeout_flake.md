---
name: MCP list first-navigation timeout flake
description: McpListPage.navigate()'s card_view_button wait intermittently times out on the first navigation of a fresh pytest process (~40% observed rate) — OneDrive I/O contention on Chromium cold-start, not a product defect; also causes McpListPage.has_any_mcp() to misclassify as "empty project" and spuriously seed an extra MCP
type: feedback
---

Observed during ELITEA-1941 implementation (test_mcp_search_by_name.py):
`McpListPage.wait_for_page_load()`'s `card_view_button.wait_for(state="visible",
timeout=15000)` timed out on the very first `/mcps/all` navigation of a fresh
`pytest` process in 2 of 5 consecutive run attempts — always the *first*
navigation in the process, never a subsequent one within the same run.

**Root cause (probable, matches documented gotcha):** `.agents/testing.md`
§ Known issues already records "OneDrive slowness affects anything spawning
many file ops" — this repo's working tree is OneDrive-synced. Chromium's
cold-start (profile/cache writes) on the first navigation of a process is
the most plausible point of contention. Ruled out plain server slowness:
`curl http://localhost:5173/mcps/all` consistently returns in ~2ms even
during the flaky window.

**Downstream effect on an existing helper (not touched, out of scope for an
additive AFS change):** `McpListPage.has_any_mcp()` treats any timeout on
this same wait as "project has zero MCPs" (its `try/except` around the
identical `card_view_button.wait_for()`) and proceeds to seed a brand-new
MCP via the UI create flow. This is a latent false-negative — a slow-but-
present project gets misclassified as empty. Confirmed happening live in
the pre-existing `test_mcp_view_toggle.py` (seeded an extra
`autotest_mcp_toggle_*` MCP on a run where the project already had 6).
Flag this to whoever next touches `has_any_mcp()` or MCP dashboard tests at
scale — a longer timeout or a retry-once pattern would likely fix both
symptoms, but changing shared `mcp_list_page.py` wait behavior needs the
full shared-caller regression sweep (multiple MCP test files depend on it),
so it wasn't in scope for a single-AFS additive change.

**How to handle when you hit it:** treat as an infrastructure rerun, not a
same-root-cause R2-cap rerun (each occurrence is generic I/O timing, not a
repeatable code-level cause) — just rerun the process. It has not been
observed to affect anything past the very first navigation, so a single
retry is normally sufficient.
