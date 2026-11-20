# Test Case: Pipeline test chat — Copy markdown / Copy text icons visible, clickable, confirmed by toast

## Metadata
- **TMS ID**: ELITEA-4756
- **Linked Story**: EliteaAI/elitea_issues#5838 (copy split); manual source ELITEA-4750
- **Priority**: l1 (source: critical)
- **Environment Explored**: DEV https://dev.elitea.ai/app (live, 2026-11-20), scratch pytest probe via `PipelineDetailPage` + fixture `pipeline_with_fstring_llm_id` (APP_PREFIX=/app)
- **Status**: ready-for-automation
- **Sibling (not a target)**: ELITEA-4755 (agent surface, `tests/ui/agents/test_agent_test_chat_copy_icons.py`) — same observable on a different page object/panel; pipeline case differs in steps (Pipelines list/detail, Test Pipeline button, run). Kept as its own spec; reuse the pattern only.

## Preconditions
- Authenticated (`auth_state`). Pipeline with an LLM entry node connected to End: reuse fixture `pipeline_with_fstring_llm_id` (data_fixtures.py:312; used by ELITEA-4720). Case's "Story taller" is only an example.

## Test Data
- Input `go` (case) — any text.

## Test Steps
1. `pp.navigate(pipeline_id)`; `dismiss_banner_if_present()`; `wait_for_canvas()`. Verify Flow view loaded and `test_pipeline_button` visible+enabled. (Case says "open from Pipelines in left menu": navigate directly is acceptable transit; the list->open path is covered by other specs.)
2. `test_pipeline_button.click()` -> `test_pipeline_panel` visible, `chat_input` visible.
3. `send_message_in_embedded_chat("go")`; wait `embedded_chat_items()` count 2 and `skill_test_last_response.last` non-empty (timeout 90s). Response shown.
4. Last AI message: `chat-copy-markdown-button` and `chat-copy-text-button` both visible (no hover needed), enabled.
5. Hover markdown icon -> `[role=tooltip]` text `Copy markdown`.
6. Click -> `toast-message` text `Markdown copied to clipboard.` (`toast-alert` data-severity=info). Wait toast count 0 (<=20s) before step 8.
7. Hover text icon -> tooltip `Copy text`.
8. Click -> toast `Text copied to clipboard.`.

## Expected Results
As case; exact strings above confirmed live (no drift).

## Coverage Map
**Axis 1**
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 open pipeline, Test Pipeline visible | Flow view, button visible | step 1 | button visible/enabled | asserted (open via direct navigate, see step 1 note) |
| 2 click Test Pipeline | panel + input | step 2 | panel, chat_input visible | asserted |
| 3 enter input, send | run + final response shown | step 3 | 2 chat items, response non-empty | asserted; the "Run 1 details" label was NOT observed by analyst — implementer may optionally verify, not asserted in AFS |
| 4 icons visible | both visible | step 4 | is_visible x2 | asserted |
| 5 hover M | tooltip Copy markdown | step 5 | tooltip text | asserted |
| 6 click M | toast Markdown copied to clipboard. | step 6 | toast-message text | asserted |
| 7 hover copy | tooltip Copy text | step 7 | tooltip text | asserted |
| 8 click copy | toast Text copied to clipboard. | step 8 | toast-message text | asserted |
| Pass: "clickable" | enabled | steps 4/6/8 | `is_enabled` / to_be_enabled before click | asserted |
**Axis 2**: enabled-check = grounded in "visible and clickable" Pass criterion. Nothing else.

## Concrete Handles (verified live on DEV)
| Element | Rung | Handle | suggested_testid | Provenance |
|---|---|---|---|---|
| Test Pipeline button | testid | `PipelineDetailPage.test_pipeline_button` | - | existing, reused |
| Test panel / input | testid | `test_pipeline_panel`, `chat_input` (wrapper div) | - | existing |
| Response | testid | `skill_test_last_response`, `embedded_chat_items()` | - | existing (ELITEA-4720) |
| Copy markdown icon | testid | `chat-copy-markdown-button` | - | testid on DEV ✓ (count 1, visible, enabled) |
| Copy text icon | testid | `chat-copy-text-button` | - | testid on DEV ✓ |
| Toast | testid | `toast-alert`, `toast-message` (`PipelineDetailPage.toast_alert/toast_message` exist) | - | testid on DEV ✓ |
| Tooltip | role | `role=tooltip` (MUI popper, one visible at a time) | `chat-copy-tooltip` | ladder — unique while hovering |

Gap: `PipelineDetailPage` has NO copy-icon or open-tooltip descriptors (grep: none). Implementer declares class-level `chat_copy_markdown_button`/`chat_copy_text_button` (testid) and a tooltip descriptor on it, mirroring `AgentDetailPage` (agent_detail_page.py:514-520, 3091-3121) — scope to the last response with `.last` on the declared locator (collection of messages, not sibling pick), or consider whether the helpers can be shared.

## Network / Side channels
Clipboard write is client-side; toast is the observable (do not read clipboard). No console errors surfaced in probe.

## Known Defects
None. Case-text drift: none.

## Blocked Steps
None.

## Automation Hints
- Marker pair: tms ELITEA-4756 + allure.issue (case file under automated-full-regression-ui/pipelines/); markers p1, pipelines, regression.
- Set viewport 1600x1400 (DEV banners intercept clicks); `dismiss_banner_if_present()`.
- Wait first toast gone (count 0) before clicking the second icon.
- Env: no `automation/.env.test` in analysis sandbox -> run with `APP_PREFIX=/app`. Transit (fixture + page-object navigation) worked; no regression signal.
