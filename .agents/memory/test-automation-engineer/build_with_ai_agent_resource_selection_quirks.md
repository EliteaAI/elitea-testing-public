---
name: Build with AI agent resource-selection quirks (implementer)
description: create_agent_full()'s reasoning_effort field can just be omitted (not only value-swapped) to dodge #524; live (non-mocked) generate-draft calls need their own longer timeout constant separate from the mocked-response tests' fixed 300ms-delay timeout; a factory-shaped fixture yielding a related entity pair for suggestion-engine testing; nested page.expect_response context managers for waiting on a UI action's multiple sequential network calls concurrently
type: feedback
---

## #524 workaround: omitting `reasoning_effort` entirely also works

The established workaround for `AgentAPI.create_agent()`'s 400 (temperature +
reasoning_effort together, rejected by the current default model) has so far
always been a *value swap* — `reasoning_effort: "none"` (ELITEA-1884/1888/1899)
or `"low"`/`"medium"` when `"none"` itself broke something else downstream
(ELITEA-1897's embedded-chat 500). For ELITEA-1909's fixture agents — which are
never opened, edited, or chatted with; they exist purely as suggestion-engine
candidates — the simplest fix was to **omit the `reasoning_effort` key
entirely** from the `llm_settings` dict passed to `create_agent_full()`, rather
than picking a value. Worked cleanly, no downstream side effect (no chat, no
embedded conversation ever created for these agents). Try "omit the field"
first on any future variant of this 400 before reaching for a value swap —
it's the smaller diff and avoids inheriting whichever new landmine the chosen
value might carry (see `reasoning_effort_none_breaks_embedded_chat.md`).

## Live (non-mocked) generate-draft calls need a separate, longer timeout

ELITEA-1907/1915's `test_agent_build_with_ai.py` tests all mock
`generate_application_draft` with a fixed 300ms artificial delay, so their
shared `GENERATE_RESPONSE_TIMEOUT = 15000` constant is comfortably generous.
ELITEA-1909 deliberately calls the REAL endpoint (needed real
create→toolkit-PATCH→agent-relation-PATCH network-call-sequencing proof, which
a mock can't produce). The first local run hit the 15s ceiling — real LLM
latency, not a selector/product problem. Fix: added a second module constant,
`LIVE_GENERATE_RESPONSE_TIMEOUT = 30000`, used ONLY by the live-call test.
Don't bump the shared constant for this — that would silently widen the
mocked tests' timeout too and could mask a real regression there (a mocked
call taking >15s would itself be a bug worth catching fast).

## Factory-shaped fixture for a related entity PAIR

Every existing fixture in `data_fixtures.py` before this case yielded ONE
entity. ELITEA-1909 needed two related Agents in one fixture (a
"selected" one and a deliberately-"not_selected" one, both required to be
GitHub-relevant so the suggestion engine surfaces both as candidates) — see
`github_relevant_agents` fixture. Shape: yields a dict with `selected`/
`not_selected` sub-dicts (each `{"id", "name", "description"}`), creates both
via `create_agent_full()` in one function body, tears both down in one loop.
This is a reusable shape for any future "Build with AI" suggestion-engine
case needing more than one candidate of the same entity type — no factory
abstraction was built (still just a single `@pytest.fixture` function), since
one instance of the pattern doesn't yet justify one.

## Nested `page.expect_response` for a UI action with multiple sequential network calls

`GenerateAgentModalPage.click_approve_and_wait_for_creation()` clicks "Create
Agent" once, but the review-step click fires THREE sequential calls (base
create POST, toolkit-association PATCH, agent-association PATCH — all
`await`ed in series by the app, not one atomic call). Waiting on them with
nested `with self.page.expect_response(...) as a, self.page.expect_response(...)
as b, self.page.expect_response(...) as c: <click>` (Python's comma-joined
multi-context-manager `with` form) captures all three regardless of arrival
order or the UI's post-creation auto-navigation racing ahead — cleaner and
more explicit than the alternative of calling `click_generate_and_wait_for_response()`-style
helpers three times in sequence (which would only catch the first response
before the click handler even returns). Worth reaching for this shape any
time a single button click is known (from the AFS's Network Behavior section
or live exploration) to fire more than one call whose responses the test
needs to assert on individually.

## Confirmed-twice flake: `test_selected_suggested_resources_attached_and_non_selected_absent` (ELITEA-1909)

Running the full `TestAgentBuildWithAISelectedResourcesAttached` class turns up
this pre-existing test failing deterministically on `assert
modal.is_resource_section_visible("agent")` — `"Suggested Agents:"` section
doesn't render, i.e. the live suggestion engine isn't surfacing the
`github_relevant_agents` fixture agents as relevant for this run. Confirmed
independently in **two separate implementer sessions** (ELITEA-1914's build,
and ELITEA-1908's build) that this is NOT caused by either diff: both PRs are
pure-additive to files/methods that test never touches, and the failure
reproduces identically running that ONE test in total isolation. Root cause is
live-LLM/suggestion-engine non-determinism (same class of gap as the open bug
`EliteaAI/elitea-testing-public#1081` — project 400's suggestion engine not
reliably surfacing fixture-created candidates), not a regression. If you see
this exact assertion fail while running the covering class for an
`extend-existing` PR in this file: re-run the failing test in isolation first
— if it fails identically alone, it's this known flake, not your change; note
it in the Run Report and move on rather than debugging your own diff.

(from ELITEA-1909, confirmed recurring via ELITEA-1914 and ELITEA-1908)
