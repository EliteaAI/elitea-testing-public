# Test Case (FAMILY): Image Generation / ASR / TTS section displays model cards and default selector

## Metadata
- **TMS IDs (family, 3 members)**: **ELITEA-2402** (Image Generation), **ELITEA-2404**
  (Speech Recognition / ASR), **ELITEA-2406** (Text to Speech / TTS)
- **Linked Story**: none
- **Priority**: l3 (frontmatter `priority: medium`; folder mapping — matches every
  sibling in this feature dir)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids`, DEV backend), project `UI Testing` (id 400)
- **User set**: `${TEST_USER}` (`auth_state` fixture)
- **Analyst**: qa-engineer (analyst slot), 2026-08-30, batch `settings-w11`
- **Status**: **ready-for-automation**
- **Family AFS**: yes — the three cases differ **only in data** (which section, which
  label, which model set). Identical actions, identical order, identical assertions.
  One parameterized spec, one row per case in § Test Data.
- **Defects filed this session**: none for these three (see § Known Defects for the one
  observation, which belongs to ELITEA-2407's teardown path, not here)
- **Surface digest**: `test-specs/settings-ai-providers/_surface.md`

## Case-identity note (pre-existing, NOT re-filed)

All three cases say **"Settings → AI Configuration"**. There is no such page. The
sections they describe (Image Generation, Speech Recognition (ASR), Text to Speech
(TTS)) live on **Settings → AI Providers** (`/settings/ai-providers`). This is already
filed as a clarification — EliteaAI/elitea-testing-public#1250, raised during
ELITEA-2392 — and re-confirmed live this session. Asserting the live contract per the
reverse-masking guard; **not re-filed**.

## Case-text drift found this session — the section is COLLAPSED, and that changes step 2

Each case's step 2 is *"Locate the &lt;X&gt; section"*, and step 4 then asserts *"the
Default … selector shows a non-empty value"*. Live, those two are not reachable from the
same state:

- **Only the LLMs accordion auto-expands** on page load
  (`defaultExpanded={!expandSection || expandSection === 'llm'}`). Image Generation, ASR
  and TTS all start **collapsed** — confirmed live, `aria-expanded="false"` on all three.
- While collapsed, the accordion **summary** renders the default as **plain text**
  (`"Image Generation | Default | GPT Image 2 | 3"`) with **no testid and no combobox**
  — `querySelectorAll('[data-testid]')` inside the summary returned **zero** elements.
- On expand, that plain text **disappears from the summary** (which becomes just
  `"Image Generation | 3"`) and the real `role="combobox"` selector mounts inside the
  accordion **details**, carrying
  `ai-providers-section-{slug}-default-selector-combobox`.

So step 2 is under-specified, not wrong: "locate the section" must mean **expand it**,
or steps 3–5 have nothing to act on (accordion content unmounts on collapse). The spec
below makes the expand explicit as step 2. **Not filed as a defect** — the product is
correct and the omission is one word of case text; folded into the existing #1250
clarification rather than opening a fourth ticket for the same case family.

## Preconditions

- Logged in as `${TEST_USER}` (`auth_state`; on localhost login is skipped entirely).
- The section under test holds **≥ 1 configuration** for the active project and **has a
  default assigned**. Live this is satisfied on every project tried, because every model
  in all three sections is **shared from project 1** (`include_shared=true`) — see
  § Test Data. The spec should still assert the precondition from the product's own
  `GET …&section={param}` response (`total >= 1`, `default_model_name` non-empty) and
  fail loudly rather than silently pass on an empty section: a section with zero
  configurations renders **nothing at all** (`ConfigurationSection.jsx`:
  `if (!configurations || configurations.length === 0) return null;`), so a
  "section not visible" failure would otherwise be indistinguishable from a load failure.
- **No mutation.** None of these three cases writes anything — step 5 opens the dropdown
  and the spec closes it again without selecting. No teardown beyond closing the
  dropdown is owed.

## Test Data — the parameter table (one row per TMS case)

| TMS ID | Section title (live label) | Section slug (testid) | Cards observed (project 400, 2026-08-30) | Default observed | Option testids observed |
|---|---|---|---|---|---|
| **ELITEA-2402** | `Image Generation` | `image-generation` | 3 — `GPT Image 2`, `gpt-image-1`, `gpt-image-1.5` | `GPT Image 2` | `select-option-gpt-image-2<<>>1`, `select-option-gpt-image-1<<>>1`, `select-option-gpt-image-1.5<<>>1` |
| **ELITEA-2404** | `Speech Recognition (ASR)` | `asr` | 2 — `gpt-4o-mini-transcribe`, `whisper` | `gpt-4o-mini-transcribe` | `select-option-gpt-4o-mini-transcribe<<>>1`, `select-option-whisper<<>>1` |
| **ELITEA-2406** | `Text to Speech (TTS)` | `tts` | 1 — `gpt-4o-mini-tts` | `gpt-4o-mini-tts` | `select-option-gpt-4o-mini-tts<<>>1` |

**Every value in the last three columns is live-observed data, not an expectation.**
The model set is project-shared and can change without notice, so the spec must
**derive** the expected values from the product's own `…&section={param}` response and
assert *relationships* (count parity, non-empty default, the default appearing in the
option set), never these literal strings. The literals are here so the implementer
recognises a sane run — they are not assertions.

**TTS legitimately has ONE model.** ELITEA-2406's step 5 says only *"a dropdown of
available TTS models appears"* — one option satisfies it, and the live listbox rendered
exactly one. Do **not** write `count >= 2` into the shared assertion; that would make
the TTS row red for a product state the case never asked about. (ELITEA-2407 is where
"only one TTS model" actually bites — see that AFS.)

## Test Steps (parameterized; `{section}` / `{slug}` from § Test Data)

| # | Action | Expected result (observed live for all 3 rows) |
|---|---|---|
| 1 | Navigate to `/settings/ai-providers` | Page loads; `ai-providers-page-title` visible; the per-section `GET /api/v2/configurations/models/{project_id}?include_shared=true&section={param}` returns **200** |
| 2 | Locate and **expand** the `{section}` accordion (`ai-providers-section-{slug}`) | Header visible; `aria-expanded` flips `false` → `true`; the accordion details mount |
| 3 | Verify ≥ 1 configuration card is shown, each carrying a model name and a status badge | ≥ 1 `ai-provider-configuration-card`; each has an `ai-provider-configuration-card-name` with non-empty text and a status element reading `OK • Shared` (or `OK • Local`) |
| 4 | Verify the `Default {section} model` selector shows a non-empty value | `ai-providers-section-{slug}-default-selector-combobox` is visible, `role="combobox"`, text non-empty and equal to the default reported by the section's own API response |
| 5 | Click the selector | A `role="listbox"` opens containing one `select-option-{name}<<>>{project_id}` per configuration; the current default's option carries `aria-selected="true"` |

## Expected Results

- All three sections render, expand, list their cards, and expose a populated Default
  selector whose dropdown enumerates exactly the section's configurations.
- **0 console errors** across the whole flow — verified live on page load and after each
  expand and each dropdown open.

## Coverage Map

### Axis 1 — every case element

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — navigate to Settings → AI Configuration | page/section loads | Step 1 (route corrected to `/settings/ai-providers` per #1250) | page title visible + section GET 200 | covered |
| Step 2 — locate the `{section}` section | completes without error | Step 2 (**decomposed**: locate **and expand** — see § Case-text drift) | header visible + `aria-expanded` true | covered (clarified) |
| Step 3 — ≥1 model card with model name and status badge | condition holds | Step 3 | card count ≥ 1; name non-empty; status element visible | covered — **needs 1 new testid**, see § Concrete Handles |
| Step 4 — Default selector shows a non-empty value | condition holds | Step 4 | combobox text non-empty **and** equals the API's `default_model_name`/display name | covered |
| Step 5 — click selector, dropdown of available models appears | control responds | Step 5 | listbox present; one option per configuration; default option `aria-selected="true"` | covered |
| Expected Final State | dropdown appears | Step 5 | same | covered |
| Precondition — user logged in | — | `auth_state` fixture | — | covered (setup) |

### Axis 2 — asserted beyond the case

| Extra assertion | Why it is grounded |
|---|---|
| The section's `…&section={param}` GET returns **200** with `total >= 1` | The product hides an empty section entirely (`return null`), so "the section is missing" and "the section is correctly empty" are the same DOM. Without the API check, step 2's failure mode is ambiguous — this is the same distinction `navigate_and_capture_vectorstorage_response()` was built for. |
| The combobox text **equals the default the API reports**, not merely "non-empty" | Step 4 says "non-empty", which a stale or wrong label also satisfies. The product's own response is the honest oracle (`.agents/testing.md` § Fidelity policy — capture the real response and assert the UI against it). |
| The option **count equals** the card count / the API `total` | Step 5 says "a dropdown appears". A dropdown that silently drops a model still "appears". Parity between the cards, the options and the API total is the invariant that actually catches a regression, and it is satisfiable on every row including TTS's single model. |
| `aria-selected="true"` on the current default's option | Confirms the dropdown reflects state rather than merely listing; observed live on all three rows. |
| **0 console errors** over the flow | Standing project convention; verified live, so it is an assertion about a known-clean flow, not a hope. Use `utils/console_errors.collect_console_errors()` (URL-bearing form). |

## Concrete Handles (discovered live; **testid-only**)

| Handle | Testid | Provenance (verified `git fetch origin`, 2026-08-30) | Notes |
|---|---|---|---|
| Page title | `ai-providers-page-title` | on-main ✓ | already a `LocatorDescriptor` field |
| Section header (Image Gen) | `ai-providers-section-image-generation` | on-main ✓ | `AIProvidersPage.image_generation_section_header` — exists |
| Section header (ASR) | `ai-providers-section-asr` | on-main ✓ | `AIProvidersPage.asr_section_header` — exists |
| Section header (TTS) | `ai-providers-section-tts` | on-main ✓ | `AIProvidersPage.tts_section_header` — exists |
| Default selector combobox | `ai-providers-section-{slug}-default-selector-combobox` | on-main ✓ | **page-object gap, not a testid gap** — the testid exists in JSX (derived from the threaded `sectionTestId`) and resolved live for all three sections, but `AIProvidersPage` has `*_default_selector` (FormControl wrapper) only for these three. Add the three `*_default_selector_combobox` `LocatorDescriptor` fields, exactly like the existing `embedding_models_default_selector_combobox`. |
| Configuration card | `ai-provider-configuration-card` | on-main ✓ | `CONFIGURATION_CARD_SELECTOR` — generic, repeated per card |
| Card display name | `ai-provider-configuration-card-name` | on-main ✓ | `CARD_NAME_SELECTOR` |
| **Card status text** | **`ai-provider-configuration-card-status`** | **needs-adding** | see below |
| Tier/Default badge | `ai-provider-configuration-badge` | on-main ✓ | `TIER_BADGE_SELECTOR` — not asserted by these three cases (it is 2403/2405/2407's subject), listed because it shares the card |
| Dropdown option | `select-option-{name}<<>>{project_id}` | pre-existing shared `SingleSelect` convention | `SELECT_OPTION` template constant; use `SELECT_OPTION_PREFIX_SELECTOR` for the option SET — the bare prefix also matches `select-option-selected-icon` |

### The one testid to add — `ai-provider-configuration-card-status`

Step 3 asserts *"model name **and status badge**"*. The name has a testid; the **status
text does not**. Live DOM of a card, SVG stripped:

```html
<div data-testid="ai-provider-configuration-card">
  …<span data-testid="ai-provider-configuration-card-name">gpt-image-1.5</span>…
  <div>OK • Shared</div>          <!-- ← no testid -->
</div>
```

**Where:** `EliteaUI/src/[fsd]/features/settings/ui/ai-providers/ConfigurationCard.jsx`,
the `<Typography component={Box} … sx={styles.statusText}>` opening at **line 82**
(its `{statusText}` child is line 88). Add
`data-testid="ai-provider-configuration-card-status"` to that **existing** element.

**Zero plumbing, zero new nodes** — this is an attribute on a node that already exists,
so it clears the zero-functional-impact check (`.agents/role-overrides.md` § Reviewer
slot). Do **not** wrap `{statusText}` in a new `<span>` to get a cleaner string: that
adds a DOM node and is `CHANGES_REQUESTED`.

⚠️ **That Typography also CONTAINS the badges.** Its children are
`{statusText}{isHighTier && …}{isLowTier && …}{isDefault && …}`, so on the default card
its `innerText` reads `"OK • Shared\nDefault"` while a non-default card reads exactly
`"OK • Shared"`. Assert with `to_contain_text("OK")` / a regex — **never**
`to_have_text("OK • Shared")`, which passes on every card except the one that matters.
(Same trap the `CARD_NAME_SELECTOR` docstring records for the outer card testid.)

## Network Behavior

Per page load, all 200 (observed live):

- `GET /api/v2/configurations/models/{project_id}?include_shared=true` (summary)
- `GET /api/v2/configurations/models/{project_id}?include_shared=true&section={llm|embedding|vectorstorage|image_generation|asr|tts}` — **one per section**; the one matching the row under test is the oracle for `total` and `default_model_name`
- `GET /api/v2/configurations/configurations/{project_id}?…&section=…` (combined card listing)

**Expanding an accordion fires NO request** — the panels are fed from the already-cached
RTK-Query results. Do not wait on network after the expand; wait on the combobox testid.
**Opening the dropdown fires no request either.**

`AIProvidersPage.navigate_and_capture_section_models_response(section)` already exists
and takes the section param — use it; do not add a per-section matcher.

## Known Defects Found During Exploration

**None for these three cases.** The flow is clean: 0 console errors on load, after each
expand, and after each dropdown open.

(One pre-existing defect was re-observed this session on ELITEA-2407's *teardown* path —
a stale 404 after deleting a configuration — and was **not filed**: it is a real
duplicate of the open EliteaAI/elitea-testing-public#1666 and was recorded as a new
occurrence there instead. It cannot touch these three cases, which mutate nothing.)

## Blocked Steps

None. All 5 steps of all 3 cases executed end-to-end against the live system.

## Automation Hints

- **Parameterize over the three rows** (`pytest.mark.parametrize` with the TMS id in the
  param id, the sibling convention). One spec,
  `automation/tests/ui/settings/test_ai_provider_section_cards_and_default_selector.py`.
- **`ai-providers-section-{slug}` is on the accordion SUMMARY BUTTON, not the accordion
  root.** Cards are therefore **not** DOM descendants of it — a whole-page card query
  returns every expanded section's cards (live: the Vector Storage seed card kept
  appearing in Image Generation queries because Vector Storage was also open). Use
  `AIProvidersPage.isolate_section(header)` (collapse all, expand one) before **any**
  card count. This is the single most likely way to get a green-but-meaningless run here.
- Use the existing `expand_section` / `isolate_section` / `configuration_cards` /
  `card_for_model` / `open_select_options` / `close_open_dropdown` helpers — all fit
  unchanged.
- Close the dropdown at the end of step 5 (`close_open_dropdown()`, or `Escape`) so the
  next parameterized row starts from a clean portal. MUI renders the listbox in a portal
  and only one can be open at a time.
- **No mutation, no teardown.** Nothing in these three cases writes. If a future edit
  makes one of them select an option, it inherits ELITEA-2403's teardown obligations —
  do not let that happen silently.
- Markers: `ui, settings, p2, regression, new` (matching the merged siblings' l3 → p2).
- Wrap each step in `with allure.step("Step N — …"):`.
