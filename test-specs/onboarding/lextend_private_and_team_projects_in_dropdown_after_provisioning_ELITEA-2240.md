# ELITEA-2240: Onboarding — Private and team projects appear in the project dropdown once provisioning completes, with the full sidebar navigation

**TMS ID:** ELITEA-2240
**Priority:** medium
**Status:** `extend-existing`
**Type:** UI
**Feature:** onboarding
**Analysed:** 2026-08-24 · live, `http://localhost:5173` (EliteaUI `automation/testids`, DEV backend)
**Surface digest:** `test-specs/onboarding/_surface.md`
**Extends:** `automation/tests/ui/onboarding/test_onboarding_provisioning.py`
(`TestOnboardingProvisioning::test_get_started_starts_provisioning_poll_and_shows_tips_with_progress_footer`,
Step 11 block at `automation/tests/ui/onboarding/test_onboarding_provisioning.py:324-350`) — **merged
to `origin/automation/base`** (verified: `git diff origin/automation/base -- <that file>` is empty).
**Clarification filed:** #1767 (three case-text drifts + the progressive-fill product note — read it before implementing)

---

## Summary

Once the personal project is provisioned, the app sidebar mounts **on `/onboarding` itself** and the
project dropdown lists the user's **Private** project — marked selected with a **checkmark** — plus
every **team project** the account belongs to; the entity navigation shows its full set (9 menu
items) with **Settings** and **Catalog** below it.

The merged ELITEA-2232 spec already drives the whole first-login → provisioning → ready transition
and asserts the *skeleton* of that end state (sidebar present, trigger reads `Private`, one entity
item, the `Private` dropdown row exists). It asserts nothing about **what else is in the dropdown**,
about the **selected/checkmark indicator**, or about the **full navigation set** — which is precisely
what ELITEA-2240 is about. Hence `extend-existing`: three assertion clusters appended to the existing
Step 11 block, no new flow, no second traversal of a 30 s spec.

---

## Behavioural overlap — what the covering spec already proves

`test_onboarding_provisioning.py` (ELITEA-2232, merged) installs
`OnboardingPage.mock_fresh_user_state()` (the lead-sanctioned D3 transit that nulls
`personal_project_id`), navigates to `/onboarding`, clicks "Sure, let's go!", observes the
provisioning state, then **releases the mask** so the next 5 s poll receives the *unmodified*
backend response. Its Step 11 then asserts, from genuine backend data:

| Covering-spec assertion | `test_onboarding_provisioning.py:` | ELITEA-2240 step it satisfies |
|---|---|---|
| `expect(workspace_ready_title).to_be_visible(timeout=READY_TRANSITION_TIMEOUT)` | 334 | 3 — provisioning completed (the honest analog of "wait ~5 minutes") |
| `expect(progress_footer).to_have_count(0)` | 337 | 3 |
| `expect(sidebar_toggle).to_be_visible()` | 338 | 7 (partial — sidebar exists) |
| `expect(project_selector_trigger).to_be_visible()` + `to_contain_text("Private")` | 338-341 | 4-5 (partial — trigger shows Private) |
| `expect(sidebar_menu_item("chat")).to_be_visible()` | 345-346 | 7 (partial — ONE item only) |
| `open_project_selector()` → `expect(project_selector_option("Private")).to_be_visible()` | 347-350 | 4-5 (partial — the row exists; nothing about the checkmark) |
| `expect(sidebar_toggle).to_have_count(0)` + `expect(project_selector_trigger).to_have_count(0)` **during provisioning** | 264-265 | 2 (as absence — see clarification #1767 § 1) |

That is why this case is not `already-covered`: the covering spec proves the *transition*, not the
*content* of the state it lands in.

---

## Gap assertions — what the implementer appends

All three go **inside the existing Step 11 `allure.step` block** (or in one new
`with allure.step("Step 12 — ELITEA-2240 …")` block immediately after it, whichever reads better),
after `open_project_selector()`. Nothing before Step 11 changes.

### G1 — the Private row carries the selected / checkmark indicator (case steps 4-5)

```python
expect(onboarding_page.project_selector_option_selected("Private")).to_be_visible()
# and, in the same open dropdown, exactly one checkmark icon is rendered:
expect(onboarding_page.select_option_selected_icon).to_have_count(1)
expect(onboarding_page.select_option_selected_icon).to_be_visible()
```

One **testid** and one **state attribute** need adding (§ Handles Reference) — the checkmark was an
untestidded `<svg>` inside a MUI `ListItemIcon`, and the option exposed no `data-*` selection state.

> **Amended at implementation (2026-08-24, EliteaAI/EliteaUI@b0a7d61a).** Both landed on the SHARED
> `SingleSelectMenuItem.jsx` instead of on `SidebarProjectSelect.jsx`'s option Box — see § Handles
> Reference row 7 and § Testids to add item A for why. `project_selector_option_selected(label)` is
> unchanged as the page-object call; only the underlying selector shape moved.

### G2 — team projects are listed alongside Private (case step 6)

The team-project names are environment data, so **do not hardcode them**. Use the backend as the
oracle (`.agents/testing.md` § Fidelity policy, "capture the real response and assert the UI
against it"):

1. Capture `GET **/api/v2/projects/project/**` (the project-list query; live URL observed:
   `/api/v2/projects/project/default/1?check_public_role=true`) — a JSON array of
   `{"id", "name", …}`. Capture it with `page.expect_response` **around the mask release** (it
   fires when `personal_project_id` becomes truthy), or read the last matching response the page
   made.
2. Capture the personal project id from the *real* (post-release) `GET **/social/author/**`
   response — `personal_project_id`.
3. Expected label set = `{"Private"} ∪ {p["name"] for p in body if p["id"] != personal_project_id}`
   (the personal project renders as `Private`, never as its raw backend name; live:
   `id 399 / "project_user_659"` → `Private`). The response carried **no** public-project entry, so
   the mapping is 1:1 — every other returned project is a dropdown row.
4. Assert each expected label renders, each with its own auto-waiting expect:

```python
for label in expected_labels:                      # live: Private, Bugs & Features,
    expect(onboarding_page.project_selector_option(label)).to_be_visible(  # Elitea Development,
        timeout=UI_ELEMENT_TIMEOUT                                          # Elitea Testing Team,
    )                                                                       # UI Testing
assert len(expected_labels) >= 2, (
    "ELITEA-2240 step 6 needs an account that belongs to at least one team project; "
    f"the project-list response returned only {expected_labels}"
)
```

**⚠ Progressive fill — the trap on this step.** At the instant `workspace_ready_title` appears the
dropdown contains **only `Private`**; the four team rows arrive a few seconds later when the
project-list query resolves (measured live: only `Private` immediately after the transition, all
five present on the next probe). Per-label auto-waiting `expect()` handles this; a one-shot
`all_text_contents()` / count snapshot of the option list does **not**. Never assert the option
count.

### G3 — the full sidebar navigation is present (case step 7)

```python
_SIDEBAR_MENU_ITEMS = (
    "chat", "agents", "pipelines", "skills", "toolkits",
    "mcps", "credentials", "applications", "artifacts",
)
for value in _SIDEBAR_MENU_ITEMS:
    expect(onboarding_page.sidebar_menu_item(value)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
expect(onboarding_page.sidebar_settings_button).to_be_visible()
expect(onboarding_page.sidebar_agent_hub_button).to_be_visible()   # label "Catalog"
```

The existing single-anchor assertion (`sidebar_menu_item("chat")`) stays or is folded into the loop.
Same progressive-fill discipline: one auto-waiting expect per item, **never** a length assertion
(the digest's standing rule). `Settings` and `Catalog` are separate bottom-section buttons, not
`sidebar-menu-item-*` — see clarification #1767 § 2, which also records that the product label is
**"Toolkits & Indexes"**, not the case's "Toolkits" (assert the testid, not the label text).

**Boundary — do NOT add:** any assertion that the projects appeared *after five minutes*. The
duration is unobservable here (§ Fidelity Declaration, clarification #1767 § 3); the honest claim is
"once provisioning completes", which the covering spec's `workspace_ready_title` wait already pins.

---

## Preconditions

Unchanged from the covering spec — this extension adds no precondition:

- Authenticated user (localhost `auth_state` fast-path via `VITE_DEV_TOKEN`, no Keycloak login).
- Fresh browser context (`sessionStorage.onboarding_state` leftover skips the Welcome card).
- The account must belong to **at least one team project** (live: 4). G2's `>= 2` guard makes a
  changed account fail loudly instead of passing vacuously.
- No seeding, no cleanup, no test data.

---

## Fidelity Declaration

This extension introduces **no new substitution**. It inherits the covering spec's two, unchanged:

| # | What is substituted | Transit or terminal | Authority / what the system still produces |
|---|---|---|---|
| 1 | `GET /social/author/` has `personal_project_id` forced to `null` (all other fields byte-identical, fetched live via `route.fetch()`) | **Transit** | Establishes the case's own stated precondition (first login, no personal project) which no available account has — lead ruling `onboarding-w1` DECISIONS § D3, already merged. |
| 2 | The mask is released mid-test so the next poll receives the unmodified backend response | **Transit** (timing control) | Everything ELITEA-2240 asserts is rendered from the **genuine** post-release backend payload: the real project list, the real project names, the real selection state, the real permission-filtered menu. Nothing this case reads was authored by the test. Open canon question: #1759. |

**Coverage boundary (repeat it in the docstring):** the spec verifies that *once provisioning
completes*, the dropdown and the navigation contain what the case says they contain. It does **not**
verify the backend's ~5-minute provisioning of a brand-new account — no fresh account exists on this
environment and none can be created (open canon card #1760).

---

## Entry path (unchanged — this is the covering spec's flow)

```
context (fresh) → OnboardingPage.mock_fresh_user_state()      # before any navigation
                → navigate("/onboarding")  → welcome card
                → click_get_started()      → tour + onboarding-progress-footer
                → [ELITEA-2232's provisioning-state assertions, incl. sidebar/dropdown count 0]
                → clear_author_details_mock()
                → onboarding-workspace-ready-title + sidebar on /onboarding
                → open_project_selector()
                → ▶ G1 / G2 / G3 assertions
```

---

## Handles Reference

Every handle is a `data-testid`; state is a `data-*` attribute filter, never a state-named testid
(`.agents/testing.md` § Locator policy). Provenance verified 2026-08-24 with
`cd ../EliteaUI && git fetch origin` + the two-stage grep.

| # | Element | Primary handle (testid) | Page-object shape | Provenance |
|---|---|---|---|---|
| 1 | Sidebar toggle (sidebar exists) | `sidebar-toggle` | `OnboardingPage.sidebar_toggle` (exists) | **on-main ✓** |
| 2 | Project-selector trigger | `project-selector-trigger` | `OnboardingPage.project_selector_trigger` (exists) | **on-main ✓** |
| 3 | Project dropdown row, by label | `project-selector-option-{label}` | `PROJECT_SELECTOR_OPTION` template + `project_selector_option(label)` (exists) | on `automation/testids` only (EliteaAI/EliteaUI@bb8b9adc) — awaiting human cherry-pick to `main` |
| 4 | Sidebar entity menu item, by value | `sidebar-menu-item-{value}` | `SIDEBAR_MENU_ITEM` template + `sidebar_menu_item(value)` (exists) | on `automation/testids` only — awaiting human cherry-pick |
| 5 | Settings button (bottom section) | `sidebar-settings-button` | **add** `OnboardingPage.sidebar_settings_button = LocatorDescriptor(testid="sidebar-settings-button")` | on `automation/testids` only — **exists in JSX**, `SettingsButton.jsx:27` `testId` prop |
| 6 | Catalog button (bottom section) | `sidebar-agent-hub-button` | **add** `OnboardingPage.sidebar_agent_hub_button = LocatorDescriptor(testid="sidebar-agent-hub-button")` | on `automation/testids` only — **exists in JSX**, `AgentHubButton.jsx:38` |
| 7 | **Selected** project row (checkmark state) | `[data-selected="true"] [data-testid="project-selector-option-{label}"]` — **AMENDED at implementation**, see item A | class-level template `PROJECT_SELECTOR_OPTION_SELECTED = '[data-selected="true"] [data-testid="project-selector-option-{}"]'` + `project_selector_option_selected(label)` (**added**) | added on `automation/testids` (EliteaAI/EliteaUI@b0a7d61a) — not on `main` |
| 8 | The checkmark icon itself | `select-option-selected-icon` | `LocatorDescriptor(testid="select-option-selected-icon")` (**added**) | added on `automation/testids` (EliteaAI/EliteaUI@b0a7d61a) — not on `main` |

### Testids to add (`add-data-testid`, EliteaUI `automation/testids`, commit subject `test: [EL-2240] …`)

Reminder from the digest: EliteaUI's commitlint rejects `[ELITEA-NNNN]` — use `[EL-2240]`.

**A. `data-selected` state attribute — AMENDED at implementation.**

*As analysed:* put `data-selected` on the project-option `Box` in
`src/[fsd]/widgets/sidebar-root/ui/SidebarProjectSelect.jsx` by widening `customRenderOption` to
`(option, isSelected)` (the second argument is already passed by `SingleSelectMenuItem.jsx:101`, just
unused today). The AFS asserted this would keep the zero-functional-impact greps clean.

*As implemented (EliteaAI/EliteaUI@b0a7d61a):* it does **not** — widening the callback modifies the
`const customRenderOption = useCallback(` line, a direct hit on the reviewer's grep #1
(`^\+.*\buse(State|Effect|Memo|Callback|Ref)\(`, `.agents/role-overrides.md` § Reviewer slot). That
hit is declarable as mandatory plumbing, but it is avoidable, so it was avoided. The attribute went
on the **MUI `MenuItem` root** in the shared `src/[fsd]/shared/ui/select/SingleSelectMenuItem.jsx`
instead, where `isSelected` is already a destructured prop:

```jsx
<MenuItem
  {...restProps}
  data-testid={option.testId ?? `select-option-${option.value}`}
  data-selected={isSelected ? 'true' : 'false'}
```

The `MenuItem` **is** the option; the `project-selector-option-*` Box is the content rendered inside
it, so the state attribute sits on the ancestor and the locator becomes
`[data-selected="true"] [data-testid="project-selector-option-{label}"]` — still testid-anchored with
a `data-*` state filter, the canon shape for state (`.agents/testing.md` § Locator policy — "testid =
stable identity; state via `data-*`"), never a state-switched testid. The generic name is required
because the component is shared (same section's shared-component rule), and `data-selected` is this
codebase's established state attribute (`CategoryRail.jsx:27`, `BucketItem.jsx:244`,
`FileTreeItem.jsx:108`).

Measured on the shipped diff: **0 hook hits, 0 new-DOM-node hits**; one removal hit — the
`ListItemIcon` opening tag reflowed from one line to three, forced by `.prettierrc`
`"singleAttributePerLine": true` once item B adds a second attribute (declared in the commit body per
`add-data-testid` § Mandatory-plumbing exceptions; `npx prettier --check` passes on the result).

**B. Generic testid on the shared selected-icon slot** —
`src/[fsd]/shared/ui/select/SingleSelectMenuItem.jsx:136-140`, the `isSelected &&` branch:

```jsx
<ListItemIcon
  data-testid="select-option-selected-icon"
  sx={[styles.menuItemIcon, styles.menuItemSelectedIcon]}
>
  <CheckedIcon />
</ListItemIcon>
```

This element lives in a **shared** component (`src/[fsd]/shared/ui/`), so the name is deliberately
**generic**, per `.agents/testing.md` § Locator policy ("a component under `src/components/` or
`src/[fsd]/shared/` gets either a GENERIC testid or a caller-supplied `testId` prop") — do **not**
name it `project-selector-…`. It renders only for the selected option, so within one open
single-select it resolves to exactly one node.

*If the reviewer or lead rules B out* (shared-component reach), G1 degrades to the `data-selected`
assertion alone and the AFS's checkmark claim becomes "selection state asserted, icon not" — say so
in the Run Report rather than substituting a raw handle. `.MuiListItemIcon-root svg` is **not** an
acceptable fallback (no testid ⇒ invisible to the coverage metric, and #579's exception does not
apply — this is our own JSX).

---

## Coverage Map

### Axis 1 — TMS case elements

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| Pre | User is logged in | Authenticated session | `auth_state` (localhost dev token) | fixture | **covered** (existing) |
| 1 | Log in to the application for the first time | Authenticated, lands on the expected page | `mock_fresh_user_state()` + `navigate("/onboarding")` → Welcome card | covering spec `:196-230` | **covered** (existing) — "first login" is modelled, not performed; open canon card #1760 |
| 2 | Click the project dropdown; no project listed initially, limited sidebar items | Dropdown empty / sidebar limited | `sidebar-toggle`, `project-selector-trigger` **absence** while the progress footer is shown | covering spec `:264-265` (`to_have_count(0)`) | **covered, REWRITTEN — case-text drift, clarification #1767 § 1.** Live: during provisioning the sidebar and the dropdown do **not exist** (all five handles count 0), so there is nothing to click. `MainSidebar` returns null while `isOnboardingPage && !personal_project_id`. The absence assertions are the honest reading. |
| 3 | Wait ~5 minutes for provisioning to complete | Wait completes, state ready | mask release → `workspace_ready_title` + footer count 0 | covering spec `:330-337` | **covered** (existing) — the *completion*, not the duration (clarification #1767 § 3) |
| 4 | Click the project dropdown again | Dropdown opens and lists projects | `open_project_selector()` → `project-selector-option-Private` visible | covering spec `:347-350`, extended by **G2** | **covered + extended** |
| 5 | Private project fully loaded **with a checkmark indicator** | Private row present and marked selected | `project-selector-option-Private[data-selected="true"]` + `select-option-selected-icon` | **G1** (new) | **gap → extend** — live: `aria-selected="true"`, `Mui-selected`, `<CheckedIcon/>` in the row's `ListItemIcon`; neither is asserted today |
| 6 | Team projects (if applicable) are now listed | Every team project the account belongs to appears | project-list response as oracle → `project-selector-option-{name}` per project | **G2** (new) | **gap → extend** — live: `Bugs & Features`, `Elitea Development`, `Elitea Testing Team`, `UI Testing` (+ `Private`) |
| 7 | Full sidebar navigation visible: Chats, Agents, Pipelines, Skills, Toolkits, MCPs, Credentials, Applications, Artifacts, Settings, Catalog | All present | 9 × `sidebar-menu-item-*` + `sidebar-settings-button` + `sidebar-agent-hub-button` | **G3** (new) | **gap → extend** — the covering spec asserts ONE item. Case-text drift on the grouping + the "Toolkits & Indexes" label: clarification #1767 § 2 |
| Final | Full sidebar navigation items visible | as step 7 | same as 7 | **G3** | **gap → extend** |

### Axis 2 — coverage beyond the case (each with its reason)

| Observable | Reason | Assertion |
|---|---|---|
| The dropdown's option set **equals** the project-list response (not merely "contains Private") | A "contains" check passes even if the UI silently drops projects — the exact failure a user would report as "my team project is missing". Deriving the expectation from the response keeps it deterministic without authoring any value. | every label in the derived set has a visible row (**G2**) |
| Exactly **one** checkmark in the open dropdown | A single-select that marks two rows selected is a real defect class and is invisible to a per-row assertion. | `expect(select_option_selected_icon).to_have_count(1)` (**G1**) |
| Team-project count `>= 2` labels expected | Makes step 6's "if applicable" non-vacuous: if the test account loses its team memberships the spec fails loudly instead of green-passing an empty check. | `assert len(expected_labels) >= 2` (**G2**) |
| No error-level console messages across the flow | Standard side channel. **0 errors** measured live across the whole run (mask → click → poll → release → dropdown open/close ×2). | already asserted by the covering spec `:353-357` — no change needed |

---

## Blocked Steps

None.

---

## Known Defects / Clarifications

- **#1767 (this case, filed 2026-08-24, `question` + `case-text-drift`)** — step 2 unexecutable as
  written; step 7's list is 9 menu items + 2 buttons and the product label is "Toolkits & Indexes";
  step 3's "~5 minutes" is an estimate label; plus the progressive-fill product note.
- **#1760 (open canon)** — "log in for the first time" is unautomatable on this project; this case
  inherits the covering spec's modelling of it.
- **#1759 (open canon)** — is releasing a precondition mock mid-test sanctioned transit? This case
  inherits it unchanged from the merged spec; nothing new is introduced.
- No product defect found. The live product behaved exactly as the case intends for steps 4-7 —
  reconfirmed at implementation: the extended spec ran GREEN first try (32.01 s, 0 reruns, 0 console
  errors), with the derived project set and all 11 navigation handles satisfied.
- **AFS accuracy note (implementation, 2026-08-24):** § Testids to add item A's claim that widening
  `customRenderOption` keeps "the zero-functional-impact greps clean" was wrong — grep #1 matches any
  added line containing `useCallback(`. Amended above; no scope and no assertion changed.

---

## Evidence

Live probes, 2026-08-24, `http://localhost:5173/onboarding` (Playwright MCP, shared browser):

- **Ready state, ordinary authenticated user** — trigger `P\nProject:\nPrivate`; 9 menu items
  (`chat, agents, pipelines, skills, toolkits, mcps, credentials, applications, artifacts`);
  `sidebar-settings-button` = "Settings"; `sidebar-agent-hub-button` = "Catalog"; 0 console errors.
- **Open dropdown** — 5 rows. `select-option-399` → inner `project-selector-option-Private`,
  `aria-selected="true"`, `Mui-selected`, `<svg>` (CheckedIcon) inside `.MuiListItemIcon-root`.
  Other rows: `Bugs & Features` (406), `Elitea Development` (25), `Elitea Testing Team` (471),
  `UI Testing` (400) — all `aria-selected="false"`, no icon.
- **Project-list response** — `GET /api/v2/projects/project/default/1?check_public_role=true` →
  5 entries; `id 399 "project_user_659"` is the personal project (rendered as `Private`); no public
  project entry.
- **Provisioning state** (author-details `personal_project_id` nulled, "Sure, let's go!" clicked) —
  footer `Configuring Personal project... / about 5 min`; `sidebar-toggle` 0,
  `project-selector-trigger` 0, `sidebar-menu-item-*` 0, `sidebar-settings-button` 0,
  `sidebar-agent-hub-button` 0.
- **Transition** — releasing the mask brought up `onboarding-workspace-ready-title` in **1.8 s**;
  the dropdown then held **only `Private`**, with the four team rows present on the next probe.
