# Batch elitea-4720 report

**Totals:** blocked 1 (1 case). Base `origin/main`, trunk `tests/batch-elitea-4720`.

| Case | Outcome | Note |
|---|---|---|
| ELITEA-4720 | blocked | gate red: playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 15000ms exceeded. Raised at spec line 57 `pp.navigate(pipeline_id)` -> pages/pipeline_detail_page.py:2210 navigate -> :2234 wait_ |

## Findings

### clarification
- C1: the case says to make the unsaved edit on the pipeline Description. The AFS directs the implementer to edit the LLM node's System field instead (pipeline-llm-node-system-value). The AFS records the full reasoning under Clarifications; I did not re-check it. (`ELITEA-4720`)
- C2: Run History is a route (/pipelines/all/<id>/history), not an inline panel. After navigating back, the panel is closed and the conversation is gone. The implementer must not carry the conversation across the Run History round-trip, so the Run History check should come last in the session or the test should re-send. (`ELITEA-4720`)
- AFS Step 12 says width persists in localStorage `pipelineTestPanelWidth:<pipelineId>`. Source (useTestPanelWidth.hooks.js) keys it by user id, and max width is 50% of the viewport. Dragging 150 px at 1600 px clamped, and the reloaded width (492) differed from the live width (523). Appended to _surface.md; the AFS body is not amended. (`test-specs/pipelines/_surface.md`)
- Three deviations from the case text are documented in the AFS, declared in the spec docstring and justified by live observation and source. They are not masking. C1: the unsaved edit is an LLM node System edit rather than the Description, because a Description edit does not gate sending. C2: the chat is re-seeded after the Run History route, and again after the reload. C3: the pill shows "0%", not… [clipped; full text in the unit's receipt under .agents/automation/_returns/] (`AFS C1/C2/C3`)

### note
- On DEV, platform banners (platform-banner-center, then platform-banner-corner) intercept clicks about 6 s after load. The test must dismiss them. The context pill shows only once a conversation exists, and its percentage varies, so assert the regex ^\d+%$.
- Container lacks automation/.env.test, so APP_PREFIX is empty and every DEV navigation times out unless APP_PREFIX=/app is exported. The lead's gate runs need it.
- Step 10 (close mid-run, running highlight still present) passed on this run with the poem prompt, but it is timing-sensitive per the AFS risks. Watch it at the 3x gate.
- Mechanical locator grep (git diff main...HEAD -- automation/pages automation/tests | grep -nE 'get_by_*|query_selector|page.locator|.locator(|.nth(|locator=|fallback=') returned 2 hits. Both are compliant under the one-hop rule. node_card_running passes self.page.locator(self.NODE_CARD_RUNNING.format(...)), where NODE_CARD_RUNNING is an UPPER_CASE class constant that is a [data-testid=...] templat… [clipped; full text in the unit's receipt under .agents/automation/_returns/] (`automation/pages/pipeline_detail_page.py:10780,10830`)
- TMS pair verified statically. The spec has @pytest.mark.tms("ELITEA-4720") plus @allure.issue pointing at ELITEA-4720_pipeline-test-pipeline-panel-controls-and-session-behavior.md under tests/automated-full-regression-ui/pipelines/. That file exists in the sibling TMS clone and its name carries the same id. All 13 steps plus 7a are wrapped in allure.step. (`automation/tests/ui/pipelines/test_pipeline_test_panel_controls_session.py:34-41`)
- Triangulation of case, AFS and diff, row by row. 1: panel hidden + button visible/enabled. 2: panel, input, model selector, controls, history, clear, close visible, and test button hidden. 3: running node card count 1, 2 items, non-empty last response, model chip. 4: pill regex ^\d+%$. 5: popover visible, tokens visible, messages =="2", summaries =="0", edit button visible. 6: exact tooltip "Run H… [clipped; full text in the unit's receipt under .agents/automation/_returns/] (`test-spec Coverage Map vs spec`)
- This is the flakiness hotspot: the running attribute must be seen within about 2s and the post-close check has a 1s timeout. The AFS flags it. The hardening gate will show it; I did not weaken or change anything. (`spec lines 128-130 (Step 10)`)
- The case's 'canvas takes the full width' is covered only by the panel being hidden, with no geometry assertion. The AFS discloses this as the Step 1 disposition, so I accept it. (`spec lines 46-47 (Step 1)`)

## Gate
Verdict: **red**, runs: 0, timings (s): [86.2]

- `tests/ui/pipelines/test_pipeline_test_panel_controls_session.py::test_pipeline_test_panel_controls_and_session` (ELITEA-4720): playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 15000ms exceeded. Raised at spec line 57 `pp.navigate(pipeline_id)` -> pages/pipeline_detail_page.py:2210 navigate -> :2234 wait_for_detail_page_load (before any test step ran). 2 reruns (pytest-rerunfailures) also failed; 1 failed, 2 rerun in 83.97s.
