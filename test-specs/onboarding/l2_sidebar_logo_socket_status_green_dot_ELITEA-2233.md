# ELITEA-2233: Onboarding — ELITEA logo displays green dot indicating active server connection

**TMS ID:** ELITEA-2233
**Priority:** medium
**Status:** `ready-for-automation`
**Type:** UI
**Feature:** onboarding (surface: **sidebar header**, not the `/onboarding` page)
**Analysed:** 2026-08-24 · live, `http://localhost:5173/chat` (EliteaUI `automation/testids`, DEV backend)
**Cluster:** analysed in ONE live session with ELITEA-2234 (sidebar-header family). **Separate AFS each** — see ELITEA-2234 AFS § Why not a family AFS.
**Surface digest:** `test-specs/onboarding/_surface.md` § The sidebar header

---

## Summary

The "green dot" is a single 8×8 `<Box>` rendered **inside** the sidebar logo `IconButton`
(`SidebarBody.jsx:229-235`), wrapped in a `<Tooltip title={`${systemSenderName} is ${socketStatus}`}>`.
Its colour is the whole state machine (`SidebarBody.jsx:393-403`):

```js
backgroundColor: socketStatus === SocketConstants.SocketStatus.Connected
  ? palette.icon.fill.success   // green  #2BD48D → rgb(43, 212, 141)
  : palette.icon.fill.error     // red    #D71616 → rgb(215, 22, 22)
```

`socketStatus` comes from `useSocketIcon()` → Redux `settings.socketConnected`, and
`isSocketIconVisible` is hardcoded `true`.

**There is exactly ONE dot element** (live count = 1). "Green dot shown" and "no red dot shown" are
therefore two readings of the same element's colour — which is what makes the case's step 4 machine-
checkable at all, and is why the spec asserts both the positive and the negative colour.

Live-confirmed 2026-08-24: `background-color: rgb(43, 212, 141)`, `aria-label="Elitea is connected"`,
8×8 at the logo button's top-right corner.

---

## Preconditions

- Standard authenticated user (`auth_state`; on localhost login is skipped via `VITE_DEV_TOKEN`).
- Backend socket connected — the ordinary state; the spec asserts it, it does not force it.
- Sidebar rendered (any authenticated route; this AFS uses `/chat`, the default landing).
  The dot lives inside `sidebar-toggle`, which renders in **both** the expanded and collapsed sidebar
  (unlike the bell of ELITEA-2234).
- ~~The first-visit interactive-tour prompt may cover the page~~ — **amended at implementation**: the
  prompt cannot fire on the suite's entry path (fresh context + empty localhost `auth_state` storage
  state ⇒ the `interactive-tour:first-elitea:pending` flag `useProposePendingTour` requires is never
  set). See ELITEA-2234 AFS § Entry-path quirk (amended). No dismissal step is implemented; the
  `#1753` console filter is kept as a cheap, ticket-linked safety net.
- **ZERO substitution.** No route mock, no injected state, no Redux poke. Every asserted value is
  produced by the product.

---

## Coverage Map

### Axis 1 — TMS case elements

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| P | Precondition: "User is logged in to the Elitea platform" | authenticated session | framework `auth_state` | `expect(sidebar_toggle).to_be_visible()` | **asserted** (transit) |
| 1 | Log in to the application for the **first time**; land on the expected landing page | authenticated, on landing page | `page.goto("/chat")` | `expect(page).to_have_url(re.compile("/chat"))` | **asserted, scope-amended** — "first time" is not reproducible for a standard user and the product does not gate the dot on it: the indicator is socket state, rendered on every session (`useSocketIcon.hooks.jsx`). Asserting the live contract per the reverse-masking guard |
| 2 | Locate the ELITEA logo icon in the top left of the sidebar | control located, no error | `sidebar-toggle` (**on-main ✓**) | `expect(sidebar_toggle).to_be_visible()` | **asserted** — this element carries the ELITEA wordmark SVG (`EliteAIcon`) |
| 3 | Verify a green dot is displayed above the ELITEA logo | green dot visible | `sidebar-socket-status-indicator` + `data-socket-status` (**added** EliteaAI/EliteaUI@2c0ac201) | `expect(dot).to_be_visible()` + `expect(dot).to_have_css("background-color", "rgb(43, 212, 141)")` + `expect(dot).to_have_attribute("data-socket-status", "connected")` + geometry: the dot's box is inside the logo button's box and top-aligned with it | **asserted** — three independent readings: the semantic state attribute, the rendered colour, and the position. "Above the logo" is, live, the logo button's **top-right corner** (dot x=44..52 y=8..16 inside button x=8..52 y=8..52) — asserted as containment + `dot.top == button.top`, never as pixel constants |
| 4 | Verify **no red dot** is shown (red would mean the server is updating) | no red indicator anywhere | same element + a page-wide count | `expect(dot).not_to_have_css("background-color", "rgb(215, 22, 22)")` **and** `expect(socket_status_indicators).to_have_count(1)` **and** `expect(page.locator(SOCKET_INDICATOR_DISCONNECTED)).to_have_count(0)` (the testid + `[data-socket-status="disconnected"]` state filter) | **asserted** — the count assertion is what makes the negative exhaustive: with exactly one indicator element in the DOM, "this one is green" *is* "no red one exists". The `[data-socket-status="disconnected"]` absence assertion states the same in the product's own vocabulary and is a first-class reference under canon ruling #511 |
| Final | No red dot is shown | as step 4 | same | same | **asserted** |

### Axis 2 — coverage beyond the case (each with its reason)

| Observable | Reason | Assertion |
|---|---|---|
| Tooltip/accessible text is `"Elitea is connected"` | The colour alone is a design token; this is the product's own *semantic* statement of the same fact, so a theme change that recolours the token cannot silently turn the assertion into a tautology. MUI's Tooltip clones `title` onto the child as `aria-label` — live-confirmed, no hover needed | `expect(dot).to_have_attribute("aria-label", "Elitea is connected")` |
| The dot is a **descendant of** `sidebar-toggle` | "displayed above the ELITEA logo" is a relationship, not a coordinate. A regression that moved the indicator elsewhere in the header would still satisfy a bare `to_be_visible()` | locator scoped as `'[data-testid="sidebar-toggle"] [data-testid="sidebar-socket-status-indicator"]'` (class constant) + bounding-box containment |
| Exactly one socket indicator exists in the DOM | See step 4 — it converts "no red dot" from unverifiable prose into an exhaustive check | `to_have_count(1)` |
| No error-level console messages, **excluding** the known `#1753` MUI focus error | Side channel. `#1753` is deterministic on the first-visit prompt path (digest quirk 4) and already ticketed | filter that one message; `# Known defect: #1753` |

---

## Concrete Handles Reference

| Element | Handle (testid-only) | Provenance (verified 2026-08-24, `git fetch origin` in ../EliteaUI) |
|---|---|---|
| Sidebar logo button (ELITEA wordmark) | `sidebar-toggle` | **on-main ✓** |
| Socket status dot | `sidebar-socket-status-indicator` + `data-socket-status="connected|disconnected"` | **ADDED** EliteaAI/EliteaUI@2c0ac201 (`automation/testids`, pushed) |

Class constants for the page object (dynamic/state-filtered shapes must live at class level per
`.claude/rules/page-objects.md`):

```python
SOCKET_INDICATOR             = '[data-testid="sidebar-toggle"] [data-testid="sidebar-socket-status-indicator"]'
SOCKET_INDICATOR_CONNECTED   = '[data-testid="sidebar-socket-status-indicator"][data-socket-status="connected"]'
SOCKET_INDICATOR_DISCONNECTED= '[data-testid="sidebar-socket-status-indicator"][data-socket-status="disconnected"]'
```

**Live-captured values (2026-08-24, standard test user):**

| Observable | Value |
|---|---|
| `background-color` | `rgb(43, 212, 141)` (`palette.icon.fill.success` = `green` = `#2BD48D`) |
| disconnected colour (from source, not observed) | `rgb(215, 22, 22)` (`palette.icon.fill.error` = `dangerRed` = `#D71616`) |
| size / shape / position | `8px × 8px`, `border-radius: 50%`, `position: absolute`, `top: 0`, `right: 0` |
| bounding box | x=44 y=8 w=8 h=8 — inside logo button x=8 y=8 w=44 h=44, top-aligned |
| `aria-label` | `Elitea is connected` (MUI Tooltip title cloned onto the child) |
| count in DOM | 1 |

**The disconnected/red state is deliberately NOT exercised.** Producing it honestly needs the
backend socket to drop, which cannot be arranged from a test without faking the connection — and
faking it would be a **terminal substitution** of the very thing the case observes
(`.agents/testing.md` § Fidelity policy). The case does not ask for simulation, so the red state is
covered only by the exhaustive-absence assertions in step 4. Flagged for the lead as a possible
future `question` card, not as work for this case.

---

## Testids to add (EliteaUI, `automation/testids`, `add-data-testid` skill)

One **attribute-only** addition on an element that already exists — no new DOM node, no hook, no
render-prop change (zero-functional-impact check passes).

`src/[fsd]/widgets/sidebar-root/ui/SidebarBody.jsx:234` — the socket dot `<Box>` inside the Tooltip:

```jsx
<Box
  data-testid="sidebar-socket-status-indicator"
  data-socket-status={socketStatus}          // already 'connected' | 'disconnected'
  sx={styles.socketIconContainer}
/>
```

`socketStatus` is already in scope (`SidebarBody.jsx:44`) and its values are exactly the two strings
(`socket.constants.js`). State goes on the `data-*` attribute, **never** into the testid value — the
element is one live element whose state flips (`.agents/testing.md` § Locator policy / PR #581).

Uniqueness verified 2026-08-24: `git grep` on `origin/automation/testids -- src/` returns **0 hits**
for `sidebar-socket-status-indicator` and for `socket-status`.

Commit subject must use `[EL-2233]`, not `[ELITEA-2233]` — EliteaUI's commitlint hook rejects the
latter (digest, w1).

---

## Known case-text drift (clarification, NOT a product defect)

| Case says | Live product | Handling |
|---|---|---|
| Step 1 "Log in … for the first time" | The indicator is socket state on every session, not a first-login artifact | Assert the live contract |
| Step 3 "a green dot … **above** the ELITEA logo" | Top-**right corner** of the logo button, overlapping it (`top: 0; right: 0`) | Assert containment + top-alignment |
| Step 4 "no red dot … (red would indicate server is updating)" | Red means **socket disconnected**, not "server updating" (`useSocketIcon.hooks.jsx`) | Semantics only; assertion unaffected |

Covered by the same clarification issue as ELITEA-2234's drift. **No product defect was found in
this case.**

---

## Suggested test location

`automation/tests/ui/onboarding/test_sidebar_socket_status_indicator.py`
(`TestSidebarSocketStatusIndicator::test_logo_shows_green_connected_dot`)

Page object: `automation/pages/sidebar_header_page.py` (`SidebarHeaderPage`) — the same new page
object ELITEA-2234 introduces; whichever case is implemented first creates it, the second extends it.
Not `onboarding_page.py`: this surface is the persistent app sidebar, not `/onboarding`.

Markers: `@pytest.mark.p2`, `@pytest.mark.regression`, `@pytest.mark.ui`.

---

## Blocked Steps

None.

## Known Defects

None found. (`#1753` — MUI focus console error on the first-visit tour prompt — is pre-existing,
already filed, and only filtered here.)

---

## Evidence

- `test-results/screenshots/ELITEA-2234-step-05-notifications-popover-open.png` — shared cluster frame: the
  green dot at the logo's top-right corner is visible in it.

---

## Implementation amendment (test-automation-engineer, 2026-08-24)

- **Shipped:** `automation/tests/ui/onboarding/test_sidebar_socket_status_indicator.py`
  (`TestSidebarSocketStatusIndicator::test_logo_shows_green_connected_dot`) on the shared new page
  object `automation/pages/sidebar_header_page.py` (`SidebarHeaderPage`). Green first run, 0 reruns.
- **Every live value in § Live-captured values re-confirmed by the run**: `rgb(43, 212, 141)`,
  `data-socket-status="connected"`, `aria-label="Elitea is connected"`, DOM count 1, and the dot
  contained in the logo button's box and flush with its top edge (asserted with a 1 px sub-pixel
  tolerance, not as pixel constants).
- **Entry path simplified** — no first-visit-prompt dismissal (see § Preconditions, amended).
- Everything else implemented as specced; every Coverage-Map row is asserted.
