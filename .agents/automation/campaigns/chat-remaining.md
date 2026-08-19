# Campaign: chat-remaining

## Tracking issue
elitea-testing-public#1393 — "[Automate][chat] 127 remaining test cases to automate"

## State
- Stage: **IN PROGRESS — wave-01 starting**
- Conductor: none — plain sequential `batch-build` waves. Foundation is null and already
  evidenced: `automation/pages/` has 4 chat page objects (`chat_page.py`,
  `chat_canvas_page.py`, `chat_diagram_canvas_page.py`, `chat_table_canvas_page.py`) and
  `automation/tests/ui/chat/` has 33 existing test files. Per `campaign-planning.md`
  § When NOT to run a campaign, the full conductor apparatus is skipped; card + waves
  still used because the backlog (127) is far over 2×M.
- Operator checkpoint: **substituted** — factory/unattended mode has no interactive
  `AskUserQuestion`. The operator's own comment on #1393 ("group similar ones into
  larger batches — maybe 4-12 cases per implementation group... several waves fine")
  is the standing plan approval, same pattern as `pipelines-remaining` (#1297) and
  `skills-remaining` (#1399). Documented here for a human to override at any point by
  commenting on #1393.
- Foundation merged: n/a — foundation is null (see Conductor note)
- Intake re-verification (2026-08-14, card generated 2026-08-09 — 5 days stale):
  - All 127 TMS case files re-checked directly (`onetest-ai-tm-Elitea`, fresh `git fetch`):
    still `status: draft`, `execution_type: manual`, no `automation_test_id` on any of
    the 127. **0 already-automated.**
  - Re-ran the card's dedup command (`gh issue list --state all --limit 300`) against
    this repo: **0 of the 127 IDs appear in any existing issue title.** No cards filed
    since 2026-08-09.
  - Cross-checked `test-specs/` and `.agents/automation/*/report.json`: two incidental
    content hits (ELITEA-2079's AFS *mentions* ELITEA-2078 as an unautomated sibling
    precondition; `elitea-2042-pipeline-state-panel/report.json` lists ELITEA-2077 in
    a `case_ids` field for `test_pipeline_flow_editor_add_llm_node_from_chat_canvas.py`,
    a test **merged to `automation/base`** that is currently sanctioned-RED on a known
    defect (#1039) — but ELITEA-2077's own TMS case file was never back-written).
    **Flagged for wave-16 (canvas-creation, contains ELITEA-2077/2078)**: the analyst on
    that wave MUST check `test_pipeline_flow_editor_add_llm_node_from_chat_canvas.py`
    first — this may be `already-covered` or `extend-existing` rather than net-new, and
    if so the missed back-write should be corrected as part of that wave's close.
  - **Verdict: exclusion list is clean, all 127 are live candidates.**
- Sync: `sync-base-branches` run fresh at campaign start. `automation/base` had 0 drift
  from `main` (pushed local memory-log commit only). EliteaUI `automation/testids` and
  `elitea_assistant automation/testids` both already fully in sync with their `main`s
  (0 behind, 0 ahead-untracked). No merge occurred on either UI repo — testid-loss guard
  N/A this cycle. Dev server confirmed live (`localhost:5173` → 200).

## Plan — 16 waves, clustered by feature sub-area (all 127 cases, verified 1:1 partition)

| Wave | Theme | Case IDs | N | Status |
|---|---|---|---:|---|
| 01 | Conversation entry / navigation into existing conversations | 2091,2093,2096,2097,2098 | 5 | **LANDED** — PR #1512, 3 automated / 2 blocked (question #1511) |
| 02 | Conversation rename — basic flow + length boundaries | 2099,2100,2101,2102,2103,2104 | 6 | **LANDED** — PR #1518, 6/6 automated |
| 03 | Conversation rename — check-icon states + edge chars | 2105,2106,2107,2108,2109,2110,2111,2112,2113 | 9 | **LANDED** — PR #1522, 9/9 automated |
| 04 | Conversation deletion + chat search (left-panel micro-UI) | 2115,2116,2117,2456,2163,2164,2165,2463 | 8 | **LANDED** — PR #1528, 7 automated/extended + 1 already-covered |
| 05 | Folder creation | 2118,2119,2120,2133,2134,2457 | 6 | **LANDED** — PR #1532, 6/6 automated |
| 06 | Folder rename | 2121,2122,2123,2124,2125,2126,2127,2128,2129,2130,2131 | 11 | **LANDED** — PR #1539, 7 automated/extended + 4 already-covered |
| 07 | Move/drag conversation between folders + list scrolling | 2136,2138,2139,2140,2141,2142,2143,2144,2145,2146,2147,2148 | 12 | **LANDED** — PR #1545, 11/12 automated + 1 blocked (#1541) |
| 08 | Pin/unpin — conversation & folder basics | 2150,2151,2152,2153,2154,2155,2156 | 7 | **LANDED** — PR #1552, 7/7 automated |
| 09 | Pin/unpin — edge cases + newer duplicate-family cases | 2157,2158,2159,2160,2161,2461,2462,2460 | 8 | **LANDED** — PR #1555, 4/8 automated + 4/8 already-covered |
| 10 | Team Project — participants management | 2169,2171,2172,2173,2174,2175,2176 | 7 | **LANDED** — PR #1561, 5/7 automated + 2/7 already-covered |
| 11 | Team Project — public conversation / non-owner restrictions | 2188,2189,2190,2191,2192,2193,2194 | 7 | **LANDED (partial)** — PR #1566, 2/7 automated + 2/7 already-covered + 3/7 blocked (#1563) |
| 12 | Message input + generation controls (stop/regenerate/send-button/starters) | 2177,2178,2179,2182,2183,2184,2185,2186,2187,2465,2466 | 11 | **LANDED (partial)** — PR #1586, 8/11 automated + 3/11 blocked (#1569) |
| 13 | File attachments | 2195,2196,2198,2199,2201,2467 | 6 | **LANDED** — PR #1595, 6/6 automated |
| 14 | Slash commands / # mentions / MCP dropdown | 2205,2206,2207,2208,2468,2469,2470 | 7 | **LANDED** — PR #1601, 7/7 automated (2 merged sanctioned-RED, #1596) |
| 15 | Tool call/output rendering + HITL + context management | 2209,2210,2216,2217,2471,2472,2473,2474 | 8 | pending |
| 16 | Canvas creation (agent/pipeline/toolkit/MCP from conversation) — check ELITEA-2077 already-covered first | 2073,2074,2076,2077,2078,2081,2083,2084,2089 | 9 | pending |

**Total: 127/127, verified unique + complete partition (no gaps, no dupes).**

## Waves landed

- **wave-01 LANDED** — elitea-testing-public#1512, merged (`406883d1`). 3/5 automated
  (ELITEA-2091 #1508, ELITEA-2093 #1509, ELITEA-2098 #1510); 2 blocked (ELITEA-2096/2097
  — genuine test-data-age gap, no honest seed path per `.agents/testing.md` § Fidelity
  policy, routed to question elitea-testing-public#1511 for a human decision, NOT
  parking the campaign). Lead's own gate: 3/3 green (165s/138s/258s; run 3's one
  transient rerun on ELITEA-2093 matched the project's standing pytest.ini
  `--only-rerun` transient-infra allowlist — not a new flake). TMS back-written (3
  cases, Form C verified against junit.xml + surgical index.json by-path edit, NOT
  `build_index` — see `build_index_regression_must_be_reverted_not_carried.md`). New
  testid: `chat-composer-dropzone` (EliteaAI/EliteaUI@dd417746 on `automation/testids`,
  confirmed NOT yet on `main` via fresh fetch — awaiting human cherry-pick).

- **wave-02 LANDED** — elitea-testing-public#1518, merged (`485231ea`). 6/6 automated
  (ELITEA-2099 #1514, ELITEA-2100 #1515, ELITEA-2101/2102 #1516, ELITEA-2103/2104
  #1517). Internal gate went red 1/2 on ELITEA-2104 (non-reproducing console 500 on
  an unrelated resource, not the rename PUT) — investigated: 4 standalone clean runs
  + lead's own 3/3 clean full-set gate = 7 consecutive clean after 1 occurrence,
  classified transient noise, recorded in `.agents/testing.md` § Unconfirmed (not a
  defect ticket — nothing reproduced to file). Case-text drift on ELITEA-2099 already
  covered by question elitea-testing-public#1513 (sibling of #695). TMS back-written
  (6 cases; parametrized 2101/2102 ids quoted to dodge the known bracket-stripping
  YAML bug). New testids: `chat-conversation-name-input`,
  `chat-conversation-name-confirm-button` (+`data-disabled`),
  `chat-conversation-name-cancel-button` — EliteaAI/EliteaUI@ff56e29d on
  `automation/testids`, confirmed NOT yet on `main`.

- **wave-03 LANDED** — elitea-testing-public#1522, merged (`ec634072`). 9/9 automated:
  ELITEA-2105-2109 cluster (#1519, 1 fix round — dead console-error instrumentation,
  fixed + re-reviewed APPROVED), ELITEA-2110/2112/2113 cluster (#1520), ELITEA-2111
  `extend-existing` onto #1520's spec as a 3rd parametrize row (#1521). Lead's own
  gate: 3/3 clean, 9/9 node-ids every run (230s/215s/200s). TMS back-written (9 cases,
  parametrized ids quoted). New testid: `chat-conversation-name-confirm-tooltip-content`
  — EliteaAI/EliteaUI@888dac13 on `automation/testids`, confirmed NOT yet on `main`.
  **Process fix applied:** the `.agents/automation/chat-remaining-w0N/cases/` intake
  snapshot dir was never written for w01-w03 (lead's own gap, not a workflow bug —
  went straight from the card's table to clustering); zero drift found each time the
  analyst fell back to a live TMS fetch, but fixed properly starting wave-04 (case
  bodies copied from the TMS sibling clone into `.../chat-remaining-w04/cases/` before
  dispatch).

- **wave-04 LANDED** — elitea-testing-public#1528, merged (`778d02a8`). 7/8
  automated/extended (ELITEA-2115/2116/2117 #1524, ELITEA-2163/2164/2165/2463
  #1527) + 1 already-covered (ELITEA-2456, Rule-6 dedup onto ELITEA-2114's merged
  spec PR #696 — blind-audited by the lead against the actual merged code per
  the batch's own 5/8 extend-rate quality flag, citations verified accurate).
  Two sanctioned-RED-by-design cases (ELITEA-2117→#1523, ELITEA-2163→#1525), both
  real filed open product bugs. Gate investigation: (1) root-caused and cleaned 6
  stray same-prefix conversations left by the implementer's own earlier debug runs
  (verified live via direct API query, not guessed) that were breaking ELITEA-2165's
  count assertion; (2) one non-reproducing toast-timing flake on an unrelated
  pre-existing spec, recorded in `.agents/testing.md` § Unconfirmed. Lead's own gate:
  2 back-to-back clean pairs, exact sanctioned-RED signature both times. TMS
  back-written (8 cases + reciprocal "Also satisfies" note on ELITEA-2114). New
  testids: `chat-search-no-results-message`, `chat-conversations-empty-state-message`
  — EliteaAI/EliteaUI@d5e0ba63 on `automation/testids`, confirmed NOT yet on `main`.

- **wave-05 LANDED** — elitea-testing-public#1532, merged (`58e1d93f`). 6/6
  automated, all `extend-existing` (ELITEA-2118 #1529, 2119+2120 #1529 [1 fix
  round — POM construction-site violation], 2133+2134 #1530, 2457 #1531 —
  2119/2133/2457 share one test, 2120/2134 share another). Confirms (3rd
  instance) this TMS module carries near-duplicate case-ID clusters not
  confined to adjacent ranges — durable memory updated. Gate: 3rd occurrence
  of the recurring console-500 pattern (wave-02/wave-04/wave-05), formally
  confirmed as environmental in `.agents/testing.md`. Lead's own gate 3/3
  clean. TMS back-written (6 cases). No new testids.

- **wave-06 LANDED** — elitea-testing-public#1539, merged (`79ce975b`). 7/11
  automated/extended (ELITEA-2121/2130 #1535 [1 fix round], ELITEA-2122 #1536,
  ELITEA-2125/2131 #1537, ELITEA-2128/2129 #1538 [net-new]) + 4 already-covered
  (ELITEA-2123/2127 → ELITEA-2459, ELITEA-2124/2126 → ELITEA-2458). Real
  regression found+fixed: FolderItem.jsx's Rename menuitem lost its testid to
  an unrelated main commit (#764), confirmed via a LIVE pre-fix failure of the
  already-merged ELITEA-2458 test — filed+fixed #1533 (sibling of #1309),
  case-text drift filed #1534. **Process gap, self-caught and logged:** manual
  gate (workflow's own gate was cut off) was scoped from memory instead of
  `git diff --name-only`, missing `test_chat_folder_rename_length_boundaries.py`
  (ELITEA-2128/2129) — merged before gating those 2; caught during TMS
  back-write, verified 3/3 clean immediately after (code was fine, process
  wasn't) — new durable memory entry written
  (`manual_gate_must_discover_touched_files_via_diff_not_memory.md`). TMS
  back-written (11 cases). Testids `chat-folder-menu-rename`/`-pin` (restored)
  confirmed NOT yet on `main`.

- **wave-07 LANDED** — elitea-testing-public#1545, merged (`d2b5d1a`). 11/12
  automated (ELITEA-2136/2138/2139/2140/2141 #1540, ELITEA-2142/2143/2145 #1543
  [recovered], ELITEA-2146/2147/2148 #1544) + 1 blocked (ELITEA-2144 — real open
  bug #1541, folder→folder drag-drop lands in ungrouped list, 3× pristine repro).
  2139/2140 share one test (`TestMoveConversationBackToList`). Canon-gap question
  #1546 filed distinguishing ELITEA-2140's precondition-as-narrative pattern
  (automated) from wave-01's precondition-as-observable pattern (blocked). Two
  more defects: #1533 (folder Rename menuitem testid regression, fixed same
  session, sibling of #1309) and #1542 (drag-drop success-toast — filed then
  self-corrected mid-triage: toast does fire via a different hook path than
  first examined, left OPEN for human disposition rather than silently closed).
  **Two process incidents, both self-caught and logged:** (1) PR #1543's second
  internal review pass crashed on a harness bug (`StructuredOutput retry cap
  exceeded`) after the one real reviewer finding had already been fixed; the
  workflow's report writer mechanically labelled the 3 cases "blocked" on that
  crash — not accepted at face value, verified the PR was still open with the
  fix present, dispatched a fresh qa-engineer review, got `APPROVED` 0-blocking,
  merged. (2) 3-way merge conflict during the trunk merge — 2 memory daily-logs
  spliced directly (allowed path), `automation/pages/chat_page.py` (forbidden
  path — two independent non-overlapping `LocatorDescriptor` additions at the
  same insertion point) dispatched to test-automation-engineer for resolution,
  verified clean before completing the merge myself. Gate: 11 node-ids, 3 full
  independent runs; 1 flake on `test_drag_drop_conversation_back_to_general_list`
  (`data-drop-active` hover-highlight timing race), not reproduced standalone or
  in 3 subsequent clean full-set runs — recorded in `.agents/testing.md` §
  Unconfirmed. TMS back-written (11 cases; ELITEA-2144 deliberately left
  `draft`/`manual`, blocked by #1541). New testids: `chat-folder-drop-zone`,
  `chat-conversation-list-drop-zone` (+`data-drop-active`),
  `chat-conversation-list-scroll-container`, `chat-move-to-submenu-popover` —
  EliteaAI/EliteaUI@86f4a564 + @1787ad67 (+rewired @1b35a0a2) on
  `automation/testids`, confirmed NOT yet on `main`.

- **wave-08 LANDED** — elitea-testing-public#1552, merged (`fb306056`). 7/7
  automated (2/7 ready-for-automation: ELITEA-2152/2153; 5/7 extend-existing:
  ELITEA-2150/2151/2154/2155/2156). Quality-flag response: extend-rate 5/7 >
  0.5 triggered the workflow's own audit requirement; blind-audited 2 of the
  5 extend-existing conclusions myself against case text + merged diff before
  trusting the batch (ELITEA-2151's 4-tier panel-order claim, ELITEA-2154's
  plural-conversations claim onto ELITEA-2152's single-conversation test) —
  both genuine, sound. Gate: 2 non-reproducing console-404 flakes across the
  lead's own 3 independent full-set attempts (different tests each time,
  byte-identical message text), classified as a new flavor of the project's
  known background-resource noise class (distinct from the confirmed 500
  bucket, tracked separately) — 3 consecutive clean full-set runs followed
  before merge. Recorded in `.agents/testing.md` § Unconfirmed. No new
  testids (surface already covered by wave-06). TMS back-written (7 cases).

- **wave-09 LANDED** — elitea-testing-public#1555, merged (`9fb2d9d9`). 4/8
  automated (ELITEA-2157/2158 family, ELITEA-2160, ELITEA-2161) + 4/8
  already-covered (ELITEA-2159→2151, ELITEA-2461→2149+2151 combined — first
  case needing 2 covering specs, ELITEA-2462→2152 word-for-word TMS-side dup,
  ELITEA-2460→2148 wave-07). Real product fix: "Duplicate" context-menu item
  (`ConversationItem.jsx`) was the only item in its 7-item menu array missing
  a `key` prop, leaving it testid-invisible — added
  `key: 'chat-conversation-menu-duplicate'` (composes to `-menuitem` at
  runtime via `DotMenu.jsx`), `EliteaAI/EliteaUI@a53b9d4b`. Reviewer caught a
  real AFS/diff drift (AFS claimed "no new testids" while the shipped test
  depended on this one) in round 1, fixed round 2. Quality-flag response:
  extend-rate 6/8 — blind-audited 2 already-covered conclusions myself
  (ELITEA-2462 vs 2152, ELITEA-2159 vs 2151), both genuine. Gate: 3rd
  occurrence of the wave-08 404 console-noise flake (same test both times,
  byte-identical message) — promoted from suspected to confirmed recurring
  pattern in `.agents/testing.md`. 3 consecutive clean 11/11 full-set runs
  before merge. New testid: `chat-conversation-menu-duplicate` — confirmed
  NOT yet on `main` (composed-testid grep caveat applied — base key, not the
  rendered `-menuitem` suffix). TMS back-written (8 cases).

- **wave-10 LANDED** — elitea-testing-public#1561, merged (`84651741`). 5/7
  automated (ELITEA-2172, 2173, 2174, 2175, 2176) + 2/7 already-covered
  (ELITEA-2169→2167, ELITEA-2171→2168). First case touching Team Project
  participants. **Workflow's internal gate was cut off mid-run** (0/3 banked,
  5 units landed as `merged-ungated`, not failed) — resolved by running my
  own independent gate directly rather than re-poking the cached workflow.
  During that gate, hit + root-caused 2 real regressions on the PRE-EXISTING
  ELITEA-2167 test (collateral gate scope, not one of wave-10's own cases):
  (1) deterministic badge-visibility failure, soft-asserted + linked to
  already-open #1082 (dispatched fix-only, not done by me directly per the
  no-code-edits guardrail); (2) a second symptom (dropdown search timeout)
  root-caused live as the SAME #1082 mechanism — search correctly excluding
  an already-participant user off a stale landed conversation — fixed by
  swapping to the stronger `_open_genuinely_blank_conversation()` guard.
  3 distinct conversation-timing flakes total across 2 full-set gate
  attempts, none reproducing standalone — new session-level heavy-load noise
  category recorded in `.agents/testing.md` (6+ continuous hours of chat
  churn this session). 3 consecutive clean 6/6 full-set runs before merge.
  No new testids (fully reused from ELITEA-2167/2168). TMS back-written
  (7 cases).

- **wave-11 LANDED (partial)** — elitea-testing-public#1566, merged (`28aad778`).
  2/7 automated (ELITEA-2188, ELITEA-2193) + 2/7 already-covered
  (ELITEA-2192→2172, ELITEA-2194→2168 Step 10, same target as ELITEA-2171) +
  3/7 genuinely blocked (ELITEA-2189/2190/2191 — no second test-user credential
  exists on localhost; every conversation in Team project 471 confirmed live
  via API to share one `author_id`; blocks any future "user B cannot see/edit/
  delete user A's X" case on any surface — routed to question #1563, NOT
  guessed around). Defect filed: #1564 (case-text clarification — owner-row
  delete control is permanently `visibility:hidden`, unreachable via real
  hit-testing; product is more protective than case text implies).
  **Workflow's internal gate cut off mid-run** (0/3 banked, `merged-ungated`) —
  resolved by running my own independent gate directly. During that gate:
  fixed 2 real regressions on pre-existing tests (collateral scope) — ELITEA-
  2188's own bare non-polling `is_visible()` dialog assertion, and ELITEA-2168's
  Setup swapped to the stronger `_open_genuinely_blank_conversation()` guard
  (same #1082 mechanism as wave-10). **New sanctioned-RED signature**: gate
  scope's pre-existing ELITEA-2168 test now deterministically fails on a
  soft-assert linked to already-open #1119 — confirmed identical 3/3 across 5
  independent gate attempts (1 non-reproducing console-500 blip in between,
  matching the already-documented noise pattern). Recorded explicitly in
  `.agents/testing.md`. **Process incident, self-caught:** two parallel
  fix-only dispatches collided on the shared working tree (both needed
  different branch checkouts in the same physical clone simultaneously) —
  recovered via `git stash`, zero work lost; logged as a durable lesson
  (never parallel-dispatch code-touching agents onto the same clone, even
  across different branches). New testids: `chat-conversation-make-public-
  confirm-dialog`/`-confirm-button`/`-cancel-button` —
  EliteaAI/EliteaUI@7292e18f on `automation/testids`, confirmed NOT yet on
  `main`. TMS back-written (4 cases; 2189/2190/2191 deliberately left
  `draft`/`manual`, blocked by #1563).

- **wave-12 LANDED (partial)** — elitea-testing-public#1586, merged (`157c46d9d`).
  8/11 automated: ELITEA-2177/2178/2465 (conversation-starters add/remove family,
  `test_chat_agent_starters_add_remove.py`, PR #1567 fix round 1 then merged into
  trunk), ELITEA-2179/2466 (composer send-button/waveform toggle family,
  `test_streaming_response.py`), ELITEA-2184/2185/2187 (regenerate exclusivity +
  click-replace family, `test_regenerate_response.py`, fix round 1). 3/11 blocked:
  ELITEA-2182/2183/2186 — all downstream of open defect **#1569** ("Stop wipes
  entire conversation", re-confirmed 4th/5th time this wave) and reclassified from
  an initial WIP `ready-for-automation` attempt to `blocked` because the failure
  hits each case's own headline Stop-button subject, not an isolated assertion
  (soft-assert-known-defect workaround doesn't cover the headline subject per
  `.agents/role-overrides.md` § Declared-improvisation protocol ceiling). Lead's
  own gate: 5 independent runs on the full 8-node-id set — run 1 clean 8/8, run 2
  hit the documented recurring console-500 noise pattern (7/8, 4th occurrence, no
  URL captured — recorded in `.agents/testing.md`), runs 3–5 clean 8/8 × 3
  consecutive. Trunk needed a large sync with `automation/base` before the PR
  (unrelated support-assistant/toolkit batch work had landed meanwhile) — 3 merge
  conflicts resolved (2 doc/memory, 1 real `chat_page.py` page-object conflict),
  re-verified 8/8 green post-merge. New testids: `chat-stop-generation-button`,
  `chat-message-sender-name`/`-avatar`, `chat-composer-focus-border`,
  `chat-voice-mode-button`/`-input-button`, `chat-conversation-starter-tile-tooltip`,
  `chat-switch-to-model-button` — all 6 confirmed NOT yet on `main` (pushed to
  `automation/testids`); 6 other referenced testids were already on `main`. TMS
  back-written (`3dcf7bb`, onetest-ai-tm-Elitea): 8 cases `ready`/`automated`;
  ELITEA-2182/2183/2186 left `draft`/`manual`, blocked by #1569. Also: this
  session hit the factory's own 3-session auto-park twice mid-wave (harness
  restarts during long-running dispatches, not stalled work) — recovered both
  times per protocol (board read `Approved` on check, resumed with no new
  steering needed).

- **wave-13 LANDED** — elitea-testing-public#1595, merged (`29e6dc831`). 6/6
  automated via `batch-build.workflow.mjs` (Task `w7cun7ws7`/`wuls3aaxi`, Run ID
  `wf_15496875-b7d`; workflow crashed once mid-gate-retry — StructuredOutput
  failure — resumed clean, all 6 units replayed from cache). Cluster
  `[2199,2467]` (attachment-preview family) confirmed genuine sibling pair, not
  duplicate. 2 clarification issues filed for case-text drift (not product
  bugs): #1589 (ELITEA-2196, "files begin uploading" — attach is 100%
  client-side, zero network at selection), #1591 (ELITEA-2199/2467, case
  implies type-specific icons — EliteaUI renders identical icon for every file
  type). Batch's own internal gate went RED once on ELITEA-2201 — an
  over-specified assertion (required ALL 4 attached filenames verbatim in the
  LLM's prose reply; the model engaged with every file's content but varied
  HOW it referenced each — not a product defect). Fixed via a per-file
  marker-list technique (`[filename, embedded content token, short
  paraphrase-resistant keyword]`, any-match per file) — iterated twice live
  before landing on short, paraphrase-resistant markers; verified 3 consecutive
  standalone green runs. Lead's own gate: 3/3 clean (102.44s/98.73s/100.53s).
  New testids (all 3 confirmed NOT yet on `main`, 2 of 3 runtime-composed —
  invisible to a literal grep, verified via file-diff instead per
  `.agents/workflow.md`): `chat-attach-menuitem-button-icon` (computed
  `${testId}-icon`, EliteaAI/EliteaUI@a17cb22d), `chat-attachment-remove-chip-
  {index}` (EliteaAI/EliteaUI@43b81dc8 + renamed @7f29c3dc to avoid a
  prefix-matcher collision), `chat-attachment-overflow-menu`
  (EliteaAI/EliteaUI@feb9101a). TMS back-written (`5daa238`): 6 cases
  `ready`/`automated`.

## In-flight run state (context-fragile — recorded immediately per doctrine)

- **wave-14 LANDED** — elitea-testing-public#1601, merged (`bceb5f8b5`). 7/7
  automated via `batch-build.workflow.mjs` (Task `waevrn93w`, Run ID
  `wf_6595674e-cc3`) — 5 clean + 2 merged sanctioned-RED (ELITEA-2205/2468's
  `test_select_mcp_from_slash_mention_no_tools_shows_empty_panel`, deterministic
  3/3, lead-verified independently, tied to open `bug` #1596: a zero-tools MCP
  still opens an empty "available tools" panel instead of hiding it —
  root-caused via source read of `SlashSuggestionList.jsx`'s hide-guard).
  Clusters `[2205,2468]`/`[2207,2469]`/`[2208,2470]` all confirmed genuine
  granularity-superset family pairs, not duplicates; 2206 standalone. Batch's
  `chat_page.py` diff carried a real, wide-blast-radius bug fix
  (`_is_transient_message()` whole-string → per-line prefix check, reached by
  `wait_for_ai_response()`/`wait_for_message_content_stable()` across 6
  non-chat spec files) — ran those 34 parametrized tests as a one-time
  regression check: 24 passed, 8 skipped (expected, no gitlab/bitbucket test
  data), 2 reruns recovered, 2 failures both `401 Bad credentials` from an
  expired `GIT_HUB_TOKEN` test-data credential (unrelated environment issue,
  no regression found). Lead's own gate: 3/3 clean on the 23-node-id main scope
  (~295-302s each) + 3/3 independently-verified identical sanctioned-RED
  signature. New testids (all 3 confirmed NOT yet on `main`, 1 of 3
  runtime-composed): `chat-hash-search-results-list` + dynamic
  `chat-hash-search-item-{project_id}_{id}` (EliteaAI/EliteaUI@7fe617e8),
  name/type/icon sub-testids (@840e251d + @58d30f08), `chat-participant-icon`
  (@dd44ce90). TMS back-written (`c04a2f8`): 7 cases `ready`/`automated`.

## In-flight run state (context-fragile — recorded immediately per doctrine)

- **wave-15** dispatching via `batch-build.workflow.mjs`. slug=`chat-remaining-w15`,
  base=`origin/automation/base`, cases 2209,2210,2216,2217,2471,2472,2473,2474
  (8), cluster `[2471,2472,2473]` (HITL authorize/block/block-with-comment —
  same interaction flow, 3 outcome variants, natural family); 2209, 2210, 2216,
  2217, 2474 standalone (2474 "complete flow from direct toolkit call in
  thinking step" may turn out family-related to 2209 during live analysis —
  not pre-clustered on title alone, left for the analyst to determine). Case
  snapshots at `.agents/automation/chat-remaining-w15/cases/`. All 8 confirmed
  still `draft`/`manual` in the TMS at intake (no dedup hits).
