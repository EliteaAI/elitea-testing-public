# Test-repair brief — `test_create_image` blocked by a dead model literal

| field | value |
|---|---|
| **Card** | [#2112](https://github.com/EliteaAI/elitea-testing-public/issues/2112) — `[FIX][2 cases] timeout: Timeout waiting for model selector during image creation` |
| **TMS case** | ELITEA-0679 (`onetest-ai-tm-Elitea/tests/automated-full-regression-ui/chat/ELITEA-0679_image-creation-internal-tool-happy-path.md`) |
| **Kind** | test-repair brief (`lfix_`, per open canon card [#1938](https://github.com/EliteaAI/elitea-testing-public/issues/1938)) — not a fresh TMS-case AFS |
| **Subject** | `automation/tests/ui/chat/test_image_creation.py::TestImageCreation::test_create_image[detailed_description]` and `[minimal_prompt]` — Step 2 (line 60-61) |
| **Triage class** | **A — UI/data drift** (model catalog changed; the test names a model the case never asked for) |
| **Status** | `ready-for-implementation` |
| **Analyst** | qa-engineer, 2026-09-09, live against `http://localhost:5173` (EliteaUI `automation/testids` @ `ebb70618`), backend `dev.elitea.ai`, project **399** |
| **New testids needed** | **none** — the repair only *removes* a step; every surviving handle is unchanged |
| **Branch** | `fix/2112-image-creation-default-model` (cut from `origin/main`) |

---

## TL;DR

`test_create_image` fails at **Step 2**, not at the image-generation step. It calls
`chat.select_model("GPT-5.2")`; **`GPT-5.2` no longer exists in the model catalog of any
working project**, so `[role="menuitem"]:has-text("GPT-5.2")` matches nothing and its
10 000 ms `wait_for` times out.

**That step should never have been there.** ELITEA-0679 names no model. Its precondition
is *"At least one shared image model is available as the default"* and its Step 3 says
*"Send a simple image prompt … **using the default image model**"*. There is no
model-selection step in the case at all — Step 2 of the case is *enable the Image
Creation tool*. `select_model("GPT-5.2")` is a **test-implementation artifact**.

**Live-verified today:** with the current default (`Anthropic Claude 4.5 Sonnet`) and
**no model switch whatsoever**, enabling Image Creation and sending the prompt produces a
real rendered image. The case's literal flow works. **The repair is to delete the model
selection, not to substitute a different literal.**

---

## What was executed, and how

Live walk of ELITEA-0679's own steps via Playwright MCP against `http://localhost:5173`
(project 399, user `Test Bot`), plus one clean-process pytest reproduction. Nothing was
substituted: no `page.route`, no `route.fulfill`, no injected state, no replaced client.
The image asserted below was produced by the real Image Creation internal tool.

### Finding 1 — the catalog no longer contains `GPT-5.2` (root cause)

`GET {ELITEA_API_BASE}/configurations/models/399?include_shared=true` → **200**, 8 items:

| display_name | name | default |
|---|---|---|
| **Anthropic Claude 4.5 Sonnet** | `eu.anthropic.claude-sonnet-4-5-20250929-v1:0` | **true** |
| Anthropic Claude 4.6 Sonnet | `eu.anthropic.claude-sonnet-4-6` | false |
| Anthropic Claude Haiku 4.5 | `eu.anthropic.claude-haiku-4-5-20251001-v1:0` | false |
| Anthropic Sonnet 5 | `global.anthropic.claude-sonnet-5` | false |
| Bedrock-GPT-5.6-Luna | `global.openai.gpt-5.6-luna` | false |
| Bedrock-GPT-5.6-Sol | `global.openai.gpt-5.6-sol` | false |
| Bedrock-GPT-5.6-Terra | `global.openai.gpt-5.6-terra` | false |
| GPT-5 mini | `gpt-5-mini` | false |

The chat composer's model menu renders **exactly these 8 `[role="menuitem"]` entries** and
no others (live snapshot, evidence 2). No entry's text contains `GPT-5.2` — note
`Bedrock-GPT-5.6-*` does **not** substring-match `GPT-5.2`, so `:has-text("GPT-5.2")`
resolves to zero elements.

This independently re-confirms, from the UI side, what issue
[#2117](https://github.com/EliteaAI/elitea-testing-public/issues/2117) established from the
API side.

### Finding 2 — the CI failure reproduces deterministically on localhost

```
cd automation && HEADLESS=true ../.venv/bin/pytest \
  "tests/ui/chat/test_image_creation.py::TestImageCreation::test_create_image[minimal_prompt]" \
  -v -p no:cacheprovider
```

```
E   playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E   Call log:
E     - waiting for locator("[role=\"menuitem\"]:has-text(\"GPT-5.2\")") to be visible
ERROR    elitea.steps:actions.py:49 Step failed: Select model — Locator.wait_for: Timeout 10000ms exceeded.
   (identical on all 3 attempts — initial + 2 pytest-rerunfailures reruns)
```

Byte-identical to the DEV CI signature on run `34331579791`, on a **different
environment**, 3/3.

**This refutes the DEV gateway-500 outage theory for these two tests.** That outage class
(`.agents/testing.md` § "Full-page gateway 500") is environment-scoped, non-reproducing,
and surfaces as a branded 500 page — it cannot produce a deterministic 10 s timeout on a
*model-option* locator on localhost. It is a genuine co-occurrence in the same CI run, not
the cause here. The call log naming the exact dead literal is decisive.

Note the two `wait_for` calls in `ChatPage.select_model` both use `timeout=10000`; the call
log proves it is the **second** one (the model option) — the menu itself opened fine.

### Finding 3 — the case's literal flow WORKS with the default model (the decisive evidence)

Walked with **no model selection at all**:

1. Open `/chat`, new conversation. Composer's model reads **`Anthropic Claude 4.5 Sonnet`**
   — the catalog's `default: true` entry.
2. Plus menu → `Modules` → toggle **`Image Creation`** → switch reads `[checked]`.
3. Send `Generate an image of a sunset over mountains`.
4. Response region shows `Anthropic Claude 4.5 Sonnet` → `ImageGen: generate_image` →
   `Anthropic Claude 4.5 Sonnet`, then renders:
   - text: *"Perfect! I've generated an image of a sunset over mountains for you. The image
     has been created and saved successfully."*
   - `img "image_20260909175243328.png"` — a real generated image.
5. **0 console errors**, no `400`, no `Invalid model name`. Conversation `/chat/10017`
   persists on DEV for re-inspection.

**Timing:** send at 17:50:56Z, image produced at 17:52:43Z (from the generated filename),
fully rendered by 17:53:13Z — **~110-140 s end to end**. The existing
`IMAGE_GENERATION_TIMEOUT = 180000` covers it. **Do not lower it**; the margin is already
modest.

### Finding 4 — the docstring's "switch resets internal tools" claim no longer holds

The test docstring justifies the model-switch-before-tool-enable ordering with
*"(after model switch to avoid reset)"*. Live: with `Image Creation` already ON, switching
the model `Anthropic Claude 4.5 Sonnet` → `GPT-5 mini` left the switch **`[checked]`**.

Scope of the observation: an existing conversation, after one message. It is enough to show
the ordering constraint is not load-bearing for a test that performs **no** model switch —
which is what this repair produces. The docstring line must go regardless, because it
documents a step that no longer exists.

### Finding 5 — the accessible name is `Image Creation`, the page object says `Image creation`

`ChatPage.enable_image_creation` uses `get_by_role("switch", name="Image creation")`.
The rendered name is **`Image Creation`** (capital C). This still matches — Playwright's
`get_by_role(name=…)` is case-insensitive substring by default — so it is **not** a break
and needs no change. Recorded so a future reader does not "fix" it into an `exact=True`
form that would then fail.

---

## Triage verdict

**Class A — UI drift**, in its data-catalog form: the product's model catalog changed under
a hard-coded display-name literal. The intended flow (the case's own flow) still works.

Explicitly **not**:

- **not class B/C (product bug)** — image generation works end to end, 0 console errors;
- **not class D (pollution/flake/infra)** — deterministic 3/3 on two environments;
- **not class F (promotion gap)** — the repair adds no testid, and the failing handle is a
  raw `[role="menuitem"]` text match, not a testid at all;
- **not the DEV gateway-500 outage** — see Finding 2.

### Relationship to #2117 (`config.default_model_name = "gpt-5.2"`)

`automation/config.py:235` still declares the dead literal `default_model_name = "gpt-5.2"`.
**That is a separate, wider decision and this repair does not depend on it.** This spec
does not read `settings.default_model_name` (grep: 0 hits in
`tests/ui/chat/test_image_creation.py`), and after the repair it names no model at all.
#2117 governs the ~30 API-seeding call sites and the specs that *assert* model display
names (`test_agent_llm_selector_openai_models.py`, `test_import_agent_valid_md_file.py`,
`test_skill_test_panel_llm_model_settings.py`) — none of which is this case.

**Corollary and the whole point of the repair:** replacing `"GPT-5.2"` with any other model
literal here would re-create exactly this failure the next time the catalog moves. The case
asks for *the default*; the test must ask for the default too, which it does by asking for
nothing.

---

## Adjustment — what changes and why

| Change | Rail classification | Justification |
|---|---|---|
| Delete `chat.select_model("GPT-5.2")` and its `allure.step` block | *how* it reaches — **free to change** | The case has no model-selection step; the deleted step is a test artifact. Removing it makes the test use the default, which is what the case's Step 3 specifies. |
| Renumber the remaining `allure.step` blocks 1-5 | *how* — free | Structure preserved, one step fewer. |
| Update module docstring (User Flow, GPT-5.2 references) | doc only | It describes a step that no longer exists. |
| **Remove the `pytest.skip(FeatureNotAvailableError)`** | see § below — **flagged for lead sign-off** | Defect masking under `.agents/profile.md` § Bug filing. |

### Expected-result changes

**NONE.** Every assertion is preserved verbatim:

- `chat.get_images_in_last_message() >= 1`
- `chat.get_generated_image_src()` non-empty

Nothing is weakened, no comparison relaxed, no count lowered, no check made conditional.
The observable — *an image is generated by the real product and displayed in the chat* —
is exactly what it was, and is now reached through the flow the case actually specifies.

### The `pytest.skip` on `FeatureNotAvailableError` — recommendation, not a silent change

Current code (lines 63-70) catches `FeatureNotAvailableError` from
`enable_image_creation` and calls `pytest.skip("Internal tools toggle not available —
image creation feature may have been moved or removed in current UI version")`.

**Assessment: this is defect masking and should be removed.**

- The case's Step 2 expected result is *"Image Creation tool is toggled ON"*. If the plus
  menu or the `Modules` entry is gone, that expected result is **not met** — which is a
  FAIL, not a skip.
- The skip's own stated trigger — *"may have been moved or removed in current UI
  version"* — is a description of **UI drift**, i.e. precisely the condition this repair
  path exists to surface. Converting it to a skip guarantees the drift is never noticed:
  the suite goes green while the case is silently unverified.
- `.agents/profile.md` § Bug filing: *"Never mask: no `test.fail()`/skip/weakened
  asserts"*. This is a `pytest.skip` on a product-side condition, in the covered path.
- Live today the toggle is present and works (Finding 3), so removing the skip changes
  **no current outcome** — it only removes a future silent green.

Removing it is a *strengthening*, and the preserve-the-nature rail governs weakening. I am
nevertheless flagging it rather than treating it as automatic, because it is the one change
in this repair that is not strictly required to turn the test green.

**Recommendation: remove it** (the diff below does). If the lead prefers minimal scope, it
may be deferred to its own card — but then it should be carded, not left silent.

### Optional coverage improvement — NOT included in the proposed diff

The test currently enables Image Creation but never asserts the toggle's state, so the
case's Step 2 expected result (*"Image Creation tool is toggled ON"*) is exercised but
unasserted. `ChatPage.is_image_creation_enabled()` exists. Adding
`assert chat.is_image_creation_enabled()` would close that Axis-1 gap at the cost of one
extra menu open/close. Left out of the minimal repair deliberately; raised here so the lead
can decide.

---

## Coverage Map

### Axis 1 — the case's own elements

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| Pre | At least one shared image model is available as the default | — | Catalog has 8 models, `Anthropic Claude 4.5 Sonnet` is `default: true` | not asserted (environment precondition) | covered-implicitly |
| Pre | User has access to Chat and ≥1 Agent | — | `conversation_id` fixture creates a conversation via API | fixture | covered |
| 1 | Open Chat and create a new conversation | Chat input is ready | `navigate_to_chat(conversation_id=…)` | Step 1 | covered |
| 2 | Enable the Image Creation tool | Tool is toggled ON | `enable_image_creation()` | Step 2 (post-repair) — exercised, **state not asserted** | **partial** — see § Optional coverage improvement |
| 3 | Send image prompt **using the default image model** | Image displayed; no error, no 400, no "Invalid model name" | default model used (no selection); `send_message` → `wait_for_image_in_response` | Steps 3-5 | covered |
| 4 | Navigate to an Agent, enable Image Creation in its chat panel | Tool ON in Agent context | — | — | **out-of-scope (pre-existing)** |
| 5 | Send same prompt in Agent chat | Image displayed in Agent chat, no errors | — | — | **out-of-scope (pre-existing)** |

**Pre-existing coverage gap, reported not repaired:** the case has 5 steps covering **both**
Chat and Agent chat; the automated spec covers Steps 1-3 (Chat) only. The TMS case's
`automation_test_id` lists these two params as the case's automation, which overstates
coverage. This predates card #2112 and is out of scope for a timeout repair — **it is
`[Automate]` work and needs its own card.** Flagged for the lead.

### Axis 2 — asserted beyond the case

| Observable | Why |
|---|---|
| `get_generated_image_src()` is non-empty | Guards against a rendered `<img>` with a broken/empty `src` — "displayed" in the case's sense requires a real source. Pre-existing; retained. |

---

## Handles Reference

The repair **removes** handles; it adds none. Provenance is therefore unchanged for every
surviving handle.

| Handle | Used by | Kind | PROVENANCE |
|---|---|---|---|
| `[role="menuitem"]:has-text("GPT-5.2")` | `ChatPage.select_model` (line 3685) | raw handle | **DELETED from the executed path** by this repair — the call site goes, the method stays |
| `plus-menu-button` | `ChatPage.open_internal_tools_menu` | testid | pre-existing, unchanged |
| `internal-tools-menuitem` | `ChatPage.open_internal_tools_menu` | testid | pre-existing, unchanged |
| `get_by_role("switch", name="Image creation")` | `ChatPage.enable_image_creation` | raw handle | pre-existing tech debt (#25/#42) — **not touched, not extended** |
| `img:not([alt="EliteaStage"]):not([class*="avatar"])` | `get_images_in_last_message`, `get_generated_image_src` | raw handle | pre-existing tech debt — not touched |

**Locator policy compliance:** this repair adds **zero** new handles of any kind, so the
reviewer's mechanical grep must come back with **no added `get_by_*` / `.locator(` lines**.
The pre-existing raw handles above are tracked tech debt, not precedent, and are left
exactly as they are.

Noted for a future card, **not** for this one: the Image Creation switch already carries the
testid `modules-toggle-image_generation`, and model options carry
`model-selector-option-<slug>`. Migrating `enable_image_creation` / `select_model` off their
raw handles is real, available work — but it is tech-debt work with its own blast radius,
not part of a timeout repair.

---

## Fidelity Declaration

**No substitutions of any kind.** The image asserted is produced by the real Image Creation
internal tool, reached through the real composer, using the product's own default model.
No `page.route`, no `route.fulfill`, no `page.evaluate`, no `monkeypatch`, no seeded state
beyond the `conversation_id` fixture (a transit precondition the spec already had — it
creates an empty conversation via API; the case's own observable is untouched by it).

---

## Environment verdict

**This spec CAN be gated on `http://localhost:5173`. DEV is not mandatory.**

Evidence:

- Localhost's `VITE_DEV_TOKEN` identity **completed a full image generation** through the
  internal tool (Finding 3). The `.agents/testing.md` § Merge gate corollary — some flows
  fail on localhost because that identity has no `user_token` — **does not apply to image
  generation**. Established empirically, which is the only way it could be established.
- The model catalog is identical by construction: localhost's UI and DEV's UI both talk to
  the **same DEV backend**, and the catalog was read directly from
  `dev.elitea.ai/…/configurations/models/399`.
- The failure itself reproduces on localhost with the DEV CI's byte-identical signature
  (Finding 2), so localhost is a faithful gate for this repair.
- The localhost identity is the *weaker* of the two; DEV's Keycloak session is strictly
  more capable, so a localhost green does not depend on an identity DEV lacks.

DEV was **not** separately walked in a browser: the two things a DEV walk could have added
(the catalog, and whether the flow is identity-gated) were both settled by direct evidence
above. `automation/.env.test` was **not modified** at any point in this analysis and remains
on the localhost pair — verified.

---

## Blocked Steps

None.

---

## Evidence

Screenshots on disk (local paths — the lead uploads/embeds per
`.agents/role-overrides.md` § screenshot evidence):

| # | What it shows | Path |
|---|---|---|
| 1 | Generated image in chat with the default model, full page | `test-results/screenshots/ELITEA-0679-image-generated-with-default-model.png` |
| 2 | Model menu open — 8 options, none named `GPT-5.2` | `test-results/screenshots/ELITEA-0679-step-02-model-menu-8-options-no-gpt-5-2.png` |
| 3 | Viewport at image render, default model | `test-results/screenshots/ELITEA-0679-step-03-image-generated-default-model-localhost.png` |

In-product evidence: conversation **`/chat/10017`** ("Generate image sunset over mountains")
in project 399, containing the generated image and the `ImageGen: generate_image` tool trace.

---

## Proposed diff (for the implementer)

Single file: `automation/tests/ui/chat/test_image_creation.py`. **No page-object change is
required.** `automation/pages/chat_page.py` is untouched.

### 1. Module docstring (lines 1-11)

```diff
-"""UI Tests for Chat Image Creation functionality.
-
-Tests the image generation capability in Elitea chat using the Image creation
-internal tool with GPT-5.2 model.
-
-User Flow:
-1. Select GPT-5.2 model
-2. Enable "Image creation" in internal tools (after model switch to avoid reset)
-3. Describe the image to generate
-4. Receive generated image in chat
+"""UI Tests for Chat Image Creation functionality.
+
+Tests the image generation capability in Elitea chat using the Image Creation
+internal tool with the project's DEFAULT model.
+
+TMS case ELITEA-0679 names no model: its precondition is "at least one shared
+image model is available as the default" and Step 3 sends the prompt "using the
+default image model". The test therefore selects no model at all.
+
+History: the test used to call select_model("GPT-5.2") first. That model was
+removed from every working project's catalog (see #2117), so the call timed out
+(card #2112). It was a test artifact the case never asked for; naming any
+replacement literal would just re-break on the next catalog change.
+
+User Flow:
+1. Enable "Image Creation" in internal tools
+2. Describe the image to generate
+3. Receive generated image in chat
```

### 2. Delete the model-selection step and renumber (lines 55-77)

```diff
         with allure.step("Step 1 — Navigate to chat"):
             chat = ChatPage(page)
             chat.navigate_to_chat(conversation_id=conversation_id)
 
-        with allure.step("Step 2 — Select GPT-5.2 model"):
-            chat.select_model("GPT-5.2", timeout=UI_ELEMENT_TIMEOUT)
-
-        with allure.step("Step 3 — Enable Image creation internal tool"):
-            try:
-                chat.enable_image_creation(timeout=UI_ELEMENT_TIMEOUT)
-            except FeatureNotAvailableError:
-                pytest.skip(
-                    "Internal tools toggle not available — image creation feature "
-                    "may have been moved or removed in current UI version"
-                )
+        with allure.step("Step 2 — Enable Image Creation internal tool"):
+            chat.enable_image_creation(timeout=UI_ELEMENT_TIMEOUT)
 
-        with allure.step(f"Step 4 — Send image generation prompt: {prompt[:50]}..."):
+        with allure.step(f"Step 3 — Send image generation prompt: {prompt[:50]}..."):
             initial_count = chat.get_message_count()
             chat.send_message(prompt, use_enter=True)
 
-        with allure.step("Step 5 — Wait for AI response with image"):
+        with allure.step("Step 4 — Wait for AI response with image"):
             chat.wait_for_input_ready()
             chat.wait_for_ai_response(initial_count=initial_count, timeout=IMAGE_GENERATION_TIMEOUT)
             chat.wait_for_image_in_response(timeout=IMAGE_GENERATION_TIMEOUT)
 
-        with allure.step("Step 6 — Verify image appears in response"):
+        with allure.step("Step 5 — Verify image appears in response"):
             assert chat.get_images_in_last_message() >= 1, (
                 "Expected at least one image in the AI response"
             )
             assert chat.get_generated_image_src(), (
                 "Generated image should have a valid non-empty source URL"
             )
```

### 3. Docstring of the test method — declare the model choice

Add one line to `test_create_image`'s docstring (per `.agents/role-overrides.md` §
Implementer slot, *declare in the docstring, not only in the AFS*):

```diff
-        """Create image from text prompt and verify image appears in response."""
+        """Create image from text prompt and verify image appears in response.
+
+        Uses the project's DEFAULT model — ELITEA-0679 Step 3 specifies "using the
+        default image model" and the case names no model. No model is selected.
+        """
```

### 4. Fix the now-unused import

Removing the `except FeatureNotAvailableError` leaves the import unused →
`ruff` `F401`.

```diff
-from pages.chat_page import ChatPage, FeatureNotAvailableError
+from pages.chat_page import ChatPage
```

`pytest` itself is still used (`@pytest.mark.parametrize`, `pytest.param`), so the
`import pytest` stays.

### Notes for the implementer

- `ChatPage.select_model` becomes **unreferenced repo-wide** (grep: this was its only
  caller). **Leave the method in place** — deleting a page-object method is a separate
  decision with its own blast radius, and it is a legitimate utility.
- `IMAGE_GENERATION_TIMEOUT = 180000` and `AI_RESPONSE_TIMEOUT` / `UI_ELEMENT_TIMEOUT`
  are unchanged. `UI_ELEMENT_TIMEOUT` is still used (by `enable_image_creation`).
- **Do not add a model-name assertion.** It would reintroduce exactly the literal that
  broke this test.
- Verify with `../.venv/bin/ruff check .` — the repair should be clean.
- Gate: 3 separate consecutive invocations of **both** node ids on `localhost:5173`
  (see § Environment verdict). Budget ~2-2.5 min per param, so ~5 min per gate run.
