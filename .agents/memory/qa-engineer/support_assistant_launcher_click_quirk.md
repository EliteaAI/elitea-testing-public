---
name: Support Assistant launcher click quirk
description: Native Playwright click on the Support Assistant launcher button times out due to a MUI overlay; must use JS-evaluate click
type: reference
---

Confirmed live on `http://localhost:5173/chat` (2026-07-10, ELITEA-1796 analysis).

A native `getByRole('button', { name: 'Support Assistant' }).click()` (or any Playwright-actionability click)
on the Support Assistant launcher (`button.elitea-assistant-button`, `aria-label="Support Assistant"`)
reproducibly times out — a MUI overlay div
(`div[data-tour="sidebar-support-assistant"][data-mui-internal-clone-element="true"]`) intercepts pointer
events on the button. `SupportAssistantPage.open_widget()` in `automation/pages/support_assistant_page.py`
already works around this via `page.evaluate(...)` doing a raw `btn.click()` — this is a real, necessary
workaround, not incidental code. Any new test/AFS touching the launcher must keep using the JS-click
approach (or `force=True` as a lighter alternative, untested here).

The **Close (X)** button (`button[aria-label="Close chat"]`) does NOT have this problem — a plain native
click works fine once the widget is open.

Also noted: none of the `data-testid` attributes the ELITEA-1796 TMS case's Test Data table cites
(`support-assistant-launcher`, `support-assistant-title`, `support-assistant-close`) exist in the live DOM.
Only the case's own documented fallback selectors are real. `support_assistant_page.py` is fallback-only
(no testids at all), which is a pre-existing violation of `.claude/rules/page-objects.md`'s testid-only
mandate — flagged as framework debt, not fixed as part of case analysis.
