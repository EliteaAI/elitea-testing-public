# Test Case: File Preview/Edit – Context Management Settings Panel Opens for Supported File

## Metadata
- **TMS ID**: ELITEA-1865
- **Linked Story**: none
- **Priority**: l3 (TMS `priority: medium` — same mapping as siblings ELITEA-1856 / ELITEA-1862)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (batch `artifacts-w05`, 2026-08-23; **re-analysed** batch `artifacts-w07`, 2026-08-28)
- **Status**: **blocked** — CONFIRMED on re-analysis; the case's central observable does not exist on the surface the case names
- **Clarification filed**: EliteaAI/elitea-testing-public#1695 (`question` + `case-text-drift`) — human ruled 2026-08-28 "Panel is expected to be in place. Double check UI."; re-analysis disproof posted as [issue comment 5451524815](https://github.com/EliteaAI/elitea-testing-public/issues/1695#issuecomment-5451524815)

## Why this case is blocked (one paragraph)

The case asserts that opening a supported file from an artifact bucket's file
preview displays a **"Context Management" settings panel** with ~14 configuration
fields and Cancel/Save buttons. **No such panel exists anywhere on the Artifacts
surface.** The Artifacts file-preview panel (`FilePreviewCanvas`) renders exactly
a file-path header, Save, Discard, a close (X) and a 3-dot actions menu — plus a
type-dependent content area — and nothing else; this is already fully documented
by the merged sibling cases ELITEA-1851 (editor UI) and ELITEA-1862 (image
branch). Every field the case lists belongs to the **Context Budget /
Context Management** form, a different feature consumed only by Chat
participants, the Pipelines ChatPanel and the Applications ConfigurationTab
(plus a near-identical Settings → Memory form, already covered by ELITEA-2374).
This is **case-text drift, not a product defect** — the product is correct and
the case text names the wrong surface. Because the observable cannot be produced
honestly against the real system, the case is routed to a human rather than
engineered around (`.agents/testing.md` § Fidelity policy).

## Re-analysis 2026-08-28 (batch `artifacts-w07`) — human ruling on #1695

A human ruled on #1695: *"Panel is expected to be in place. Double check UI."*
This section records the re-verification. **The verdict is unchanged**, but it is
now backed by *positive disproof* rather than a single negative observation —
the four gaps the first pass left open are closed below.

Environment: `http://localhost:5173`, EliteaUI `automation/testids` @ `471c4652`
(fetched fresh), DEV backend, localhost `auth_state`.

### Gap 1 — the `afa` bucket the case names does not exist

The first pass drove a *fixture* bucket, so per-bucket state could not be ruled
out. Checked the real list this time:

```
GET /artifacts   artifacts-buckets-footer-count = "Buckets: 11"
                 rows rendered = 11  (all of them; no pagination truncation)
abc-test · alita · all-file-types-attachment-small-size · attachments ·
autotest-elitea1828-dupmodal · bucket-a1b2c3d4…w3x4 · file-upload · ggr ·
intesting · scout-probe-shortname · temp
```

No `afa` — and alphabetically it would sort between `abc-test` and `alita`, so
it is genuinely absent, not scrolled out of view. **The case's Preconditions
cannot be satisfied as written**, independently of the panel question.

### Gap 2 — every affordance on the preview surface exhausted

Executed on `sample_data.md` in `all-file-types-attachment-small-size` — the
**richest** supported branch (markdown gets the render-mode toggle and language
select that the case's `1.png` image branch does not, per ELITEA-1862), at
**1280×720 and 1920×1200**:

| Affordance | Observed contents |
|---|---|
| Preview header buttons | `artifacts-preview-close-button`, `artifacts-preview-save-button` (**Save**), `artifacts-preview-discard-button` (**Discard**) |
| Preview 3-dot overflow (`file-preview-overflow-menu-menu-button`) | **Copy Content · Download · Delete** — nothing else |
| Render-mode toggle | `artifacts-preview-mode-toggle-rendered` / `artifacts-preview-mode-toggle-code` |
| **Bucket-level** 3-dot (`bucket-menu-<name>-menu-button`, hover-gated) | **Upload files · Rename · Pin to top · Share · Manage permissions** — no "Manage context"/settings entry (closes the lead's "is it per-bucket?" question) |
| Wide viewport 1920×1200 | no right-hand drawer appears; all label matches stay 0 |

Label probe over `document.body.innerText` with the preview open:

```
Context Management 0 · Context Window 0 · Max Tokens 0 · Content Strategy 0
Context Strategy 0 · Context Tokens 0 · Preserve Recent Messages 0
Summarized Link Count 0 · Summarization 0 · Summary Model 0
Summary Trigger Ratio 0 · Attribute: Clause 0 · Target Summary Tokens 0
External Messages 0 · Always preserve system messages 0 · Custom Instructions 0
"You are a helpful assistant." 0
```

### Gap 3 — positive control: the same probe DOES find the panel where it lives

To prove the zeros are a real absence and not a broken probe, the **identical**
label probe was run on `/settings/memory` in the same browser session:

```
Context Management 3 · Max Context Tokens 1 · Preserve Recent Messages 1
Summarization 2 · Target Summary Tokens 1
```

Same method, same session — finds the panel there, finds nothing on Artifacts.
This is the disproof the human can act on.

### Gap 4 — source: no Artifacts-side path exists to mount it

```
$ cd ../EliteaUI && grep -rln "ContextBudget\|ContextStrategy\|context-budget" src/ | grep -i "artifact\|bucket"
(no output)
```

`PreviewHeader.jsx` renders exactly **seven** things — close IconButton
(`:175`), file-path Typography (`:191`), Save (`:204`), Discard (`:213`),
`DotMenu` (`:239`), `ToggleButtonGroup` (`:260`), language `Select.SingleSelect`
(`:290`) — and there is **no feature flag** anywhere under
`src/[fsd]/features/artifacts/` or `src/pages/Artifacts/` that could gate an
eighth. Consumers of the widget are unchanged from the first pass:
`Participants.jsx` (Chat), `ChatPanel.jsx` (Pipelines), `ConfigurationTab.jsx`
(Applications), plus the separate `features/settings/ui/memory/` variant
(ELITEA-2374).

### Evidence

- `automation/test-results/screenshots/ELITEA-1865-reanalysis-preview-no-context-panel.png`
  — uploaded to the `evidence` release and embedded in the #1695 comment.
- Console during the run: 0 errors on the preview render itself.

### What did NOT change

Nothing in the sections below is superseded. The label→component mapping, the
Coverage Map and the three unblock options all still hold; this section only
raises the confidence from "observed absent once, on a fixture bucket" to
"absent on the real bucket list, on the richest branch, at two viewports, with
every menu opened, with a working positive control, and with no source path".

## Preconditions (as executed)
- Localhost `auth_state` (no login step).
- A fresh bucket seeded via the `artifact_bucket` fixture, with `1.png`
  (minimal valid 1×1 PNG) uploaded via `ArtifactAPI.upload_file()`.
  The case's literal `afa` bucket is **not** a fixture anywhere in the suite —
  same finding as every other preview case in this folder.

## What WAS executed and observed live (2026-08-23)

Fresh bucket + `1.png`, Artifacts → bucket row → row "View/Edit file" icon.
Probe run with the suite's own fixtures (`page`, `artifact_api`,
`artifact_bucket`) driving `ArtifactsPage`; probe deleted after the run.

```
URL=http://localhost:5173/artifacts?bucket=<bucket>&file=1.png
artifacts-preview-file-path:            count=1  text='<bucket>/1.png'
artifacts-preview-save-button:          count=1  text='Save'
artifacts-preview-discard-button:       count=1  text='Discard'
artifacts-preview-close-button:         count=1
file-preview-overflow-menu-menu-button: count=1
artifacts-preview-mode-toggle-group:    count=0
artifacts-preview-language-select:      count=0
artifacts-preview-code-editor:          count=0
PANEL_TEXT='<bucket>/1.png\nSave\nDiscard'

'Context Management'       → 0 matches on the page
'Context Window'           → 0
'Max Context Tokens'       → 0
'Max Tokens'               → 0
'Context Strategy'         → 0
'Preserve Recent Messages' → 0
'Summarization'            → 0
'External Messages'        → 0
'Custom Instructions'      → 0
CONSOLE_ERRORS=[]
```

Screenshot: `automation/test-results/screenshots/ELITEA-1865-preview-no-context-panel.png`
(uploaded to the `evidence` release and embedded in #1695).

Note also: the case's step 12 expects **"Cancel" and "Save"** at the bottom of
the panel. The Artifacts preview panel's pair is **Save + Discard** — there is
no Cancel button on this surface at all. The Cancel/Save pair belongs to
`ContextStrategyModalContent.jsx:218,226`.

## Where the described panel actually lives (source-confirmed)

| Case element | Real label / component |
|---|---|
| "Context Management" panel + toggle (step 5) | `label="Context Management"` — `src/[fsd]/widgets/context-budget/ui/ContextStrategyModalContent.jsx:130` |
| "Content Strategy & Token Management" (step 6) | `title="Context Strategy & Token Management"` (**Context**, not Content) — `ContextStrategyModalContent.jsx:158` |
| "Context Tokens" (step 6) | `label="Max Context Tokens"` — `ContextStrategyTokenManagement.jsx:62` |
| "Preserve Recent Messages" (step 6) | `ContextStrategyTokenManagement.jsx:85` |
| "Enable automatic summarization" (step 7) | `ContextStrategySummarization.jsx:55` |
| "Summarization Instructions" (step 8) | `ContextStrategySummarization.jsx:88` |
| "Summary Model" / "Summary Trigger Ratio" (step 9) | `ContextStrategySummarization.jsx:97,133` — both behind a **hidden feature toggle** in the current source |
| "Target Summary Tokens" (step 9) | `ContextStrategySummarization.jsx:178` |
| "Always preserve system messages" (step 10) | `ContextStrategySystemMessages.jsx:36` |
| "Cancel" / "Save" (steps 12–14) | `ContextStrategyModalContent.jsx:218,226` |

`ContextBudgetUI` consumers (the only entry points): `Participants.jsx:6` (Chat),
`ChatPanel.jsx:9` (Pipelines), `ConfigurationTab.jsx:15` (Applications).
The Settings → Memory variant (`src/[fsd]/features/settings/ui/memory/`) is
already covered by **ELITEA-2374** —
`test-specs/settings-user-profile/l3_context-management-toggle-enables-disables-fields_ELITEA-2374.md`.
"Context Window" and "Summarized Link Count" (case steps 5–6) match **no** label
in EliteaUI source at all.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Click the "afa" bucket | bucket selected | executed (fixture bucket, not literal `afa`) | file table renders | **out-of-scope here** — already covered by ELITEA-1803 / ELITEA-1838 |
| 2 Left tree shows the bucket with `1.png` | file visible | executed | file row present | **out-of-scope here** — covered by ELITEA-1838 (file-tree) |
| 3a Hover `1.png`, click "View/Edit file" icon | file opens | executed | preview panel opened, path header `<bucket>/1.png` | **already-covered** by ELITEA-1851 / ELITEA-1862 (icon is NOT hover-gated — see #994) |
| 3b …"and Context Management panel appears" | panel appears | — | — | **blocked** — 0 matches live |
| 4 Context Management panel is visible | panel visible | — | — | **blocked** |
| 5 Toggle/switch, "Context Window", "Max Tokens" fields | fields present | — | — | **blocked** (labels live in `context-budget`; "Context Window" exists nowhere) |
| 6 "Content Strategy & Token Management" section + 4 fields | fields present | — | — | **blocked** (real title is "**Context** Strategy…"; "Summarized Link Count" exists nowhere) |
| 7 "Summarization" section + toggle | toggle present | — | — | **blocked** |
| 8 "Summarization Instructions" text area | visible | — | — | **blocked** |
| 9 Summary Model / Trigger Ratio / Attribute: Clause & Format / Target Summary Tokens | present with values | — | — | **blocked** (two of them are behind a hidden feature toggle even on their real surface; "Attribute: Clause & Format" exists nowhere) |
| 10 "External Messages" section + toggle | toggle present | — | — | **blocked** |
| 11 "Custom Instructions" text area, placeholder "You are a helpful assistant." | visible | — | — | **blocked** (that string appears only in `settings/lib/helpers/codeExamples.helpers.js`, a code sample) |
| 12 "Cancel" and "Save" at the bottom | both present | — | — | **blocked** — the Artifacts panel's pair is **Save + Discard**, no Cancel |
| 13 Cancel closes the panel without saving | closes | — | — | **blocked** |
| 14 Save saves the context-management settings | save succeeds | — | — | **blocked** |

### Axis 2 — Analyst additions
None. No AFS steps are specced: 12 of 14 case elements are unproducible, and the
2 that are producible are already asserted by merged specs. Writing a spec that
asserted "no Context Management panel appears" would invent an observable the
case never asked for and prove nothing about the feature the case is named after.

## Blocked Steps

**Steps 3 (second half) through 14 — the entire subject of the case.**

What could not be produced: a "Context Management" settings panel (with its
toggle, Context Window / Max Tokens, the Content-Strategy section, the
Summarization section, External Messages, Custom Instructions, and a
Cancel/Save pair) rendered from the **Artifacts** file-preview surface. The
product never emits it there; the panel is a different feature on three other
surfaces.

**What unblocks it (human decision — EliteaAI/elitea-testing-public#1695):**
1. **Retarget** — rewrite the case against the Context Budget modal on its real
   surface (Chat participants / Pipelines ChatPanel / Applications
   ConfigurationTab) and move it out of the `artifacts` module; then re-analyse; or
2. **Retire as duplicate** of ELITEA-2374 if the Settings → Memory form is the
   intended subject; or
3. **Delete** the case if the panel was never meant to be an Artifacts feature.

Until one of those lands there is no honest observable, so no test is specced.

## Known Defects Found During Exploration
None. The Artifacts file-preview panel behaved exactly as ELITEA-1851 /
ELITEA-1862 document (image branch: no mode toggle, no language select, no code
editor; Save/Discard present). Zero console errors across bucket open, file
open, and panel render.

## Cleanup
1. `artifact_bucket` fixture teardown deletes the bucket — hit the known `#636`
   404-on-teardown again (2/2 probe runs this session); already swallowed by the
   fixture.

## Automation Hints
- **Do not implement this case.** It is `blocked` pending #1695.
- If the human retargets it (option 1), the new analysis belongs in
  `test-specs/chat-interface/` or `test-specs/pipelines/`, not `test-specs/artifacts/`,
  and should first check ELITEA-2374's merged spec for behavioural overlap.
- Handles for the Artifacts preview surface itself are unchanged and already in
  `test-specs/artifacts/_surface.md` — nothing new was needed here.
