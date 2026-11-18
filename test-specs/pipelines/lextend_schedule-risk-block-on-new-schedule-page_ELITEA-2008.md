# Extension AFS: Entry Point Node — schedule blocked by Printer/HITL/interrupt (schedule part moves to the New Schedule page)

## Metadata
- **TMS ID**: ELITEA-2008 (card #2981, ADJUST — schedule part only; keep the same 4 checks in the same order)
- **Status**: extend-existing
- **Covering spec**: `automation/tests/ui/pipelines/test_pipeline_entry_point_trigger_restricted_interactive_nodes.py:test_entry_point_trigger_restricted_interactive_nodes` (merged to main). Its Webhook/Chat-Message Trigger-dropdown assertions are UNCHANGED in the brief ("schedule part only") — see Open question 1 on how it currently stands on DEV.
- **Environment explored**: DEV `https://dev.elitea.ai/app`, 2026-11-18, 5 pipelines
- **surface_key**: `pipeline-schedules-section`
- **Known defect**: #2984 (interrupt not blocked) — drives step 3, see below. Per `testing.md` § Merge gate / Analysis-time entry: classified `extend-existing` with a declared improvisation, not `defect-found`.
- **Prior AFS**: `l3_entry-point-trigger-restricted-interactive-nodes_ELITEA-2008.md`

## Overlap argument
The existing spec already builds the exact lifecycle: add Printer, Save, remove, add HITL, Save, remove, YAML `interrupt_before`, Save, clear, Save, reload. All of it stays. What changes is the OBSERVABLE: the Trigger dropdown (Schedule option disabled) is replaced by the New Schedule page's risk box + disabled Save. The un-saved-canvas check (Step 3 of the existing spec: restriction keyed on the saved YAML) carries over: the risk check reads the saved version, so a Printer that is on the canvas but not saved must show no box (re-verify in the implementation run; analysed with saved-state only).

## Flow, verified live (each state executed; 2 pipelines for Printer/HITL, 3 for interrupt)
Observation sequence per state: pipeline editor -> `pipeline-schedules-section-add` -> create page -> wait ~3-5 s for the risk check (`POST …/schedules/prompt_lib/<project>/check`) -> read.

| State (SAVED version) | Risk box `schedule-risk-block-box` | Save | "Fix the risk check to save" | `/check` response |
|---|---|---|---|---|
| baseline (LLM only) | absent | enabled once Name typed | absent | `blocking: []` |
| 1 Printer after entry | present: "This pipeline asks a person for input at step 'Printer 1'." / "Scheduled runs can't answer it." / "You can't save this schedule." / "Remove the human-input step, or run the pipeline from the chat." / link "Open pipeline to change steps" | `disabled` + `aria-disabled=true` (even with a Name) | present | `blocking[code=human_input_step]` |
| 2 HITL (Printer removed) | present, same text, step 'HITL 1' | disabled | present | same |
| 3 interrupt_before `[Code 1]` (Code node added, YAML edited, saved, reload shows key) | **ABSENT** | **enabled**, schedule saves (201) | absent | `blocking: []` — **#2984** |
| 3b `interrupt_after: [LLM 1]`, and `interrupt_before` on the entry node | absent | enabled | absent | `blocking: []` — same defect |
| 4 all removed | absent | enabled | absent | `blocking: []` |

Step wording: Printer text says "at step 'Printer 1'" and, when several human-input steps exist, "and N more step(s)" (`… 'Printer 1' and 2 more steps.`). Assert the stable prefix "This pipeline asks a person for input" + the other four lines, not the node name tail or counts (node names are auto-numbered and accumulate across edits).

"Open pipeline to change steps": `role=link`, **`target=_blank`**, href `https://dev.elitea.ai/app/<projectId>/pipelines/all/<pipelineId>/<versionId>?viewMode=owner…` — opens the editor in a NEW TAB (page `context.expect_page()`), canvas renders there (`rf__wrapper` present). The brief's "click link -> replace Printer" therefore edits in the popup page; the original create page stays open. Implementer: either do the edit on the popup (faithful to the brief) and then re-open "+ Schedule" from it, or assert the link's `href`/opening and continue on the original page. Both are acceptable provided the link click itself is exercised once (Step 2).

## Step 3 — declared improvisation + known defect (#2984)
Brief expects a block for interrupt; DEV does not block it. Per the project's analysis-time sanctioned-RED rule (deterministic 3/3 across 3 pipelines, single cause, filed): write the assertion as the CORRECT behaviour (box present, Save disabled, hint present) with `expect.soft()` / `pytest_check` style and `# Known defect: #2984`. The step-3 observable is still driven (YAML edit, save, "+ Schedule") so the tail of step 4 stays covered. If the product ruling says "interrupts never block", rewrite the case instead (the lead decides on #2984). No `skip`, no weakened assert.
Note the old spec's Step 7 (Trigger dropdown disabled for interrupt) used the Trigger select; with the schedule part removed it is now the Webhook disabled check only.

## Open questions for the lead
1. The Trigger dropdown now lists only "Chat Message" (`get_trigger_option_states()` -> `{'chat_message': True}`, `get_trigger_options()` -> `['Chat Message']`) — Webhook is also gone from the entry-node dropdown on DEV. The existing spec's `ALL_OFFERED_ENABLED = {"chat_message": True, "webhook": True}` therefore also fails (the file's own comment says Schedule left; Webhook seems to have followed, same redesign — webhooks now live in a WEBHOOKS section next to SCHEDULES, "+ Webhook"/"Manage Webhooks"). The brief says "schedule part only" and "Do not add or drop coverage"; the Webhook-restriction check as written cannot pass, and re-pointing it to the WEBHOOKS section is beyond this brief. Disposition: clarification #2985 filed (question, not filed as a bug: it's the same intentional redesign). Implementer should keep the Chat-Message-only half and NOT silently drop the Webhook assertions without the lead's okay.
2. Whether the "unsaved Printer has no effect" check (old Step 3) should be re-asserted against the page's risk box: recommend yes (open the page right after adding the Printer without saving: the risk check is version-based, so no box) — verify in the first implementer run.

## Handles Reference
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| + Schedule | testid | `pipeline-schedules-section-add` | — | on DEV ✓ |
| Risk block box | testid | `schedule-risk-block-box` (yellow variant `schedule-risk-wait-box` is a different state) | — | on DEV ✓ |
| Risk title/intro/outro lines | none | text inside the box (`get_by_text` scoped to the box; keep prefix-based) | `schedule-risk-block-message-text` | ladder — no testid on DEV |
| "Open pipeline to change steps" | role+name | `role=link name="Open pipeline to change steps"` scoped to the box, `target=_blank` | `schedule-risk-block-open-pipeline-link` | ladder — no testid on DEV |
| Save | testid | `schedule-save-button`; blocked state = `disabled` (use `to_be_disabled`; `aria-disabled=true` also set) | — | on DEV ✓ |
| Hint | text | "Fix the risk check to save" (beside Save; `id=schedule-risk-hint`, referenced by Save's `aria-describedby`) | `schedule-risk-hint-text` | ladder — `css=#schedule-risk-hint` is unique and stable; use as rung 4 |
| Name input | role+name | `role=textbox name="Name"` | `schedule-name-input` | ladder |
| Create-page ready signal | testid | `schedule-save-button` visible, then wait for the risk check response (`/check` 200) rather than sleeping | — | — |

Existing page-object reuse (for the pipeline edits): `add_node("Printer"|"Human-in-the-loop"|"Code")`, `delete_node(id)`, `set_interrupt_before_via_yaml(id)`, `clear_interrupt_before_via_yaml()`, `save_and_wait_for_update(project_id, pipeline_id)` — all verified working on DEV today (transit). Quirk: with the node panel open the left column collapses; after `save_and_wait_for_update` call `close_node_panel()` and, if `pipeline-schedules-section-add` is absent, `config_panel_collapse_button` before clicking "+ Schedule". Also dismiss BOTH `platform-banner-close` buttons before `delete_node` (the corner banner intercepts the delete click).

## Coverage Map (Axis 1)
| Case element | Expected | Covered by | Disposition |
|---|---|---|---|
| 1 Printer after entry | schedule blocked | state 1 above: box text, Save disabled, hint | changed observable |
| 2 (case steps 5) HITL replaces Printer | same block | state 2 | changed observable; "Open pipeline to change steps" exercised here |
| 3 (case step 6) interrupt via YAML | same block | state 3 — **#2984**, soft-asserted | known defect |
| 4 (case step 7) all removed | no box, Save enabled | state 4 (+ reload) | changed observable |
| Webhook-disabled / Chat-and-Webhook-enabled (case steps 4-7, Trigger dropdown) | Webhook disabled while restricted | Chat-Message-only enabled asserted at baseline (live contract, Step 1); Webhook option no longer exists on DEV | clarification — out of scope (Webhook left the dropdown; case-text drift filed as #2985, declared per reverse-masking guard) |
| Console errors | none | existing guard (none observed during the new flow) | kept |
