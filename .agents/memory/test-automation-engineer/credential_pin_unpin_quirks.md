---
name: Credential pin/unpin quirks (implementer)
description: Shared PinButton.jsx testid scoping across 5 entity types via checkCardType.js helpers (not the shared getEntityType utils), the pinMenuItem-missing-key pattern recurring a third time (ELITEA-1794 export menuitem, ELITEA-1794 rework, now ELITEA-1974), commitlint's [EL-NNNN] format (not [ELITEA-NNNN]) on EliteaUI, and relative DOM-order assertion via entity-card-name instead of absolute position
type: feedback
---

## Shared PinButton.jsx — entity-scoped per-row testid

`PinButton.jsx` (`EliteaUI/src/[fsd]/widgets/pin-toggler/ui/`) is reused
across Skills/Toolkits/Applications/MCPs/Credentials list rows (`Card.jsx`
card-list view AND `DataTableRow.jsx` table view both pass it the same
`entityId`/`entityType` props — `entityType` is literally the page's
`cardType` constant, e.g. `ContentType.CredentialAll`). It had zero
`data-testid`, only a flipping `aria-label`.

Fix: added a **local-only** slug helper inside `PinButton.jsx` using the
existing `checkCardType.js` predicates (`isCredentialCard`, `isSkillCard`,
`isToolkitCard`, `isMCPCard`, `isApplicationCard`) to map `entityType` →
a clean lowercase slug, then `data-testid={entityId ? \`${slug}-pin-toggle-button-${entityId}\` : undefined}`.
Deliberately did **not** route through `common/utils.jsx`'s
`getEntityType`/`getEntityTypeByCardType` — those already have many other
callers and don't cover Credentials/MCPs, so extending them would be
scope creep on a shared-caller file for a one-case fix. Result:
`credential-pin-toggle-button-1570`, and free coverage for Skills/
Toolkits/Applications/MCPs the next time one of those needs pin/unpin
automated (same component, same helper, already landed).

## pinMenuItem missing `key` — third occurrence of the same shape

`DotMenu.jsx`'s `BasicMenuItem` sets `data-testid={testId}-menuitem`` where
`testId = item.key`. Any menu-item object built without a `key` silently
renders with no testid — this is a **missing-wiring bug, not a missing
feature** (the capability existed all along on the sibling item that DID
set a key). Confirmed pattern recurrence: ELITEA-1794 (Export menuitem,
Agents), and now ELITEA-1974 (`CredentialsControls.jsx`'s `pinMenuItem`
spread). Fix is always the same one-line addition:
`key: 'some-stable-slug'` in the object literal, mirroring the sibling
item that already works (usually `Delete`, which reliably sets its own
`key`). **Grep for `usePinMenu` call sites** (`SkillControls.jsx`,
`ToolkitsControls.jsx`, `ApplicationControls.jsx` per the AFS's own
Concrete Handles note) before assuming a future pin-toggle-menu-item case
needs re-discovery — the same gap likely exists there too, unconfirmed.

## EliteaUI commitlint format is `[EL-NNNN]`, not `[ELITEA-NNNN]`

`git commit -m "test: [ELITEA-1974] ..."` on `automation/testids` is
REJECTED by husky/commitlint (`subject must container ticket number -
[EL-XXXX]`) even though the TMS case ID is `ELITEA-1974`. The convention
in every prior commit on that branch is the short `EL-` prefix
(`[EL-1974]`, `[EL-1884]`, `[EL-1737]`, ...) — always strip `ELITEA-` down
to `EL-` before committing on the EliteaUI repo, regardless of what the
TMS case ID or the elitea-testing-public branch/PR title use.

## Relative order assertion — DOM index, not absolute position

For "moved to the top of the list" claims, assert the **relative** DOM
order of two seeded entities' `entity-card-name` text nodes (index of A
vs index of B in the queried locator list), never an absolute position
(`.first()`, index 0). A single seeded entity trivially satisfies "moved
to the top" (nothing above it) — always seed a second, distinctly-timed
entity so there's a real before/after position to diff against (same
reasoning already established for other list-ordering cases in this
suite). Card list view exposes this via the shared `entity-card-name`
testid (`Card.jsx`) — same selector as `CredentialDetailPage`'s
`ENTITY_CARD_SELECTOR` already uses for `open_credential_by_name()`.

(from ELITEA-1974)
