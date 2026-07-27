---
name: Blocker #524 blocks all agent creation (pipeline-wide, not just one case)
description: Open bug #524 (temperature vs reasoning_effort 400 on agent create) breaks both the UI form and the AgentAPI.create_agent() fixture used across the whole agent test suite — check its status before dispatching any analyst on an agent-creation-dependent case
type: project
---

## What #524 is

`EliteaAI/elitea-testing-public#524` — "[BUG] Agent create fails 400: default LLM
settings send temperature with reasoning_effort on a reasoning-capable model".
Filed from case #67 (ELITEA-1889). `POST .../applications/prompt_lib/399` returns
400 with `temperature is not allowed together with a reasoning_effort (other than
'none')` whenever agent creation is attempted with the platform's current default
LLM settings.

## Why it's wider than it looks

It's not just the raw "create agent" UI form. `automation/api/client.py`'s
`AgentAPI.create_agent()` hard-codes the same conflicting combo
(`temperature: 0.6` + `reasoning_effort: "medium"`) in its default `llm_settings`
payload (~lines 386-390). That means **any test that provisions an agent via the
`agent_id` fixture, or any direct call to `AgentAPI.create_agent()`, currently
fails at setup** — not just tests that exercise the create form directly. This
spans a large fraction of `tests/ui/agents/`, `tests/ui/chat/`, `tests/ui/skills/`.

Confirmed twice independently: once from #67/ELITEA-1889's original analyst pass,
again from #71/ELITEA-1897's analyst pass (2026-07-15) which additionally
reproduced the API-fixture failure via `test_agent_detail_page_loads` and
`test_agent_instructions_field`.

## What this means for future dispatches

**Before dispatching an analyst on any case whose Steps require creating an
agent (or that likely uses the `agent_id` fixture), check #524's state first**
(`gh issue view 524 --repo EliteaAI/elitea-testing-public`). If it's still open
and unfixed, the case is going to hit the same wall — don't burn an analyst
dispatch re-discovering an already-diagnosed blocker. Either:

- Park the case immediately as `Blocked` / "Waiting on #524" without dispatching
  an analyst at all, if the case is agent-creation-dependent end-to-end, OR
- If only some of a case's fixture setup touches `agent_id` and the rest doesn't,
  judge case-by-case whether analysis can still proceed on the non-blocked parts.

Once #524 is fixed: every case parked on it should be resumed (checked via a
quick `gh issue search`/label sweep for `Waiting on #524` in comments), not just
the one that happened to surface it first.
