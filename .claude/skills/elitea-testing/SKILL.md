---
name: elitea-testing
description: Test, run, debug, and schedule ELITEA agents and pipelines. Covers the predict endpoint (sync, async, callback), conversation+participant+message flow, send-and-poll for long-running predicts, classification of failure modes from conversation state (hung predicts, explicit errors, user-timeout, awaiting-approval interrupts), the analytics endpoints, idempotency guards, and scheduling via native pipeline cron/webhook triggers (with GitHub Actions as the fallback for interactive pipelines). Includes a full case study (`references/nudge-case-study.md`) walking through how `ConversationHealthAnalyzer` was built, debugged, deployed to two projects, and scheduled. Also bundles `scripts/update_agent.py` for pushing local instruction files to a deployed agent. Use this skill whenever the user wants to run, predict, test, debug, or schedule an ELITEA artifact.
---

# ELITEA Testing — Run, Debug, Schedule

> **Growing this skill:** new failure-mode patterns, scheduling tricks, idempotency rules, or smoke-test scripts should land in `references/test-patterns.md` or `scripts/`. Multi-step debugging case studies go in `references/<artifact-name>-case-study.md`. See `elitea-platform/references/growing-this-toolkit.md` for the routing decision tree and the script-generalization checklist.

ELITEA artifacts (agents, pipelines, toolkits) are tested by **calling the same REST API users hit at runtime**. There is no separate test harness — production endpoints serve test traffic, and you observe outcomes via the conversation/message endpoints.

## Quick lookup

| If you need... | Load |
|---|---|
| How to fire a single prediction (sync, async, callback) | `references/test-patterns.md` § "Predict" |
| Conversation → participant → message → poll lifecycle | `references/test-patterns.md` § "Conversation flow" |
| How to classify conversation outcomes (errored / completed / active / pending) | `references/test-patterns.md` § "Outcome classification" |
| Patterns mined from ELITEA's pytest integration suite | `references/test-patterns.md` § "Integration test patterns" |
| Real worked example: build → debug → deploy → schedule | `references/nudge-case-study.md` |
| Push a local instruction `.md` to an existing agent | `scripts/update_agent.py` (see end of this file) |
| Schedule recurring runs (native cron; GH Actions as fallback) | this file § "Scheduling" + `elitea-pipeline/references/workflows.md` § "Pipeline entry-point triggers" |
| Trigger a pipeline from an external system (webhook) | this file § "Webhook triggering" |
| A run that pauses for human approval (HITL / sensitive-action guardrail) | `references/test-patterns.md` § 3b |
| Error rates + latency per agent, without scraping conversations | `references/test-patterns.md` § 8 "Analytics endpoints" |

## Core capabilities & when to use each

| Capability | Endpoint | When |
|---|---|---|
| **Stateless predict** | `POST /api/v2/elitea_core/predict/prompt_lib/{project_id}/{version_id}` | One-shot agent run; webhook handlers; testing a version without persisting a conversation; CI smoke tests |
| **Conversational predict** | `POST /api/v2/elitea_core/conversations/...` → `/participants/...` → `/messages/...` | Multi-turn conversations; testing chat flows; reproducing user scenarios |
| **Direct LLM predict** | `POST /api/v2/elitea_core/predict_llm/prompt_lib/{project_id}` | Compare raw LLM output against agent output; bypass tool selection logic |
| **Test a single toolkit operation** | `POST /api/v2/elitea_core/test_toolkit_tool/prompt_lib/{project_id}` | Validate a toolkit operation BEFORE linking it to an agent |
| **Async with callback** | Same predict endpoints with `callback_url` + `callback_headers` in body, `async_mode: true` | Long-running predicts; integrating with external systems that have their own webhook receivers |
| **Run a pipeline (first-class)** | `POST /api/v2/elitea_core/pipeline_run/prompt_lib/{project_id}?async=true` | Purpose-built pipeline invocation with optional async + callback. ⚠️ The spec documents **no request body** — how the version is selected is unclear. **Probe it live before preferring it over `/predict/{version_id}`.** |
| **Stop a hung run** | `DELETE /api/v2/elitea_core/task/prompt_lib/{project_id}/{message_group_uuid}` | Kill a predict stuck in `is_streaming=True, items=0`. We could always *detect* hung runs; this is how you *clear* them. |
| **Project/agent health at a glance** | `GET /api/v2/elitea_core/analytics_agents/{mode}/{project_id}` | Error counts + avg duration per agent. Cheapest first move when debugging — see `references/test-patterns.md` § 8. |
| **Regenerate a failed reply** | `POST /api/v2/elitea_core/regenerate/prompt_lib/{project_id}/{message_group_uuid}` | ⚠️ **Not a clean REST retry** — `SioRegenerateModel` requires `sid` (a socket.io session id) plus `question_id` and `conversation_uuid`. Don't present it as a drop-in for the nudge pattern without a live probe. |

## Outcome classification — pattern reference

The deterministic classifier we use in `ConversationHealthAnalyzer` (see `references/nudge-case-study.md`) reads only the **last message group** of a conversation:

| Last-group shape | Status |
|---|---|
| `is_streaming=True, items=0, task_id≠null` AND age ≥ 10 min | `errored: hung` |
| `is_streaming=True, items=0, task_id≠null` AND age < 10 min | `active` (legitimate in-flight predict) |
| Last assistant text contains `An unexpected error\|Traceback\|ConnectionError\|RateLimitError\|...` | `errored: explicit error` |
| Last group is from a user, age ≥ 15 min, no assistant reply | `errored: timeout` |
| Last group is from a user, age < 15 min | `pending` |
| Last group is an assistant message with real content | `completed` |

The two thresholds (`ASSISTANT_HUNG_MINUTES=10`, `USER_TIMEOUT_MINUTES=15`) are tunable in the pipeline YAML.

> ⚠️ **Known false positive: awaiting-approval runs are classified `errored: hung`.** Since 2.0.1, a run can pause indefinitely waiting for a human to authorize a sensitive tool call (and since 2.0.4, a single run can raise *several* such pauses in parallel). That run is streaming with zero items and a `task_id` — indistinguishable, to this table, from a hang. After 10 minutes we class it `errored` and **nudge it, which does nothing**: it's waiting on a button, not on the model.
>
> The missing row is `awaiting_approval`, checked *before* the hung rule. It isn't implemented because the `item_type` the authorization dialog renders from is undocumented, and a guessed marker would be worse than a known bug. **To close it:** park a live conversation on an approval, dump the last message group, record the real marker. See `references/test-patterns.md` § 3b.

## Idempotency for auto-triggered actions

When running on a schedule (cron) and taking real actions (e.g., sending a nudge), guard against runaway loops:

1. **Embed a stable marker** in every action you POST (we use the literal string `[Pipeline retry — operator-triggered]`).
2. **Scope the check to "since the last real user message"** — NOT "anywhere in history". Otherwise a single old nudge blocks the conversation from ever being nudged again, even after weeks of successful turns. Find the chronologically-latest user message that is NOT a marker-containing message; if any marker exists after it, skip.

Full implementation in `ConversationHealthAnalyzer.yaml` → `already_nudged_for_current_failure()`. Walkthrough in `references/nudge-case-study.md`.

## Test-locally workflow

```bash
# 1. Set up auth (one-time)
cp .env.example .env
# edit .env to paste your PAT into ELITEA_TOKEN

# 2. Stateless predict against a deployed agent version
curl -X POST -H "Authorization: Bearer $ELITEA_TOKEN" -H "Content-Type: application/json" \
  -d '{"user_input": "test"}' \
  "https://next.elitea.ai/api/v2/elitea_core/predict/prompt_lib/$PROJECT_ID/$VERSION_ID"
```

For multi-turn or stateful tests, follow the **conversation flow** in `references/test-patterns.md`.

## `scripts/update_agent.py`

Pushes a local Markdown instruction file (e.g., `my_instr/foo.md`) to an existing ELITEA agent via the REST API. Always does a **GET first** to preserve `llm_settings`, `tools`, `tags`, then a **dry-run diff** before any `PUT`.

```bash
# Dry-run (default — no --apply)
python3 .claude/skills/elitea-testing/scripts/update_agent.py path/to/instruction.md

# Apply after review
python3 .claude/skills/elitea-testing/scripts/update_agent.py path/to/instruction.md --apply

# Update other fields too
python3 .claude/skills/elitea-testing/scripts/update_agent.py path/to/instruction.md \
  --set description="..." --set welcome_message="..." --apply
```

The `.md` file's header lines specify the target:

```
Agent ID: 79
Version ID: 79
Project ID: 29
URL: https://next.elitea.ai/

# Instruction body starts here
```

Auth: reads `ELITEA_API_TOKEN` from env or `.env` (walks up to nearest `.git` boundary). Header values can be overridden per-invocation via `--agent-id`, `--version-id`, `--project-id`, `--base-url`.

## Scheduling

**Default since 2.0.3: the native pipeline trigger.** The pipeline's entry-point node carries its own trigger — no external scheduler. Set it over REST:

```
PUT /api/v2/elitea_core/pipeline_trigger/prompt_lib/{project_id}/pipeline/{version_id}/trigger
{"type": "schedule", "cron": "0 9 * * MON-FRI", "timezone": "America/New_York"}
```

Trigger types: `chat_message` (default) · `schedule` · `webhook`.

Hard constraints — all four have bitten us:

- **A pipeline containing HITL, Printer, or any interrupt config can ONLY use `chat_message`.** If someone adds an interactive node while a schedule/webhook trigger is active, **the trigger silently resets back to Chat Message.** Your "scheduled" pipeline quietly stops being scheduled.
- **Cron floor is hourly.** Sub-hourly expressions (`*/15 * * * *`) are accepted with a 200 and then **never fire**. The docs confirm this for scheduled indexing (*"Schedules cannot execute more frequently than once per hour"*); we've observed the same for pipeline triggers.
- **The schedule's timezone is auto-detected from the browser** that configured it. Worth pinning explicitly rather than inheriting whatever laptop set it up.
- **A version PUT wipes the trigger.** It lives in server-side `pipeline_settings.trigger`, not in the YAML — so it also does **not** survive an export/import. Re-arm after every version update.

Verifying a scheduled run actually did something: each fire creates a conversation named `Scheduled run: <pipeline>` with `source: "pipeline"`, which is **invisible in the default conversation list**. Fetch with `?source=pipeline`. "`last_run` advanced" is not proof the run did its job.

**Fallback: GitHub Actions cron** (`references/nudge-case-study.md` § "Scheduling"). Still the right answer when:
- the pipeline has interactive nodes (Printer/HITL), so native cron is forbidden; or
- you need sub-hourly cadence (native can't do it); or
- you need logic outside ELITEA — matrix fan-out across projects, artifact persistence, alerting.

Pattern: `cron: '7,22,37,52 * * * *'` (offset — GH drops top-of-hour ticks), `concurrency.cancel-in-progress: false`, `timeout-minutes` per job, `secrets.ELITEA_NEXT_API_KEY` for the PAT. **Idempotency guards belong in the pipeline, never in the scheduler.**

## Webhook triggering (external system → pipeline)

Arm the trigger (bearer auth, as the pipeline owner):

```
PUT /api/v2/elitea_core/pipeline_trigger/prompt_lib/{project_id}/pipeline/{version_id}/trigger
{"type": "webhook", "webhook_type": "github"}     # github | gitlab | custom
```

`GET` the same path to read back the trigger object. It returns `webhook_url`, `secret_header`, `secret_value`, and a human-readable `secret_instructions`. `POST` to it rotates the secret.

> 🔐 **`secret_value` comes back in PLAINTEXT** (43 chars) on a GET — it is **not** masked, despite what our api-reference used to claim (`webhook_secret_masked` doesn't exist). Verified live 2026-07-13. Treat any log, transcript, or screenshot of that GET as containing a live credential.

Then fire it — **no bearer token; the signature IS the auth**:

```
POST /api/v2/elitea_core/webhook/prompt_lib/{project_id}/{version_id}/{webhook_type}
```

| `webhook_type` | `secret_header` returned | Auth |
|---|---|---|
| `custom` | **`X-Webhook-Token`** ✅ verified | send the secret directly in that header |
| `gitlab` | `X-Gitlab-Token` | send the secret directly |
| `github` | **`null`** | HMAC path — GitHub computes `X-Hub-Signature-256: sha256=<hmac-sha256(raw_body, secret)>` itself |

(`X-Webhook-Token` for `custom` is now settled — an earlier note in our api-reference claiming `X-Hub-Signature-256` for custom was wrong.)

```bash
curl -X POST "https://next.elitea.ai/api/v2/elitea_core/webhook/prompt_lib/630/153/github" \
  -H "Content-Type: text/plain" \
  -H "X-Hub-Signature-256: sha256=<computed_hmac>" \
  -d 'Your message or data here'
```

Body is the **raw** provider payload (`text/plain`, not JSON) and reaches the pipeline as `user_input` — the entire body, as a string. The secret is a 32-byte base64url token, auto-generated and regenerable; **copy it when it's shown — you cannot retrieve it after the modal closes**, only regenerate. 200 = accepted · 401/403 = signature mismatch · 404 = bad project/version id.

> ⚠️ The published webhooks how-to (`how-tos/credentials-toolkits/how-to-use-webhooks.md`) is **stale**: it documents a v1 path (`/api/v1/applications/webhook/...`) and the retired `nexus.elitea.ai` host. Use the v2 path above.

## Related skills

- **`elitea-platform`** — for the exact REST endpoint shapes (predict, conversations, messages)
- **`elitea-pipeline`** — for authoring the pipeline being tested
- **`elitea-toolkit`** — for `test_toolkit_tool` operation-level testing

## Upstream documentation (self-learning)

Live docs are fetchable as plain markdown — append `.md` to any `docs.elitea.ai` path. Start from **https://docs.elitea.ai/llms.txt** (the full page index).

- https://docs.elitea.ai/how-tos/pipelines/pipeline-runs.md
- https://docs.elitea.ai/how-tos/pipelines/entry-point.md
- https://docs.elitea.ai/integrations/third-party-integrations/api-usage.md
- https://docs.elitea.ai/how-tos/chat-conversations/sensitive-action-authorization-guardrail.md
- https://docs.elitea.ai/support/troubleshooting.md

When a doc contradicts the live platform, the live platform wins: check the live spec at **https://next.elitea.ai/shared/openapi/?all=true** (raw JSON) or **https://next.elitea.ai/shared/swagger/?all=true** (Swagger UI). `?all=true` matters — the bare form omits 52 paths. Easiest: `python3 elitea-platform/scripts/fetch_openapi_spec.py --grep <term>`.

**Known-stale doc pages — do not copy from them:** the Power Automate integration guide (entirely v1, `source=alita`, no deprecation notice) and the webhooks how-to (v1 + retired `nexus.elitea.ai` host).
