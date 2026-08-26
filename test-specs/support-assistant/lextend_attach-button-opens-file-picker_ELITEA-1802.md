# Test Case: Attach button is present and opens file picker in Support Assistant

## Metadata
- **TMS ID**: ELITEA-1802
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/support-assistant/ELITEA-1802_attach-button-present-and-opens-file-picker.md`
- **Linked Story**: https://github.com/EliteaAI/elitea-testing-public/issues/110
- **Priority**: l2 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173/chat`, EliteaUI `automation/testids`, Support Assistant served from `../elitea_assistant/src` via the `VITE_ASSISTANT_LOCAL=1` alias, dev backend via `VITE_DEV_TOKEN`)
- **User set**: `${TEST_USER}` (auto-authenticated on localhost via dev token)
- **Analyst**: qa-engineer (Sage)
- **Status**: extend-existing
- **Revision**: **2026-08-27 — re-analysed. Supersedes the 2026-07-16 pass** (see § Supersession notice). Original pass: 2026-07-16.

---

## Supersession notice — the third-party framing is RETRACTED

The 2026-07-16 revision of this AFS classified the Support Assistant's DOM as
**permanently un-remediable**, on the claim that the widget ships from a
*third-party npm package* (`@eliteaai/elitea-assistant`) with "no first-party JSX
to edit", and therefore that raw `aria-label` selectors were "not a policy
violation to fix in this repo" but "the only handle this external widget
currently exposes".

**That claim is false and is withdrawn in full.** Canon overturned it on
2026-07-23 (`.agents/testing.md` § Locator policy, connected-first-party-repo
bullet, ruling #705 — which names issue #110, i.e. *this* card, as the framing it
supersedes):

> A component we OWN but that ships from a separate repo (today: the Support
> Assistant, `@eliteaai/elitea-assistant`, source in the `../elitea_assistant`
> sibling) is testid-able — we control its source, so a missing testid there is
> *work to do in that repo*, NOT a #579 "testid can't be placed" waiver.

Three facts, each re-confirmed live during this pass, close the question:

1. **We own the source.** `EliteaAI/elitea_assistant` is a first-party repo
   (push access per `.agents/profile.md` § Repo access map), cloned as the
   sibling `../elitea_assistant`, with its own permanent `automation/testids`
   integration branch — the exact mirror of EliteaUI's.
2. **The dev server serves that source, not the published dist.**
   `EliteaUI/vite.config.js:27-32,49-53` aliases `@eliteaai/elitea-assistant` →
   `../elitea_assistant/src/index.ts` whenever `VITE_ASSISTANT_LOCAL=1`;
   `EliteaUI/.env:13` sets it. Testids added in the connected repo are live
   under HMR on `localhost:5173`.
3. **Every handle this case touches already carries a testid.** Seventeen
   `support-assistant-*` testids now exist on
   `EliteaAI/elitea_assistant` `origin/automation/testids`, added by the
   ELITEA-2418/2419/2420/2421/2423 waves — including the one this case is
   *about*. Verified in the live DOM this pass (§ Live Execution Evidence).

Consequently the old § Stable Handles table — which listed CSS/ARIA handles as
"not remediable" and declared "no testid work is in scope here regardless" — is
replaced by § Handles Reference below, in which **every** row is a testid with a
verified provenance value.

---

## Covering Test (behavioural proof)

- **File**: `automation/tests/ui/support_assistant/test_support_assistant_smoke.py`
- **Class**: `TestSupportAssistantAttachments` (line 409)
- **Test**: `test_attach_button_present_and_opens_picker` — **line 423**
- **Page object**: `automation/pages/support_assistant_page.py` —
  testid-era fields `attach_file_button` (L211), `attachment_chips` (L216),
  `widget` (L179), `widget_header_title` (L184), `message_input_field` (L189),
  `sidebar_launcher` (L174); helpers `attach_file_via_testid()` (L924),
  `get_attachment_chip_count()` (L965), `open_widget_via_sidebar()` (L709),
  `wait_for_widget_ready()` (L688)

**Behavioural-overlap argument.** The covering test already performs, in order:
open the Support Assistant widget on `/chat` → wait for it ready (title + input
visible) → assert the Attach button is visible (case Step 4) → create
`tmp_path/test_attachment.txt` with content `"Test attachment content"`
(byte-identical to the case's Test Data) → open a `page.expect_file_chooser()`
context and click Attach inside it (case Step 5) → assert the resulting
`FileChooser` is not `None` (case Step 6) → `file_chooser.set_files(...)` (case
Step 7) → `wait_for_network()` (case Step 8). Every one of the case's eight steps
maps onto an executed action or assertion. It is merged on `automation/base` and
green (run this pass: **1 passed in 9.71s**, `reruns.json` = 0 reruns).

The residual gap is therefore **not** missing behaviour. It is two bounded
defects in *how* the existing test observes that behaviour — one policy, one
substance — detailed in § Gap assertions. Both are small, local edits to an
existing merged spec, not a rewrite; hence `extend-existing`.

> **Traceability is already delivered — do not re-do it.** The 2026-07-16 pass's
> sole gap assertion (an `@allure.issue` decorator pointing at ELITEA-1802's own
> case file) **shipped** and is present at lines 419-422. The TMS case's
> `automation_test_id` and `automation_pr` (PR #581) are likewise already
> back-written. Nothing in this revision re-opens traceability.

---

## Live Execution Evidence (this pass, 2026-08-27)

Executed the case's own eight steps live against `http://localhost:5173/chat`
via Playwright MCP — not inferred from the covering test's pass, and not from the
prior AFS.

**Steps 1-3 — navigate, open widget, widget ready.** Navigated to `/chat`;
clicked `[data-testid="sidebar-support-assistant-button"]` with a plain native
click. Widget opened **first try, no `page.evaluate` needed** — the MUI-overlay
intercept quirk that forced a JS click in the legacy `open_widget()` does not
apply to the sidebar launcher. Widget title read live: **"ELITEA Support"**.

**Step 4 — Attach button visible, and it carries the testid.** Direct DOM read:

```json
{"widgetPresent": true,
 "widgetTitle": "ELITEA Support",
 "attachByTestid": {"tag": "BUTTON", "ariaLabel": "Attach file",
                    "className": "elitea-assistant-attach-button",
                    "disabled": false, "visible": true,
                    "rect": {"x": 79, "y": 805.5, "width": 28, "height": 28}},
 "sameElementAsLegacy": true,
 "legacyCount": 1}
```

Two things this settles for the implementer:
`data-testid="support-assistant-attach-button"` **does render** through the alias
(answering the "does the running dev server predate the flag?" question — it does
not), and the testid resolves to the **same single element** as the legacy
`button[aria-label="Attach file"]` (`sameElementAsLegacy: true`, `legacyCount: 1`).
So the migration in § Gap assertions is a pure handle swap with **zero**
behavioural change — including the now-redundant `.first`, since only one such
button exists.

Full testid inventory rendered inside the widget this pass (32 nodes):
`support-assistant-widget-title`, `-new-chat-button`, `-history-button`,
`-expand-button`, `-message-item` ×7, `-message-bubble` ×7,
`-message-copy-button` ×5, `-drop-zone`, `-attach-button`, `-message-input`,
`-send-button`.

**Steps 5-6 — click Attach, native file chooser opens.** Clicked the testid'd
button; Playwright reported page modal state `[File chooser]`. The chooser is
opened by the browser in response to the real click — the case's own observable,
produced by the system.

**Step 7 — select the file.** Wrote `test_attachment.txt` (content
`"Test attachment content"`) and drove `fileChooser.setFiles(...)` against the
real chooser. Result, read from the DOM:

```json
{"chipCount": 1,
 "chipText": ["test_attachment.txt"],
 "chipDataAttrs": [{"class": "elitea-assistant-file-chip",
                    "data-testid": "support-assistant-attachment-chip"}],
 "attachStillEnabled": true, "sendDisabled": true, "inputValue": ""}
```

**Step 8 — the case's premise is FALSE: no upload fires on attach.** Network
capture filtered on `attachment|support_assistant` across the whole attach flow:

```
1963. [GET] /api/v2/support_assistant/config/          => [200] OK
1964. [GET] /api/v2/support_assistant/conversations/   => [200] OK
1967. [GET] /api/v2/support_assistant/config/          => [200] OK
1968. [GET] /api/v2/support_assistant/conversations/   => [200] OK
1975. [GET] /api/v2/support_assistant/config/          => [200] OK
2386. [GET] /api/v2/support_assistant/conversation/55bd36b5-… => [200] OK
```

**Zero** `POST /api/v2/support_assistant/attachments/{uuid}`. By design: the
upload fires on **Send** (`MessageInput.handleSend` → `startUpload`), not on
attach; attaching only stages a `PENDING` chip in local state. This independently
re-confirms the surface digest's quirk 37.

The case's Step 8 (*"`networkidle` reached … indicating the file upload request
has been processed"*) therefore **passes vacuously** — it settles because nothing
was ever in flight. The product is correct; the case text drifted. Per the
reverse-masking guard this is a CLARIFICATION, not a defect: filed as
**#1827**, and § Gap assertions replaces the vacuous wait with the observable the
product genuinely produces.

**Side channels.** Zero console errors across the entire flow (`browser_console_messages`
at level `error`: *"Returning 0 messages"*; 8 messages total, 1 pre-existing
warning at page load, unrelated to the Support Assistant).

**Covering-spec regression check.**
```
cd automation && HEADLESS=true ../.venv/bin/pytest \
  tests/ui/support_assistant/test_support_assistant_smoke.py::TestSupportAssistantAttachments::test_attach_button_present_and_opens_picker \
  -v -p no:cacheprovider
→ 1 passed in 9.71s   (reruns.json: 0 tests, 0 total reruns)
JUnit: automation/reports/archive/junit_20260827_001315.xml
```

---

## Preconditions
- User authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- Dev server running with `VITE_ASSISTANT_LOCAL=1` so the Support Assistant is
  served from `../elitea_assistant/src` — **this is what makes the testids
  present**. Confirmed live this pass.
- A temp test file (`test_attachment.txt`, content `"Test attachment content"`)
  from the `tmp_path` fixture — already how the covering test builds it.
- Support Assistant enabled — confirmed live: sidebar launcher renders on `/chat`.

## Test Data
### reuse-existing
- `${BASE_URL}` = `http://localhost:5173`; page under test `/chat`
- Test file name/content: `test_attachment.txt` / `"Test attachment content"`
  (matches the case's Test Data exactly; already built via `tmp_path`)
- `WIDGET_TIMEOUT` — already used by the covering test

No new test data. `tmp_path` is function-scoped and self-cleaning.

---

## Handles Reference

**Locators are testid-only** (`.agents/testing.md` § Locator policy). Every
handle this case's steps touch already has a testid — **nothing here is
`needs-adding`**. Provenance verified this pass with a fresh `git fetch origin`
in **both** repos (`.agents/role-overrides.md` § Every role — fresh ground truth).

Because the Support Assistant is a **connected first-party repo**, the honest
provenance value is the connected-repo analog of
`on-automation/testids only (awaiting human promotion to main)` — and the repo
named below is `EliteaAI/elitea_assistant`, **not** EliteaUI. Note the extra
promotion hop (`.agents/workflow.md` § Connected repos): a testid on the
assistant's `main` reaches a *deployed* env only after EliteaUI bumps the
`@eliteaai/elitea-assistant` git-dependency. Local tests are green immediately
via the alias.

| Element | Handle (testid) | Page-object field | Owning repo | PROVENANCE (verified 2026-08-27) |
|---|---|---|---|---|
| Sidebar launcher | `sidebar-support-assistant-button` | `sidebar_launcher` | **EliteaUI** | `on automation/testids only` (EliteaUI@37176b46) — **not on `EliteaAI/EliteaUI` `main`**; awaiting human cherry-pick |
| Widget window | `support-assistant-widget` | `widget` | **elitea_assistant** | `on automation/testids only` (EliteaAI/elitea_assistant@b8a287b) — **not on `EliteaAI/elitea_assistant` `main`**; awaiting human promotion, then the EliteaUI dep bump |
| Widget header title | `support-assistant-widget-title` | `widget_header_title` | **elitea_assistant** | `on automation/testids only` (EliteaAI/elitea_assistant@b8a287b) — not on that repo's `main` |
| Message input | `support-assistant-message-input` | `message_input_field` | **elitea_assistant** | `on automation/testids only` (EliteaAI/elitea_assistant@b8a287b) — not on that repo's `main` |
| **Attach file button** | `support-assistant-attach-button` | `attach_file_button` | **elitea_assistant** | `on automation/testids only` (EliteaAI/elitea_assistant@1960c8e, `src/components/chat/MessageInput.tsx:276`) — **not on that repo's `main`**; added by the ELITEA-2421 wave |
| Attachment chip (composer) | `support-assistant-attachment-chip` | `attachment_chips` | **elitea_assistant** | `on automation/testids only` (EliteaAI/elitea_assistant@1960c8e, `src/components/chat/attachments/AttachmentChip.tsx`) — not on that repo's `main` |
| File-chooser event | `page.expect_file_chooser()` | — | — | Playwright browser API, not an app handle — no testid applicable |

Verification command (run in each repo after `git fetch origin`):

```bash
FILTER='(data-testid|testid[[:space:]]*[:=])'
for t in support-assistant-widget support-assistant-widget-title \
         support-assistant-message-input support-assistant-attach-button \
         support-assistant-attachment-chip; do
  printf "%-40s main:%-4s testids:%s\n" "$t" \
    "$(git grep -- "$t" origin/main -- src/ 2>/dev/null | grep -qiE "$FILTER" && echo YES || echo no)" \
    "$(git grep -- "$t" origin/automation/testids -- src/ 2>/dev/null | grep -qiE "$FILTER" && echo YES || echo no)"
done
```

Output this pass (`../elitea_assistant`) — all five `main:no  testids:YES`:

```
support-assistant-widget                 main:no   testids:YES
support-assistant-widget-title           main:no   testids:YES
support-assistant-message-input          main:no   testids:YES
support-assistant-attach-button          main:no   testids:YES
support-assistant-attachment-chip        main:no   testids:YES
```

and (`../EliteaUI`): `sidebar-support-assistant-button   main:no   testids:YES`.

**No handle this case touches lacks a testid — there is no `add-data-testid`
work in either repo for ELITEA-1802.** (Contrast the retracted 2026-07-16
finding, which reached the same "no testid work in scope" conclusion from the
opposite and wrong premise: that none *could* be added.)

---

## Coverage Map

### Axis 1 — case elements → disposition

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| Precond | User authenticated | dev-token auth works | `auth_state` / `VITE_DEV_TOKEN` | `conftest.py` | covered |
| Precond | Temp test file created | `test_attachment.txt` exists with expected content | `tmp_path` fixture | test L440-441 | covered |
| Precond | Support Assistant enabled | launcher renders | live observation this pass | `/chat` | covered |
| 1 | Navigate to `/chat` | page loads | `chat_page.navigate_to_chat()` | test L430 | covered |
| 2 | Open Support Assistant widget | widget panel opens, title visible | `open_widget()` (legacy JS-click) | test L432 | covered — **migrate** to `open_widget_via_sidebar()` (gap 1c) |
| 3 | Wait for widget fully ready | title + message input visible | `wait_for_widget_ready()` | test L433 | covered |
| 4 | Assert Attach button visible | button is visible | inline raw `page.locator('button[aria-label="Attach file"]').first` | test L436-437 | covered but **policy-violating** — see gap 1a |
| 5 | Click Attach inside `expect_file_chooser` | chooser context active, click executed | `page.expect_file_chooser()` wrapping `attach_btn.click()` | test L442-443 | covered — **migrate** the handle (gap 1a) |
| 6 | Assert file-chooser opened | `fc_info.value` is not `None` | explicit assert | test L446-447 | covered |
| 7 | Select test file in chooser | `set_files()` sets the temp file | `file_chooser.set_files(str(test_file))` | test L448 | covered |
| 8 | Wait for network idle after upload (≤10 s) | `networkidle` reached, *"indicating the file upload request has been processed"* | `wait_for_network()` | test L449 | **clarification #1827** — premise false (no upload fires on attach); assertion is vacuous. Replaced by gap 2 |
| — | Traceability to ELITEA-1802's own case file | `@allure.issue` present | delivered 2026-07-16 | test L419-422 | covered — **already shipped, do not re-do** |

### Axis 2 — assertions beyond the case

| Observable | Grounded reason |
|---|---|
| The staged attachment chip renders bearing the file name (`support-assistant-attachment-chip`, text `test_attachment.txt`) | Replaces case Step 8's vacuous `networkidle` wait with the observable the product *actually* produces on attach. Without it the case's back half proves nothing: `set_files()` returning cleanly is not evidence the app received the file. This is the honest system-produced observable, verified live this pass. |

No other observables added. The case's Pass/Fail criteria are otherwise fully
satisfied by the existing assertions.

---

## Gap assertions (what the implementer must add)

Two bounded edits to
`automation/tests/ui/support_assistant/test_support_assistant_smoke.py`
(`TestSupportAssistantAttachments::test_attach_button_present_and_opens_picker`,
L423-449). **No new page-object fields and no testid work are required** —
every handle below already exists as a class-level `LocatorDescriptor`.

### Gap 1 — migrate off the inline raw handle (locator policy)

Current L436 builds a raw locator **inside the spec file**, which is a *double*
violation of `.agents/testing.md` § Locator policy: a non-testid handle, and a
locator constructed outside a page-object class field.

```python
# BEFORE (L436-437, L443)
attach_btn = page.locator('button[aria-label="Attach file"]').first
assert attach_btn.is_visible(), "Attach file button should be visible"
...
    attach_btn.click()
```

Replace with the existing testid-backed field. `.first` is not carried over —
verified live that exactly one such button exists (`legacyCount: 1`).

```python
# AFTER
expect(support_page.attach_file_button).to_be_visible()
...
    support_page.attach_file_button.click(timeout=WIDGET_TIMEOUT)
```

The two-line click-inside-`expect_file_chooser` block may instead be collapsed
onto the already-merged helper `support_page.attach_file_via_testid(str(test_file))`
(L924), which does exactly `expect_file_chooser` → click `attach_file_button` →
`set_files`. Implementer's call; both are compliant. If the helper is used, the
Step-6 `fc_info.value is not None` assertion moves inside the helper's contract
and is proven instead by the chip assertion in gap 2 — state which shape was
chosen in the Run Report.

**(1c, optional but recommended)** L432 uses the legacy `open_widget()`, which
JS-`evaluate`-clicks the floating launcher to dodge a MUI overlay intercept.
`open_widget_via_sidebar()` (L709) drives the testid'd sidebar launcher with a
real click — confirmed working first try this pass. Preferring it removes a
`page.evaluate` from the flow and is a genuine fidelity improvement (a real
user-equivalent gesture). Not mandatory for this case; do not expand it into
other specs.

### Gap 2 — replace the vacuous network wait with the real observable

```python
# BEFORE (L449)
support_page.wait_for_network(timeout=WIDGET_TIMEOUT)
```

Verified live: **zero** attachment requests fire on attach, so this settles
vacuously. Replace with the chip the product genuinely stages:

```python
# AFTER
with allure.step("Step 5 — Verify the selected file is staged in the composer"):
    # Case Step 8's "wait for upload to settle" is a false premise: the upload
    # fires on Send, not on attach (MessageInput.handleSend -> startUpload), so
    # networkidle passes vacuously. Case-text clarification filed as #1827.
    # The staged chip is the observable the product actually produces here.
    expect(support_page.attachment_chips).to_have_count(1)
    expect(support_page.attachment_chips.first).to_contain_text("test_attachment.txt")
```

Keep every step wrapped in `allure.step` (`.agents/testing.md` § Step reporting)
and renumber the blocks if a step is added.

### Not in scope

- **No other support-assistant spec, and no legacy field on
  `support_assistant_page.py`.** The pre-policy `fallback=` fields
  (`attach_button`, `launcher_button`, `widget_title`, …) and the legacy
  `attach_file()` helper have other callers and are grandfathered tech debt
  (#25/#42) — migrating them is a separate card, not this one.
- **No testid work in either repo** — all six handles exist (§ Handles Reference).
- **No traceability work** — `@allure.issue` and the TMS `automation_test_id`
  back-write already shipped in 2026-07-16 / PR #581.

---

## Cleanup

None beyond pytest teardown — `tmp_path` removes the temp file at test end
(matches the case's own Postconditions). Attaching stages the file only in local
component state and fires no request, so **nothing is created server-side** by
this case; the chip dies with the page. No cleanup call is present or needed.

---

## Known Defects Found

**None — no product defect.** The attach flow works end-to-end on the live
product: button visible and testid'd → real click opens the browser's native
file chooser → file selects → chip stages with the correct file name → zero
console errors.

**One case-text clarification filed: #1827** — *"[Clarification][ELITEA-1802]
Case Step 8 asserts an upload that never fires on attach; Test Data selector
superseded by a testid"*. Both items are stale **case text**, not product
behaviour (reverse-masking guard: the product is correct, so this is a
clarification and never a `bug`). Dedup pass before filing:
`gh issue list --state all --limit 400` keyword-matched on `1802` / `attach`+`support`
returned only #1653, #1584, #1583 — all ELITEA-2420/2421 *product* bugs about the
send-side attachment behaviour, none about ELITEA-1802's case text. Not
duplicates.

---

## Implementation note (implementer, 2026-08-27)

Both gap assertions shipped as specified. Recorded here so the § Gap assertions
line references above are not read as the shipped state.

- **Gap 1 — shape chosen: the explicit two-line form**, not the
  `attach_file_via_testid()` helper. Rationale: the case's Step 6 is its own
  expected result (*"file chooser dialog opens"*), and Coverage Map Axis-1 row 6
  points at a spec-level assertion for it. Collapsing onto the helper would move
  that observable behind a helper contract and leave the row pointing at nothing.
  The explicit form keeps the migration a pure handle swap — `attach_btn` →
  `support_page.attach_file_button` — with zero behavioural change, exactly as
  the live evidence (`sameElementAsLegacy: true`, `legacyCount: 1`) licenses.
  `.first` dropped as specified. `attach_file_via_testid()` keeps its existing
  callers untouched.
- **Gap 1c — taken.** `open_widget()` → `open_widget_via_sidebar()`; removes a
  `page.evaluate` from the flow. Not propagated to any other spec.
- **Gap 2 — shipped**, and **red-green verified**: temporarily asserting
  `to_have_count(2)` failed with `Actual value: 1`, proving the assertion
  discriminates rather than passing vacuously like the `wait_for_network()` it
  replaces.
- **Docstring `Covers:` widened to `7.1.1, 7.1.2, 7.1.3`** — the chip assertion
  is what makes 7.1.3 (*"selected file appears as preview"*) genuinely covered;
  the class docstring already claimed it while no test asserted it.
- **Import block sorted** (pre-existing `ruff I001` on the block the `expect`
  import joins). File-level ruff errors 11 → 10; the 10 remaining are
  pre-existing `E501`s on long `@allure.issue` URLs, untouched.
- **Shipped step layout:** Step 1 open (sidebar) · Step 2 attach button visible ·
  Step 3 click inside `expect_file_chooser` · Step 4 chooser opened + `set_files` ·
  Step 5 staged chip. All wrapped in `allure.step`.
