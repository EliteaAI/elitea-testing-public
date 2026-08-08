---
name: Multi expect_response with-block hangs if one leg never fires
description: A helper entering N expect_response context managers in one `with` block requires ALL N responses — reusing it for a scenario where only a subset of calls fire will hang/timeout, not skip gracefully.
type: reference
---

Seen in `automation/pages/generate_agent_modal_page.py`: `click_approve_and_wait_for_creation()`
(ELITEA-1909) enters three `page.expect_response(...)` context managers in one `with` block
(base-create POST + toolkit-association PATCH + agent-relation PATCH) — Python's `with a, b, c:`
semantics mean the block only exits once every manager's condition is satisfied. That is correct
for the resources-selected flow (all three calls always fire together) but silently wrong for any
sibling scenario where one of the legs never fires — e.g. a plain/no-resources draft approve,
which only ever fires the base-create POST (ELITEA-1914).

Reviewing a PR that reuses (or claims to reuse) a multi-`expect_response` wait helper for a
narrower/different scenario: check whether every leg's triggering condition genuinely holds for
the new scenario. If not, the correct fix is a **new, narrower helper** waiting only on the calls
that actually fire for that path (as ELITEA-1914's `click_approve_and_wait_for_agent_created()`
does) — not reusing the broader helper "because it already exists." A hang here reads as a plain
timeout failure with no obvious cause unless you trace back to the `with` block's fan-in semantics.
