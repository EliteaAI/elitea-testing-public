---
name: Guardrails config is reachable by REST under mode administration
description: The standard test user CAN read/write platform guardrails config — mode must be `administration`, not `prompt_lib` (403); no Admin UI needed
type: reference
aliases: [guardrails config, sensitive_tools, plugin_config_values, admin config API, sensitive action tools, HITL precondition, admin UI 404]
tags: [area/chat, area/fixtures, type/endpoint]
created: 2026-08-27
updated: 2026-08-27
---

## The endpoint

```
GET  /api/v2/admin/plugin_config_values/administration/guardrails   → 200
PUT  /api/v2/admin/plugin_config_values/administration/guardrails   → 200
     {"saved": true, "requires_restart": []}
```

Authenticated with the ordinary `ELITEA_API_TOKEN` — **no admin account needed**.
`requires_restart: []` means a change applies **immediately**: mid-conversation,
no restart, no re-attach, no new conversation.

**The `mode` segment is the whole trick.** The same path under `prompt_lib` (the
OpenAPI spec's own default) returns `403 access_denied`, which reads exactly like
"you lack permission" and is why this avenue was written off for three weeks.

Payload shape: `sensitive_tools` is a dict of `{toolkit_type: [tool_name, ...]}`,
e.g. `{"artifact": ["delete_file"]}` — toolkit-**TYPE** scoped and **org-wide**,
not per-instance, so anything setting it must read-mutate-**restore the captured
original** and must arm the `try:` *before* the mutating PUT (see
[[arm_the_finally_before_the_mutating_write]] and `sensitive_delete_file_toolkit`
in `automation/fixtures/data_fixtures.py`).

`artifact`/`delete_file` is **not** sensitive by default on DEV — with the stock
config the tool executes and the file is really deleted, no HITL card.

## Why it matters beyond guardrails

The **Admin UI is a separate deployed application**, not part of the EliteaUI SPA —
`EliteaUI/src/routes.js` has no `/admin` route and never did, so
`localhost:5173/admin/...` renders `Page404` by design, not by regression. Any
precondition previously driven through the Admin UI is unreachable from the local
loop *via the UI*, but the config it edits is usually reachable by REST. Look for
the endpoint before declaring the case blocked (#1140 is the cautionary example).

Setting a precondition this way is **transit** substitution under
`.agents/testing.md` § Fidelity policy — permitted, and it must be declared in the
AFS § Fidelity Declaration *and* the test docstring.

Related: [[blocker_premise_symptom_vs_cause]] · [[a_parked_case_is_a_hypothesis_not_a_verdict]]
