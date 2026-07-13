# ELITEA Testing — Patterns Reference

Patterns mined from the `elitea-api-testing` pytest suite and from real production debugging. Each pattern has a goal, the minimum REST sequence, and the gotchas.

## 1. Predict — stateless agent run

**Goal:** Fire one prediction against a deployed agent version. No conversation persistence.

**Endpoint:** `POST /api/v2/elitea_core/predict/prompt_lib/{project_id}/{version_id}`

### Sync (block until complete)
```bash
curl -X POST -H "Authorization: Bearer $ELITEA_TOKEN" -H "Content-Type: application/json" \
  -d '{"user_input": "Hello", "chat_history": []}' \
  "https://next.elitea.ai/api/v2/elitea_core/predict/prompt_lib/630/153"
# → {"result": "...", "task_id": "...", "error": null}
```

### Async (fire-and-poll)

The **documented** way to go async is the body field `async_mode: true` — not a query param. The request schema (`ApplicationPredictRequest`) declares exactly four optional fields: `project_id`, `callback_url`, `callback_headers`, `async_mode` (bool, default `false`).

```bash
# Fire — returns immediately with task_id
curl -X POST -H "Authorization: Bearer $ELITEA_TOKEN" -H "Content-Type: application/json" \
  -d '{"user_input": "Long task", "chat_history": [], "async_mode": true}' \
  "https://next.elitea.ai/api/v2/elitea_core/predict/prompt_lib/630/153"
# → {"task_id": "abc123", "result": null}

# Poll
curl -H "Authorization: Bearer $ELITEA_TOKEN" \
  "https://next.elitea.ai/api/v2/elitea_core/application_task/prompt_lib/630/abc123?result=yes"
# → {"status": "SUCCESS", "result": "..."}  | "PENDING" | "FAILURE"
```

> **Two undocumented-but-working things, don't let anyone "correct" them away:**
> - **`?async=yes` as a query param works** (verified live 2026-06-25) even though it isn't declared on the path. Prefer `async_mode` in the body — that's what the schema says and what will survive.
> - **`GET /application_task/...` is absent from the live v2 spec** — even from the full 133-path `?all=true` surface — yet it works (verified live 2026-06-25 and 2026-07-13). For anything meant to last, prefer `callback_url` over polling it.

### Async with callback (no polling needed)
```json
{
  "user_input": "Generate report",
  "chat_history": [],
  "async_mode": true,
  "callback_url": "https://my-service.com/webhook",
  "callback_headers": {"Authorization": "Bearer my-token"}
}
```
Platform POSTs result to your `callback_url` when done.

**Gotchas:**
- `chat_history` is REQUIRED to be at least `[]` (empty array). Some clients send `null` and get 400. (It isn't in the request schema either, but the 400 is real.)
- `llm_settings` in the body **overrides** the version's baseline for this run only.
- `variables` in the body **replaces** the version's variables for this run.
- **A predict has no approval surface.** If the agent calls a sensitive tool, the run parks forever — see § 3b.

## 2. Conversation flow — full multi-turn lifecycle

**Goal:** Reproduce or test a real user scenario where the agent maintains state across messages.

> **Testing discipline (don't skip — these produce false passes):**
> - **Conversation caching → a NEW conversation per test round.** A conversation pins (caches) the
>   agent's version + state. After ANY change to the entity under test (new version, edited
>   instructions, swapped model, relinked tools), create a FRESH conversation and re-add the agent
>   pinned to the new `version_id`. Reusing an old conversation silently tests the STALE version.
>   (Multiple turns *within one round* share one conversation — that's intended.)
> - **One turn per message — never cram.** A genuine multi-turn test sends each turn as its own
>   `POST /messages` and reads the real reply before sending the next. Putting all turns into one
>   `user_input` is a SINGLE turn; the agent often just echoes the "expected" answers you wrote into
>   the prompt — a fake pass. Ground-truth check: a real N-turn test leaves `2N` message groups
>   (alternating user/agent), not 2.
> - **Report only observed replies.** Read the answer from the response `message_items` and the model
>   from `meta.thinking_steps[].generation_info.model_name`. Never report a result you didn't fetch.

```
1. POST /conversations/...    body: {name, is_private, participants:[]}
   → save {id, uuid}

2. POST /participants/{conv_id}    body: [{entity_name, entity_meta, entity_settings}]
   → save response[0].id as participant_id

3. POST /messages/{conv_UUID}    body: {participant_id, user_input, await_task_timeout}
   → 201 with message_groups OR 202 streaming OR 200 with task_id

4. (Optional) GET /messages/{conv_id}?limit=N    to fetch latest groups
```

### Minimal Python end-to-end

```python
import httpx, os
HEADERS = {"Authorization": f"Bearer {os.environ['ELITEA_TOKEN']}", "Content-Type": "application/json"}
BASE = "https://next.elitea.ai/api/v2/elitea_core"
PROJECT, AGENT, VER = 630, 101, 153

with httpx.Client(headers=HEADERS, timeout=120) as c:
    # 1. Create conversation
    conv = c.post(f"{BASE}/conversations/prompt_lib/{PROJECT}",
                  json={"name": "Smoke test", "is_private": True, "participants": []}).json()
    cid, uuid = conv["id"], conv["uuid"]

    # 2. Add agent participant
    parts = c.post(f"{BASE}/participants/prompt_lib/{PROJECT}/{cid}",
                   json=[{"entity_name": "application",
                          "entity_meta": {"id": AGENT, "project_id": PROJECT},
                          "entity_settings": {"version_id": VER}}]).json()
    pid = parts[0]["id"]

    # 3. Send first message (use UUID, not id!)
    r = c.post(f"{BASE}/messages/prompt_lib/{PROJECT}/{uuid}",
               json={"participant_id": pid, "user_input": "Hello", "await_task_timeout": 60})
    print(r.status_code, r.json())

    # 4. Send a follow-up
    r2 = c.post(f"{BASE}/messages/prompt_lib/{PROJECT}/{uuid}",
                json={"participant_id": pid, "user_input": "Tell me more", "await_task_timeout": 60})
    print(r2.status_code, r2.json())
```

**Gotchas:**
- `POST /messages/...` uses the conversation **UUID** in the URL, not the integer id. Everywhere else uses id.
- Body of `POST /participants/...` is a JSON **list**, even for one participant. Response is also a list — use `response[0]`.
- For long-running predicts, set `await_task_timeout: -1` and pair with `return_task_id: true` to fire-and-forget.

## 3. Send-and-poll — long-running predicts

Sometimes the agent takes minutes to reply (multi-step tool calls, large LLM jobs). Don't block the HTTP request:

```python
# 1. Fire with return_task_id
r = c.post(f"{BASE}/messages/prompt_lib/{PROJECT}/{uuid}",
           json={"participant_id": pid, "user_input": "...",
                 "await_task_timeout": -1, "return_task_id": True}).json()
# → {"task_id": "..."} or {"message_groups": [...]} with last group streaming

# 2. Poll messages list
while True:
    msgs = c.get(f"{BASE}/messages/prompt_lib/{PROJECT}/{cid}", params={"limit": 1, "sort_order": "desc"}).json()
    last = msgs["rows"][0]
    if not last["is_streaming"] and last["message_items"]:
        print("Done:", last["message_items"][0]["item_details"]["content"])
        break
    time.sleep(5)
```

**Gotchas:**
- `return_task_id=True` AND `await_task_timeout > 0` are **mutex** — pick one mode (else `400 "Can not return task id and wait for task completion simultaneously"`).
- `await_task_timeout=-1` means "no wait, return immediately" — pair with `return_task_id=True`.
- `await_task_timeout=0` is the same as -1 in practice (returns immediately).
- The `messages` POST body uses **`user_input`**, not `content`/`role` (sending `{content, role}` → `500`).

### Long-running PIPELINE runs — invoke directly, not via a conversation

A pipeline (`agent_type: pipeline`) that runs for many minutes (e.g. a per-item loop over dozens of entities) needs the **direct predict** path, not the conversation/participant flow:

```python
# Fire the pipeline DIRECTLY and poll its task — runs the graph with its real meta.step_limit
r = c.post(f"{BASE}/predict/prompt_lib/{PROJECT}/{VERSION_ID}?async=yes",
           json={"user_input": "..."}).json()          # → {"task_id": "...", "message": "Task started"}
task = r["task_id"]
while True:
    t = c.get(f"{BASE}/application_task/prompt_lib/{PROJECT}/{task}",
              params={"result": "yes", "meta": "yes"}).json()
    if t["status"] in ("SUCCESS", "FAILURE", "REVOKED", "stopped"):   # see below
        break
    time.sleep(20)
report = t["result"]["chat_history"][-1]["content"]    # the final assistant message
```

Two non-obvious things, both verified live (2026-06-25):
- **An async pipeline predict ends in status `stopped`, NOT `SUCCESS`** — with a fully populated `result`. If your poll loop only breaks on `SUCCESS`, it never finishes (it spins until your own deadline). **Treat `stopped` + a populated `result` as done.**
- **Do NOT run a long pipeline via a conversation participant.** Adding the pipeline as an `entity_name:"application"` participant and sending a message routes it through a **wrapper agent that calls the pipeline as a sub-agent tool with a tool step-limit of 0** — it bails partway (e.g. ~24 of 73 items) emitting a *"Step Limit Hit — tool step limit of 0"* message and never produces the pipeline's final output. The direct `/predict/{version_id}` path has no wrapper and honours the version's `meta.step_limit`.NOTE: maybe need to try adding to conversation using entity_name:"pipeline", worth checking next time.

## 3b. Interrupted / awaiting-approval runs — the poll loop's blind spot

**A run can pause indefinitely waiting for a human, and it looks exactly like a hang.** Every polling loop above breaks only on `not is_streaming and message_items`. A paused run satisfies neither, so the loop spins until its own deadline and then reports a false "hung".

Three things pause a run:

1. **Sensitive Action Authorization Guardrail** (2.0.1) — when an agent calls a tool listed in the server-side `ALITA_SENSITIVE_TOOLS` env var, the tool does **not** execute. The run raises a HITL interrupt and the UI shows an authorization dialog. Sensitive parameter values (tokens, passwords, API keys) are masked in it.
2. **Any `hitl` node** in a pipeline.
3. **Parallel sub-agent fan-out** (2.0.4) — a *single* run can now raise **multiple simultaneous** interrupts, because several child agents can each need approval.

The human picks one of three outcomes:

| Choice | Effect |
|---|---|
| **Authorize** | Tool runs as planned. |
| **Block** | Tool skipped; the agent receives a blocked-action message. |
| **Block with Comments** (2.0.4) | Tool skipped; the user's free-text note is passed back to the agent as the blocked action's `denial_reason`. |

On block, the agent receives:

```json
{
  "type": "sensitive_tool_blocked",
  "status": "blocked",
  "action_label": "github.delete_repo",
  "message": "User blocked the sensitive action 'github.delete_repo'..."
}
```

**What this means for anything calling ELITEA from outside:**

- **Never treat "streaming, no items, N minutes old" as automatically hung.** It may be waiting on a human.
- **A cron- or webhook-triggered pipeline has no approval surface.** Nobody is looking at a dialog. This is precisely why the platform forbids HITL/Printer/interrupt nodes on non-chat triggers — but the guardrail can still fire from a *tool call inside an agent* your pipeline invokes. **If an agent uses a sensitive tool, keep it on the Chat Message trigger.** Otherwise the scheduled run parks forever.
- **A stateless `POST /predict/...` has no approval surface either.** Don't route a sensitive-tool agent through predict from CI or a webhook.

> ⚠️ **UNRESOLVED — there is no documented REST way to detect or resume an awaiting-approval run.** The guardrail docs describe only UI buttons, and the v2 OpenAPI spec contains no `interrupt` / `resume` / `approve` path (grepped: zero hits). Until that's confirmed, an external caller's only options are:
> - a hard deadline on the poll loop, and
> - `DELETE /api/v2/elitea_core/task/prompt_lib/{project_id}/{message_group_uuid}` to **stop** the parked task.
>
> Ask the ELITEA team for the resume endpoint before building anything that depends on it.

## 4. Outcome classification

Reading conversation state to decide if a turn worked, hung, or errored.

> ⚠️ **This classifier has a known false-positive: it labels awaiting-approval runs as `errored`.** A run paused on a HITL interrupt or the sensitive-action guardrail (§ 3b) hits *Pattern A* — assistant, streaming, no items, has a `task_id` — and once it's older than `hung_minutes` it's classed `errored`. `ConversationHealthAnalyzer` then **nudges** it, which accomplishes nothing: the run is waiting on a button, not on the model.
>
> The fix is an `awaiting_approval` branch checked *before* Pattern A. It is not implemented here because **the `item_type` (or `meta` key) the authorization dialog is rendered from is not documented**, and guessing it would be worse than the current known bug. **To close this: find a live conversation parked on an approval, dump its last message group, and record the actual marker.** Then add the branch and a matching row to the classification table in `SKILL.md`.

```python
def classify_last_group(detail, user_pids, hung_minutes=10, user_timeout_minutes=15):
    """Inspect a conversation's last message group and return one of:
       errored / active / pending / completed / empty.
    """
    from datetime import datetime, timezone
    groups = sorted(detail.get('message_groups') or [],
                    key=lambda g: g.get('created_at') or '')
    if not groups:
        return 'empty'
    last = groups[-1]
    is_user = last['author_participant_id'] in user_pids
    streaming = last.get('is_streaming', False)
    items = last.get('message_items') or []

    # Pattern A: assistant streaming with no items
    if not is_user and streaming and not items and last.get('task_id'):
        age = (datetime.now(timezone.utc) -
               datetime.fromisoformat(last['created_at'].replace('Z',''))).total_seconds() / 60
        return 'errored' if age >= hung_minutes else 'active'

    # Pattern B: explicit error string in assistant reply
    if not is_user and items:
        text = ''.join(it['item_details'].get('content','') for it in items
                       if it.get('item_type') == 'text_message')
        if any(s in text for s in ['An unexpected error', 'Traceback', 'ConnectionError', 'RateLimitError']):
            return 'errored'

    # Pattern C: last group is user — pending or timed out
    if is_user:
        age = (datetime.now(timezone.utc) -
               datetime.fromisoformat(last['created_at'].replace('Z',''))).total_seconds() / 60
        return 'errored' if age >= user_timeout_minutes else 'pending'

    return 'completed'
```

Full version with all edge cases is in `eliteapipelines/ConversationHealthAnalyzer.yaml` (now under `elitea-pipeline/examples/`).

## 5. Direct tool invocation testing

Before linking a toolkit to an agent, smoke-test one operation:

```bash
curl -X POST -H "Authorization: Bearer $ELITEA_TOKEN" -H "Content-Type: application/json" \
  -d '{
    "project_id": 630,
    "toolkit_config": {... full settings dict ...},
    "tool_name": "list_branches_in_repo",
    "tool_params": {"repository": "octocat/Hello-World"},
    "llm_model": "gpt-5"
  }' \
  "https://next.elitea.ai/api/v2/elitea_core/test_toolkit_tool/prompt_lib/630?await_response=true&timeout=60"
```

Returns `{result: ...}` on success or `{error: ...}` on failure.

## 6. Integration test patterns (from `elitea-api-testing`)

The pytest suite uses these helpers:

### `post_conversation(project_id, name, participants=[])`
Just `POST /conversations/...`. Returns `{id, uuid}`.

### `post_participant(project_id, conv_id, list_of_participants)`
Wraps the list-body requirement. Always returns `response[0]`.

### `post_message(project_id, conv_uuid, payload)`
Always sets `await_task_timeout=30` if caller didn't.

### `update_entity_settings(project_id, conv_id, participant_id, body)`
Full-replace PUT — caller responsible for including all fields they want to keep.

### `wait_for_configuration_status_ok(config_id, max_tries=5, delay=3)`
Polls `GET /configuration/{id}` until `status_ok: true`. AI/embedding configs sometimes need a few seconds.

### Common fixtures

| Fixture | Value |
|---|---|
| `TEST_GITHUB_REPOSITORY` | `octocat/Hello-World` |
| `TEST_EMBEDDING_MODEL_NAME` | `text-embedding-ada-002` |
| `TEST_CHAT_MODEL_NAME` | `gpt-5` |
| `TEST_AZURE_OPENAI_API_VERSION` | `2024-02-01` |
| `bucket.expiration_value` | 30 days (workaround for a backend bug with non-null `data_retention_limit`) |
| `await_task_timeout` default in `post_message` | 30 seconds |

## 7. Common gotchas (cheat sheet)

| Gotcha | Detail |
|---|---|
| `Content-Type: application/json` on GET | Drop it. Use `Accept: application/json`. Some proxies 400 with it. |
| Empty `chat_history` | Send `[]`, not `null`. |
| Wrong `participant_id` | Use the integer `id` from `POST /participants/...` response, NOT the agent's `application_id`. |
| URL with `id` instead of `uuid` for `POST /messages/` | Get 400 `"...does not exist..."`. |
| Bare `await_task_timeout` < -1 | 400 validation error. |
| `meta.step_limit` not set | Defaults to 25; bump for long agentic chains. |
| First version name not `"base"` | Create fails with 400. |
| Subsequent version named `"base"` | Create fails with 400. |
| Sending `Content-Type` on GET via Pyodide httpx in a pipeline | Got us a 400. Don't. |
| `entity_settings.llm_settings` override on non-published agent | Gets stripped; if it doesn't match version baseline → 400. |
| Any `/api/v1/...` path | **404 since 2.0.4.** v1 is removed, not deprecated. |
| A run that "hangs" with no items | May be **awaiting human approval**, not hung — see § 3b before you nudge it. |

**Runtime errors any looping test harness must handle** (these come from the platform, not your payload):

| Error | What it actually means |
|---|---|
| `429` — *"Hit token rate limit. Minute limit: 0 / 120000 tokens"* | Per-second/minute/day token limits on shared environments. **Back off and retry, or switch model.** A harness that fires predicts in a loop WILL hit this. |
| `400` — *"This model's maximum context length is 128000 tokens. However, your messages resulted in 217815 tokens"* | Not a payload-shape bug. Compress/summarize, or index instead of pasting documents. Context limits: Claude Sonnet 200k · GPT-4o 128k · GPT-5 400k. |
| `400` — *"The message you submitted was filtered due to containing prohibited or sensitive content"* | **A test input can trip this.** Don't misread it as an agent failure. |

## 8. Analytics endpoints — check these BEFORE scraping conversations

The Analytics doc says there's no REST surface. There is — seven endpoints, in the live v2 spec:

```
GET /api/v2/elitea_core/analytics/prompt_lib/{project_id}
GET /api/v2/elitea_core/analytics_agents/{mode}/{project_id}
GET /api/v2/elitea_core/analytics_agent_detail/{mode}/{project_id}
GET /api/v2/elitea_core/analytics_tools/{mode}/{project_id}
GET /api/v2/elitea_core/analytics_tool_detail/{mode}/{project_id}
GET /api/v2/elitea_core/analytics_users/{mode}/{project_id}
GET /api/v2/elitea_core/analytics_user_detail/{mode}/{project_id}
GET /api/v2/elitea_core/context_analytics/prompt_lib/{project_id}/{conversation_id}
```

`analytics_agents` ("paginated agent/application usage statistics") takes `date_from`, `date_to` (ISO 8601; defaults to the last 7 days), `limit` (≤100), `offset`, `search`, `sort_by` ∈ `events|users|avg_duration_ms|errors|entity_name`, `sort_order`. It returns `{total, rows: [{entity_name, events, users, avg_duration_ms, errors, ...}]}`.

**Use it as the cheap first pass.** Sorting by `errors` descending over the last 24h tells you *which* agent is failing before you fetch a single conversation:

```bash
curl -H "Authorization: Bearer $ELITEA_TOKEN" \
  "https://next.elitea.ai/api/v2/elitea_core/analytics_agents/prompt_lib/630?sort_by=errors&sort_order=desc&limit=10"
```

Caveats: responses are cached for 5 minutes; scope is per-project; correlating a tool failure back to its calling agent needs trace-ID propagation.

## 9. End-to-end debugging checklist

When a pipeline / agent isn't behaving:

1. **Start with analytics** (§ 8) — `analytics_agents?sort_by=errors&sort_order=desc` narrows it to one entity in one call.
2. **Check the calling user has access to the project** — `get_auth_user` then `get_projects_project` should include the target.
3. **Confirm the version_id is current** — `get_elitea_core_application` and verify `version_details.id`.
4. **Look at the last few message groups** — `GET /messages/?limit=5&sort_order=desc`. Check `is_streaming`, `task_id`, `meta.tool_calls[*].finish_reason`. **If it's streaming with no items, rule out an approval pause (§ 3b) before calling it hung.**
5. **For a code node, turn on `debug: true`** and read the assembled Python + injected state from the `code-debug` artifact bucket. This beats guessing — see `elitea-pipeline/references/yaml-schema.md`.
6. **For pipelines, look at the structured `result` block in predict** — `chat_history[-1].content` often contains a wrapped JSON with diagnostics.
7. **Test the failing operation in isolation** via `test_toolkit_tool` if it's a tool issue.
8. **Compare model output to baseline** via `/predict_llm/` (no agent, just LLM).
9. **Stop a genuinely stuck run:** `DELETE /api/v2/elitea_core/task/prompt_lib/{project_id}/{message_group_uuid}`.

**The UI surfaces, and their limits:**
- **Run History** (Agents/Pipelines menu → clock icon 🕐): per-run date, version, duration, full message replay; share-link / delete / restore. **No REST equivalent exists** — confirmed absent from both the docs and the v2 spec. Conversation-scraping remains the only programmatic path. That's a finding, not an oversight.
- **Pipeline Runs** (Flow Editor): node-by-node timeline, per-node state snapshots before/after, stack traces. Statuses: **In Progress / Completed / Error / Stopped / Interrupt**. (`Stopped` being first-class is consistent with async pipeline predicts ending in `stopped`, not `SUCCESS` — see § 3.)
- **Toolkit Run History tab:** ⚠️ tracks **only** Test-Settings runs and Indexes-tab operations. It does **not** track toolkit calls made from chats, agents, or pipelines. Don't send anyone there to debug an agent's tool call.
