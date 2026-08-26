---
name: Promotability grep must be component-scoped for reused testid names and catch prop/template forms
description: A closure-record testid promotability check by bare string-presence can be doubly wrong — a reused testid name can be on main in a DIFFERENT component than the test drives, and prop/backtick-template testids false-negative a literal data-testid= grep
type: feedback
---

Two independent ways the closure-record promotability grep (`.agents/workflow.md`
§ Closure record) can report a FALSE row, both hit on #370/ELITEA-2167 and caught
by a fresh reviewer, not by me:

## 1. Reused testid name, different component → string-presence lies
`chat-participants-badge-button` / `chat-participants-popper` EXIST on `origin/main`
— but in `CollapsedPerticapantsList.jsx` (the Agents-participants flavor). The
ELITEA-2167 test drives `UsersParticipantDropdown/index.jsx`, where those same
testid strings were added by a SEPARATE, undisclosed commit (EliteaUI@7ecc041d) that
is on `automation/testids` ONLY. A bare `git grep 'data-testid="chat-participants-badge-button"' origin/main`
returns YES and would ship a false "already on main / promotable" row. The AFS's
own "on-main ✓" rows were this exact mistake.
**Fix:** for any testid whose NAME is reused across components, scope the grep to the
component the test actually drives: `git grep '"<testid>"' origin/main -- '*UsersParticipantDropdown*'`.
When in doubt which component, read the page-object method → the live DOM → the JSX.
A name-only presence check is not a promotability check.

## 2. Prop-passed and backtick-template testids false-negative a `data-testid=` grep
Several EliteaUI testids are NOT literal `data-testid="x"` attributes:
- `closeButtonTestId="add-users-close-button"` / `inputTestId="add-users-search-input"` (prop forms — `BaseModal`/`AutoComplete` thread them onto `data-testid` internally)
- `chipTestId={user => `add-users-chip-${user.id}`}` / `getOptionTestId={o => `add-users-option-${o.id}`}` (backtick TEMPLATE literals, dynamic)

A grep for `data-testid[=^"]*"<t>` misses ALL of these → reports `testids:NO` for a
testid that is present and working. This is the same "resolved via source-read, not
literal grep" trap `.agents/role-overrides.md` already warns about for runtime-composed
testids.
**Fix:** grep the BARE string with BOTH quote prefixes — `git grep -e '"<t>' -e '`<t>' <ref> -- src/`
— or read the component source. Prove presence, then paste the source line in the record.

## Rule
The closure record's promotability block is the load-bearing artifact (`#35/#36/#37`
shipped false rows by copying; `#19` from a stale clone). Add to that discipline:
(a) fresh `git fetch` (already canon), (b) COMPONENT-SCOPE the grep for any reused
testid name, (c) grep the bare string with `"` AND backtick prefixes so prop/template
testids don't false-negative. Never trust the AFS/implementer's provenance column —
re-derive it, and expect a second hidden testid commit when a case touches a
component whose sibling flavor already carries the same testid name.

## 3. Fully split composition (`${PREFIX}-suffix` where PREFIX is a named constant) — no grep survives this at all
Hit on #1297 wave-01 (pipelines-remaining, ELITEA-2038/2036/2009 etc.). EliteaUI's
pipeline-node testids increasingly use a two-part composition where the prefix is a
component-level constant and the suffix is appended only at the call site:
```js
const AGENT_NODE_TESTID_PREFIX = 'pipeline-agent-node';
...
dataTestId={`${AGENT_NODE_TESTID_PREFIX}-input-select`}
```
or a map form:
```js
const TEST_ID_PREFIX_BY_NODE_TYPE = { custom: 'pipeline-custom-node' };
const testIdPrefix = TEST_ID_PREFIX_BY_NODE_TYPE[type];
...
dataTestId={testIdPrefix ? `${testIdPrefix}-input-select` : undefined}
```
The concrete testid string (`pipeline-agent-node-input-select`) **never appears
literally anywhere in the source** — not as a plain string, not as a backtick
template with the value inline. Neither fix 1 nor fix 2 above catches this: a
bare-string grep for `pipeline-agent-node-input-select` (any quote style) returns
ZERO matches on a ref where the testid demonstrably works, because it is assembled
at render time from two separately-declared tokens.
**Fix:** grepping for the concrete testid is the wrong operation entirely here — fall
back to a **per-component-FILE diff against the ref in question**:
`git diff origin/main origin/automation/testids -- '<path/to/Component.jsx>'`. If the
file differs at all, none of its testid wiring — literal, prop-passed, or composed —
is on that ref yet; if it's identical, all of it is. This is coarser than a
testid-level check (it can't tell you WHICH testid moved) but it is the only
check that doesn't silently return a false negative for this composition shape.
Recognize the shape before reaching for a grep: any `*_TESTID_PREFIX` constant or
`TEST_ID_PREFIX_BY_*` map in the diff is the signal to switch techniques immediately.
