---
name: Toolkit TEST SETTINGS panel — shared-tooltip testid threading, replace-in-place chat, detail-title race
description: ELITEA-1866 — how to thread a caller-scoped testid through a 4-component shared MUI tooltip chain, why the TEST SETTINGS panel's result message list needs a content-poll not a count-poll, and the toolkit-detail-title load race
type: feedback
---

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

**When NOT to thread further**: reading the tooltip's rendered CONTENT
(not the trigger icon) would require the SAME treatment one layer deeper,
into `TooltipMarkdownContent.jsx` — but that component wraps
`react-markdown`'s `<Markdown>` with NO wrapping element today; adding a
testid there means introducing a NEW wrapping DOM node, which risks
breaking every tooltip's layout/CSS across the whole app (a component that
generic is used far beyond this one case). Judged out of scope / too high
blast-radius for a single case; used a sanctioned `get_by_role("tooltip")`
read instead (see below), encapsulated in a page-object method, with the
tradeoff documented explicitly in the AFS/PR rather than silently done.

## Sanctioned non-testid exceptions — a recognizable, bounded class

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
