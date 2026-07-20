---
name: Chat participants version_id mixup fires at participant-SWITCH time, not just Send (#684 refinement)
description: Live-confirmed the stale version_id race documented in #684 actually fires the instant a pipeline becomes the active participant while an agent was previously active — Send was only ever an incidental later trigger, not the cause. Same field (entity_settings.agent_type) that badge-grouping relies on is what onSelectVersion mutates, giving a concrete no-crash mechanism for badges silently misclassifying instead of #684's crash.
type: feedback
---

Discovered while investigating two non-enumerated 4th-failures the orchestrator found on
its merge-gate runs of `test_add_agent_pipeline_toolkit_mcp_participants_and_verify_panel`
(ELITEA-2094, PR #688): a Step 9 nav-crash whose captured signature did NOT match #684's
documented one, and a Step 10 "agents" badge vanishing after a *successful* Send.

- **Ran the spec fresh 8× via pytest**: 6 clean, 1 hit a THIRD new variant (Step 3 hard-fail,
  "Pipelines badge should appear after adding a pipeline participant" — composer correctly
  switched to the pipeline's name but the pipelines badge itself never rendered). Neither of
  the orchestrator's 2 exact anomalies reproduced in my 8 runs — this whole area is genuinely
  intermittent, not flaky-in-a-fixable way.
- **Reproduced the underlying mechanism live, manually, outside pytest** (fresh agent + fresh
  LLM pipeline via API, added as participants via Playwright MCP in project 399, not via the
  test file). Network capture showed, the INSTANT the pipeline becomes the active participant
  (composer switches to "Switch Pipeline"), BEFORE any message is sent:
  ```
  GET .../version_validator/prompt_lib/399/{pipeline_id}/{pipeline's OWN version_id} → 200 (correct)
  GET .../version/prompt_lib/399/{pipeline_id}/{the AGENT's version_id}             → 400 (stale/wrong id reused)
  ```
  with the same `TypeError: Cannot read properties of undefined (reading 'icon_meta')` at
  `ChatBox.jsx` #684 already documents. **This refines #684's own text**: the mixup is NOT
  Send-specific — Send was only ever an incidental *later* trigger because it commonly follows
  a participant switch. The race itself looks close to 100% (fired on my one live trial);
  what's actually intermittent is its BLAST RADIUS.
- **Crucially, that same trial caused zero visible damage**: Send still succeeded, both
  badges stayed correct, and a direct backend `ConversationAPI.get_conversation()` GET on the
  persisted conversation confirmed both participants' `entity_settings.agent_type`/
  `version_id` were fully correct server-side. So the crash can be completely absorbed with no
  symptom at all — consistent with #684's own "~1/5" framing, but now with a concrete
  mechanism for WHY the outcome varies: it depends on which async callback's result wins the
  race, not on whether the race happens.
- **Concrete no-crash escalation path (source-traced, not directly reproduced)**: agents-vs-
  pipelines badge grouping (`CollapsedPerticapantsList.jsx`) is keyed SOLELY off
  `entity_settings.agent_type` (`'pipeline'` vs anything else). `ChatBox.jsx`'s
  `onSelectVersion` conditionally copies `agent_type` from the fetched `versionDetails` onto
  `entity_settings` (`...(activeParticipant?.entity_name === 'application' &&
  versionDetails.agent_type && { agent_type: versionDetails.agent_type })`). If the
  wrong-participant's version fetch resolves successfully instead of 400ing (plausible —
  version ids from the SAME "applications" table, per `PipelineAPI`'s own docstring:
  "Pipelines share the `application` API endpoints with agents... the only difference is
  `agent_type` in the version payload"), this silently propagates the WRONG participant's
  `agent_type` onto the RIGHT one's `entity_settings` — reclassifying a badge into the wrong
  section with no crash at all. This is the best candidate mechanism for both Step 10's
  badge-vanish and Step 3's badge-miss variants, and for #689's own "not yet root-caused"
  picker-exclusion gap (same `entity_settings.agent_type` field, same
  `getChatParticipantUniqueId` discriminator).
- **Data-pollution check (routed as infra note, not a defect)**: project 399 held 2 stale
  orphaned `autotest_test_add_agent_pipeline` agents, 1 orphaned pipeline, 2 orphaned
  `autotest-art-*` toolkits, and 1 empty "New Chat" conversation, all ~16:42/18:45/18:46 that
  day, predating this session. My own 8 pytest runs + 1 manual repro left ZERO new orphans,
  and every delete (including MCP/artifact toolkits) succeeded with no permission errors — the
  orchestrator's one-off "403 models.applications.tool.delete" did NOT reproduce; most likely
  a hard process-kill mid-run on one of the 2 historical occasions (one orphan cluster
  includes a pipeline, which is created inline in the test body, not a fixture — implying that
  whole process died before fixture teardown ever got a chance, not a graceful failure).
- **Separately, 100%-reproducible-but-unrelated noise**: `artifact_bucket` fixture's own
  explicit `delete_bucket(name)` 404s on every single run, because the (torn-down-first)
  `artifact_toolkit` fixture's delete already cascades the bucket away. Harmless
  fixture-ordering redundancy, not test-data pollution, not touched.
- Posted refined evidence to #684 (comment
  https://github.com/EliteaAI/elitea-testing-public/issues/684#issuecomment-5026383880) and
  cross-linked the Step-3 variant to #689 (comment
  https://github.com/EliteaAI/elitea-testing-public/issues/689#issuecomment-5026388178) as a
  root-cause lead, rather than filing new tickets — verdict was "same underlying defect
  family," not independent new defects.
