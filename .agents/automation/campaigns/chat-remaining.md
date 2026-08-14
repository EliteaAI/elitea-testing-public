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
| 03 | Conversation rename — check-icon states + edge chars | 2105,2106,2107,2108,2109,2110,2111,2112,2113 | 9 | pending |
| 04 | Conversation deletion + chat search (left-panel micro-UI) | 2115,2116,2117,2456,2163,2164,2165,2463 | 8 | pending |
| 05 | Folder creation | 2118,2119,2120,2133,2134,2457 | 6 | pending |
| 06 | Folder rename | 2121,2122,2123,2124,2125,2126,2127,2128,2129,2130,2131 | 11 | pending |
| 07 | Move/drag conversation between folders + list scrolling | 2136,2138,2139,2140,2141,2142,2143,2144,2145,2146,2147,2148 | 12 | pending |
| 08 | Pin/unpin — conversation & folder basics | 2150,2151,2152,2153,2154,2155,2156 | 7 | pending |
| 09 | Pin/unpin — edge cases + newer duplicate-family cases | 2157,2158,2159,2160,2161,2461,2462,2460 | 8 | pending |
| 10 | Team Project — participants management | 2169,2171,2172,2173,2174,2175,2176 | 7 | pending |
| 11 | Team Project — public conversation / non-owner restrictions | 2188,2189,2190,2191,2192,2193,2194 | 7 | pending |
| 12 | Message input + generation controls (stop/regenerate/send-button/starters) | 2177,2178,2179,2182,2183,2184,2185,2186,2187,2465,2466 | 11 | pending |
| 13 | File attachments | 2195,2196,2198,2199,2201,2467 | 6 | pending |
| 14 | Slash commands / # mentions / MCP dropdown | 2205,2206,2207,2208,2468,2469,2470 | 7 | pending |
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

## In-flight run state (context-fragile — recorded immediately per doctrine)

(none — wave-02 closed; wave-03 not yet dispatched)
