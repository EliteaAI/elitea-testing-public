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

**Root cause of the missing testids, confirmed 2026-07-16 (ELITEA-1802 analysis):** the Support
Assistant widget is NOT first-party EliteaUI JSX — it ships as the third-party npm package
`@eliteaai/elitea-assistant` (`EliteaUI/node_modules/@eliteaai/elitea-assistant`), mounted once at
`[fsd]/app/root.jsx` via `[fsd]/widgets/support-assistant/ui/SupportAssistant.jsx`.
`grep -rn 'aria-label="Attach file"' EliteaUI/src` (and equivalents for the launcher/title/attach
selectors) returns nothing in first-party source. This means `add-data-testid` (which edits
EliteaUI JSX files) **cannot** remediate any Support Assistant selector — there is no first-party
JSX to add a `data-testid` to. Treat every raw selector in `support_assistant_page.py` as a
permanent scope exception, not open tech debt to fix via the normal testid workflow. If testid
coverage on this widget is ever required, it has to be requested upstream in the
`@eliteaai/elitea-assistant` package itself, not patched in this repo.
