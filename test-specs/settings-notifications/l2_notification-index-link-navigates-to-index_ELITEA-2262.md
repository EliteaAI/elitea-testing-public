# Test Case: Clicking an index notification link navigates to the correct index

## Metadata
- **TMS ID**: ELITEA-2262
- **Linked Story**: batch `settings-w02` (campaign EliteaAI/elitea-testing-public#1398)
- **Priority**: l2 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **Analyst**: qa-engineer (Sage), analyst slot, cluster ELITEA-2261/2262/2263, 2026-08-26
- **Status**: **blocked** — no `index_data_changed` notification on this account points at a
  surviving toolkit, and the environment cannot produce a new one.

## Why this is blocked (not a defect, not automatable today)

The mechanism itself is sound — `resolveHref()` builds
`{origin}/{project_id}/toolkits/indexes/{meta.toolkit_id}?index_name={meta.index_name}`
and the link renders correctly. What cannot be produced is a notification whose **target
still exists**.

**Every one of the 7 `index_data_changed` notifications on `${TEST_USER}`'s history is
stale** (verified live 2026-08-26, each navigated individually):

| Notification | Message | Toolkit id in href | Result of navigating |
|---|---|---|---|
| `49122` | Index **marian** is successfully created: `{"indexed": 60}` | 146 | 400 → redirected to the toolkits LIST |
| `45789` | Index **asd** is successfully created | 146 | (same toolkit) |
| `45712` | Index **otherac** is successfully created | 146 | (same toolkit) |
| `45708` | Index **new_ind** is successfully reindexed | 146 | (same toolkit) |
| `49011` | Index **RFC** is successfully reindexed | 30 | 400 → redirected to the toolkits LIST |
| `49009` | Index **attach** is successfully reindexed | 118 | 400 → redirected to the toolkits LIST |
| `49002` | Index **broken** is failed | 137 | 400 → redirected to the toolkits LIST |

In every case: `GET /api/v2/elitea_core/tool/prompt_lib/406/{toolkit_id}` → **400**, ditto
`/elitea_core/index_meta/prompt_lib/406/{toolkit_id}`, and the SPA silently drops to
`/toolkits/indexes` (the list) with **no** "not found" message. The surviving toolkits in
that project carry ids in the 850–890 range — ids 30/118/137/146 are from a much older era
and are gone. This is stale real history, **not a product defect**.

**A fresh index notification cannot be produced from the test side**, per the environment
gap already recorded for ELITEA-2265 (`test-specs/settings-notifications/_surface.md`
§ Environment gap): the test user's personal project has zero toolkits and zero credentials,
the artifact toolkit's vector-store select offers only "None", and no `PGVECTOR*` secret
exists in `automation/config.py` / `.env.test`. No indexable toolkit ⇒ no index run ⇒ no
`index_data_changed` notification.

Executing the case's steps 4–5 against a dead toolkit would only prove the stale-link
behaviour, which is not what the case asks. Per `.agents/testing.md` § Fidelity policy, an
observable that cannot be produced honestly is a routing decision, not an implementation
detail — hence `blocked` rather than a weakened assertion or a fabricated toolkit response.

## What WAS executed and confirmed

1. **Case step 1** — `${BASE_URL}/settings/notifications` loads; page-info `"1 - 50 of 89"`. ✅
2. **Case step 2** — index notifications are findable via the product's own search
   (`"Index "` / `"is successfully created"` / `"reindexed"`); 7 rows total. ✅
3. **Case step 3** — the link is clickable; it is `target="_blank"` + `rel="noopener
   noreferrer"` and opens a **new tab**. ✅
4. **Case step 4** — the browser navigates to the **toolkits/indexes area of the correct
   project** (`Bugs & Features`, project 406) but NOT to the referenced index. ❌ (target gone)
5. **Case step 5** — no "not found" error is shown; instead the app **silently falls back to
   the toolkit list**. ❌ (cannot be verified against a live index)

The link-contract half IS verifiable today and is the natural first assertion once the
blocker clears: `href == {origin}/{project_id}/toolkits/indexes/{meta.toolkit_id}?index_name={urlencode(meta.index_name)}`.

## Blocked Steps

| Step | What is needed to unblock |
|---|---|
| 4–5 | An `index_data_changed` notification whose `meta.toolkit_id` still resolves (200 on `/elitea_core/tool/prompt_lib/{project}/{toolkit_id}`). Either (a) provision a vector-store credential + an indexable toolkit in the test user's personal project so the suite can run a real index (the ELITEA-2265 gap — human/lead decision), or (b) confirm a shared project where the test user may run a re-index against a toolkit that will persist. |

## Concrete Handles (captured for whoever picks this up after the unblock)

| Element | Primary handle | Provenance | Notes |
|---|---|---|---|
| Notification row (repeats) | `[data-testid="notification-row"]` | on-main ✓ | scope per row via checkbox id |
| Row checkbox (dynamic) | `[data-testid="notification-checkbox-{id}"]` | on-`automation/testids` only | |
| Row message cell | `[data-testid="notification-message-text"]` | on-main ✓ | |
| **In-message link** | `[data-testid="notification-message-link"]` | **needs-adding** | same single add as ELITEA-2261/2263 — see ELITEA-2261's AFS § Testid work |
| Search input | `[data-testid="notifications-search-input"]` | on-`automation/testids` only | |
| Toolkit-detail indexes tab / index row | — | **needs discovery** | the toolkit detail page was never reached; no handle may be invented (`test-case-analysis` § Anti-patterns) |

## Fidelity Declaration
No substitutions were made, and none may be introduced to unblock this case. Stubbing
`/elitea_core/tool/prompt_lib/...` to make a dead toolkit resolve would be a **terminal**
substitution — the case's own observable read off fabricated data — which
`.agents/testing.md` § Fidelity policy forbids absent a case line asking for simulation
(ELITEA-2262's text asks for none).

## Known Defects Found During Exploration
None. The silent fallback to the toolkit list for a deleted toolkit is arguably poor UX
(the chat surface shows an explicit "Conversation not found" dialog in the analogous
situation — see ELITEA-2261's AFS), but it is out of this case's scope and was not filed;
noted here and in the batch findings so the lead can decide whether it deserves its own
observation.

## Automation Hints (for after the unblock)
- Model the spec on ELITEA-2263's (`test-specs/settings-notifications/l2_notification-bucket-retention-link-navigates-to-bucket_ELITEA-2263.md`)
  — same shape: discover a live-target notification, assert the meta-derived `href`, click
  into a popup, assert the target page opened on the right entity.
- File: `automation/tests/ui/admin/test_notification_link_navigates_to_index.py`.
