# Test Case: Default tier selection persists after page reload

## Metadata
- **TMS ID**: ELITEA-2414
- **Source case**: `../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/settings/ai-configuration/ELITEA-2414_default-tier-selection-persists-after-page-reload.md`
  (intake snapshot read directly; TMS module `settings-ai-configuration`)
- **Linked Story**: none (`requirements: []`)
- **Priority**: l3 (case frontmatter `priority: medium`). The covering spec
  (ELITEA-2397) is also `priority: medium`, module `pytestmark` already `p2` —
  no per-function marker override needed.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend), project **400 "UI Testing"**
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login)
- **Analyst**: qa-engineer (Sage), analyst slot — cluster session with
  ELITEA-2412 / ELITEA-2413, 2026-08-30
- **Status**: extend-existing
- **Surface**: `settings-ai-providers-llms`

## Case-identity notes (inherited, NOT re-filed)
1. "Settings → AI Configuration" is Settings → **AI Providers**
   (`/settings/ai-providers`) — EliteaAI/elitea-testing-public#1250.
2. The case's **title** says "Default **tier** selection" while its **step 2**
   says "Change the **Default LLM model selector** to a different model". Those
   are the same control: the LLMs section's `Default` selector (the section also
   has separate `High-tier` and `Low-tier` selectors). This AFS follows the
   STEP text — the Default selector — because that is the concrete instruction
   and it is also what the Expected Final State refers back to ("the model
   selected in step 2"). The High/Low tier selectors are out of scope here;
   their non-reload mechanics are already ELITEA-2397's subject. No new
   clarification filed — the step text is unambiguous and the title is merely
   loose.

## Extension target

**Covering spec**:
`automation/tests/ui/settings/test_set_llm_model_default_high_low_tier.py`
(class/method `test_set_llm_model_default_high_low_tier`) — ELITEA-2397,
**merged to `origin/automation/base`** (verified via `git cat-file -e
origin/automation/base:automation/tests/ui/settings/test_set_llm_model_default_high_low_tier.py`).

**Behavioural-overlap argument.** This case's steps 1-2 are the covering
spec's Steps 1-6 exactly: navigate to AI Providers, capture the current tier
state from the product's own `section=llm` response, pick a **different** model
via `pick_alternative_llm_model()`, select it in the Default combobox, assert
the `POST /configurations/models/{project_id}` returns `200 {"result":
"success"}`, assert the selector's text updates, assert the new model's card
gains the `Default` badge and the previous one loses it. It goes further still
(Steps 7-8 prove a brand-new `/chat` composer starts on the new Default).
Nothing about "change the Default selector to a different model" is unproven.

**Gap — nothing is re-read after a reload.** `grep -rn "reload"
automation/tests/ui/settings/test_set_llm_model_default_high_low_tier.py` →
**zero hits**. This matters more here than on the sibling cases: the tier
change has **no Save button** — selecting an option fires the POST immediately
— so the only in-session evidence is the client's optimistic render plus the
follow-on refetch inside the same document. This case's steps 3-4 add the one
observation nobody makes today: after a cold document load, the Default
selector still reads the model chosen in step 2. Delta is one reload plus two
assertions. See § Gap assertions.

**Why not `test_change_section_default_model.py`** (ELITEA-2403/2405, the other
default-selector spec): it drives the **Image Generation** and **ASR** sections,
not LLMs, and it is on the batch trunk but **not** merged to
`origin/automation/base`. ELITEA-2397 is both the right section and a merged
target.

## Preconditions
- Logged in on localhost; active project `400`.
- The LLMs section has **≥2 models** so "a different model" exists. Live: 12.
  The covering spec derives the alternative from the product's own `items[]`
  and never hardcodes a model name — the shared model set (project `1`) is
  mutable and must not be assumed.
- The project's Default LLM is **set**. Live: `GPT-5.6 Luna`
  (`gpt-5.6-luna<<>>1`). The covering spec asserts this before mutating, and
  must: **the dropdown offers no blank/"None" option** (confirmed live again
  this session — the listbox lists only selectable models), so a tier that
  starts UNSET cannot be restored via the UI. Refusing to mutate in that case is
  the correct behaviour, not a workaround.

## Test Data
| Field | Value used live | Note |
|---|---|---|
| Original Default | `GPT-5.6 Luna` → option value `gpt-5.6-luna<<>>1` | Read from the product's `section=llm` body, never hardcoded. |
| New Default | `GPT-5.4` → option value `gpt-5.4<<>>1` | Any model ≠ the current Default; the spec derives it with `pick_alternative_llm_model(items, original_default["value"])`. |
| Option-value grammar | `{name}<<>>{project_id}` | Shared models carry `project_id: 1`; project-local ones carry `400`. |

## Test Steps (as executed live, 2026-08-30)

1. **Navigate** to `${BASE_URL}/settings/ai-providers` — the case's step 1.
   *Observed*: LLMs accordion auto-expanded after a clean load; Default
   `GPT-5.6 Luna`, High-tier `Bedrock-GPT-5.6-Terra`, Low-tier `GPT-5.6 Luna`;
   12 LLM cards.
   ⚠️ The session's very FIRST load arrived with LLMs **collapsed** and TTS
   expanded (stale `expandSection` route state). Assert expansion; do not assume it.
2. **Open the Default selector and pick a different model** — the case's step 2.
   *Observed*: the listbox lists 13 options (12 models + the model this session
   had created), each `[data-testid="select-option-{name}<<>>{project_id}"]`,
   with `aria-selected="true"` on the current Default (`select-option-gpt-5.6-luna<<>>1`).
   Selecting `GPT-5.4` fired `POST /api/v2/configurations/models/400` → **200**.
   No Save button exists and none is needed.
   *Immediately after*: selector text `GPT-5.4`; the `GPT-5.4` card gained the
   `Default` badge; the previous Default `GPT-5.6 Luna` retained only its
   `Low-Tier` badge (it holds both tiers on this project).
3. **Reload the page** (`page.reload()`) — the case's step 3.
4. **Verify the Default selector still shows the model from step 2** — step 4.
   *Observed after reload*: Default **`GPT-5.4`**; High-tier
   `Bedrock-GPT-5.6-Terra` and Low-tier `GPT-5.6 Luna` **unchanged**;
   `GPT-5.4`'s card still carries the `Default` badge; `GPT-5.6 Luna`'s card
   still carries only `Low-Tier`; exactly one `Default` badge on the page.

**PASS** — the Default selection persisted across a full document reload, and
did not disturb the other two tiers.

**Restore (performed live):** Default re-selected back to `GPT-5.6 Luna`;
verified all three tiers returned to their captured values.

## Expected Results
- Selecting a different model in the Default selector persists immediately
  (POST 200, no Save action).
- After a full reload, the Default selector still shows the model chosen in
  step 2, its card still carries the `Default` badge, and the High-tier /
  Low-tier selectors are unchanged.

## Coverage Map

### Axis 1 — Case coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — navigate to the AI-configuration surface | page loads | covering spec Step 1 (title, accordion expanded, ≥1 card, `section=llm` 200) | `test_set_llm_model_default_high_low_tier.py` Step 1 | already covered |
| Step 2 — change the Default LLM selector to a different model | completes, expected UI state | covering spec Steps 2-6 (POST 200 `{"result":"success"}`, selector text, badge moves on AND off) | same file, Steps 2-6 | already covered |
| Step 3 — reload the page | completes without error | **NEW** | § Gap assertions A | gap |
| Step 4 — the Default selector still shows the step-2 model | condition holds | **NEW** | § Gap assertions B | gap |
| Expected Final State — selector still shows the step-2 model | — | **NEW** | § Gap assertions B | gap |
| Precondition — user logged in | — | `auth_state` | conftest | already covered |

### Axis 2 — Analyst additions (each grounded)
| Addition | Why |
|---|---|
| After reload, assert the new Default's **card badge** as well as the selector text | Selector and badge are rendered from the same response but by different components; a persisted value that fails to re-derive the badge is a real regression the selector alone would hide. Both were live-confirmed to survive. |
| After reload, assert **High-tier and Low-tier are unchanged** | The three tiers share one POST endpoint discriminated only by a `section` field (`llm` / `llm_high_tier` / `llm_low_tier`). A regression that wrote the wrong section would move a tier the case never touched, and a Default-only assertion would never see it. Live-confirmed unchanged. |
| After reload, assert there is exactly **one** `Default` badge in the LLMs section | Catches a persist-that-adds-rather-than-replaces. Live-confirmed: one `Default`, one `High-Tier`, one `Low-Tier`. |
| Assert `aria-expanded="true"` on the LLMs header before reading the selectors | Accordion content unmounts on collapse, so the selectors would simply be absent. |

## Gap assertions (implementer: append to the covering spec)

Insert after the covering spec's Step 6 (the "previous model loses the Default
badge" assertion) and **before** Step 7's chat navigation — the reload must
observe the Default change alone, before the High/Low tier work in Steps 9a/9b
touches anything else. Extend the docstring + `@allure.issue` set to name
ELITEA-2414 as a second covered case.

**As SHIPPED** (implementer, ELITEA-2414). Three deltas from the draft block,
each recorded below with its reason:

```python
with allure.step("Step 6b (ELITEA-2414) — The Default selection survives a full page reload"):
    reload_response = ai_providers_page.reload_and_capture_llm_response()
    assert reload_response.status == 200, (
        f"Expected the LLM-scoped models request after reload to return 200, "
        f"got {reload_response.status}"
    )
    reloaded = reload_response.json()
    assert reloaded.get("default_model_name") == new_default["name"], (
        f"After reload the persisted Default is {reloaded.get('default_model_name')!r}, "
        f"expected the model selected before the reload, {new_default['name']!r}"
    )
    expect(ai_providers_page.llms_section_header).to_have_attribute(
        "aria-expanded", "true", timeout=UI_ELEMENT_TIMEOUT
    )
    expect(ai_providers_page.llms_default_selector_combobox).to_have_text(
        new_default_label, timeout=UI_ELEMENT_TIMEOUT
    )
    expect(ai_providers_page.card_tier_badge(new_default_label, "Default")).to_be_visible(
        timeout=UI_ELEMENT_TIMEOUT
    )
    expect(ai_providers_page.card_tier_badge(original_default_label, "Default")).to_have_count(
        0, timeout=UI_ELEMENT_TIMEOUT
    )
    if original_high_label and captured_high_text:
        expect(ai_providers_page.llms_high_tier_selector_combobox).to_have_text(
            captured_high_text.strip(), timeout=UI_ELEMENT_TIMEOUT
        )
    if original_low_label and captured_low_text:
        expect(ai_providers_page.llms_low_tier_selector_combobox).to_have_text(
            captured_low_text.strip(), timeout=UI_ELEMENT_TIMEOUT
        )
```

1. **The reload response's status is asserted, and its body is used as the
   oracle** — `default_model_name` read from the product's own cold response.
   § Network Behavior already called this "the oracle for what actually
   persisted, independent of the DOM… asserting the API value **and** the
   selector text is the strongest form here"; the draft code block simply did
   not carry it. Same observable, stronger evidence — and it is the one
   assertion that survives any DOM-level regression.
2. **`all_default_badges` count(1) → per-card absence of the OLD Default's
   badge.** Two reasons, and the AFS's own § Gap assertions authorises the
   substitution ("confirm its scope is the LLMs section… or drop that one line
   to the per-card badge assertion, which is sufficient on its own"):
   `all_default_badges` is a **`@property`**, not a method — the draft's `()`
   call would have raised — and it is **page-wide**, counting the Image
   Generation / ASR / TTS sections' own `Default` badges too. On a clean reload
   only LLMs auto-expands so the count is 1, but the digest's own § Quirk
   records stale `expandSection` route state leaving *another* accordion open —
   which would make that line a false red. Asserting the previous Default's card
   no longer carries the `Default` badge catches the same failure mode
   ("persist adds rather than replaces"), is scoped by card identity rather than
   by accordion state, and honours § Automation Hints' warning that a model may
   hold two tiers at once (so it targets the `Default` badge specifically, never
   "no badges at all"). `isolate_section` was rejected as the alternative: it
   mutates accordion state the covering spec's later steps run against.
3. **The sibling-tier assertions are guarded** on both `original_*_label` (as
   the AFS instructs) **and** the captured selector text being non-`None` —
   `Locator.text_content()` is `str | None`, so `.strip()` on an unset tier
   would raise.

Original draft block, for reference:

```python
with allure.step("Step 6b (ELITEA-2414) — The Default selection survives a full page reload"):
    ai_providers_page.reload_and_capture_llm_response()
    expect(ai_providers_page.llms_section_header).to_have_attribute("aria-expanded", "true")
    expect(ai_providers_page.llms_default_selector_combobox).to_have_text(new_default_label)
    expect(ai_providers_page.card_tier_badge(new_default_label, "Default")).to_be_visible()
    expect(ai_providers_page.all_default_badges()).to_have_count(1)
    # Axis 2 — the sibling tiers were not disturbed by the Default write.
    expect(ai_providers_page.llms_high_tier_selector_combobox).to_have_text(captured_high_text.strip())
    expect(ai_providers_page.llms_low_tier_selector_combobox).to_have_text(captured_low_text.strip())
```

`captured_high_text` / `captured_low_text` are already captured by the covering
spec's Step 2. If either is empty (tier legitimately unset — the covering spec
tolerates that), guard the corresponding assertion the same way the spec's own
`if original_high_label:` guards do.

`reload_and_capture_llm_response()` is the **same new page-object method**
ELITEA-2412's AFS specifies (`automation/pages/ai_providers_page.py`); whichever
unit lands first adds it.

⚠️ **Do NOT use `BasePage.reload_and_wait()`** — two `networkidle` waits against
an app holding a persistent Socket.IO poll open is the #1847 race
(`.agents/testing.md`). Wait on the product's own `section=llm` response.

`all_default_badges()` already exists on `AIProvidersPage`; confirm its scope is
the LLMs section before relying on the `count(1)` assertion — if it is
page-wide, isolate the section first (`isolate_section`) or drop that one line
to the per-card badge assertion, which is sufficient on its own.

## Cleanup
Unchanged from the covering spec and already correct: its `finally` restores
Default, High-tier and Low-tier to the values captured in Step 2 (each read
from the product's own response, not assumed), and it navigates back to the
page first. **This is org/project-level shared state** — the LLM Default feeds
every new `/chat` conversation's model — so a skipped restore is exactly the
green-but-damaging shape `.agents/testing.md` § Teardown-guard ordering warns
about. The extension adds **no new mutation**, so no new teardown obligation.
Verified live: after restoring, the three tiers read `GPT-5.6 Luna` /
`Bedrock-GPT-5.6-Terra` / `GPT-5.6 Luna`, matching the captured baseline.

## Concrete Handles (confirmed live this session)
| Element | Handle | Provenance |
|---|---|---|
| LLMs accordion header | `[data-testid="ai-providers-section-llms"]` (+ `aria-expanded`) | existing `llms_section_header` |
| Default selector (combobox) | `[data-testid="ai-providers-section-llms-default-selector-combobox"]` | existing `llms_default_selector_combobox`; its `text_content()` is the selected model's display name |
| High-tier / Low-tier selectors | `…-llms-high-tier-model-selector-combobox` / `…-low-tier-model-selector-combobox` | existing |
| Dropdown option (dynamic) | `[data-testid="select-option-{name}<<>>{project_id}"]` — e.g. `select-option-gpt-5.4<<>>1` | existing `SELECT_OPTION` class-constant template; `aria-selected="true"` marks the current value |
| Card tier badge | `[data-testid="ai-provider-configuration-badge"]` (`Default` / `High-Tier` / `Low-Tier`) | existing `TIER_BADGE_SELECTOR`, via `card_tier_badge()` |
| Card name | `[data-testid="ai-provider-configuration-card-name"]` | existing |

**No new testid needed.**

## Network Behavior
- Selecting an option → `POST /api/v2/configurations/models/400` → **200**,
  body `{"result": "success"}`; request body `{name, target_project_id,
  section}` where `section` ∈ `llm` / `llm_high_tier` / `llm_low_tier`. No Save
  action exists.
- Immediately after the POST the app re-fetches the whole section fan-out
  (`configurations/models/400?include_shared=true` + one per `section=`).
- Reload → the same fan-out from a cold document. `section=llm`'s body carries
  `default_model_name` / `default_model_project_id` (+ `high_tier_…` /
  `low_tier_…`) — the oracle for what actually persisted, independent of the DOM.
  Asserting the API value **and** the selector text is the strongest form here.

## Known Defects Found During Exploration
**None new.** The tier change + reload produced **zero** console errors (the
session's only two were the pre-existing type-picker React `unique key` warning,
**#656**, and the expected post-delete 404 from the sibling cases' teardown).

## Blocked Steps
None.

## Automation Hints
- **This case's value is entirely in the cold re-read** — there is no Save
  button, so an in-session assertion cannot distinguish "persisted" from
  "optimistically rendered". Use `page.reload()`, not a `goto`.
- Never `networkidle` (#1847).
- Never hardcode a model name — derive the alternative from the response
  `items[]` via `pick_alternative_llm_model()`. The shared model set (project
  `1`) changes; this session alone saw `GPT-5.6 Luna`, `GPT-5.4`,
  `Bedrock-GPT-5.6-*` and four Anthropic models.
- A model can hold **two tiers at once** (live: `GPT-5.6 Luna` was both Default
  and Low-tier). So "the previous Default's card has no badges" is WRONG as an
  assertion — assert the absence of the **`Default`** badge specifically, as the
  covering spec already does via `card_tier_badge(label, "Default")`.
- Serial only — the Default LLM is project-level state read by chat specs.
