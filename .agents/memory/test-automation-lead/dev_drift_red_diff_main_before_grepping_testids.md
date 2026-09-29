---
name: Triaging a DEV "element not found" red
description: On a DEV red whose call log is "waiting for get_by_test_id(...)", diff main's recent commits for that component BEFORE grepping for the testid — presence in source is not presence in the DOM; and the automation/testids gate is blind to this whole class
type: feedback
---

## Rules

1. **Presence in source ≠ presence in the DOM. Grepping the testid is the WRONG
   first move.** On a DEV red reading `waiting for get_by_test_id("x")`, the
   reflex is to check whether `x` was promoted to EliteaUI `main` (the promotion
   gap). That check can come back "present on main" and still leave you with a
   red, because the element is wrapped in a render conditional. **First move:
   diff `main`'s recent commits touching that component** (`gh api
   repos/EliteaAI/EliteaUI/commits/<sha>`, then read the file on `main` at the
   testid's line and look UPWARD for an enclosing `{cond && (`). Lived 2026-09-29
   on #2377 / ELITEA-1826: `471b753c` ("fix: [EL-6687] Fixed Artifacts section UI
   issues") wrapped the artifacts toolbar in `{!isEmptyFiles && (`
   (`ArtifactTableToolbar.jsx:93`, enclosing `artifacts-upload-files-button` at
   `:118`), so on an EMPTY bucket the button is never rendered. The testid was on
   `main` the whole time — the lead's promotion-gap check was a red herring that
   cost a full hypothesis cycle.

2. **A commit timestamp ~hours before the run is the tell.** `471b753c` landed
   2026-09-23T09:35Z; run #197 started 2026-09-24T01:14Z (~15.6 h later). When a
   test that passed for weeks dies on all 3 retries with an identical call log,
   date the product change first — it localises the cause faster than reading the
   test.

3. **The `automation/testids` local gate CANNOT detect DEV drift — do not trust a
   green there for this class.** That branch runs behind `main` (2026-09-29: 497
   ahead / **152 behind**), so a `main` conditional simply does not exist on it —
   `isEmptyFiles` had **zero** occurrences. Both the broken AND the fixed test
   pass on `localhost:5173`. For any DEV-drift fix, verification must run against
   DEV/`main`, or `automation/testids` must first be synced past the offending
   commit. Say this out loud in the closure/blocker record; a local green is false
   confidence and an audit will read it as evidence.

4. **Differential triage beats deep-diving one failure.** Before blaming env,
   credentials, project-id or the fixture, check what ELSE ran in the same job.
   19 artifacts tests passed in the same user2 job on the same token/project —
   which disproves every environment hypothesis in one step. Then ask what makes
   the failing test unique: here it was the only spec calling toolbar
   `upload_files()` on a genuinely empty bucket, while every passing sibling
   seeded a file first (`test_artifacts_upload_duplicate_skip.py:112`) or branched
   on state outright (`..._three_options_verify_selection.py:284` vs `:376`).

5. **The intake pipeline's own stated analysis is a claim, not evidence — verify
   it.** #2377's body asserted "the 404 teardown errors confirm buckets were never
   successfully created". False: **passing** tests log the same `DELETE … 404`
   (filed defect **#636**, annotated at
   `test_artifacts_create_bucket_upload_file.py:347`). Taking it at face value
   sends triage hunting a fixture bug that does not exist. Cross-check any intake
   claim against a PASSING test's log before building on it.

6. **A generic template instruction can be actively harmful — judge it, don't
   obey it.** #2377 instruction #7 said "use regular locators (role, text, label)
   instead of data-testid". It cannot fix an unrendered element, and worse,
   `get_by_role("button", name="Upload files")` matches a DIFFERENT control (the
   empty-state centre button, `ArtifactTableNoFiles.jsx`), so complying would have
   produced a silent green against the wrong element while destroying the case's
   stated entry point. It also contradicts the project's testid-only policy. Reject
   it in writing and ask a human to ratify the deviation.

7. **Reverse-masking: when the product is right and the CASE is stale, file a TMS
   clarification, not a `bug`.** A deliberate, internally-consistent UX change
   (both upload entry points still reachable) is not a defect. Check for the
   alternative affordance the product now expects
   (`artifacts-upload-files-empty-state-button`) before reaching for the `bug`
   label.
