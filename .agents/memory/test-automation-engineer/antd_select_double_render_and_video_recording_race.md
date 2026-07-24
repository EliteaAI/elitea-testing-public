---
name: antd/rc-select renders each option TWICE (invisible aria mirror + real row); pytest's video recording can expose a race invisible standalone
description: get_by_role/get_by_text against an antd/rc-select dropdown match a zero-size accessibility-only mirror as well as the real visible option row — scope to `.ant-select-item-option-content` instead. Separately, a click-pair race in a multi-select deselect sequence reproduced 100% under pytest's context fixture (which always records video via CDP screencast) but passed standalone every time — the CDP screencast overhead shifts widget render timing enough to matter.
type: feedback
---

## antd/rc-select's option list is TWO trees, not one

Confirmed live (ELITEA-2007, `react-js-cron`'s Default-mode period/hour/
minute selects — but this is generic `rc-select`/antd `Select` internals,
so it applies to ANY antd-based dropdown in this codebase, not just Cron):
the option popup renders

1. an **accessibility-only mirror list**: `<div role="listbox"
   style="height:0;width:0;overflow:hidden">` containing `<div
   role="option" aria-label="…">…</div>` rows — genuinely zero-size,
   Playwright correctly refuses to click it ("element is not visible"),
   and
2. the **real visible list** (`.rc-virtual-list` → `.ant-select-item-option`
   → `.ant-select-item-option-content`) that users actually see and click.

Both trees carry the SAME text. Consequences:
- `dropdown.get_by_role("option", name=value, exact=True)` resolves to the
  INVISIBLE mirror → `Locator.click` times out ("element is not visible").
- `dropdown.get_by_text(value, exact=True)` matches BOTH the mirror's
  `role="option"` div AND the real row's `.ant-select-item-option-content`
  div → strict-mode violation (2 elements).

**Fix:** scope directly to the real-list's class,
`dropdown.locator(".ant-select-item-option-content").filter(has_text=re.compile(rf"^{re.escape(value)}$"))`
— the mirror lacks this class entirely, so this always resolves to exactly
one (real, clickable) element. Applies to option lists having no testid at
all (this is a third-party/library-internal render node — sanctioned #579
exception in `.agents/testing.md` § Locator policy, same shape as
`mcp_form_page.py`'s CodeMirror per-line-div precedent).

## A back-to-back click pair (add-then-deselect) raced ONLY under pytest

`react-js-cron`'s hour/minute Default-mode fields are ant-design
MULTI-selects whose default ("00") must be explicitly deselected after
adding a new value (clicking a new option ADDS, never replaces). The
natural "click value, then click 00 to deselect" sequence:
- passed 100% of the time in a bare `sync_playwright()` script (no pytest,
  no video recording), even after adding a `expect(row).to_have_class(...
  selected...)` wait between the two clicks;
- failed **100% of the time** under `pytest` (`HEADLESS=true pytest ...`),
  leaving BOTH values selected ("00,09" instead of "09").

Root cause: `conftest.py`'s `context` fixture always passes
`record_video_dir=...` (video is recorded for every test, only SAVED to
disk on failure) — Playwright implements this via a CDP screencast, and
that extra CDP traffic is enough to consistently shift this specific
widget's render timing relative to the click sequence. This is a
same-process, environment-triggered race, not a flake that comes and goes
randomly — it was 100% reproducible in each environment, just with
DIFFERENT outcomes per environment. A quick standalone reproduction
WITHOUT pytest's context fixture is not proof an interaction is stable;
if a `context`-fixture-specific setting (video/trace recording) differs
from your debug script, reproduce WITH it before concluding a fix works.

**Fix that held up (3/3 green under pytest):** don't trust a single
click-and-hope for the deselect step. Click, then verify the OBSERVABLE
result (the trigger's own displayed text now equals the target value) with
a bounded retry (3 attempts, each gated by a short `expect().to_have_text()`
check) before letting a real failure surface via the final `expect()` at
full timeout. This is a condition-check-and-retry against the actual DOM
state, not a blind sleep, and it isn't defect-masking (there's no product
bug here — it's a raw-DOM-interaction timing subtlety in a third-party
widget, and the loop still fails loudly if the deselect genuinely never
lands).
