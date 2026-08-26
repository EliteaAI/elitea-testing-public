---
name: A live generate-draft response is the oracle — never a hand-written payload
description: Capture the real POST response and assert the UI against it; deterministic without substituting the producer
type: feedback
aliases: [nondeterministic producer, llm assertion, generate draft oracle, response as oracle]
tags: [area/fidelity, type/pattern]
created: 2026-08-26
updated: 2026-08-26
---

`click_generate_and_wait_for_response()` returns the real Playwright response. Assert:

1. `response.status == 200` — the producer answered.
2. `body["<field>"]` is non-empty — it produced *something*.
3. the UI's rendered value **equals `body["<field>"]`** — the UI carried it through.

That is fully deterministic and fully honest: the model's variance lives on both sides of
the comparison. Cost is 5-20 s per call (Project Context generate-draft, 2026-08-26).

## Two traps when the asserted value is generated markdown

- **CodeMirror `.cm-content` has no newlines in `textContent`.** Compare per `.cm-line`.
- **`expect(locator).to_have_text([...])` normalizes only the ACTUAL text** (trim +
  collapse). Generated markdown can carry leading spaces (nested bullets), so normalize
  the EXPECTED side the same way — `" ".join(line.split())` — or the comparison fails on
  whitespace the product never mangled.

Related: [[build_with_ai_shared_generate_entity_modal]]
