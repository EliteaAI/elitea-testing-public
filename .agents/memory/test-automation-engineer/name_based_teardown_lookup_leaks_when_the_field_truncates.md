---
name: A name-based teardown lookup leaks silently when the name field truncates
description: If a spec types a name longer than the field's maxLength and then looks the object up BY THAT NAME, the lookup never matches, the teardown skips, and the test still reports PASS — the leak is invisible on green runs
type: feedback
aliases: [teardown leak, silent truncation leak, created_id stays None, maxLength lookup miss, cleanup skipped but passed]
tags: [area/teardown, area/test-data, type/failure-mode]
created: 2026-09-10
updated: 2026-09-10
---

## The mechanism

Three ordinary choices combine into an invisible leak:

1. the spec generates a name longer than the field's `maxLength`;
2. the browser **truncates silently** — no error, no toast, no field error;
3. teardown finds the object by **name** (`next(t for t in rows if t["name"] == name)`),
   so the lookup misses, `created_id` stays `None`, and `if created_id:` skips the delete.

If the lookup's result is not asserted, **the test PASSES while leaking**. That is the
part worth remembering: this failure mode does not produce a red, so no gate catches it,
and `N`x-green makes it *more* confident, not less.

Found on `test_create_toolkit` (#2123): `AutoTest {display} Toolkit {ts}` is 34-38 chars
against `MAX_NAME_LENGTH = 32`, so github / gitlab / bitbucket / confluence leaked a
toolkit on **every** run for as long as the spec existed. Jira happened to be exactly 32
and did not. Confirmed by control: the leaked object's stored name was
`AutoTest GitHub Toolkit 17890038` — visibly clipped.

## What to do instead

- **Take the id from the create response, not from a name lookup.** `page.expect_response`
  on the create POST gives you `body["id"]` — it cannot be lost to truncation, to
  pagination, or to an assert that raises first.
- **Assert the value landed** — `expect(name_input).to_have_value(name)` is what converts
  the silent truncation into a loud, immediate Step-3 failure. It is the cheapest guard
  in the file and it is what surfaced this.
- **Keep generated names inside the cap**, and guard the construction with a named
  constant so a future entity type with a longer display name fails loudly instead of
  quietly.
- Suspect this whenever a spec's cleanup is conditional on a lookup you never asserted.

`MAX_NAME_LENGTH = 32` (`EliteaUI src/common/constants.js:66`) is shared by the agent,
toolkit and application name fields — see [[pipeline_agent_name_field_32char_silent_truncation]]
for the agent-side sighting and [[build_with_ai_review_form_name_32char_validation_blocks_approve]]
for the one form that blocks instead of truncating.

Related: [[teardown_restore_route_guard]] · [[users_batch_edit_roles_cleanup_leak_diagnosis]]
