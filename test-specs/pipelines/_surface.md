# Surface digest: Pipeline Flow Editor — LLM node fields & AI Assistant modal

Confirmed handles/waits/quirks from live exploration. This is a cache for
same-surface analysts and the implementer — it does NOT replace live
execution; verify handles as you use them, and update this file (create or
edit) after your own run. Lives on the base branch — commit alongside your
AFS, never on a case branch.

First digest for this surface (written during GAP-007 analysis, 2026-07-24,
project `Bugs & Features`, local `http://localhost:5173`, pipeline
`GetUserName` id `690`/version `1251`).

## Reaching an LLM node's inline config fields

The Flow-view canvas (`[data-testid="rf__wrapper"]`, ReactFlow) renders each
node's config **always inline/expanded** on the card — no click-to-expand
step needed (same finding as ELITEA-1954 for MCP nodes). An LLM node
(`[data-testid="rf__node-{id}"]`, e.g. `rf__node-LLM 1`) shows **System**,
**Task**, **Chat History** sub-fields (each: a "Type" select + a "Value"
field), then `Input`/`Output` state-variable selects, then Toolkits/
Interrupt-before/Interrupt-after/Structured-output.

**Canvas is heavily zoomed-out by default** — a freshly-opened pipeline's
node bounding rect can be as small as ~52×72px, with content clipped by the
ReactFlow pane's `overflow`. Zoom in first: click `.react-flow__controls-zoomin`
~7× (no testid on ReactFlow's own controls — third-party widget, `rf__wrapper`
sanctioned-exception territory per `.agents/testing.md` §579), then
`.react-flow__controls-fitview` to re-center. A 1600×1000 viewport gives
enough room to see 2–3 stacked nodes without further panning.

## STATE drawer — zero testids

The "State" button (top-right of the canvas toolbar, opens/closes a right-side
drawer listing `input`/`messages`/custom vars with rename input, type badge
("Abc"), `+`/delete icons, and per-var enable toggles) has **no `data-testid`
anywhere** — button, drawer container, row inputs, icons, toggles, close (X)
button. Confirmed via full testid enumeration of the open drawer (zero hits).
If a case needs state seeded and doesn't specifically test the STATE-drawer
UI itself, **seed via the pipeline's own YAML/API PUT instead** — the `state:`
block shape is:
```yaml
state:
  input:
    type: str
  messages:
    type: list
  <custom_name>:
    type: str
    value: ''
```
(confirmed live via the Yaml-view tab). This avoids needing any STATE-drawer
testids for cases whose actual assertions live elsewhere (e.g. GAP-007's
f-string autocomplete). A future case that specifically exercises the STATE
drawer's own CRUD/toggle behavior is a separate coverage-gap scope and should
request its own testids then.

## Duplicate DOM id on every "Type" select — use testid, never the id

`SingleSelect.jsx` (`src/[fsd]/shared/ui/select/SingleSelect.jsx:657`)
defaults to `id={id || 'simple-select-' + label}` when no explicit `id` prop
is passed. `SimpleLLMInputItem.jsx` renders `<SingleSelect label="Type" .../>`
for System/Task/Chat-History without ever passing one, so **all three (and
any sibling node's own "Type" field) share the literal `id="simple-select-Type"`**
— confirmed `document.querySelectorAll('#simple-select-Type').length === 5`
on one canvas view. Filed `EliteaAI/elitea-testing-public#1006` (MINOR, not
blocking). **Never locate by this id in new code** — always testid + container
scope. `SingleSelect` already supports a `data-testid` prop (wires
`SelectDisplayProps={{'data-testid': \`${dataTestId}-combobox\`}}`) — same
mechanism already used for `pipeline-mcp-node-toolkit-select-combobox`
(ELITEA-1954/1955); a per-`variableName` dynamic testid
(`pipeline-llm-node-{variableName}-type-select`) is the correct shape if a
case needs to select this field's Type value directly rather than going
through `select-option-{value}` alone.

## AI Assistant modal (System/Task/Code/Printer/User-message fields, Type=F-String)

Opens via a fullscreen icon in the Value field's hover-toolbar
(`aria-label="AI Assistant"`, no testid — 3-icon toolbar order is
Copy / **AI Assistant** / Expand, only appears `showFullScreenAction &&
isHovering`). The modal (`role="dialog"`, no testid) hosts a CodeMirror
editor (`.cm-content`, no testid) preloaded with the field's current value,
plus a separate bottom "Describe your idea to generate or rewrite the value"
AI-generation prompt input (a DIFFERENT feature, not the f-string
autocomplete) and a Copy/Close icon pair top-right (`aria-label="Close"`, no
testid).

**All of these have a trivial existing wiring point — zero shared-component
edits needed, only a prop passed at the feature call site:**

| Element | File to touch | Prop already available |
|---|---|---|
| Modal root | `AIAssistantModal.jsx` → `<Modal.ExpandedViewerModal>` | `data-testid` (destructured as `dataTestId` in `ExpandedViewerModal.jsx:30`, applied line 136) |
| Editor content (`.cm-content`) | `AIAssistantCodeMirrorInput.jsx` → `<Field.CodeMirrorEditor>` | `contentTestId` (`CodeMirrorEditor.jsx:82`, applies via `EditorView.contentAttributes` — same mechanism as `skill-instructions-editor-content`/`toolkit-raw-json-editor-content`; **use the `-editor-content` suffix convention**, not a bare `-editor` guess) |
| Fullscreen/"AI Assistant" icon button | `SimpleLLMInputItem.jsx`'s `NodeFieldInput` `commonProps` | `fullScreenButtonProps` (threaded `InputBase.jsx` → `InputActionsToolbar.jsx`, spread onto the `IconButton`) |

## F-string autocomplete popper — mechanism confirmed fully working (one exception)

`useCodeMirrorFStringAutocomplete.hooks.js` (AI-Assistant/modal path) and
`useFStringInputAutocomplete.hooks.js` (plain inline-field path, no modal)
are TWO DIFFERENT HOOKS feeding the SAME shared `FStringAutocompletePopper`
UI component (`fstring-autocomplete/ui/FStringAutocompletePopper.jsx` — bare
`Popper`/`Paper`/`MenuList`/`MenuItem`, zero testids). Confirmed live,
end-to-end, on the modal path (GAP-007):

- Typing `{` opens the popper listing every current state variable, first
  option `Mui-selected` by default.
- Typing a prefix filters case-insensitively (`filterFStringAutocompleteOptions`).
- **ArrowUp/ArrowDown wrap at both ends** (`getNextAutocompleteIndex`) —
  confirmed both directions.
- **Enter** and **mouse click** both insert `{value}` with cursor after the
  closing brace, and close the popper. Mouse click additionally leaves the
  parent modal OPEN (confirmed) — this is the control case that isolates the
  next finding to the keyboard path specifically.
- **Escape is BROKEN**: closes the entire AI Assistant modal (not just the
  popper) and commits the in-progress value — filed `#1003` (MAJOR),
  reproduced in a fresh isolated session too. Root cause: the CodeMirror
  keymap's Escape handler doesn't stop the native keydown from bubbling to
  MUI's Modal-level Escape-to-close listener.
- Typing a literal `}` right after an auto-closed `{}` (cursor between) is a
  **type-over** of the auto-inserted brace (standard CodeMirror bracket
  matching, not part of this feature) and correctly closes the popper
  (`getFStringAutocompleteState` sees the closing brace already present).

**Typing-simulation gotcha:** simulate every character as its OWN keypress
(`page.keyboard.press()` per char / `press_sequentially()`), never a bulk
`fill()`/single-insert — a bulk insert of `"user"` after an auto-closed `{}`
landed as `{}user` (wrong) instead of `{user}` (correct) during exploration.
Per-character `press()` calls produced the correct result every time.

## Console — clean

Zero `error`-level console messages across the full GAP-007 session
(popper open/filter/navigate/insert/dismiss, both defect reproductions,
modal open/close cycles).
