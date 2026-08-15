---
name: Conversation API ignores caller-supplied timestamps
description: PUT with custom created_at/updated_at is silently ignored server-side — no way to backdate a conversation into "Older" via any test-accessible surface.
type: feedback
---

Live-verified (2026-08-15, ELITEA-2140): `PUT /elitea_core/conversation/prompt_lib/{project}/{id}`
with body `{"updated_at": "2020-01-01T00:00:00Z", "created_at": "2020-01-01T00:00:00Z"}` returns
`200` but the persisted/returned timestamps are UNCHANGED from their real creation-time values.
Both fields are server-controlled. There is no test-accessible surface (UI or REST) that can seed a
conversation into the "Older" (or even "This Week") date group on demand — the shared DEV project
also commonly has zero naturally-occurring Older/Today conversations at rest (everything gets
created-and-cleaned-up by tests), so there's nothing to reuse read-only either.

**Practical consequence for any case whose precondition needs a specific date-group origin**: don't
attempt to fabricate it via `page.evaluate()`/DB injection (fidelity-policy substitution). Instead
check whether the flow under test is origin-independent — e.g. `ChatPage.select_move_to_back_to_list()`
unconditionally refreshes `updated_at` to "now" on every call, empirically confirmed via network
capture on a conversation that had never been touched since creation, so ANY conversation moved out
of a folder lands in Today regardless of its prior recency. If the flow genuinely depends on the
literal prior state and that state can't be produced, that's a real `blocked`/clarification, not an
implementation puzzle to solve around.

Also empirically confirmed same session: the "Move to" submenu, opened for a conversation already
inside a folder, lists that folder's OWN entry `aria-disabled="true"` (present, not absent, not
enabled) — self-move prevention. Read via `get_move_to_folder_item(folder_id).get_attribute("aria-disabled")`,
same `MOVE_TO_FOLDER_ITEM` template ELITEA-2135 already provisions, no new testid needed.
