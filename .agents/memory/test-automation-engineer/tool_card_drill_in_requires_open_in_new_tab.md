---
name: Tool-card drill-in requires open-in-new-tab, not a bare card click
description: A Tools/Toolkits-section card (toolkit, MCP, or attached sub-agent) is inert to a plain click — navigating into the linked entity's own detail page always means the toolkit-open-button / AgentDetailPage.click_toolkit_open_in_new_tab() path, which opens a NEW browser tab via window.open()
type: feedback
---

## The mistake

While automating ELITEA-1902 (import agent .zip with nested agent
dependencies), I needed to verify a newly-imported nested Agent — shown as
an attached sub-agent card in the main Agent's Tools section — had been
recreated with a brand-new, distinct ID. I wrote a naive
`card.click()` expecting same-tab navigation into the nested agent's
detail page. It silently did nothing: the assertion caught it because
`AgentDetailPage.get_name()` still returned the MAIN agent's name, not the
nested one.

## Root cause

Read `EliteaUI/src/pages/Applications/Components/Tools/ToolCard.jsx`: a
card's own body (`agent-toolkit-card` testid, shared across
Toolkit/MCP/sub-Agent attachments) is NOT a navigation trigger at all — it
only expands/collapses variable display and reveals hover actions. The
ONLY way to navigate into the linked entity's own page is the card's
dedicated "open in new tab" icon button (`toolkit-open-button` testid,
`onOpenInNewTab` handler), which does `window.open(url, '_blank')` — a
**new browser tab**, not an in-page navigation.

## The existing handle (already built, just not obvious from the name)

`AgentDetailPage.click_toolkit_open_in_new_tab(toolkit_name, timeout)`
already does the right thing for external toolkit cards: hovers the card
to reveal actions, clicks `toolkit_open_button`, and uses
`self.page.context.expect_page()` to catch the new tab, returning its URL
(without leaving it open/interacted-with). It works identically for a
sub-agent-attached card since ELITEA-1887's "+ Agent" attach renders via
the exact same `ToolCard`/`agent-toolkit-card` component.

## The pattern for next time

**Any test that needs to "drill into" a Tools/Toolkits-section card's own
entity page — toolkit, MCP, or attached sub-agent — should reuse
`click_toolkit_open_in_new_tab()` (or a same-shaped sibling if the return
value needs to differ), parse the ID out of the returned URL, then
`SomeDetailPage(page).navigate(id)` on the MAIN page** rather than trying
to interact with the new tab or attempting a same-tab card click. Grep for
`toolkit_open_button` / `click_toolkit_open_in_new_tab` before writing a
new drill-in method — `pipeline_detail_page.py` and `toolkit_detail_page.py`
have their own analogous versions already.
