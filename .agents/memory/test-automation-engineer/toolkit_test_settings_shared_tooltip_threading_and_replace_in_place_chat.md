---
name: Toolkit TEST SETTINGS panel — shared-tooltip testid threading, replace-in-place chat, detail-title race
description: ELITEA-1866 — how to thread a caller-scoped testid through a 4-component shared MUI tooltip chain (including a SECOND prop for the tooltip's popper CONTENT, not just the trigger), why the TEST SETTINGS panel's result message list needs a content-poll not a count-poll, and the toolkit-detail-title load race. RESOLVED (PR #670 review round 1): the "sanctioned non-testid exception" framing below was wrong for all 3 of its examples — every one got a real testid instead. See RESOLUTION section.
type: feedback
---

## RESOLUTION (PR #670 review round 1 fix) — the "sanctioned exception" framing below was wrong

A fresh-session reviewer rejected all 3 items in the "Sanctioned non-testid
exceptions" section below as real testid gaps, not genuine exceptions —
correctly: only 1 of 5 grouped AFS rows (the type-picker heading) actually
carried an explicit `(optional)` qualifier; "high blast-radius" described
COST, not IMPOSSIBILITY, which is the actual bar for `.agents/role-
overrides.md`'s non-testid exception. All 3 were closed with real testids
in the round-1 fix, and closing them was cheap in every case:

1. **Configuration/Indexes tabs**: `EditToolkit.jsx` already had a
   `tabProps: { 'data-tour': ... }` mechanism for the Indexes tab (used to
   stamp a tour-target attribute). Adding `'data-testid': '...'` to that
   SAME object (plus one for Configuration) was a 2-line change — the
   "icon-only, no visible text" framing below was never actually a
   blocker; the tab config object accepts arbitrary extra DOM props
   already, nothing about icon-only-ness prevented a testid.
2. **Tooltip popper CONTENT**: the "would require wrapping
   `TooltipMarkdownContent.jsx` in a new DOM element, high blast-radius"
   reasoning below assumed the wrap had to happen INSIDE the shared
   markdown renderer. It doesn't — `InfoTooltip.jsx` (one layer up) already
   computes `titleContent` as a local JSX variable before handing it to
   `<Tooltip title={titleContent}>`; wrapping THAT variable in
   `<Box data-testid={contentTestId}>` (opt-in, only when a NEW
   `contentTestId` prop is passed) touches zero lines of
   `TooltipMarkdownContent.jsx` and has zero effect on any caller that
   doesn't pass the prop. The "blast radius" was imagined at the wrong
   layer.
3. **Category filter tabs**: `CategoryFilter.jsx`'s `Chip` render loop was
   a single missing `data-testid="category-filter-tab"` line — no
   threading needed at all, since (unlike the Bucket tooltip) this
   observable never needs per-tab identification, only presence/count, so
   a bare hardcoded generic value (same shape as `entity-card`) sufficed.

**Lesson: "no testid exists yet" is not the same as "adding one is hard."**
Before writing a `get_by_role(...)` workaround and calling it a sanctioned
exception, actually attempt the `add-data-testid` addition first — in all
3 cases here the real fix took less code than the workaround it replaced.
Reserve the exception path for genuinely unplaceable cases (third-party
widgets, elements outside `EliteaUI/src`), not "I didn't try."

## Threading a testid through a deep shared-component chain (InfoTooltip)

When a shared component's ONLY handle is a non-unique ambient attribute
(`data-info-tooltip` on `InfoTooltip.jsx` — matches every info icon on a
form, e.g. 3 on the Artifact toolkit form), and the interactive element is
several component layers below the actual page-object call site, the
compliant fix is a **caller-supplied prop threaded through every
intermediate layer**, scoped to ONE call site via a conditional spread —
never a blanket testid on the shared component itself (that would light up
every consumer, violating "testids go ONLY on elements tests actually
touch").

Concrete chain for the Bucket field's info icon (ELITEA-1866):
`ToolBaseProperty.jsx` (the schema-driven form-field renderer, has the
`k === 'bucket'` check) → `StyledInputEnhancer.jsx` → `InputBase.jsx` →
`InfoLabelWithTooltip.jsx` → `InfoTooltip.jsx` (renders the actual
`data-testid` on the icon `<Box>`). Prop name threaded end-to-end:
`tooltipTestId` (renamed to `testId` only at the final `InfoTooltip`
layer, matching that component's own prop-naming). Scoping line, one
place only:
```jsx
{...(k === 'bucket' && { tooltipTestId: 'toolkit-field-bucket-info-icon' })}
```
Every intermediate layer just forwards the prop (`undefined` by default —
zero behavior change for every OTHER consumer of the same chain). Verified
live via `data-testid`'s absence on the other 2 info icons on the same
form (Pgvector Configuration, Embedding Model) after the change — only the
Bucket field's icon carries it.

**WRONG at the time this was written — see RESOLUTION section at the top.**
The actual fix needed only a SECOND opt-in prop (`contentTestId`) on
`InfoTooltip.jsx` itself, one layer above `TooltipMarkdownContent.jsx`,
never touching that shared markdown renderer at all. Kept below as a
record of the reasoning that turned out to be wrong — re-read the
RESOLUTION section before repeating it.

## Sanctioned non-testid exceptions — a recognizable, bounded class

**SUPERSEDED — see RESOLUTION section at the top. None of the 3 examples
below turned out to be genuine exceptions; all 3 got real testids in PR
#670's round-1 fix, each cheaper than the workaround.** Kept for the
record, not as current guidance — do not cite this section to justify a
new `get_by_role(...)` workaround without first attempting `add-data-testid`.

Three flavors of "genuinely no testid, and adding one is out of proportion
to the case" all resolved the same way — a `get_by_role(...)` (or role +
name) read, ALWAYS encapsulated inside a page-object method (never inline
in a test file), with an explicit docstring naming the exception:

1. Icon-only tabs with no visible text and no testid (Configuration/Indexes
   tabs on the toolkit-detail page) → `get_by_role("tab")` count.
2. A known, finite, confirmed-live set of category-filter button labels
   that the case never clicks (just needs to prove they render) →
   `get_by_role("button", name=<label>)` per label.
3. Ephemeral, portaled popper CONTENT whose TRIGGER already carries a real
   testid → `get_by_role("tooltip")` (see threading section above for why
   the content itself isn't also testid'd).

If a case's own AFS explicitly frames a gap as "OPTIONAL — satisfied by
URL/role-count checks" (this project's own carve-out language, seen twice
now — ELITEA-1868's picker heading, ELITEA-1866's tab pair), that's
license for #1/#2 above. #3 (content-of-an-already-testid'd-trigger) is
NOT pre-authorized by that language and needs its own justification in the
PR — don't silently extend the carve-out's scope without saying so.

## TEST SETTINGS panel's message list replaces content, does not append

`TestTools.jsx` renders its center chat/output panel via the SAME shared
`ChatMessageList.jsx` every chat surface in the app uses — including its
`data-testid="chat-message-list"` container, which is GENERIC and already
on `automation/testids` (no new testid needed to read it). BUT its
`chat_history` prop starts empty and shows a static mock welcome message
(`getMockToolkitIndexConversation`) — once `RUN TOOL` actually executes,
the REAL result REPLACES that mock state rather than appending after it.
Confirmed live twice (two separate toolkit instances): li-count under
`chat-message-list` is 1 both BEFORE and AFTER running a tool. A
count-based wait (`ChatPage.wait_for_ai_response`'s `initial_count + 1`
pattern, which works for the REAL chat surface where messages genuinely
append) never resolves here — it would time out waiting for a count delta
that never happens. Use a CONTENT-based wait instead:
`expect(locator).to_contain_text(re.compile(r"[✅❌]"), timeout=...)`.

## toolkit-detail-title needs a polling assertion, not visibility + read

Right after Save navigates to `/toolkits/all/{id}`, `toolkit-detail-title`
becomes VISIBLE immediately but with a generic "Edit Toolkit" placeholder
— the real toolkit name only lands once its own data fetch resolves. A
`wait_for(state="visible")` + single `text_content()` read races this and
intermittently returns the placeholder. Always use
`expect(locator).to_have_text(expected_name, timeout=...)` (Playwright's
auto-retrying assertion) for this specific element, never a getter-style
single read right after a Save-triggered navigation.

## `create_artifact_toolkit()` lives on `ToolkitAPI`, not `ArtifactAPI`

`automation/api/client.py:1634` — inside the `ToolkitAPI` class (alongside
`list_all_toolkits()`, `delete_toolkit()`, `get_toolkit()`), NOT
`ArtifactAPI` (which only has bucket-level CRUD:
`create_bucket`/`delete_bucket`/`list_bucket_files`/`get_file`). An AFS
mislabeling this class is a one-line correction, not a scope issue — note
it and move on.
