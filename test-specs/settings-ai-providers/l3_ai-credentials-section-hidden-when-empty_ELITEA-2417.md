# Test Case: AI Credentials section is hidden when no credentials are configured

## Metadata
- **TMS ID**: ELITEA-2417
- **Linked Story**: none
- **Priority**: l3 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost)
- **Analyst**: qa-engineer (Sage), batch `settings-w10`, 2026-08-29
- **Status**: **blocked** — the case's core observable ("the section is NOT
  shown") cannot be produced against the live system; see § Blocked Steps
- **Surface digest**: `test-specs/settings-ai-providers/_surface.md`
- **Filed**: clarification **EliteaAI/elitea-testing-public#1982** (`question`,
  `case-text-drift`) — carries the decision the lead/human needs to make
- **Cluster**: dispatched with ELITEA-2393 / ELITEA-2394. This case **diverged**:
  those two live on Settings → General's "AI Configurations" accordion, this one
  on Settings → **AI Providers**. No shared spec.

---

## Why this AFS exists even though the case is blocked

Everything the analyst learned is here so the next attempt (after the #1982
decision) does not re-explore: the flow, the handles, the exact reason the
precondition is unreachable, and the two honest assertions that *are* available.

## Case-identity note

"Settings → AI Configuration" here means Settings → **AI Providers**
(`/settings/ai-providers`) — the page whose seven accordion sections include
**AI Credentials**. Same nonexistent-page drift already tracked by #1250 /
#1772 / #1906.

## What was executed live (2026-08-29)

| Case step | What actually happened |
|---|---|
| 1 — Navigate to Settings → AI Configuration "in a project with no AI credentials configured" | `/settings/ai-providers` loads. **No such project exists via the UI** — see step 2. |
| 2 — Verify the AI Credentials section is NOT shown | **FAILS by precondition, not by defect.** `ai-providers-section-ai-credentials` is **present** on both projects tried — `UI Testing` (400) and `Private` (399) — each showing count badge `1` and a single card `ELPS` / `OK • Shared`. The page fetches with `include_shared=true` for every non-public project, so a shared AI credential renders the section everywhere. |
| 3 — Add a new credential via "+" → "AI Credentials" | **No such option.** `sidebar-create-button` → `/settings/create-ai-provider?viewMode=owner&from=ai-providers`, a type picker with 12 concrete provider types (`toolkit-type-card-{ai_dial,amazon_bedrock,azure_open_ai,embedding_model,image_generation_model,llm_model,ollama,open_ai,pgvector,asr_model,tts_model,vertex_ai}`). Choosing OpenAI opens `/settings/create-ai-provider/open_ai` with fields Display Name / ID / Api Base / Api Key. |
| 4 — Complete and save the credential | **Not executed.** Requires real API-key secret material, and no teardown (delete) path was verified — creating one would pollute the shared project irreversibly as far as this analysis established. |
| 5 — Verify the section now appears with the new card | **Unreachable** — it is already showing, so the transition the case asserts cannot be observed. |

Side channels: the type-picker page logs one React *"Each child in a list should
have a unique key prop"* `console.error` from `CategorySection.jsx` →
`GroupedCategory.jsx` → `CredentialTypeSelector.jsx` — **already tracked as
EliteaAI/elitea-testing-public#656** (OPEN), not re-filed. A spec that visits this
picker must expect exactly that one error.

## Blocked Steps

1. **Step 2's observable cannot be produced.** A visible shared AI credential
   (`ELPS`) makes `ai-providers-section-ai-credentials` render on every project
   reachable from the UI. Per `.agents/testing.md` § Fidelity policy, this is a
   route-to-a-human decision, not something to engineer around: fabricating an
   empty `configurations` response (`route.fulfill`) would be a **terminal
   substitution** — the case's entire observable read off the test's own payload —
   and is forbidden.
2. **Step 3's entry point does not exist as written** ("+ → AI Credentials").
3. **Steps 4–5 need real secret material and a verified teardown.** Neither is
   available; creating a credential on the shared project without a proven delete
   path is state pollution.

**Unblocks when** #1982 is decided — one of:
- (a) the case is re-scoped to an observable assertion (see below), or
- (b) a project/environment with no *visible* (own or shared) AI credential is
  provided, or
- (c) the hide-when-empty half is retired as already covered elsewhere.

## What IS honestly assertable today (for option (a))

- **The hide-when-empty rule itself is already proven** on this page by
  ELITEA-2392's merged spec, which asserts Vector Storage's absence *against the
  API response* (`navigate_and_capture_vectorstorage_response`: HTTP 200 + zero
  items ⇒ no accordion) — the correct way to tell "correctly hidden" from
  "silently broken". Vector Storage is still absent on both projects (confirmed
  this session), so that coverage is live.
- **A count-parity assertion** would be new and honest: the AI Credentials
  accordion's count badge equals the number of `section=ai_credentials` items in
  the page's own combined `configurations/configurations/{project_id}` response,
  and the section renders iff that count > 0. That covers the case's *rule* in
  both directions without needing an empty project.

## Concrete Handles (all verified live this session)

| Element | Primary handle (testid-only) | Provenance (verified `git fetch origin`, EliteaUI, 2026-08-29) | Notes |
|---|---|---|---|
| AI Credentials accordion header | `ai-providers-section-ai-credentials` | **on `main` ✓** and `automation/testids` | `AIProvidersPage.ai_credentials_section_header`; `aria-expanded` carries expand state |
| Configuration card | `ai-provider-configuration-card` | **on `main` ✓** and `automation/testids` | `AIProvidersPage.CONFIGURATION_CARD_SELECTOR` |
| Card display name | `ai-provider-configuration-card-name` | on `automation/testids` (EliteaAI/EliteaUI@e1ea650c) | use `AIProvidersPage.card_for_model()` |
| "+" create control | `sidebar-create-button` | **on `main` ✓** | `AIProvidersPage.create_button` / `click_create()` |
| Provider type card | `toolkit-type-card-{type}` | **on `main` ✓** | `AIProvidersPage.TYPE_CARD_SELECTOR`; 12 values listed above |
| Provider form fields | `toolkit-field-{label,elitea_title,api_base,api_key}-input`, `credential-form-save-button`, `credential-form-discard-button`, `credential-form-test-connection-button` | pre-existing (shared credential form) | `CredentialFormFieldsMixin` already owns these — do not re-declare |

No new testid is required for this case as written; the blocker is data/precondition, not locators.

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result (case) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` | fixture | asserted (setup) |
| Step 1 — Navigate to Settings → AI Configuration in a project with **no** AI credentials | page loads | executed (navigation only) | — | **blocked** — no such project exists via the UI |
| Step 2 — AI Credentials section is NOT shown | condition holds | — | — | **blocked** (§ Blocked Steps 1) |
| Step 3 — Add a credential via "+" → "AI Credentials" | operation completes | explored | — | **clarification (#1982)** — the entry point is a provider type picker |
| Step 4 — Complete and save the credential | expected UI state | — | — | **blocked** (§ Blocked Steps 3) |
| Step 5 / Expected Final State — section now appears with the new card | condition holds | — | — | **blocked** — already visible, so the transition is unobservable |

### Axis 2 — observables beyond the case
None asserted — no spec is produced by this AFS.

## Cleanup
Nothing was created or mutated. The project selector was left on the project it
started on (`UI Testing`, 400) after switching to 399 to compare.

## Known Defects Found During Exploration
- React "unique key prop" console error on the AI-provider type picker —
  **already tracked as #656**, not re-filed.
- No product defect. The hide-when-empty logic is correct; the case's assumption
  about the data is what no longer holds.

## Known traps
- **`test-specs/settings-ai-providers/_surface.md`'s 2026-08-06 line "AI
  Credentials: 0 configs — section absent" is STALE** and has been corrected in
  that digest. Re-verify before relying on any zero-config claim there.
- **Never fabricate the empty response to make this case green.** That is a
  terminal substitution (`.agents/testing.md` § Fidelity policy) — the case's
  only observable would come from the test's own payload.
