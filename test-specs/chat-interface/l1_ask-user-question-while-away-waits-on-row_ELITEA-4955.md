# Test Case: An Ask User question reached while away waits on the chat row and can be answered on return

## Metadata
- **TMS ID**: ELITEA-4955
- **Linked Story**: EliteaAI/elitea_issues#7385
- **Priority**: l1 (TMS `critical`)
- **Environment Explored**: dev (`https://dev.elitea.ai/app`), 2026-11-27, scripted python-playwright probe + source read of `ConversationRunIndicator.jsx` / `ClarifyingQuestionControl.jsx` (origin/main)
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (combined slot)
- **Status**: ready-for-automation

> Neighbours: ELITEA-4953/4956/4957 specs share the run fixtures. None covers the Ask User pause or the `waiting` dot; new spec `test_chat_ask_user_while_away.py`.

## Fixtures
New `ask_user_agent` fixture (`automation/fixtures/chat_run_fixtures.py`): same two OpenAPI toolkits, agent with `meta.internal_tools: ["ask_user"]` and `test-data/chat-runs-continue/r7385-askuser.instructions.md`. Conversations A and B created by API per run.

## Test Steps (live-observed)
1. In A (agent added via plus menu, active chip shown) send `Look up a post for me.`, click B in the list. B opens, no dialog.
2. After ~10-15 s A's row loses the spinner and shows `chat-list-item-unread-badge` `data-reason=waiting` (aria-label "Waiting for your answer").
3. Open A: card "Which JSONPlaceholder post should I look up?" with options Post 1 / Post 2, Skip button enabled; "Agent paused - waiting for your input" pill.
4. Pick Post 2 (button flips Skip -> Continue), Continue: row spins again.
5. End: `ASK-DONE post 2` with Leanne Graham; message_traces tool_call rows = waitSeconds, ask_user, getPost, getUser; has_running_task False.

## Handles Reference
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| Waiting dot | 1 | `chat-list-item-unread-badge` in row, `data-reason=waiting` | - | testid on DEV ✓ |
| Row spinner | 1 | `chat-list-item-running-icon` | - | testid on DEV ✓ |
| Card question/option text | 5 | xpath exact text | `chat-clarifying-question-text-{}` | ladder - card renders no testid/role |
| Skip/Continue | 2 | role button name Skip / Continue | `chat-clarifying-question-skip-button` / `-continue-button` | ladder, unique |

## Coverage Map
| Case element | Covered by | Asserted where | Disposition |
|---|---|---|---|
| Step 1 | step 1 | URL B, no dialog | covered |
| Step 2 | step 2 | data-reason=waiting + aria-label (hover tooltip not rendered as role=tooltip in headless) | covered |
| Step 3 | step 3 | question, options, enabled action button | covered |
| Step 4 | step 4 | spinner count 1 after Continue | covered |
| Step 5 | step 5 | final text + traces | covered |

## Gotchas
- Tooltip text lives in aria-label of the badge; no `role=tooltip` appears without real hover.
- `APP_PREFIX=/app` must be set (no `.env.test` in this sandbox) or navigation 404s.
- The agent chip "base" version; Ask User is enabled via agent `meta.internal_tools`.

## Known Defects
None.
