# Batch Report — pipelines-remaining-w5

**Totals:** 6 merged-ungated, 1 blocked | Gate verdict: not-run (1 run, 360.97s, no failures recorded)

## Cases at a glance

| Case ID | Outcome | Note | PR | AFS |
|---------|---------|------|-----|-----|
| ELITEA-2017 | merged-ungated | gate never produced verdict — merged but unproven | #1357 | test-specs/pipelines/l2_pipeline-execution-long-response-streaming_ELITEA-2017.md |
| ELITEA-2052 | merged-ungated | gate never produced verdict — merged but unproven | #1358 | test-specs/pipelines/l2_pipeline-welcome-message-shown-before-first-input_ELITEA-2052.md |
| ELITEA-2053 | merged-ungated | gate never produced verdict — merged but unproven | #1359 | test-specs/pipelines/l2_pipeline-chat-starters-visible-and-clickable_ELITEA-2053.md |
| ELITEA-2058 | merged-ungated | gate never produced verdict — merged but unproven | #1360 | test-specs/pipelines/lextend_pipeline-llm-model-selection-and-execution-usage_ELITEA-2058.md |
| ELITEA-2059 | merged-ungated | gate never produced verdict — merged but unproven | #1361 | test-specs/pipelines/l2_pipeline-attach-files-in-chat_ELITEA-2059.md |
| ELITEA-2062 | merged-ungated | gate never produced verdict — merged but unproven | #1362 | test-specs/pipelines/l2_pipeline-multiple-browser-tabs_ELITEA-2062.md |
| ELITEA-2071 | blocked | defect-found: pipeline chat panel missing fullscreen-mode toggle (filed #1363) | — | test-specs/pipelines/l2_pipeline-fullscreen-chat-mode_ELITEA-2071.md |

## Findings by kind

### Defects (5 total)

1. **ELITEA-2017** — Found and fixed during implementation: naive length-only streaming check unsound due to transient loading placeholders ('Waking the agent…', 'Packing its tools…') that fool a length-growth assertion.

2. **ELITEA-2052** — Dead/unreferenced LocatorDescriptor fields on PipelineDetailPage (chat_message_item, chat_read_out_button, chat_answer_content, chat_message_delete_button) declared but never invoked. **RESOLVED in follow-up commit 00319726** — fields removed and replaced by UPPER_CASE string constants.

3. **ELITEA-2059** — Coverage-Map row 6 claims 'message bubble shows text+chip, composer's chip count resets to 0' but the shipped test only asserts message count. **RESOLVED in follow-up commit 6a112add** — index-based getters added to avoid `.last` race condition with transient placeholders.

4. **ELITEA-2071** — Pipeline chat panel is missing the Fullscreen Mode toggle present on every other chat-hosting surface (Agents, Skills, Toolkit Indexes). Source-level root cause identified: ConfigurationTab.jsx:205 dead isFullScreenChat literal; ChatPanel.jsx never imports FullScreenToggle.jsx. **Blocks this case; filed elitea-testing-public#1363.**

### Clarifications (6 total)

1. **ELITEA-2017** — AFS Concrete Handles table and pipelines _surface.md both claimed `model-selector-option-{slug}` testid was on-main. Fresh git fetch + git grep revealed it is automation/testids-only, pending human cherry-pick to main. **Amended both documents in PR #1357.**

2. **ELITEA-2052** — Case text step 2 ('Expand Welcome message section') is a no-op on live product — section renders expanded by default. **Documented per reverse-masking guard.**

3. **ELITEA-2052** — Case text step 5 ('Open new chat session') — pipeline detail route has no distinct 'open chat' UI action; embedded chat panel always mounted. AFS uses full-page reload as pristine-session equivalent. **Documented in AFS.**

4. **ELITEA-2053** — Case step 2 ('Expand Chat starters section') is a no-op — accordion expanded by default, same pattern as Welcome message (ELITEA-2052) and Advanced (ELITEA-2021). **Documented in AFS.**

5. **ELITEA-2058** — Case Test Data claims default model is 'Anthropic Claude 4.6 Sonnet', but live default is 4.5 Sonnet. Case text already hedges ('or current default'). **Noted in AFS so implementer doesn't hardcode a specific model name.**

6. **ELITEA-2059** — Case's Task/execution assertion (step 7, 'pipeline processes the attachment') cannot be satisfied literally for a bare LLM-only pipeline node — node only receives path-like reference, not extracted file content. **Expected pipeline architecture; documented in AFS.**

### Notes (80+ total across all cases)

Key recurring patterns:

- **Case-snapshot path drift:** Dispatch specified `.agents/automation/pipelines-remaining-w5/cases/` for 6 cases, but that directory does not exist. Actual snapshots under `.agents/automation/pipelines-remaining/cases/` (un-suffixed batch slug). Already flagged by earlier analysts in this batch.

- **Testid provenance misstatements:** Multiple AFS/digest claims of testids being "on-main ✓" were incorrect upon fresh verification (git fetch origin + git grep). Implementers amended them in their PRs. Pattern suggests analyst-pass testid state tracking may be stale or cache-heavy.

- **Model-API fixture consistency:** The `pipeline_with_llm_id` fixture hardcodes TASK as Fixed/empty-string, not the F-String '{input}' some cases specify literally. Existing tests pass anyway with plain-text questions, so wiring is opaque. Implementer resolved by creating `pipeline_with_fstring_llm_id` fixture reusing generic helper.

- **Chat streaming gotchas:** Transient loading placeholders ('Waking the agent…', 'Packing its tools…') are non-empty and different lengths. Length-only assertions fail easily. Implementers learned to use index-based (not `.last`) accessors and content-aware waits.

- **No per-case board tracking:** No originating GitHub issue numbers found on board #9 for ELITEA-2017, ELITEA-2052, ELITEA-2059. PR-link comment step skipped per profile.md policy. Orchestrator should verify batch-level vs per-case issue tracking.

- **Locator-policy compliance:** All diffs passed mechanical non-testid-handle grep (0 added get_by_role/get_by_label/get_by_text/raw page.locator calls). Testid scoping respected (UPPER_CASE constants, chained off proper parent testids).

- **Additive-only on shared files:** All shared-caller edits (pipeline_detail_page.py, data_fixtures.py, conftest.py) verified additive via `git diff | grep -E '^-[^-]'` (empty results).

## Gate Verdict

**verdict:** not-run
**runs:** 1 (360.97s)
**failures:** none recorded

The gate was not executed — all 7 cases were merged onto the trunk but remain unproven by the independent hardening gate. The orchestrator should re-run the gate (3 consecutive runs of the merged specs) before marking any of these cases as promotable-to-main.

## Action Items for Orchestrator

1. **Re-run the independent hardening gate** on the merged specs (3 consecutive runs, N/M verdict, green only).
2. **Verify case-snapshot path templating** — dispatch should name cases under `.agents/automation/pipelines-remaining/cases/`, not the non-existent `-w5` variant.
3. **Check board #9 tracking** — determine whether this batch uses per-case issues or batch-level issue for PR-link comments.
4. **Testid promotion status** — verify which new testids (model-selector-option-{slug}, chat-attach-button, etc.) have been cherry-picked from automation/testids to main and deployed. See individual case closure records for SHA details.

---

**All files on disk at:** `.agents/automation/pipelines-remaining-w5/report.json` and `.report.md`
