# Test Case (FAMILY): Change the default Image Generation / ASR model

## Metadata
- **TMS IDs (family, 2 members)**: **ELITEA-2403** (Image Generation), **ELITEA-2405**
  (Speech Recognition / ASR)
- **Linked Story**: none
- **Priority**: l3 (frontmatter `priority: medium`; folder mapping)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids`, DEV backend), project `UI Testing` (id 400)
- **User set**: `${TEST_USER}` (`auth_state` fixture)
- **Analyst**: qa-engineer (analyst slot), 2026-08-30, batch `settings-w11`
- **Status**: **ready-for-automation**
- **Family AFS**: yes — identical actions, identical order, identical assertions;
  the two cases differ **only in which section and which two models**.
- **Sibling that is NOT in this family**: **ELITEA-2407** (TTS) — same case text, but the
  TTS section holds **one** model live, so it needs a transit create + delete that these
  two do not. Different **steps** ⇒ its own AFS
  (`l3_change-the-default-tts-model_ELITEA-2407.md`).
- **Surface digest**: `test-specs/settings-ai-providers/_surface.md`

## ⚠️ WRITE-HEAVY — this test mutates a shared project default

Selecting an option **immediately** persists (`POST /api/v2/configurations/models/{project_id}`
→ 200) — there is no Save button and no confirmation. The Default image-generation / ASR
model is **project-level shared state** every other user and every later spec reads.
`.agents/testing.md` § Teardown-guard ordering is binding here; see § Cleanup.

## Case-identity note (pre-existing, NOT re-filed)

Both cases say **"Settings → AI Configuration → &lt;X&gt; section"**. There is no such
page; the sections live on **Settings → AI Providers** (`/settings/ai-providers`).
Already filed as EliteaAI/elitea-testing-public#1250 (ELITEA-2392); re-confirmed live.
Asserting the live contract per the reverse-masking guard; **not re-filed**.

## Case-text drift — step 1 lands on a COLLAPSED section

Step 1 says *"Navigate to … → &lt;X&gt; section"*. Only the **LLMs** accordion
auto-expands; Image Generation and ASR both start collapsed (`aria-expanded="false"`,
confirmed live), and the accordion's content — including the real Default combobox —
**unmounts while collapsed**. While collapsed the summary shows the default as untestable
plain text with no testid. So step 1 must include the expand, or step 2 has nothing to
read. Same one-word omission as the ELITEA-2402/2404/2406 family; folded into #1250,
**not** filed separately.

## Preconditions

- Logged in as `${TEST_USER}` (`auth_state`).
- **The section holds ≥ 2 configurations and has a default assigned.** This is the
  case's real precondition, and step 3 ("select a **different** model") is unsatisfiable
  without it. Live, both sections satisfy it on every project tried because their models
  are **shared from project 1** (`include_shared=true`): Image Generation 3, ASR 2.
  **Assert it from the product's own `…&section={param}` response** (`total >= 2`,
  `default_model_name` non-empty) and fail loudly — a silent pass on a one-model section
  would make step 3 a no-op and the whole case vacuous.
- **No blank/"None" option exists** in these dropdowns (live-confirmed, and already
  documented for LLM tiers in `_surface.md`). A section that starts with **no** default
  could not be restored, so the spec must refuse to run in that state rather than create
  an unrestorable mutation.

## Test Data — the parameter table (one row per TMS case)

| TMS ID | Section title | Section slug | Default observed (project 400, 2026-08-30) | Alternative selected during analysis | Option testids |
|---|---|---|---|---|---|
| **ELITEA-2403** | `Image Generation` | `image-generation` | `GPT Image 2` (`gpt-image-2<<>>1`) | `gpt-image-1` (`gpt-image-1<<>>1`) | 3 options, all `<<>>1` (shared) |
| **ELITEA-2405** | `Speech Recognition (ASR)` | `asr` | `gpt-4o-mini-transcribe` (`gpt-4o-mini-transcribe<<>>1`) | `whisper` (`whisper<<>>1`) | 2 options, all `<<>>1` (shared) |

**Do not hardcode any of these values.** They are live observations of shared,
mutable project state. The spec must **read the current default from the section's own
API response**, then **pick any other option from the same response** — the
`pick_alternative_llm_model(items, current_value)` helper already implements exactly this
shape and is section-agnostic apart from its name.

**All options are `<<>>1`** (project 1 = shared) for both rows — unlike Vector Storage,
whose local configurations key on `<<>>400`. Never assume the active project's id is the
option suffix; take the whole `"{name}<<>>{project_id}"` value from the response body.

## Test Steps (parameterized; `{section}` / `{slug}` from § Test Data)

| # | Action | Expected result (observed live on BOTH rows) |
|---|---|---|
| 1 | Navigate to `/settings/ai-providers` and **expand** the `{section}` accordion | Page loads; section GET **200**; `aria-expanded` `false` → `true`; combobox mounts |
| 2 | Note the currently selected default model | `ai-providers-section-{slug}-default-selector-combobox` text == the API's default; the card with that name carries a `Default` badge, and **no other card does** |
| 3 | Open the Default dropdown and select a **different** model | `POST /api/v2/configurations/models/{project_id}` → **200**; every section's models GET refetches |
| 4 | Verify the selector updates to reflect the new selection | combobox text == the newly selected model's display name (live: `gpt-image-1` / `whisper`) |
| 5 | Verify the selected model's card gains a `Default` badge | that card's `ai-provider-configuration-badge` reads `Default` |
| 6 | Verify the previously default card no longer shows the `Default` badge | the old card has **0** badges |

**No reload is needed between 3 and 4–6** — all three observations landed in the same
render pass, driven by the app's own post-POST refetch. Confirmed live on both rows.

## Expected Results

- The default moves, persists, and both badges move with it — atomically, in one render.
- **0 console errors** across the flow (verified live on both rows).
- After teardown the project reads back **exactly as found**.

## Coverage Map

### Axis 1 — every case element

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — navigate to Settings → AI Configuration → `{section}` | page/section loads | Step 1 (**decomposed**: route corrected per #1250 **+** expand) | GET 200 + `aria-expanded` true | covered (clarified) |
| Step 2 — note the current default | completes without error | Step 2 | combobox text == API default; exactly one `Default` badge, on that card | covered |
| Step 3 — open dropdown, select a different model | control responds | Step 3 | listbox opens; option clicked; POST 200 | covered |
| Step 4 — selector updates | condition holds | Step 4 | combobox text == new model | covered |
| Step 5 — selected card gains `Default` badge | condition holds | Step 5 | badge text `Default` on the new card | covered |
| Step 6 — previous card loses the badge | condition holds | Step 6 | old card badge count 0 | covered |
| Expected Final State | previous card no longer `Default` | Step 6 | same | covered |
| Precondition — user logged in | — | `auth_state` | — | covered (setup) |

### Axis 2 — asserted beyond the case

| Extra assertion | Why it is grounded |
|---|---|
| The mutation **persisted server-side**: `POST …/configurations/models/{project_id}` returns **200** | Steps 4–6 are all DOM reads. A purely optimistic UI update would satisfy every one of them while the server rejected the change. The POST is the only evidence the default actually moved — and it is the product's own response, not a fabricated one. |
| Exactly **one** card carries a `Default` badge, before and after | The case checks the new card gained one (5) and the old one lost it (6) but never that no *third* card has one. "Exactly one" is the real invariant and is what catches a badge-keying regression — the class of defect that produced #1987 in the Vector Storage section. |
| The precondition read (`total >= 2`, default non-empty) | Without it, a one-model section turns step 3 into a no-op and the case passes vacuously. Read from the product's own response. |
| **0 console errors** over the flow | Verified live on both rows; use `utils/console_errors.collect_console_errors()`. |
| Teardown read-back: the default is the original value again | A green-but-damaging spec is exactly what the N×-green gate cannot catch (`.agents/testing.md` § Teardown-guard ordering). Prove the restore, do not assume it. |

## Cleanup (MANDATORY — this test mutates shared project state)

**Teardown-guard ordering (`.agents/testing.md`, AUTHORITATIVE):** set the
`default_changed` flag **immediately BEFORE** the selection that changes the default,
never after. The window between "the POST fired" and "the flag says it did" is a window
in which any failure skips the restore while the damage is already done.

```python
# RIGHT — the flag can only be wrong in the safe direction
self.default_changed = True
providers_page.select_default_configuration(combobox, new_option_value)
```

In `finally`:

1. Re-select the **original** option value (captured in step 2 **from the API response**,
   as `f"{default_model_name}<<>>{default_model_project_id}"`).
2. **Read the default back** and assert it equals the original — the restore is an
   assertion, not a hope.

`utils/ai_provider_teardown.restore_section_default()` already implements exactly this
(navigate → isolate section → select) and is section-agnostic. Reuse it; do not
re-derive.

⚠️ **Re-selecting an already-selected option fires NO request** (live-confirmed,
`_surface.md`). A restore helper that waits for the POST will hang its full timeout when
the test failed *before* it changed anything. Read the persisted default first and only
re-select when it actually moved — which is exactly what the guard flag is for.

**Nothing is created or deleted by these two cases** — the only mutation is the default
pointer, and it is restored. (ELITEA-2407 is the one that also creates.)

## Concrete Handles (discovered live; **testid-only**)

| Handle | Testid | Provenance (verified `git fetch origin`, 2026-08-30) | Notes |
|---|---|---|---|
| Section header (Image Gen) | `ai-providers-section-image-generation` | on-main ✓ | `AIProvidersPage.image_generation_section_header` |
| Section header (ASR) | `ai-providers-section-asr` | on-main ✓ | `AIProvidersPage.asr_section_header` |
| Default selector combobox | `ai-providers-section-{slug}-default-selector-combobox` | on-main ✓ | **page-object gap only** — testid exists in JSX and resolved live for both sections; add the two `LocatorDescriptor` fields mirroring `embedding_models_default_selector_combobox` |
| Dropdown option | `select-option-{name}<<>>{project_id}` | pre-existing shared `SingleSelect` convention | `SELECT_OPTION` class template. For the option SET use `SELECT_OPTION_PREFIX_SELECTOR` — the bare prefix also matches `select-option-selected-icon` |
| Configuration card | `ai-provider-configuration-card` | on-main ✓ | `CONFIGURATION_CARD_SELECTOR` |
| Card display name | `ai-provider-configuration-card-name` | on-main ✓ | `CARD_NAME_SELECTOR` — required for exact identification; the outer card's text concatenates name + status + badge with no separator |
| **`Default` badge** | `ai-provider-configuration-badge` | on-main ✓ | `TIER_BADGE_SELECTOR` — generic, repeated per badge; distinguish by its own text (`Default`), scoped inside `card_for_model(name)`. `AIProvidersPage.card_tier_badge(name, "Default")` already does exactly this |

**No new testid is needed for these two cases.** (The `ai-provider-configuration-card-status`
gap named in the ELITEA-2402 family AFS belongs to that family's step 3, not here.)

## Network Behavior

- Per page load: the summary GET, one `…&section={param}` GET per section, and the
  combined `configurations/…` listing — all 200.
- **Selecting an option**: `POST /api/v2/configurations/models/{project_id}` → 200,
  immediately followed by a refetch of the summary and of **every** section's models GET
  (observed live: 6 follow-on GETs). The card re-render rides that refetch.
- **Expanding an accordion and opening a dropdown fire NO request.** Wait on the target
  testid, never on network, after those two actions.

## Known Defects Found During Exploration

**None for these two cases.** Both executed clean end-to-end, badges moved correctly,
0 console errors, and the project restored exactly.

Worth knowing (not a defect here): the sibling Vector Storage section is sanctioned-RED
on EliteaAI/elitea-testing-public#1987 because its cards never render a `Default` badge —
a `data.name`-vs-`elitea_title` key mismatch. **Image Generation and ASR both supply
`data.name`, so both badge correctly** — verified live this session. Do not copy
ELITEA-2401's soft-assert treatment into this spec; there is nothing red here.

## Blocked Steps

None. All 6 steps of both cases executed end-to-end against the live system, including
the restore.

## Automation Hints

- **Parameterize over the two rows**; put the TMS id in the param id. One spec,
  `automation/tests/ui/settings/test_change_section_default_model.py`.
- **`isolate_section()` before every card assertion.** `ai-providers-section-{slug}` sits
  on the accordion **summary button**, so cards are not its DOM descendants and a
  whole-page card query mixes in every other expanded section's cards (live: the Vector
  Storage seed card kept surfacing in Image Generation queries).
- Derive the original and the alternative from **one** section GET response body — that
  single response carries `default_model_name`, `default_model_project_id` and `items`.
  `navigate_and_capture_section_models_response(section)` + `pick_alternative_llm_model`
  cover it; neither needs a new matcher.
- **Do not run these two in parallel with each other or with any other AI-Providers
  spec** — they mutate project-level state. Serial (pytest-xdist is installed; shared
  state must not run parallel, `.agents/testing.md` § Test data strategy).
- Markers: `ui, settings, p2, regression, new`.
- Wrap each step in `with allure.step("Step N — …"):`.
- Docstring must state, in one line, that the spec mutates and restores the project's
  default model for the section under test.
