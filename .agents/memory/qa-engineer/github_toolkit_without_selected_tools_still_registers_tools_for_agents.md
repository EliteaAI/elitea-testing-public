---
name: github_toolkit without selected_tools STILL registers tools for an agent chat participant
description: Disproves generalising the ELITEA-2010 zero-tools finding to the agent-participant chat path; also records the two distinct failure signatures of ELITEA-0143.
type: feedback
aliases: [ELITEA-0143, github_toolkit fixture, selected_tools agent chat, no GitHub toolkit tool available]
tags: [area/toolkits, area/chat, type/finding]
created: 2026-08-27
updated: 2026-08-27
---

## The fact (verified live 2026-08-27, 3/3 runs)

`fixtures/data_fixtures.py::github_toolkit` creates the toolkit WITHOUT
`settings.selected_tools`. Attached to an agent and driven through the
**agent-as-chat-participant** path, the agent still receives the toolkit's
tools and invokes them. Evidence = the product's own thought-accordion chip:
`autotest_gh_toolkit_test_agent_w: list_branches_in_repo`.

So the ELITEA-2010 finding recorded in that fixture's sibling docstring
(`github_toolkit_with_selected_tools`) is **scoped to the pipeline Toolkit
node's Tool dropdown**, a UI form that reads the toolkit's own
`settings.selected_tools`. Do NOT generalise it to agent runtime tool
registration. Same caveat applies to my
[[slash_mention_zero_tools_panel_still_renders_1596]] note — that is the
chat `/`-mention panel, also a UI reader of `selected_tools`, not the runtime.

## Two DISTINCT signatures — don't conflate them

| Signature | Cause | Where seen |
|---|---|---|
| `...call failed with an authentication error: 401 Bad credentials` (agent authored the message, tool chip present) | expired `GIT_HUB_TOKEN` in the local `.env.test` (#1673) | localhost, 3/3 |
| `I don't have a GitHub toolkit tool available in this session — no such function/tool has been provided to me` (message authored by **Elitea**, model chip **Anthropic Sonnet 5**, NO tool chip) | unknown, dev/CI-user-specific | GHA dev-stable runs 32910843812 (08-25) + 32931571484 (08-26) |

An expired credential NEVER produces the second wording — the tool is
registered and the failure is reported as a tool error. If you see
"no tool available", the credential is not your answer.

## Local runs hit the DEV backend

`ELITEA_API_BASE = https://dev.elitea.ai/api/v2`, project 399. Only the UI is
localhost. So "works locally" already proves the DEV backend's agent+toolkit
path works — for MY user/project. CI shards run as `user1..user9/ADMIN`, each
with its own project id secret, so a CI-only failure is a per-project
difference, not a backend-wide defect.

## Latent test defect found in passing

`ChatPage.add_agent_participant("autotest_")` picks
`li[role=menuitem]:has-text("autotest_")`.**first**, and the plus-menu search is
fuzzy — `query="autotest_"` on dev project 399 returns agents literally named
`autotest GH PR Reviewer 735022` (no underscore). Not identity-safe in a
populated project. `add_agent_participant_by_id(project_id, agent_id)`
(ELITEA-2089, testid-based) is the correct call for a test that just created
its own agent.

## PROVEN 2026-08-27: `add_agent_participant(prefix)` picks the ALPHABETICALLY-FIRST match

Live probe against project 399, driving the real `ChatPage` page object.
The plus-menu agent list is ordered **alphabetically ascending by name**
(recency-desc only breaks ties between identical names), so `.first` is
"alphabetically first `autotest_*` agent in the project", never "the agent
this test just created".

```
### MENU ORDER for prefix 'autotest_' (n=6)
###   [0] agents-menu-item-agent-399-9980  'autotest_aaa_probe'              <- pre-existing
###   [1] agents-menu-item-agent-399-9979  'autotest_test_add_toolkit_to_age'<- pre-existing
###   [2] agents-menu-item-agent-399-9981  'autotest_test_agent_with_toolkit'<- the fresh one
### ADDED PARTICIPANT: agent_id=9980
### VERDICT: fresh=9981 added=[9980] -> WRONG AGENT ADDED
```

Same-name duplicates are SAFE (newest wins) — the hazard is any *other*
`autotest_*` agent sorting earlier. `autotest_test_add_toolkit_to_age`
(from `test_agent_with_github_toolkit.py`, same TMS case) is exactly such a name.
Fix: `add_agent_participant_by_id(project_id, agent_id)`.
