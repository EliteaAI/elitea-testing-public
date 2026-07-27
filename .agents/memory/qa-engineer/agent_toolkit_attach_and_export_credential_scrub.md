---
name: Agent toolkit-attach flow and export credential-scrub proof technique
description: How to attach an external toolkit to an Agent via UI (agent-add-toolkit-button under Tools, always-visible sub-row), and the byte-level grep technique for proving an exported .md file never leaks a toolkit credential's raw secret value.
type: feedback
---

## Attaching an external toolkit to an Agent (UI)

On the Agent detail page, the Tools section always shows a row of 4
sub-buttons above the MODULES grid: **Toolkit / MCP / Agent / Pipeline** —
these are visible without needing to click "Show all" (that toggle only
expands/collapses the MODULES switches grid below them). The Toolkit button
resolves via `data-testid="agent-add-toolkit-button"` (confirmed on `main`,
ELITEA-1894 run). Clicking it opens a search popper with
`toolkit-search-input`; the toolkit itself is selected by its exact name as
a `menuitem` (no dedicated per-item testid observed live — matches the
existing `add_toolkit()` page-object pattern,
`automation/pages/agent_detail_page.py:471`). **The toolkit must already
exist** — this UI flow only attaches a pre-created toolkit, it does not
create one inline. Create the toolkit (and its backing credential) via API
first: `CredentialAPI.create_github_credential()` →
`ToolkitAPI.create_github_toolkit(credential_elitea_title=...)`
(`automation/api/client.py:1037`, `:1437`), or reuse the existing
`github_credential`/`github_toolkit` pytest fixtures
(`automation/fixtures/data_fixtures.py:204`, `:241`) — both already skip
cleanly when `GIT_HUB_TOKEN` is unset and self-cleanup on teardown. Both
`CredentialAPI`/`ToolkitAPI` fall back to Bearer-token auth
(`ELITEA_API_TOKEN`) when constructed with `browser_cookies=[]`, so they can
be driven from a bare python script outside pytest/browser context — handy
for fast manual test-data setup during analyst exploration.

## Proving credential non-leakage in an exported .md file

The exported Agent `.md`'s `toolkits:` YAML block contains a
`github_configuration.elitea_title` field — a non-secret *reference* to the
credential, never the underlying access token. To prove this convincingly
(not just "no `access_token:` key present", which would miss leakage under
an unexpected key name), grep the raw downloaded file's bytes for the
**literal live secret value** itself:

```bash
GH_TOK=$(grep "^GIT_HUB_TOKEN=" ../.env.test | cut -d= -f2-)
grep -c "$GH_TOK" downloaded-file.md   # must be 0
grep -i "access_token\|api_key\|secret\|password\|ghp_\|github_pat_" downloaded-file.md   # sanity net for other patterns
```

This is the load-bearing technique — asserting on key names alone is a
weaker proof than grepping for the actual secret value, since it also
catches leaks under a different/unexpected key.

## Cross-reference

Companion case to `test-specs/skills/l3_export-agent-with-attached-skills_ELITEA-1794.md`
(Skill-content export) — see
`test-specs/skills/l3_export-agent-no-nested-dependencies_ELITEA-1894.md`
for the full worked case using both techniques above.
