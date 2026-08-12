---
name: verify_on_detail_page races SPA route push
description: Always call wait_for_page_load() before verify_on_detail_page() after a save/navigate — the verify reads page.url with no internal wait
type: feedback
---

## The bug (ELITEA-2605, PR #1461, 2026-08-12)

`AgentDetailPage.verify_on_detail_page()` (`agent_detail_page.py:662`) and
`SkillDetailPage.verify_on_detail_page()` (`skill_detail_page.py:403`) both read
`self.page.url` **synchronously with no wait of their own**. Called right after
`save_and_wait_for_navigation()` (which only waits for `networkidle` + a 1s
settle), this races the SPA's client-side route push (React Router's
`history.pushState` fires asynchronously relative to the render — the detail
page can be **fully rendered** — name populated, Save disabled — before
`page.url` actually flips from `/agents/create` to `/agents/all/<id>`).

Confirmed via a failure screenshot: at the moment of the failed assertion the
Agent detail page showed all detail-page-only state (populated name, disabled
Save/Discard) while `page.url` still read `/agents/create?viewMode=owner`. Not
a product bug — a pure test-side timing gap.

## The fix pattern

Always call `wait_for_page_load(timeout=NAVIGATION_TIMEOUT)` **before**
`verify_on_detail_page()`, never call `verify_on_detail_page()` bare right
after a save/create action:

```python
agent_form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)
agent_detail_page = AgentDetailPage(page)
agent_detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)   # <- do not skip
agent_detail_page.verify_on_detail_page()
```

`wait_for_page_load()` waits for the INFORMATION section to be visible + the
Name input to be populated — by the time that resolves, the URL has always
settled too. This is exactly the pattern `test_agent_management.py::
test_create_agent_via_ui` already used (and passes 3/3 on) — ELITEA-2605's
Step 7 simply omitted the call, which is how it went red while everything
else in the same file (steps 1/5, which call `SkillDetailPage
.verify_on_detail_page()` the same bare way) happened not to race in
observed runs.

## Known-unfixed risk surface (not yet hardened)

~50 call sites across the suite call `verify_on_detail_page()` — most (not
all) already precede it with `wait_for_page_load()`. Two call sites in
`test_skill_custom_icon_visibility_across_ui.py` (steps 1 and 5, via
`SkillDetailPage`) still call it bare and have not yet raced in practice — a
project-wide hardening (e.g. `page.wait_for_url()` inside
`verify_on_detail_page()` itself) would close the whole risk class in one
shared-file change, but touches ~50 callers and needs its own PR under the
additive-only shared-file protocol, not a test-file patch. Flag it if you hit
this race on any OTHER test — don't silently re-patch the same way file by
file.
