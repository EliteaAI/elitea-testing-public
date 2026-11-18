# Extension AFS: Entry Point Node — Schedule settings (moved to SCHEDULES section / New Schedule page)

## Metadata
- **TMS ID**: ELITEA-2007 (card #2981, ADJUST — keep every check, change only where/how the schedule is created)
- **Status**: extend-existing
- **Covering spec**: `automation/tests/ui/pipelines_2/test_pipeline_schedule_trigger_settings_modal.py:test_schedule_trigger_settings_modal` (merged to main; currently RED — `select-option-schedule` gone, EL-7011/#7338)
- **Environment explored**: DEV `https://dev.elitea.ai/app`, 2026-11-18, headless Playwright via storage state
- **surface_key**: `pipeline-schedules-section`
- **Fixture**: `pipeline_with_llm_id` (entry `LLM 1`, no Printer/HITL/interrupt) — unchanged
- **Prior AFS superseded for the flow**: `l3_entry-point-schedule-trigger-settings-modal_ELITEA-2007.md` (Trigger dropdown + modal; keep for history)

## Overlap argument
The existing spec already proves: "on" hides for day, summary re-derives for 09:30, Default<->Advanced round trip with the cron carried over, save, persistence after reload. The observables are unchanged; only the entry (Trigger dropdown -> modal -> Apply) and the container (modal -> page + card) changed. Rewrite the Steps 2-9 bodies; keep the 9-step shape and the console-error guard.

## Flow, verified live (every step executed)
| Step | Action | Observed (DEV) |
|---|---|---|
| 1 | Navigate to pipeline (`?viewMode=owner`), dismiss banner | SCHEDULES section reads "No schedules run the base version yet." (empty state; add button `pipeline-schedules-section-add`). Entry node `LLM 1`. |
| 2 | Click "+ Schedule" | URL `/pipelines/all/<id>/schedules/create?viewMode=owner&name=<pipeline>&versionId=<v>`; breadcrumb "Pipelines / <name> / New Schedule". **No pipeline PUT.** |
| 3 | Verify page | Pipeline (locked, `schedule-locked-entity`, "To schedule a different pipeline…"), Version `base` preselected, Starting input = Entrypoint; SCHEDULE SETTINGS: Builder / Cron Expression toggle, Every=Week / on=Sat / at 00:00, summary "Runs every week at 00:00 on Saturday.", "Next run: …". Save enabled only after Name typed (initially disabled; ~1-3s after fill). Cancel present. |
| 4 | Every -> "Day" | `schedule-cron-weekdays-select-week` is removed from the DOM (3 cron selects left: period, hour, minute). Summary "Runs every day at 00:00." |
| 5 | Hour 09, minute 30 | Summary exactly `Runs every day at 09:30.` (no quotes; the old modal text `"At 09:30"` is gone). |
| 6 | Cron Expression tab | `pipeline-schedule-cron-input` visible, value `30 9 * * *` (carried over). |
| 7 | Back to Builder | period/hour/minute selects return, summary unchanged `Runs every day at 09:30.` |
| 8 | Save | `POST /api/v2/elitea_core/schedules/prompt_lib/<project>` -> 201, body `cron: "30 9 * * *"`, `enabled: true`, `run_mode: entry_point`. Navigates back to `/pipelines/all/<id>?viewMode=owner&name=…` (NOT the create page). |
| 9 | Reload | SCHEDULES section lists one card; cron round-trips. |

Card (after save, and after reload; section may take ~3-6s to populate after load — wait on the card testid):
`pipeline-schedule-card-<scheduleId>` text "At 09:30 · UTC / <name> / Last run: Never run / Next run: 19.11.2026 / Active". Rule line `pipeline-schedule-card-rule-<id>` = **"At 09:30"** (NOT "every day at 09:30"; the brief's wording is illustrative — assert "09:30" via the rule line equal to `At 09:30`), timezone `…-timezone-<id>` "· UTC", state `…-state-<id>` "Active".

## Handles Reference (all verified on DEV; rung | handle | suggested_testid | provenance)
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| SCHEDULES accordion header | testid | `pipeline-schedules-section` | — | testid on DEV ✓ |
| "+ Schedule" | testid | `pipeline-schedules-section-add` | — | testid on DEV ✓ |
| Name input | role+name | `role=textbox name="Name"` (unique, 1 match; the field has no testid) | `schedule-name-input` | ladder — no testid on DEV |
| Locked pipeline | testid | `schedule-locked-entity` (text contains "Pipeline"; input value = pipeline name) | — | testid on DEV ✓ |
| Version | testid | `schedule-version` | — | testid on DEV ✓ |
| Builder / Cron tabs group | testid | `pipeline-schedule-mode-tabs` | — | testid on DEV ✓ |
| Builder tab / Cron tab | role+name | `role=button name="Builder"` / `name="Cron Expression"` within the group (ToggleButton: `aria-pressed`, `value=builder|cron`; **role is button, NOT tab**) | `pipeline-schedule-mode-builder-button` / `…-cron-button` | ladder — no testid on DEV |
| Every select | testid | `schedule-cron-period-select` (MUI Autocomplete; options "Day","Week","Month" — capitalised; role=option) | — | testid on DEV ✓ |
| "on" (week) | testid | `schedule-cron-weekdays-select-week` (month period: `-monthdays-select`, `-weekdays-select-month`) | — | testid on DEV ✓ |
| hour / minute | testid | `schedule-cron-hour-select` / `schedule-cron-minute-select` (Autocomplete, options "00".."23"/"00".."59"; **single-select, no multi-checkbox mechanics** unlike the old modal; click then `role=option name="09"` exact) | — | testid on DEV ✓ |
| Summary | testid | `pipeline-schedule-summary-text` | — | testid on DEV ✓ |
| Next run | testid | `pipeline-schedule-next-run` | — | testid on DEV ✓ |
| Cron input | testid | `pipeline-schedule-cron-input` (the `<input>` itself carries the testid; value `30 9 * * *`) | — | testid on DEV ✓ |
| Save / Cancel | testid | `schedule-save-button` / `schedule-cancel-button` (Save is `aria-disabled=true` AND `disabled` when blocked) | — | testid on DEV ✓ |
| Schedule card | testid | `pipeline-schedule-card-{id}`, `-rule-{id}`, `-timezone-{id}`, `-next-{id}`, `-state-{id}`, `-toggle-{id}` | — | testid on DEV ✓ (ids are numeric, per project) |

Do NOT use `pipeline-schedule-modal-*` / `schedule_modal` handles — the modal is gone (page-object fields `schedule_modal*`, `trigger_schedule_edit_button`, `select_trigger_type("schedule")`, `apply_schedule_settings`, `get_schedule_cron_select_count` become dead; `get_trigger_option_states()` now returns `{'chat_message': True}` only).

## Quirks
- The platform announcement dialog (`platform-banner-center`, close `platform-banner-close`) intercepts clicks on first load; the corner banner can intercept node-panel clicks too — dismiss all `platform-banner-close` buttons.
- Before the first card render the SCHEDULES section header exists with no body for several seconds; wait on `pipeline-schedule-card-*` / the add button, never read same-tick.
- Save of the schedule is independent of the pipeline's own Save (stays disabled, no pipeline PUT).
- Create-page URL carries `name=<pipeline name>`; post-save URL also keeps it. The page uses its own Save/Cancel (`TabBarItems`), not `agent-save-button`.
- Console errors: none observed (the old react-js-cron `popupClassName` warning filter is no longer needed; keep the console guard but drop `_is_known_1021_warning` only if the guard stays green over the 3x gate).

## Coverage Map (Axis 1 — every element of the case + card brief)
| Case element | Expected | Covered by | Disposition |
|---|---|---|---|
| Pre: pipeline w/ entry point, no HITL/Printer/interrupt | single entry node | `pipeline_with_llm_id` + `get_entrypoint_node_id()` | covered |
| 1 Create pipeline | ready | existing Step 1, plus empty-state text "No schedules run the base version yet." | covered |
| 2 Open schedule creation | New Schedule page (was: Trigger->Schedule) | click `pipeline-schedules-section-add`; assert URL ends `/schedules/create…`, breadcrumb-current "New Schedule", **no pipeline PUT** (keeps the old "no auto-save" check) | changed flow |
| 3 Modal elements | summary, mode radio, Every/on/at, helper, Cancel/Apply | summary (default "Runs every week at 00:00 on Saturday."), Builder+Cron tabs, 4 cron selects (period/weekdays-week/hour/minute), Cancel, Save; Pipeline locked, Version preselected, fill Name | changed (Apply->Save) |
| 4 Every=day hides "on" | 3 selects | `schedule-cron-weekdays-select-week` count 0 (and cron-select total 3) | covered |
| 5 09:30 + summary | dynamic | `Runs every day at 09:30.` exact | covered, new string |
| 6 Advanced -> cron input | shown | Cron Expression tab; input value `30 9 * * *` (carry-over, existing assertion kept) | covered |
| 7 back to Default | dropdowns return | Builder tab; 3 selects back; summary unchanged | covered |
| 8 Apply -> modal closes, Trigger "Schedule" | persisted type=schedule, cron 09:30 | Save; response 201 `cron` split -> minute `30` hour `9`; navigated back to pipeline; **card appears** with rule line "At 09:30" | changed |
| 9 Save pipeline, reload, persists | schedule persists, cron round-trips | reload; card `rule` still "At 09:30"; Save of pipeline stays disabled | covered |
Axis 2 (beyond the case, each justified): the 201 body `cron` (existing spec asserted the PUT body — same strength); card `state` "Active" (cheap, proves enabled); cleanup — the pipeline delete cascades the schedule (verified: pipeline deleted with a schedule attached, no residue seen in the list API afterwards — `GET …/schedules/prompt_lib/575` rows 0).

## Implementer notes
- Add class-level declarations (ladder) for the new page; a new page object is reasonable (`ScheduleFormPage` in `automation/pages/`) with testids above; the SCHEDULES section add button/cards belong on `PipelineDetailPage`. Schedule id for the card handle: read from the 201 response `id` (or a `ScopedLocator` `pipeline-schedule-card-{}`).
- `ScopedLocator`s needed for the cron option rows: `role=option name="{}"` exact (open-listbox scoped, one listbox at a time).
- Update TMS case ELITEA-2007 text to the SCHEDULES-section flow (the card asks for it); the case file lives in onetest-ai-tm-Elitea — orchestrator-owned.
