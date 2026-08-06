---
name: Asserting absence of autosave PUT on client validation failure
description: Pattern for proving an out-of-range numeric field blocked its autosave submit
type: feedback
---

Surface: `/settings/memory` numeric fields (Max Context Tokens, Preserve Recent
Messages, Target Summary Tokens) — `useFormikAutoSaveOnBlur` calls
`validateForm()` before `submitForm()` and returns early when Yup validation
fails. So an out-of-range value never fires `PUT /api/v2/social/author/` at
all — there is no response to `page.expect_response(...)` (that only proves a
positive). This is a genuine "prove absence" case, not a masked sleep:

```python
put_seen: list[Response] = []

def _capture_put(response: Response) -> None:
    if _is_autosave_put_response(response):
        put_seen.append(response)

page.on("response", _capture_put)
try:
    profile.set_target_summary_tokens(99)  # below min
    expect(profile.target_summary_tokens_input).to_have_attribute("aria-invalid", "true")
    page.wait_for_timeout(2_000)  # bounded — no positive condition exists to wait on
finally:
    page.remove_listener("response", _capture_put)
assert not put_seen
```

The invalid-state assertion (`aria-invalid="true"` via Playwright's
auto-retrying `expect(...).to_have_attribute(...)`) already proves the
mechanism; the bounded wait + listener only proves the *consequence* (no
network call). Document the 2s bound's reasoning inline — it's not an
arbitrary "hope it's enough," it's specifically bounding a negative check.
`not_to_have_attribute("aria-invalid", "true")` is the valid-state counterpart
(no positive/negative parity gap — Playwright's `LocatorAssertions` has both).

Reused established siblings on this same surface: `settings_memory_autosave_put_get_refetch_race.md`
(the dual PUT+GET wait already used for valid toggles/values).
