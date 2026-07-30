---
name: Never assume a transition settled — the four wait/race rules
description: Four independently-confirmed classes of false-settle in this suite (networkidle before a debounced request, capture_requests_matching status None, an action returning before the SPA navigates, a cold direct-URL nav landing elsewhere) plus the two structural rules that prevent all of them.
type: feedback
---

## Rule

Between any action and the read that judges it, name the signal that proves
the transition landed. "The method returned" and "networkidle resolved" are
not signals.

1. **`networkidle` ≠ the request happened.** `wait_for_load_state("networkidle")`
   is satisfied by zero in-flight connections for 500 ms — trivially true if
   the app debounces before dispatching. Never assert on a captured response
   right after `click_save()`. Poll the captured list for a **resolved
   status** (15 s budget, not the usual 8–10 s).
2. **`capture_requests_matching()` is proven for ABSENCE only.** A positive
   `status == 200` read races to `None`. Two valid fixes: `page.expect_response()`
   (blocks; use when no other completion signal exists) or **defer the read**
   until an independent UI completion condition has already resolved (better
   for N concurrent requests). Where the response fires relative to your
   natural anchor is a fact you read out of the frontend source, not guess —
   it can fire BEFORE the wait you'd anchor to, in which case register the
   capture before Setup and still defer the read.
3. **An action method returns when the event is dispatched, not when the app
   settled.** `send_message(use_enter=True)` returns on keypress, before the
   SPA reaches `/chat/{id}`. Any state read keyed on that navigation must be
   a polling `expect(...)`, never a synchronous `.is_enabled()`/`.text_content()`.
   Two "equivalent" user actions (Enter vs button, `fill()` vs
   `press_sequentially()`) do not share timing — an AFS sentence "I verified
   path A but the test uses path B" IS a to-verify marker.
4. **A cold direct-URL nav can land somewhere else entirely** and never time
   out (`/artifacts?bucket=X` → an unrelated bucket; loose text waits don't
   catch it, #638). Re-read the live URL params after the wait and retry once;
   `AssertionError` on the second failure, never silent. Both
   `navigate_to_bucket()` and `navigate_to_bucket_folder()` are guarded — use
   them, don't roll your own `navigate()`.

**Two structural rules that pre-empt all four:**

- **A wait condition must not itself be gated behind a different
  interaction.** A `display:none`-until-hover element can never satisfy a
  visibility wait on an unhovered row. Pick an ungated ancestor, or add a
  testid to one.
- **Match the idiom to the condition's shape.** Locator `.filter(has_text=)`
  + `.wait_for(state="visible")` for pure existence/text-equality; a manual
  `time.monotonic()` poll only when Python-side logic is required (transient-
  message filtering, swallowing re-render detaches). Defaulting to whichever
  you saw last is itself "inventing an idiom."

**Infrastructure timeouts that are NOT product races** — rerun, don't fix:
first-navigation cold-start timeouts (~40%, OneDrive I/O), and the Support
Assistant's 60 s AI-response ceiling (3 sittings, up to 4 tests in one run).
Record them honestly in the Run Report; never patch a shared constant inside
an unrelated case's PR. Separately, a typed-text field has a real ceiling:
`fill_form()` uses `press_sequentially(delay=80)` against a 10 s action
timeout ⇒ any field text over ~120 chars times out looking like a product
hang. Keep planted markers short.

## Seen 7×

- ELITEA-1884 / PR #536 — networkidle resolved before the Save PUT dispatched.
- ELITEA-1808 / PR #643 — hover-gated wait condition; `capture_requests_matching()` status `None`. Addenda: ELITEA-1826 (defer-the-read), ELITEA-2114/#696 (register before Setup).
- ELITEA-2090 / PR #682 — `send_message(use_enter=True)` raced the `/chat/{id}` nav.
- …plus 4 earlier occurrence(s) — full per-case detail in the source entries below.

See also: save_networkidle_race_quirk.md ·
hover_gated_wait_condition_and_response_status_race.md ·
send_message_enter_key_races_spa_navigation.md ·
artifacts_direct_bucket_url_nav_project_id_race.md ·
mcp_list_first_navigation_timeout_flake.md ·
support_assistant_ai_response_timeout_flakiness.md ·
agent_form_fill_form_timeout_ceiling.md
