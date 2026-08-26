---
name: Build with AI suggested-resources has no display cap
description: ResourceSuggestions.jsx renders all items unconditionally, no .slice(0,5) anywhere — filed #1317
type: feedback
---

## What

`../EliteaUI/src/[fsd]/features/agent/ui/generate-agent-modal/ResourceSuggestions.jsx`
(shared by all five "Suggested {Category}:" sections in the "Build with AI" agent
draft review form — Toolkits/MCP/Pipelines/Agents/Skills) renders every item in
`items.map(...)` unconditionally. No `.slice(0, 5)` or count guard exists anywhere
in that component, `GenerateAgentReviewForm.jsx`, or `GenerateAgentModal.jsx`
(confirmed by grepping all three for `slice|MAX_|limit|cap` — only unrelated
`MAX_*` constants for name/description/welcome-message/conversation-starters).

## ⚠️ How it was "verified" — and why that is NOT a reproduction (corrected 2026-08-14)

A throwaway scratch pytest test mocked `generate_application_draft`
(`GenerateEntityModalPageBase.mock_generate_success()` / `page.route()`) with a
7-item `suggested_skills` payload; all 7 cards rendered.

**That is not a reproduction.** It demonstrates that `items.map()` maps the items it
is given — which the source grep above already established. It does **not** show the
system can reach that state. The entry originally called the technique "sanctioned";
**nothing sanctions it** — the word was borrowed from unrelated project rules
(scoped-raw-locator exceptions, sanctioned-RED merges). Mocking the response to
produce the observable a case came to check is a **terminal substitution**, forbidden
by `.agents/testing.md` § Fidelity policy.

## Status of #1317: unresolved, not established

The concern is legitimate — the suggestion source is an LLM, so ">5" is rare, not
impossible, and if neither tier caps, the requirement holds by luck. But three
questions are open and the issue was filed as though they were closed:

1. **Where does "5" come from?** It appears in exactly one TMS case (ELITEA-1910,
   `requirements: []`) and nowhere in the product source. It may be a real AC or the
   case author's assumption. Untraced.
2. **Does the backend cap?** Never checked. `generate_application_draft` has no
   documented response schema (`https://dev.elitea.ai/shared/openapi/?all=true` — NO
   `/api/v2` prefix; `/api/v2/shared/openapi/` 404s). The issue's claim that this is
   "strictly a frontend gap" **presupposes** ownership rather than establishing it.
3. **Is there a real repro?** Not yet — see above.

**The experiment that settles all three at once:** create ~8 relevant Skills as
fixtures, run **one live** generation, read the raw API response. Both answers fall
out of it (does the backend cap; does the UI over-render). This is exactly the work
the ELITEA-1910 AFS declined as "not a good use of fixture-creation effort" in order
to justify the mock — so the mock replaced not only the test but the investigation.

## What to do with a future cap/count case on this surface

- The shared-component fact (all five categories, one root cause) still holds — cite
  it, don't re-derive.
- **Live counts have never exceeded ~2** per category (ELITEA-1907/1911 precondition
  audits). Correct conclusion: the boundary **cannot be observed honestly today** ⇒
  AFS `blocked` → lead → human decision. **Not** a mocked test.
- Do not cite #1317 as settled fact in a new AFS.

## AFS

`test-specs/agents/lextend_build-with-ai-suggested-skills-section-shown-with-up-to-5-skills_ELITEA-1910.md`
