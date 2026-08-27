# Test-repair brief — `test_chat_with_toolkit` false-positive error oracle

| field | value |
|---|---|
| **Card** | [#1817](https://github.com/EliteaAI/elitea-testing-public/issues/1817) — `[Fix][ELITEA-1140] test_chat_with_toolkit[github] — false positive error detection` |
| **TMS case** | ELITEA-1140 (`onetest-ai-tm-Elitea/tests/elitea-platform/toolkits-credentials/ELITEA-1140_google-and-bitbucket-toolkit-crud.md`) |
| **Kind** | tech-task repair brief (not a fresh TMS-case AFS) |
| **Subject** | `automation/tests/ui/toolkits/test_toolkit_parameterized.py::TestChatWithToolkit::test_chat_with_toolkit`, Step 5 (lines ~521-537) |
| **Status** | `ready-for-automation` |
| **Analyst** | qa-engineer, 2026-08-27, live against `http://localhost:5173` (EliteaUI `automation/testids` @ `0277bb28`) |
| **New testids needed** | **none** — every handle the recommended oracle uses already exists on `main` |

---

## TL;DR

**Elitea emits no structural marker for a failed toolkit tool execution.** A 401
from GitHub and a clean project list from Jira render through *byte-identical DOM
structure*, the same testids, and the same Socket.IO event sequence with
`finish_reason: "stop"` on both. The failure exists only as a *string the tool
returned*, which the LLM then re-narrates in freshly-generated prose.

Therefore **the two free-text guards on lines 526-533 cannot be repaired — they
must be deleted**, and they must be replaced (not merely removed), because the
surviving `chat_response_keywords` assertion **also passes on a genuine failure**
(§ Finding 3 — verified live). Deleting without replacing would turn a
false-positive RED into a false-negative GREEN, which is strictly worse.

The honest replacement is the **`agent_tool_end` Socket.IO frame**: it carries
the toolkit's own `tool_output`, product-produced and free of LLM prose, and it
is already reachable through the sanctioned, in-repo
`ChatPage.capture_websocket_frames()` observer. § Recommended oracle.

---

## What was executed, and how

Three live probe rounds against `localhost:5173`, each driving the **exact code
path of the spec under repair** — a throwaway pytest module that imported the
real `toolkit_config` / `managed_credential` / `managed_toolkit` fixtures from
`test_toolkit_parameterized.py` and reproduced Steps 1-5 verbatim, replacing only
the assertions with capture. The scratch module was deleted after use; nothing
about the product was substituted.

- **Failure sample — honest, not simulated.** The master `.env.test`
  `GIT_HUB_TOKEN` is expired (issue #1673; re-verified today,
  `GET api.github.com/user` → **401**). A GitHub toolkit built from it and asked
  to list branches produces a **genuine product-side failure**. Three independent
  runs.
- **Success sample.** `JIRA_USERNAME`/`JIRA_API_KEY` are valid
  (`GET /rest/api/3/myself` → **200**), so the `[jira]` param of the same
  parameterized test exercises the identical code path with a real successful
  tool execution. Three independent runs.
- **The CI-breaking payload** was recovered verbatim from GHA run
  `32931571484` (`gh run view … --log-failed`), not reconstructed.

No `page.route`, no `route.fulfill`, no injected state, no replaced client. The
only `page.evaluate` calls were **read-only DOM extraction** in the throwaway
probe (`el.outerHTML`, attribute enumeration) — not present in any deliverable.

---

## Finding 1 — how a FAILED toolkit tool execution renders

**Trigger:** GitHub toolkit (expired PAT) + `"List branches in the repository"`.

### 1a. The chat message DOM

Nothing distinguishes it from a success. The complete `data-*` inventory of the
answer `<li>`:

```
div    | data-testid=chat-answer-thought-accordion
div    | data-testid=chat-answer-model-chip
div    | data-testid=chat-answer-tool-chip
div    | data-testid=chat-answer-model-chip
div    | data-testid=skill-test-last-response      ← the answer body (isLastMessage branch)
button | data-testid=chat-read-out-button
button | data-testid=chat-copy-button
button | data-testid=chat-regenerate-button
button | data-testid=chat-delete-button
```

- **No error-specific testid.** None exists anywhere in the chat answer tree.
- **No `data-*` state attribute** carrying a status.
- **No error-styled node.** `ApplicationAnswer.jsx:810` renders `<ErrorTrace>`
  only when `!!exception` — a *conversation-level* exception. A failed tool call
  is not one, so `ErrorTrace` never mounts. (It also carries **zero testids**, so
  even when it does mount it is unaddressable under the testid-only policy.)
- **No leading marker** — no `❌`, no `Error:`, no `Tool execution failed`.
- The tool chip is *visually identical*: `ActionView.jsx:399-420` renders the
  chip from `toolkitType` and `showProgress` only; **`action.status` is never
  read for the chip's appearance**. `ToolActionStatus.error` exists
  (`src/common/constants.js:970`) but its only consumer is
  `ApplicationThinkView.jsx:546`'s HITL sub-agent wrapper classification
  (`error && !deferred → 'paused'`), which this failure class never reaches.

### 1b. What `ChatPage.get_last_message_text()` returns

LLM-generated prose, **different on every run**. Three consecutive real 401
failures, verbatim:

> **Run 1:** `It appears there's an authentication issue preventing access to the repository. The tool is receiving a "401 Bad credentials" error, which means the credentials configured for accessing the GitHub repository are invalid or expired.` …

> **Run 2:** `I encountered an authentication error (401 Bad credentials) when trying to list the branches. This indicates that the GitHub credentials being used are either invalid, expired, or not properly configured.` …

> **Run 3:** `I encountered an authentication error (401 Bad credentials) when trying to list the branches. This indicates that the GitHub credentials being used are either missing, invalid, or expired.` …

Two consequences, both load-bearing:

1. **The `"authorization error"` guard (line 526) has never fired and cannot
   fire.** Not one of three real authorization failures contains that literal —
   the model writes *"authentication error"* / *"authentication issue"*. The
   guard is dead code that only *looks* like it protects against expired
   credentials.
2. **The narration contains `"branches"`** — i.e. it satisfies
   `chat_response_keywords` (§ Finding 3).

### 1c. Where the failure IS actually visible

Two places, both carrying the toolkit's own error string rather than LLM prose:

**(i) The tool modal** (click `chat-answer-tool-chip`), OUTPUT pane:

```
Failed to list branches: 401 {"message": "Bad credentials", "documentation_url": "https://docs.github.com/rest", "status": "401"}
```

`src/components/Chat/ToolModal.jsx` has **zero testids** and renders the output
through a code-viewer widget; the chip is also click-unstable
(`Locator.click` timed out at 10 s twice in three probes while the element
re-rendered). Not a viable oracle without new testid work and a stability fix.

**(ii) The `agent_tool_end` Socket.IO frame** — the recommended channel:

```json
{
  "type": "agent_tool_end",
  "content": "Failed to list branches: 401 {\"message\": \"Bad credentials\", ...}",
  "response_metadata": {
    "tool_name": "list_branches_in_repo",
    "finish_reason": "stop",
    "tool_output": "Failed to list branches: 401 {\"message\": \"Bad credentials\", ...}",
    "metadata": { "toolkit_name": "GitHubToolkit1787823508",
                  "toolkit_type": "github",
                  "display_name": "GitHub Toolkit 1787823508" }
  },
  "sio_event": "chat_predict"
}
```

### 1d. It is NOT surfaced anywhere else

Checked and negative: no toast; the thought accordion shows only
`Thought for N secs` + the same chips; **no `socket_validation_error` frame**;
**no `agent_tool_error` event type**. The console carried only the already-known
environmental noise (a background `400`, the `parallel_hitl_ready` warning) —
nothing attributable to the failed tool call.

---

## Finding 2 — how a SUCCESSFUL toolkit tool execution renders

**Trigger:** Jira toolkit (valid credentials) + `"List all Jira projects"`.

### 2a. DOM — identical

```
div    | data-testid=chat-answer-thought-accordion
div    | data-testid=chat-answer-model-chip
div    | data-testid=chat-answer-tool-chip
div    | data-testid=chat-answer-model-chip
div    | data-testid=skill-test-last-response
button | data-testid=chat-table-edit-button          ← only difference: the answer
svg    | data-testid=ContentCopyIcon                    happened to render a table
button | data-testid=chat-read-out-button
button | data-testid=chat-copy-button
button | data-testid=chat-regenerate-button
button | data-testid=chat-delete-button
```

The two extra nodes are a *markdown-table* artefact of this particular answer, not
a success marker — a success that answers in prose has the failure's exact tree.

### 2b. `get_last_message_text()`

```
Here are all the Jira projects in your instance:
You have 6 projects in total - 5 software projects and 1 business project.
```

⚠️ **The six project rows are missing.** They render as an HTML `<table>`, and
`ChatPage._extract_message_body()` collects only `<p>` and `<li>` descendants.
The keyword assertion passed on the prose sentences alone. See § Finding 6.

### 2c. `agent_tool_end` frame

```json
{
  "type": "agent_tool_end",
  "content": "Found 6 projects:\n[{'id': '10165', 'key': 'AIPSDLC', ...}]",
  "response_metadata": {
    "tool_name": "list_projects",
    "finish_reason": "stop",
    "tool_output": "Found 6 projects:\n[{'id': '10165', 'key': 'AIPSDLC', 'name': 'AI PDLC/SDLC Demo ', 'type': 'software', 'style': ''}, ...]",
    "metadata": { "toolkit_name": "JiraToolkit1787823546",
                  "toolkit_type": "jira",
                  "display_name": "Jira Toolkit 1787823546" }
  }
}
```

### 2d. Side-by-side — the whole point

| signal | FAILURE (github, 401) | SUCCESS (jira) | discriminates? |
|---|---|---|---|
| answer-body testid | `skill-test-last-response` | `skill-test-last-response` | ❌ |
| error testid / `data-*` state | none | none | ❌ |
| `ErrorTrace` rendered | no | no | ❌ |
| tool chip markup | toolkit icon + `<toolkit>: <tool>` | same | ❌ |
| Socket.IO event sequence | `agent_tool_start` → `agent_tool_end` | identical | ❌ |
| `response_metadata.finish_reason` | `"stop"` | `"stop"` | ❌ |
| `agent_tool_error` event | absent | absent | ❌ |
| console errors | only known env noise | none | ❌ |
| **`response_metadata.tool_output`** | `Failed to list branches: 401 …` | `Found 6 projects: …` | ✅ **only** |

---

## Finding 3 — deleting the guards without replacing them would mask the defect

The GitHub failure narration reads *"…when trying to list the **branches**…"*, and
`TOOLKIT_CONFIGS["github"].chat_response_keywords == ["branch", "found", "repository"]`.
`any(kw in last_msg.lower() …)` is therefore **True on a genuine 401**, as is
`get_message_count() > initial_count` (the failure IS a message).

**Verified on all three failure runs.** So the surviving assertions do not detect
a broken toolkit. A repair that only removes lines 526-533 converts a noisy
false-RED into a silent false-GREEN — the exact trade this project's no-masking
rule forbids. The replacement in § Recommended oracle is not optional polish.

---

## Finding 4 — the exact payload that broke CI

GHA run `32931571484`, job `test / dev-stable - toolkits`, 2026-08-26.
The `[github]` param **succeeded**; the guard matched *this repo's own branch
names*. The full string the assertion evaluated (`last_msg.lower()`, 4 609 chars)
is reproduced verbatim in § Pinning data below.

Two branch names carry the substring, both real:

```
tests/elitea-1980-credential-error-states
tests/elitea-2392-ai-providers-page-sections-load-without-error
```

*(Correction to the card, which named three: `tests/ELITEA-2612-edit-with-ai-navigation-error-handling`
did not yet exist at that run and is absent from the payload. It only strengthens
the card's point — the input set grows on its own.)*

The payload's shape is stable and load-bearing for the fix:

- **first line:** `branches in eliteaai/elitea-testing-public:`
- **last line:**  `all listed branches are unprotected.`

Both are emitted by the toolkit itself (alita-sdk `list_branches_in_repo`), not
by the model — which is what makes an **anchored, positive** matcher viable where
a substring scan is not.

---

## Verdict on question 3 — is a text-level error guard viable?

**No. Not in any form, on either channel, and no marker should be invented to
keep one alive.**

1. **A negative substring scan is structurally impossible to get right.** Both
   channels' *success* payloads legitimately contain `"error"`: the chat message
   (branch names, § Finding 4) and the `tool_output` (same branch names). The
   scanned text IS user data. Any blocklist is a race against the repository's
   own branch names — the card's "self-referential" framing is exactly right.
2. **A scan over the LLM's narration is unstable in the other direction too.**
   Three runs, three phrasings; the one literal the guard looks for
   (`"authorization error"`) appeared in none.
3. **There is no structural marker to key on instead.** Verified at every layer:
   DOM, testids, `data-*` attributes, component source, Socket.IO event types,
   `finish_reason`, console. § Finding 2d.

**The honest oracle is a POSITIVE, ANCHORED assertion on the toolkit's own
`tool_output`, plus a wire-level assertion that the tool actually ran** —
never a negative scan for the word "error", on any channel.

---

## Recommended oracle

Replace Step 5's four asserts with **three tiers**, all read off values the
system produced.

### Tier 1 — the tool actually ran (wire-level, no free text)

Wrap Steps 1-5 in `utils.websocket_frames.capture_socketio_frames(page)` —
**entered before `navigate_to_chat()`**, per that function's own contract (the
`"websocket"` page event fires only at connection-open time). Then:

> **Amended R1 (2026-08-27).** This brief originally said
> `ChatPage.capture_websocket_frames()`. The shared util is called **directly**
> instead, and no `ChatPage` delegator is added on this branch. Reason: this
> branch targets `main`, whose `chat_page.py` lacks the HITL block that
> `automation/base` places the identical method *after*, so an identically-added
> **method** lands at two different anchors — `git merge-tree --write-tree HEAD
> origin/automation/base` conflicts in `chat_page.py`, and a human taking both
> sides ships two `capture_websocket_frames` definitions (ruff `F811`, second
> wins silently). An identically-added **file** merges clean. Side benefit: this
> branch then touches no shared page object at all.

```
frames where _direction == "received"
             and type    == "agent_tool_end"
             and response_metadata.tool_name == cfg.test_tool_result_indicator
             and response_metadata.metadata.display_name == managed_toolkit["name"]
```

- assert **exactly one** such frame → the toolkit participant really invoked its
  tool (today nothing proves this; the assertions can be satisfied by a model
  that never called the tool at all);
- assert its `response_metadata.tool_output` is a non-empty string.

**Amended R1 — the count assertion must name its own cause.** `len(matched) == 1`
reports identically for three unrelated things: *zero frames captured at all*
(a harness failure — the collector entered late, or the environment's Socket.IO
transport fell back to polling; every frame in this brief was captured on
localhost, while this spec runs in GHA against deployed envs), *the model never
calling the tool* (the real signal), and *a legitimate double call*. The message
therefore carries the **total** `len(frames)` and the distinct received
`(type, tool_name)` pairs (`utils.toolkit_output.observed_frame_kinds`), so
`0 of 0 frames` and `0 of 214 frames` triage themselves from a CI log.

This is passive observation, explicitly sanctioned as non-substitution by
`utils/websocket_frames.py`'s module docstring and `.agents/testing.md`
§ Known issues.

### Tier 2 — the tool SUCCEEDED (positive, anchored, per toolkit)

Add one optional field to `ToolkitConfig`:

```python
tool_output_success_pattern: str = ""   # anchored regex the tool_output must match
```

Populated **only from live capture**, never guessed:

| toolkit | pattern | provenance |
|---|---|---|
| `jira` | `r"^Found \d+ projects:"` | **verified live** 2026-08-27, 3 runs |
| `github` | ~~`r"^Branches in \S+:"`~~ | **REFUTED by capture** — see § Q1; shipped value is `r'^\[\s*\{[^}]*"name"\s*:'` |
| `confluence` | `r'^\[\s*(\]\|\{\s*"id"\s*:)'` | **verified live R1** 2026-08-27 — see § Amendment R1 |

Assert `re.match(pattern, tool_output)` when the pattern is set.

> ⚠️ **Caveat the implementer must not paper over.** The GitHub *success*
> `tool_output` could **not** be captured locally — the local `GIT_HUB_TOKEN` is
> expired (#1673). The `^Branches in \S+:` pattern is derived from the CI-captured
> **chat message text**, whose first line is `Branches in <owner>/<repo>:` and
> whose closing line `all listed branches are unprotected.` is characteristic of
> the toolkit's own output rather than model prose — strongly suggesting the
> message is a pass-through of `tool_output`. **That is an inference, not an
> observation.** Two honest options:
>
> - **(a) Preferred** — leave `github.tool_output_success_pattern` **empty** until
>   someone with a valid PAT captures the real `tool_output` (a 90-second probe),
>   and let github run on Tier 1 + Tier 3 in the meantime. Strictly better than
>   today, and asserts nothing unobserved.
> - **(b)** Ship the candidate pattern **and** have the first CI run confirm it —
>   with the understanding that a mismatch is a *test* bug, not a product bug.
>
> Do **not** silently ship the pattern as if it were verified.

**Fallback rule (required):** when `tool_output_success_pattern` is empty for a
toolkit, attempt no success/failure classification — an unverified pattern would
be exactly the invention this brief refuses.

> **Amended R1 (2026-08-27) — the fallback is a `pytest.skip`, not a log line.**
> As first written ("run Tier 1 + Tier 3 only") the empty-pattern branch was
> implemented as a `logger.warning` plus no assertion, and that is a **false-GREEN
> generator**: on a failed tool call Tier 1 still passes (a frame exists, the
> output is non-empty) and Tier 3 still passes (the model narrates the failure
> using the very keywords `chat_response_keywords` looks for). A warning in a GHA
> transcript is not a gate. The branch now calls `pytest.skip(...)` naming the
> missing capture, so an unclassifiable toolkit reports **"not verified"** instead
> of "verified good". This masks no product defect and hides no red — the
> alternative was reporting green on a broken toolkit, which is strictly worse
> than the false-RED this brief exists to remove. A static twin
> (`test_every_toolkit_that_actually_runs_has_a_captured_success_shape`) fails the
> unit suite if a new `TOOLKIT_CONFIGS` entry has neither a captured pattern nor a
> `skip_reason`, so the next toolkit added inherits the guarantee at authoring
> time as well as at run time.

### Tier 3 — the UI carried the result through (keep, unchanged)

```python
assert chat.get_message_count() > initial_count
last_msg = chat.get_last_message_text()
assert any(kw in last_msg.lower() for kw in cfg.chat_response_keywords)
```

> **Amended R1 — `assert last_msg.strip()` was deliberately NOT shipped.** It is
> strictly implied by the keyword assertion on the next line: no keyword from
> `chat_response_keywords` can be found in a blank string, so the emptiness check
> can never be the assertion that fires, and a redundant assert only adds a second
> place to read when triaging. Declared here rather than left as silent drift.

### DELETE

```python
assert "authorization error" not in last_msg.lower(), (...)          # line 526 — dead code (Finding 1b)
assert "error" not in last_msg.lower() or "no results" in last_msg.lower(), (...)  # line 530 — the defect
```

```python
assert "thinking" not in last_msg.lower()                            # line 532
```

> **Amended R1 (2026-08-27) — the `"thinking"` scan is DELETED too.** This brief
> originally said "keep it, note it is a weak proxy, not in scope to change".
> That was wrong on this branch's own terms: `last_msg` is the same LLM prose over
> the same arbitrary user data as the guard being removed one line above, so a
> branch named e.g. `tests/ELITEA-XXXX-agent-thinking-accordion` re-creates #1817
> exactly, one line below its own fix. It also proves nothing — this brief already
> records that `wait_for_ai_response()` waits on the Copy button (generation
> finished), and Tier 3's keyword assertion cannot pass on a `"Thinking…"`
> placeholder. Deleting it is also what makes the PR paragraph's closing sentence
> ("No negative substring scan survives, on any channel") true as shipped.

### One paragraph, for the PR description

> The chat message text is not a channel on which tool success can be judged: it
> is LLM-generated prose wrapped around arbitrary user data, so scanning it for
> `"error"` matches this repository's own branch names while missing every real
> authorization failure (which the model narrates as *"authentication error"*).
> Elitea publishes no structural error marker for a failed toolkit tool
> execution — success and failure share DOM, testids, Socket.IO events and
> `finish_reason` — so the only value that discriminates them is the toolkit's own
> `tool_output`, carried on the `agent_tool_end` frame. The oracle therefore
> asserts, positively: exactly one `agent_tool_end` for the expected tool of the
> expected toolkit; its `tool_output` non-empty and matching that toolkit's
> captured success shape; and the UI carrying the result through to a new message
> containing the expected keywords. No negative substring scan survives, on any
> channel.

---

## Pinning data — the unit test

Location: `automation/tests/unit/test_toolkit_chat_error_oracle.py`
(precedent: `tests/unit/test_console_error_capture_includes_url.py`).

The classifier under test must be a **pure function** — extract the Tier-2 match
into e.g. `automation/utils/toolkit_output.py::tool_output_matches_success(output, pattern)`
so it is unit-testable without a browser.

Reading these captured strings back in a unit test is **not** substitution: they
are real product output, recorded. Fabricating one would be.

### Sample A — real SUCCESS (github, GHA run 32931571484, 2026-08-26)

`last_msg.lower()`, from the CI log, 4 609 chars. **Store as a data file** — not
as a Python literal.

> **Amended R1 — shipped storage form.** Chat-channel samples are stored as
> `.txt`, wire-channel samples as the **whole `agent_tool_end` frame** in JSON,
> both under `automation/tests/unit/data/` and both named
> `elitea1140_<channel>_<toolkit>_<outcome>`:
> `elitea1140_github_branch_list_chat_message_ci.txt`,
> `elitea1140_agent_tool_end_{github_success,github_401_failure,jira_success,confluence_success,confluence_success_empty,confluence_auth_failure}.json`.
> Storing the frame rather than the bare string is an improvement over this
> brief's loose prescription: it lets the unit test exercise
> `find_tool_end_frames` (Tier 1) on real frames too, not just the Tier-2 matcher,
> and keeps `tool_name` / `display_name` provenance attached to the payload.
> One wording precision, since a reader diffing Sample A against #1817's excerpt
> will otherwise re-litigate it: Sample A is verbatim **of `last_msg.lower()`** —
> the chat text as the removed assertion saw it, lower-cased by the guard itself —
> which is why it reads lower-case where #1817 quotes mixed case. It was matched
> against the CI log before being stored. The `agent_tool_end` JSON samples are
> byte-verbatim wire frames.

```text
branches in eliteaai/elitea-testing-public:
aqa/main-release-2.0.5
automation/base
chore/remove-qa-orchestrator
coverage/runtime-execution-wiring
docs/testid-zero-functional-impact
docs/1776-lead-memory
fix/canon-512-repro-skill-openapi-check
fix/ghost-skill-hang-cleanup
fix/skill-and-toolkit-tests-after-night-run
fix/skills-suite-hang-at-27-percent
gh-pages
main
skills/add-data-testid-connected-repos
test/elitea-1694-1695-1696-guardrails-live-reload-v2
test/5968-bucket-permissions-api-verification
tests/elitea-1810-bucket-retention-edit-persistence
tests/elitea-1818-1819-bucket-name-56-char-boundary
tests/elitea-1822-scroll-bucket-list
tests/elitea-1830-1833-duplicate-replace-and-close-x
tests/elitea-1834-upload-to-selected-subfolder
tests/elitea-1842-1843-download-cancel-zip
tests/elitea-1844-1845-delete-single-file-dropdown
tests/elitea-1925-1926-mcp-edit-name-url
tests/elitea-1935-1936-mcp-tools-connection
tests/elitea-1940-mcp-run-history
tests/elitea-1942-mcp-type-filter-remote
tests/elitea-1961-mcp-back-navigation
tests/elitea-1964-delete-credential
tests/elitea-1966-1973-credentials-filter-view-toggle
tests/elitea-1967-credential-type-specific-form-fields
tests/elitea-1968-1969-credential-secret-password-toggle
tests/elitea-1970-credential-test-connection
tests/elitea-1977-create-project-credential-from-toolkit
tests/elitea-1980-credential-error-states
tests/elitea-1986-build-with-ai-skill-role-visibility
tests/elitea-1989-live-generate-draft
tests/elitea-1994-1995-1996-1998-live-generate
tests/elitea-1994-1995-build-with-ai-description-instructions-character-limits
tests/elitea-2003-delete-pipeline-version-falls-back-to-base
tests/elitea-2011-pipeline-run-history-view-executions
tests/elitea-2012-pipeline-import-via-file
tests/elitea-2013-pipeline-tags-add-and-filter
tests/elitea-2016-decision-node-multi-branch-execution
tests/elitea-2017-pipeline-execution-long-response-streaming
tests/elitea-2022-delete-pipeline-redirect-assertion
tests/elitea-2023-pipeline-dashboard-search-filter-clear
tests/elitea-2024-pipeline-view-toggle-default-layout
tests/elitea-2026-pipeline-yaml-editor-view
tests/elitea-2027-pipeline-node-config-verified-via-yaml
tests/elitea-2035-state-modifier-node-config
tests/elitea-2036-pipeline-custom-node-configuration
tests/elitea-2038-pipeline-agent-node-integration
tests/elitea-2039-pipeline-printer-node-config
tests/elitea-2041-entry-point-trigger-shown-only-on-entry-node
tests/elitea-2044-state-panel-delete-custom-variable
tests/elitea-2046-structured-output-toggle-persistence
tests/elitea-2048-pipeline-unsaved-changes-discard
tests/elitea-2049-pipeline-three-dot-menu-actions
tests/elitea-2050-pipeline-export-verify-structure
tests/elitea-2051-pipeline-fork-to-different-project
tests/elitea-2057-canvas-control-panel
tests/elitea-2058-pipeline-llm-model-selection-execution-usage
tests/elitea-2061-pipeline-node-auto-increment-naming
tests/elitea-2062-pipeline-multiple-browser-tabs
tests/elitea-2067-pipeline-yaml-editor-edit-save
tests/elitea-2070-pipeline-run-history-panel-close
tests/elitea-2089-canvas-edit-agent
tests/elitea-2094-chat-new-conversation-participants
tests/elitea-2232-onboarding-provisioning
tests/elitea-2240-project-dropdown-full-sidebar
tests/elitea-2242-2243-2244-settings-drawer-navigation
tests/elitea-2251-settings-sections-loading-state
tests/elitea-2252-settings-profile-logout-visible
tests/elitea-2338-delete-secret-three-dot-menu
tests/elitea-2351-team-project
tests/elitea-2353-multi-category-filter
tests/elitea-2355-unlike-agent-from-list
tests/elitea-2355-unlike-agent-from-list-view
tests/elitea-2358-like-agent-modal
tests/elitea-2360-start-conversation-redirect
tests/elitea-2361-agent-hub-participant
tests/elitea-2362-agent-chip-visible
tests/elitea-2362-agent-chip-with-settings
tests/elitea-2364-my-liked-filter
tests/elitea-2366-trending-category
tests/elitea-2367-empty-state-no-matching
tests/elitea-2367-empty-state-w3
tests/elitea-2370-catalog-default-agents-tab
tests/elitea-2370-catalog-tabs-navigation
tests/elitea-2392-ai-providers-page-sections-load-without-error
tests/elitea-2418-empty-message-cannot-be-sent
tests/elitea-2419-copy-assistant-response-to-clipboard
tests/elitea-2420-drag-and-drop-file-attachment
tests/elitea-2421-send-message-with-attached-file
tests/elitea-2422-widget-state-navigation
tests/elitea-2428-skills-card-view-fields
tests/elitea-2429-skill-editor-back-button
tests/elitea-2430-skill-mandatory-fields-validation
tests/elitea-2431-skill-edit-persistence
tests/elitea-2432-skill-instructions-markdown-toggle
all listed branches are unprotected.
```

Required assertions:

- `"error" in SAMPLE_A` → **True** (proves the old guard's premise was met by a
  legitimate payload — this is the regression the fix exists for);
- `tool_output_matches_success(SAMPLE_A, r"^Branches in \S+:")` → **True** when
  matched case-insensitively / against the original-case form, i.e. the
  `error`-bearing branch names do **not** make it a failure;
- an explicit assertion that the *old* predicate misclassifies it:
  `("error" in SAMPLE_A.lower()) is True` documented as the removed guard's
  behaviour, so a future author cannot reintroduce it innocently.

### Sample B — real FAILURE (github, localhost, 2026-08-27, expired PAT)

Verbatim `response_metadata.tool_output` — single line, no trailing newline:

```text
Failed to list branches: 401 {"message": "Bad credentials", "documentation_url": "https://docs.github.com/rest", "status": "401"}
```

Required assertions:

- `tool_output_matches_success(SAMPLE_B, r"^Branches in \S+:")` → **False**;
- `tool_output_matches_success(SAMPLE_B, r"^Found \d+ projects:")` → **False**.

### Sample C — real SUCCESS (jira, localhost, 2026-08-27) — recommended third row

Verbatim `response_metadata.tool_output`:

```text
Found 6 projects:
[{'id': '10165', 'key': 'AIPSDLC', 'name': 'AI PDLC/SDLC Demo ', 'type': 'software', 'style': ''}, {'id': '10066', 'key': 'AT', 'name': 'AI tests', 'type': 'business', 'style': ''}, {'id': '10099', 'key': 'DA', 'name': 'Demo AI', 'type': 'software', 'style': ''}, {'id': '10198', 'key': 'EDP', 'name': 'Elitea Demo Playground', 'type': 'software', 'style': ''}, {'id': '10033', 'key': 'EL', 'name': 'EliteaTest', 'type': 'software', 'style': ''}, {'id': '10000', 'key': 'SCRUM', 'name': 'test_project', 'type': 'software', 'style': ''}]
```

`tool_output_matches_success(SAMPLE_C, r"^Found \d+ projects:")` → **True**;
against github's pattern → **False**. Pins that patterns don't cross-match.

---

## Handles Reference

**Locator policy: testid-only.** No new testid is required — the recommended
oracle reads the wire and reuses existing page-object fields.

PROVENANCE verified 2026-08-27 after `cd ../EliteaUI && git fetch origin`:

```
chat-message-list                    main:YES  testids:YES
chat-answer-thought-accordion        main:YES  testids:YES
chat-answer-tool-chip                main:YES  testids:YES
chat-answer-content                  main:YES  testids:YES
skill-test-last-response             main:YES  testids:YES
```

| element | handle | page-object field | provenance |
|---|---|---|---|
| messages list | `LocatorDescriptor(testid="chat-message-list")` | `ChatPage.messages_list` (`chat_page.py:826`) | on-main ✓ |
| thought accordion | `LocatorDescriptor(testid="chat-answer-thought-accordion")` | `ChatPage.answer_thought_accordion` (`chat_page.py:916`) | on-main ✓ |
| tool chip | `LocatorDescriptor(testid="chat-answer-tool-chip")` | `ChatPage.answer_tool_chip` (`chat_page.py:944`) | on-main ✓ |
| answer body (last) | `skill-test-last-response` | — (read via `_extract_message_body`) | on-main ✓ |
| tool modal (input/output panes) | **none — no testids exist** | — | `needs-adding` **if** the UI channel is ever chosen (§ Finding 5); NOT needed for the recommended oracle |
| `agent_tool_end` frame | not a locator — `ChatPage.capture_websocket_frames()` (`chat_page.py:6763`) | existing | n/a |

---

## Defects / observations found (lead files, analyst does not)

1. **Product observation — a failed toolkit tool execution is structurally
   indistinguishable from a successful one.** Same DOM, same testids, no `data-*`
   state, no `agent_tool_error`, `finish_reason: "stop"` on both. A user (not just
   automation) can only tell them apart by reading prose or opening the tool
   modal. `ToolActionStatus.error` exists in the frontend but is unreachable for
   this class. Suggested as a `question`/product-observation card, **not** a
   `bug` — it reads as a design gap, and per the interaction-discovery ladder the
   intended mode is confirmed by code, not contradicted by it.
2. **Test defect — the `"authorization error"` guard (line 526) is dead code.**
   Three real 401 failures, zero matches; the model writes *"authentication
   error"*. It has never protected anything. Fixed by this repair.
3. **Test defect — the `"error"` guard (line 530) scans user data.** The card's
   root cause; confirmed. Fixed by this repair.
4. **Test-design gap — `chat_response_keywords` do not discriminate failure.**
   § Finding 3. Fixed by Tier 1 + Tier 2.
5. **Testid gap — `src/components/Chat/ToolModal.jsx` has zero testids**, so the
   only UI surface exposing raw tool output is unaddressable under the
   testid-only policy. Not needed for the recommended oracle; worth a card if the
   tool modal is ever asserted on.
6. **Page-object gap — `ChatPage._extract_message_body()` drops table content.**
   It collects only `<p>`/`<li>`, so a markdown-table answer (the Jira project
   list) is invisible to `get_last_message_text()`. `RENDERED_TABLE_HEADER_CELL` /
   `RENDERED_TABLE_ROW` / `RENDERED_TABLE_CELL` constants already exist
   (`chat_page.py:861-863`) for callers that need it. Out of scope here; worth a
   card.
7. **Known, already open — #1673**, expired `GIT_HUB_TOKEN` in the master
   `.env.test`. Re-verified today (401). It is what made the failure sample
   obtainable honestly; it is also what blocks capturing the github *success*
   `tool_output` (§ Recommended oracle, Tier 2 caveat).
8. **Environment note — CI is unprotected against this too.**
   `TOOLKIT_CONFIGS["github"]` declares no `credential_check`, so
   `_validate_credentials()` never skips it; a CI run with an expired PAT would
   produce the failure narration and (per Finding 3) still satisfy every
   surviving assertion. Tier 1 + Tier 2 close this.

Nothing was filed. Per `.agents/profile.md` § Bug filing the lead routes these.

---

## Coverage Map

### Axis 1 — the repair brief's own elements

| Brief element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Q1 — how a FAILED tool execution renders | DOM, testids, state attrs, marker, exact `get_last_message_text()` | Findings 1a-1d, 3 live runs | brief only (analysis) | ✅ answered |
| Q1b — surfaced as a chat message, or elsewhere? | toast / accordion / WS checked | Finding 1d | brief only | ✅ answered — chat message only; nothing else |
| Q2 — how a SUCCESSFUL tool execution renders | same capture | Finding 2a-2c | brief only | ✅ answered |
| Q3 — is a text-level guard viable? | plain verdict, no invented marker | § Verdict | brief only | ✅ answered — **no** |
| Q4 — the exact CI-breaking payload | quoted verbatim, pinnable | Finding 4 + § Pinning data Sample A | `tests/unit/test_toolkit_chat_error_oracle.py` | ✅ supplied |
| Q4b — two real strings, one success one failure | captured, not fabricated | Samples A/B/C | same unit test | ✅ supplied (3, from 2 channels — provenance stated per sample) |
| github SUCCESS `tool_output` | capture live | — | — | ⚠️ **blocked on #1673** — inference documented, not asserted (Tier 2 caveat) |

### Axis 2 — asserted beyond the ask

| Observable | Why |
|---|---|
| exactly one `agent_tool_end` for the expected tool + toolkit | Today nothing proves the tool ran at all; a model that answers from memory passes every current assertion. The card's "structural oracle" ask is only satisfiable here. |
| `tool_output` non-empty | Cheap invariant that survives every toolkit, including those with no captured success pattern. |
| patterns do not cross-match (Sample C vs github pattern) | Guards against a future pattern so loose it re-admits the original bug. |

## Blocked Steps

**None blocking.** One capture is deferred, not blocked: the github *success*
`tool_output` needs a valid `GIT_HUB_TOKEN` (#1673). Handled by the Tier-2
fallback rule; it does not stop implementation.

## Evidence

Live captures for this analysis (ephemeral, `/tmp/elitea1140/`): per-toolkit
`*-summary.json` (message text + full `data-*` inventory), `*-last-li.html`
(answer `<li>` outerHTML), `*3-frames.json` (all 40/32 Socket.IO frames),
`*3-toolmodal.txt` (tool-modal INPUT/OUTPUT panes), `*-chat.png`. The two
verbatim samples are reproduced above so nothing load-bearing depends on `/tmp`.
CI evidence: `gh run view 32931571484 --repo EliteaAI/elitea-testing-public --log-failed`.


---

## Follow-up probe — github success capture (2026-08-27)

| field | value |
|---|---|
| **Dispatch** | narrow live-capture probe on card [#1817](https://github.com/EliteaAI/elitea-testing-public/issues/1817) — two questions, ~1 h |
| **Analyst** | qa-engineer, 2026-08-27, live against `http://localhost:5173` (EliteaUI `automation/testids` @ `0277bb28`, post-`main`-merge; dev server already up) |
| **Method** | throwaway pytest module (`tests/ui/toolkits/test_probe_1140b.py`, **deleted after use**) creating real credentials + toolkits through `CredentialAPI`/`ToolkitAPI`, driving real chat turns, passively observing frames via `ChatPage.capture_websocket_frames()`. No `page.route`, no `route.fulfill`, no injected state, no `page.evaluate`. |
| **Runs** | `github_anon` x3, `github_expired` x1, `jira` x1 — 5 live chat turns |
| **Cleanup** | every credential and toolkit created was deleted; verified by listing afterwards — `LEFTOVER CREDS: []`, `LEFTOVER TOOLKITS: []`. Throwaway module removed; tree clean before this edit. |
| **Verdicts** | **Q1 = YES, captured** · **Q2 = NO discriminating field exists** |

---

### Q1 — can a genuine GitHub SUCCESS `tool_output` be captured without a valid PAT?

**YES.** Anonymous auth is enough, and it produced a real, product-generated
`list_branches_in_repo` success. The github row no longer has to ship empty.

**What was done**

1. **Credential — Anonymous auth**, created via `CredentialAPI.create_credential`
   with the token field simply *absent* — exactly what the UI's
   `GitHubAuthenticationTypes.None` / `label: 'Anonymous'` option produces
   (`EliteaUI/src/common/constants.js:753-756`, `ToolSection.jsx:46-53`):

   ```json
   {"type": "github", "elitea_title": "github_anon_<ts>", "label": "GitHub Anon <ts>",
    "data": {"base_url": "https://api.github.com"}, "shared": false}
   ```

   `POST /configurations/check_connection/399/github` → **200** `{"success": true}`,
   matching #1673's own note that the Anonymous path still works.

2. **Toolkit** — type `github`, `repository: EliteaAI/elitea-testing-public`
   (**public**, and already the value of `settings.github_repo`, `config.py:126`),
   `selected_tools: ["list_branches_in_repo"]` — i.e. the exact
   `github_toolkit_settings()` shape; only the credential differs.

3. **Chat** — toolkit added as participant, `"List branches in the repository"`
   sent, `agent_tool_end` captured. **3 independent runs, byte-identical
   `tool_output` (7 818 chars each).**

**The captured github SUCCESS `tool_output` — verbatim**

A **JSON array of `{"name", "protected"}` objects** (100 entries; parses cleanly
with `json.loads`). It is *not* the `Branches in <owner>/<repo>:` prose the prior
pass inferred:

```text
[{"name": "aqa/main-release-2.0.5", "protected": false}, {"name": "automation/base", "protected": false}, {"name": "chore/remove-qa-orchestrator", "protected": false}, {"name": "coverage/runtime-execution-wiring", "protected": false}, {"name": "docs/testid-zero-functional-impact", "protected": false}, {"name": "docs/1776-lead-memory", "protected": false}, {"name": "fix/canon-512-repro-skill-openapi-check", "protected": false}, {"name": "fix/ghost-skill-hang-cleanup", "protected": false}, {"name": "fix/skill-and-toolkit-tests-after-night-run", "protected": false}, {"name": "fix/skills-suite-hang-at-27-percent", "protected": false}, {"name": "fix/1816-elitea-1140-test-settings-route", "protected": false}, {"name": "gh-pages", "protected": false}, {"name": "main", "protected": false}, {"name": "skills/add-data-testid-connected-repos", "protected": false}, {"name": "test/ELITEA-1694-1695-1696-guardrails-live-reload-v2", "protected": false}, {"name": "test/5968-bucket-permissions-api-verification", "protected": false}, {"name": "tests/ELITEA-1810-bucket-retention-edit-persistence", "protected": false}, {"name": "tests/ELITEA-1818-1819-bucket-name-56-char-boundary", "protected": false}, {"name": "tests/ELITEA-1822-scroll-bucket-list", "protected": false}, {"name": "tests/ELITEA-1830-1833-duplicate-replace-and-close-x", "protected": false}, {"name": "tests/ELITEA-1834-upload-to-selected-subfolder", "protected": false}, {"name": "tests/ELITEA-1842-1843-download-cancel-zip", "protected": false}, {"name": "tests/ELITEA-1844-1845-delete-single-file-dropdown", "protected": false}, {"name": "tests/ELITEA-1925-1926-mcp-edit-name-url", "protected": false}, {"name": "tests/ELITEA-1935-1936-mcp-tools-connection", "protected": false}, {"name": "tests/ELITEA-1940-mcp-run-history", "protected": false}, {"name": "tests/ELITEA-1942-mcp-type-filter-remote", "protected": false}, {"name": "tests/ELITEA-1961-mcp-back-navigation", "protected": false}, {"name": "tests/ELITEA-1964-delete-credential", "protected": false}, {"name": "tests/ELITEA-1966-1973-credentials-filter-view-toggle", "protected": false}, {"name": "tests/ELITEA-1967-credential-type-specific-form-fields", "protected": false}, {"name": "tests/ELITEA-1968-1969-credential-secret-password-toggle", "protected": false}, {"name": "tests/ELITEA-1970-credential-test-connection", "protected": false}, {"name": "tests/ELITEA-1977-create-project-credential-from-toolkit", "protected": false}, {"name": "tests/ELITEA-1980-credential-error-states", "protected": false}, {"name": "tests/ELITEA-1986-build-with-ai-skill-role-visibility", "protected": false}, {"name": "tests/ELITEA-1989-live-generate-draft", "protected": false}, {"name": "tests/ELITEA-1994-1995-1996-1998-live-generate", "protected": false}, {"name": "tests/ELITEA-1994-1995-build-with-ai-description-instructions-character-limits", "protected": false}, {"name": "tests/ELITEA-2003-delete-pipeline-version-falls-back-to-base", "protected": false}, {"name": "tests/ELITEA-2008-trigger-restriction-disabled-state", "protected": false}, {"name": "tests/ELITEA-2011-pipeline-run-history-view-executions", "protected": false}, {"name": "tests/ELITEA-2012-pipeline-import-via-file", "protected": false}, {"name": "tests/ELITEA-2013-pipeline-tags-add-and-filter", "protected": false}, {"name": "tests/ELITEA-2016-decision-node-multi-branch-execution", "protected": false}, {"name": "tests/ELITEA-2017-pipeline-execution-long-response-streaming", "protected": false}, {"name": "tests/ELITEA-2022-delete-pipeline-redirect-assertion", "protected": false}, {"name": "tests/ELITEA-2023-pipeline-dashboard-search-filter-clear", "protected": false}, {"name": "tests/ELITEA-2024-pipeline-view-toggle-default-layout", "protected": false}, {"name": "tests/ELITEA-2026-pipeline-yaml-editor-view", "protected": false}, {"name": "tests/ELITEA-2027-pipeline-node-config-verified-via-yaml", "protected": false}, {"name": "tests/ELITEA-2035-state-modifier-node-config", "protected": false}, {"name": "tests/ELITEA-2036-pipeline-custom-node-configuration", "protected": false}, {"name": "tests/ELITEA-2038-pipeline-agent-node-integration", "protected": false}, {"name": "tests/ELITEA-2039-pipeline-printer-node-config", "protected": false}, {"name": "tests/ELITEA-2041-entry-point-trigger-shown-only-on-entry-node", "protected": false}, {"name": "tests/ELITEA-2044-state-panel-delete-custom-variable", "protected": false}, {"name": "tests/ELITEA-2046-structured-output-toggle-persistence", "protected": false}, {"name": "tests/ELITEA-2048-pipeline-unsaved-changes-discard", "protected": false}, {"name": "tests/ELITEA-2049-pipeline-three-dot-menu-actions", "protected": false}, {"name": "tests/ELITEA-2050-pipeline-export-verify-structure", "protected": false}, {"name": "tests/ELITEA-2051-pipeline-fork-to-different-project", "protected": false}, {"name": "tests/ELITEA-2057-canvas-control-panel", "protected": false}, {"name": "tests/ELITEA-2058-pipeline-llm-model-selection-execution-usage", "protected": false}, {"name": "tests/ELITEA-2061-pipeline-node-auto-increment-naming", "protected": false}, {"name": "tests/ELITEA-2062-pipeline-multiple-browser-tabs", "protected": false}, {"name": "tests/ELITEA-2067-pipeline-yaml-editor-edit-save", "protected": false}, {"name": "tests/ELITEA-2070-pipeline-run-history-panel-close", "protected": false}, {"name": "tests/ELITEA-2089-canvas-edit-agent", "protected": false}, {"name": "tests/ELITEA-2094-chat-new-conversation-participants", "protected": false}, {"name": "tests/ELITEA-2232-onboarding-provisioning", "protected": false}, {"name": "tests/ELITEA-2240-project-dropdown-full-sidebar", "protected": false}, {"name": "tests/ELITEA-2251-settings-sections-loading-state", "protected": false}, {"name": "tests/ELITEA-2338-delete-secret-three-dot-menu", "protected": false}, {"name": "tests/ELITEA-2351-team-project", "protected": false}, {"name": "tests/ELITEA-2353-multi-category-filter", "protected": false}, {"name": "tests/ELITEA-2355-unlike-agent-from-list", "protected": false}, {"name": "tests/ELITEA-2355-unlike-agent-from-list-view", "protected": false}, {"name": "tests/ELITEA-2358-like-agent-modal", "protected": false}, {"name": "tests/ELITEA-2360-start-conversation-redirect", "protected": false}, {"name": "tests/ELITEA-2361-agent-hub-participant", "protected": false}, {"name": "tests/ELITEA-2362-agent-chip-visible", "protected": false}, {"name": "tests/ELITEA-2362-agent-chip-with-settings", "protected": false}, {"name": "tests/ELITEA-2364-my-liked-filter", "protected": false}, {"name": "tests/ELITEA-2366-trending-category", "protected": false}, {"name": "tests/ELITEA-2367-empty-state-no-matching", "protected": false}, {"name": "tests/ELITEA-2367-empty-state-w3", "protected": false}, {"name": "tests/ELITEA-2370-catalog-default-agents-tab", "protected": false}, {"name": "tests/ELITEA-2370-catalog-tabs-navigation", "protected": false}, {"name": "tests/ELITEA-2392-ai-providers-page-sections-load-without-error", "protected": false}, {"name": "tests/ELITEA-2418-empty-message-cannot-be-sent", "protected": false}, {"name": "tests/ELITEA-2419-copy-assistant-response-to-clipboard", "protected": false}, {"name": "tests/ELITEA-2420-drag-and-drop-file-attachment", "protected": false}, {"name": "tests/ELITEA-2421-send-message-with-attached-file", "protected": false}, {"name": "tests/ELITEA-2422-widget-state-navigation", "protected": false}, {"name": "tests/ELITEA-2428-skills-card-view-fields", "protected": false}, {"name": "tests/ELITEA-2429-skill-editor-back-button", "protected": false}, {"name": "tests/ELITEA-2430-skill-mandatory-fields-validation", "protected": false}, {"name": "tests/ELITEA-2431-skill-edit-persistence", "protected": false}, {"name": "tests/ELITEA-2432-skill-instructions-markdown-toggle", "protected": false}]
```

Store as `automation/tests/unit/data/elitea1140_github_list_branches_tool_output_success.txt`.
Companion to — **not** a replacement for — the prior pass's Sample A, which is the
*chat message* channel. The two are different channels and must not be conflated.

#### ⚠️ The prior pass's candidate github pattern is REFUTED

> `github` | `r"^Branches in \S+:"` | **candidate — see caveat**

**That pattern does not match the real `tool_output`.** Had option (b) been
shipped, the `[github]` param would have gone RED on a *genuine success* — the
same class of false-RED this repair exists to remove, merely relocated from the
chat text to the wire. The inference chain was reasonable and it was wrong: the
CI-captured `Branches in eliteaai/elitea-testing-public:` and `all listed branches
are unprotected.` are **LLM narration**, not tool pass-through. This probe's own
run narrated the identical tool output as *"Here are all the branches in the
EliteaAI/elitea-testing-public repository:"* … *"All branches are currently
unprotected"* — and announced *"Total: 102 branches"* for an array of **100**.
The narration is prose *about* the data, never the data.

#### Recommended github pattern (derived only from what was captured)

```python
"github": r'^\[\s*\{[^}]*"name"\s*:'
```

Anchored at position 0; asserts the array-of-objects shape with a `name` key —
both directly observed. Rejects the captured failure
(`Failed to list branches: 401 …`); does not cross-match jira's `Found 6 projects:`.

*(A looser `^\[\s*\{` also works and tolerates SDK key-order changes; a stricter
`^\[\s*\{"name": "` matches today byte-for-byte but pins JSON whitespace and key
order the SDK never promised. The middle form above is the recommendation.)*

#### The one residual gap, stated honestly

What was captured is a **real success of the real tool, through the real toolkit,
against the real GitHub API**. The only unobserved variable is the credential's
**auth mode** (anonymous vs PAT). Auth mode decides whether GitHub answers 200 or
401; it does not participate in how the SDK serialises a 200. Two independent
corroborations that the authenticated shape is the same:

- the CI run's narration says *"all listed branches are **unprotected**"*, which can
  only come from a per-branch `protected` field — present in this anonymous
  capture, absent from any prose-style output;
- GitHub's `GET /repos/{owner}/{repo}/branches` returns the identical
  `name`/`protected` schema authenticated or not.

This is corroborated inference about **auth mode only** — not about the payload
shape, which was observed. It is a materially smaller gap than the prior pass's,
which inferred the entire string format from a different channel. It closes
completely the moment #1673 is fixed: re-run the same probe with a valid PAT and diff.

#### Routing note for the lead (out of scope here, needs a human decision)

Anonymous auth is a **viable honest source of a successful GitHub toolkit call**
for read-only tools on public repos. That reaches beyond this card — #1673
currently blocks every case needing a *working* GitHub toolkit. It is **not** a
drop-in swap for `TOOLKIT_CONFIGS["github"]`: pointing the parameterized test at an
anonymous credential changes *what the case verifies* (a credentialed toolkit
becomes an uncredentialed one), which per § declared-improvisation ceiling is a
human decision, not an implementer's. Flagged, not recommended.

---

### Q2 — is there ANY status/error field on the frames that discriminates?

**NO. Verified exhaustively at the frame level, not inferred.**

#### 2a. Recursive key-path diff of `agent_tool_end` — zero differences

Every key path (recursing into nested dicts and list elements) was extracted from
the `agent_tool_end` frame of all three scenarios and set-differenced:

```
anon-only vs expired : []
expired-only vs anon : []
jira-only vs expired : []
expired-only vs jira : []
identical anon==expired: True | jira==expired: True
```

`response_metadata` carries exactly `finish_reason`, `metadata`, `timestamp_finish`,
`timestamp_start`, `tool_meta`, `tool_name`, `tool_output`, `tool_run_id` — on **all
three**. `finish_reason == "stop"` on all three. `content` duplicates `tool_output`
on all three. No `status`, no `error`, no `is_error`, no discriminating `type`, no
extra key on failure and no missing key on failure.

#### 2b. Exhaustive scan for an error-ish key ANYWHERE in the frame streams

Every key path of every frame in all three streams (52/60 · 34 · 32 frames) was
matched against `(status|error|is_error|failed|success|exception|severity|level)`.
**Two hits, and they are the same two in every scenario:**

```
github_anon    -> ['.meta.error', '.meta.is_error']
github_expired -> ['.meta.error', '.meta.is_error']
jira           -> ['.meta.error', '.meta.is_error']
```

Both live on the `chat_message_sync` frame, and on the **genuine 401 run** they read:

```json
"error": "", "is_error": false
```

— **byte-identical to both successes.**

This **confirms and sharpens** the prior pass's `ToolActionStatus.error` finding.
The prior pass said the field exists in the UI source but is never populated for
this failure class; the frame level shows *why*: the error channel that does exist
on the wire is **conversation-level** (`chat_message_sync.meta.is_error` — the same
`exception` that gates `ErrorTrace` in `ApplicationAnswer.jsx:810`), and a failed
*tool* execution is not a conversation-level error. The backend never raises it,
so there is nothing for the frontend to render and nothing for a test to key on.

#### 2c. Neighbouring frames — identical sequence

```
-- github_anon (52)      -- github_expired (34)   -- jira (32)
10 agent_llm_start        10 agent_llm_start       10 agent_llm_start
11 agent_llm_chunk        11 agent_llm_chunk       11 agent_llm_chunk
12 agent_llm_end          12 agent_llm_end         12 agent_llm_end
13 agent_tool_start       13 agent_tool_start      13 agent_tool_start
14 agent_tool_end         14 agent_tool_end        14 agent_tool_end
15 agent_llm_start        15 agent_llm_start       15 agent_llm_start
16 agent_llm_chunk        16 agent_llm_chunk       16 agent_llm_chunk
```

Same index, same order, same types. The failing turn proceeds to a second LLM
round exactly like a succeeding one — because to the graph the tool *returned a
string*, and an error string is a string.

#### 2d. Two near-misses, named so nobody tries them

| tempting signal | why it is not an oracle |
|---|---|
| **frame count** (34 failure · 52/60 github success · 32 jira success) | driven by `agent_llm_chunk` count = answer length. jira's *success* (32) is **lower** than github's *failure* (34) — anti-correlated with truth. |
| **tool duration** (`timestamp_finish - timestamp_start`: 0.23 s failure, 2.26 s success) | a latency heuristic, not a contract. A slow 401 or a cached 200 inverts it. Not asserted. |

#### Q2 verdict

The prior pass's § Finding 2d table stands **unchanged and now frame-verified**:
`response_metadata.tool_output` is the **only** discriminating value on the wire.

---

### Full frame payloads

Verbatim, nothing redacted — no secrets appear on this channel (the credential
never travels on it).

#### A — SUCCESS · `agent_tool_start` (github, anonymous auth)

```json
{
  "type": "agent_tool_start",
  "stream_id": "d1c0edd7-37a4-4c17-9058-3573236ae7e3",
  "message_id": "531c9d7b-38b3-4aa2-b8f8-4b38e557c8e7",
  "question_id": "b8dc73ae-9fbf-42b1-a6e1-5b7ecb35172a",
  "content": null,
  "thinking": null,
  "response_metadata": {
    "tool_name": "list_branches_in_repo",
    "tool_run_id": "01a042a4-8471-7dd0-894a-7b3152c3480d",
    "tool_meta": {
      "name": "list_branches_in_repo",
      "description": "Repository: EliteaAI/elitea-testing-public\nToolkit: Probegithub_anonTK1787824449828\n\nThis tool will fetch a list of all branches in the repository. It will return the name of each branch. No input parameters are required.",
      "metadata": {
        "toolkit_name": "Probegithub_anonTK1787824449828",
        "toolkit_type": "github",
        "display_name": "Probe github_anon TK 1787824449828"
      }
    },
    "tool_inputs": {},
    "metadata": {
      "thread_id": "d1c0edd7-37a4-4c17-9058-3573236ae7e3",
      "ls_integration": "langgraph",
      "langgraph_step": 2,
      "langgraph_node": "agent",
      "langgraph_triggers": "('branch:to:agent',)",
      "langgraph_path": "('__pregel_pull', 'agent')",
      "langgraph_checkpoint_ns": "agent:68e24623-f6a3-726b-2304-049d4acca945",
      "checkpoint_ns": "agent:68e24623-f6a3-726b-2304-049d4acca945",
      "toolkit_name": "Probegithub_anonTK1787824449828",
      "toolkit_type": "github",
      "tool_name": "list_branches_in_repo",
      "display_name": "Probe github_anon TK 1787824449828"
    },
    "timestamp_start": "2026-08-27T09:54:33.201961+00:00"
  },
  "references": [],
  "sio_event": "chat_predict",
  "created_at": "2026-08-27T09:54:33.202406Z",
  "parent_message_id": null,
  "agent_name": null,
  "execution_generation": "700d3f63-96bf-4a57-910a-0ba7420cb113",
  "event": "chat_predict",
  "_direction": "received"
}
```

#### A — SUCCESS · `agent_tool_end` (github, anonymous auth)

*(`content` and `response_metadata.tool_output` are the identical 7 818-char string
reproduced in full under Q1; placeholdered here so the structure stays readable.
Every other byte is verbatim.)*

```json
{
  "type": "agent_tool_end",
  "stream_id": "d1c0edd7-37a4-4c17-9058-3573236ae7e3",
  "message_id": "531c9d7b-38b3-4aa2-b8f8-4b38e557c8e7",
  "question_id": "b8dc73ae-9fbf-42b1-a6e1-5b7ecb35172a",
  "content": "<<TOOL_OUTPUT — reproduced in full under Q1>>",
  "thinking": null,
  "response_metadata": {
    "tool_name": "list_branches_in_repo",
    "tool_run_id": "01a042a4-8471-7dd0-894a-7b3152c3480d",
    "tool_meta": {
      "name": "list_branches_in_repo",
      "description": "Repository: EliteaAI/elitea-testing-public\nToolkit: Probegithub_anonTK1787824449828\n\nThis tool will fetch a list of all branches in the repository. It will return the name of each branch. No input parameters are required.",
      "metadata": {
        "toolkit_name": "Probegithub_anonTK1787824449828",
        "toolkit_type": "github",
        "display_name": "Probe github_anon TK 1787824449828"
      }
    },
    "metadata": {
      "thread_id": "d1c0edd7-37a4-4c17-9058-3573236ae7e3",
      "ls_integration": "langgraph",
      "langgraph_step": 2,
      "langgraph_node": "agent",
      "langgraph_triggers": "('branch:to:agent',)",
      "langgraph_path": "('__pregel_pull', 'agent')",
      "langgraph_checkpoint_ns": "agent:68e24623-f6a3-726b-2304-049d4acca945",
      "checkpoint_ns": "agent:68e24623-f6a3-726b-2304-049d4acca945",
      "toolkit_name": "Probegithub_anonTK1787824449828",
      "toolkit_type": "github",
      "tool_name": "list_branches_in_repo",
      "display_name": "Probe github_anon TK 1787824449828"
    },
    "finish_reason": "stop",
    "tool_output": "<<TOOL_OUTPUT — reproduced in full under Q1>>",
    "timestamp_start": "2026-08-27T09:54:33.201961+00:00",
    "timestamp_finish": "2026-08-27T09:54:35.204559+00:00"
  },
  "references": [],
  "sio_event": "chat_predict",
  "created_at": "2026-08-27T09:54:35.204990Z",
  "parent_message_id": null,
  "agent_name": null,
  "execution_generation": "700d3f63-96bf-4a57-910a-0ba7420cb113",
  "event": "chat_predict",
  "_direction": "received"
}
```

#### B — FAILURE · `agent_tool_start` (github, expired PAT)

```json
{
  "type": "agent_tool_start",
  "stream_id": "c6f9ef41-62b9-4711-8e66-91704b1b102c",
  "message_id": "84975768-fe89-4f66-a2f4-4cccc64fe68f",
  "question_id": "ba41b414-efdd-4ef3-a6b1-c2bf68df53f1",
  "content": null,
  "thinking": null,
  "response_metadata": {
    "tool_name": "list_branches_in_repo",
    "tool_run_id": "01a042a2-32f1-7a91-9761-8a2f74294011",
    "tool_meta": {
      "name": "list_branches_in_repo",
      "description": "Repository: EliteaAI/elitea-testing-public\nToolkit: Probegithub_expiredTK1787824297621\n\nThis tool will fetch a list of all branches in the repository. It will return the name of each branch. No input parameters are required.",
      "metadata": {
        "toolkit_name": "Probegithub_expiredTK1787824297621",
        "toolkit_type": "github",
        "display_name": "Probe github_expired TK 1787824297621"
      }
    },
    "tool_inputs": {},
    "metadata": {
      "thread_id": "c6f9ef41-62b9-4711-8e66-91704b1b102c",
      "ls_integration": "langgraph",
      "langgraph_step": 2,
      "langgraph_node": "agent",
      "langgraph_triggers": "('branch:to:agent',)",
      "langgraph_path": "('__pregel_pull', 'agent')",
      "langgraph_checkpoint_ns": "agent:55d0a546-bc6e-0aa4-7d66-5c54c6cf2a85",
      "checkpoint_ns": "agent:55d0a546-bc6e-0aa4-7d66-5c54c6cf2a85",
      "toolkit_name": "Probegithub_expiredTK1787824297621",
      "toolkit_type": "github",
      "tool_name": "list_branches_in_repo",
      "display_name": "Probe github_expired TK 1787824297621"
    },
    "timestamp_start": "2026-08-27T09:52:01.265921+00:00"
  },
  "references": [],
  "sio_event": "chat_predict",
  "created_at": "2026-08-27T09:52:01.266543Z",
  "parent_message_id": null,
  "agent_name": null,
  "execution_generation": "cb04da2c-5a69-49c3-8f2d-5976a35070ea",
  "event": "chat_predict",
  "_direction": "received"
}
```

#### B — FAILURE · `agent_tool_end` (github, expired PAT)

```json
{
  "type": "agent_tool_end",
  "stream_id": "c6f9ef41-62b9-4711-8e66-91704b1b102c",
  "message_id": "84975768-fe89-4f66-a2f4-4cccc64fe68f",
  "question_id": "ba41b414-efdd-4ef3-a6b1-c2bf68df53f1",
  "content": "Failed to list branches: 401 {\"message\": \"Bad credentials\", \"documentation_url\": \"https://docs.github.com/rest\", \"status\": \"401\"}",
  "thinking": null,
  "response_metadata": {
    "tool_name": "list_branches_in_repo",
    "tool_run_id": "01a042a2-32f1-7a91-9761-8a2f74294011",
    "tool_meta": {
      "name": "list_branches_in_repo",
      "description": "Repository: EliteaAI/elitea-testing-public\nToolkit: Probegithub_expiredTK1787824297621\n\nThis tool will fetch a list of all branches in the repository. It will return the name of each branch. No input parameters are required.",
      "metadata": {
        "toolkit_name": "Probegithub_expiredTK1787824297621",
        "toolkit_type": "github",
        "display_name": "Probe github_expired TK 1787824297621"
      }
    },
    "metadata": {
      "thread_id": "c6f9ef41-62b9-4711-8e66-91704b1b102c",
      "ls_integration": "langgraph",
      "langgraph_step": 2,
      "langgraph_node": "agent",
      "langgraph_triggers": "('branch:to:agent',)",
      "langgraph_path": "('__pregel_pull', 'agent')",
      "langgraph_checkpoint_ns": "agent:55d0a546-bc6e-0aa4-7d66-5c54c6cf2a85",
      "checkpoint_ns": "agent:55d0a546-bc6e-0aa4-7d66-5c54c6cf2a85",
      "toolkit_name": "Probegithub_expiredTK1787824297621",
      "toolkit_type": "github",
      "tool_name": "list_branches_in_repo",
      "display_name": "Probe github_expired TK 1787824297621"
    },
    "finish_reason": "stop",
    "tool_output": "Failed to list branches: 401 {\"message\": \"Bad credentials\", \"documentation_url\": \"https://docs.github.com/rest\", \"status\": \"401\"}",
    "timestamp_start": "2026-08-27T09:52:01.265921+00:00",
    "timestamp_finish": "2026-08-27T09:52:01.499327+00:00"
  },
  "references": [],
  "sio_event": "chat_predict",
  "created_at": "2026-08-27T09:52:01.499614Z",
  "parent_message_id": null,
  "agent_name": null,
  "execution_generation": "cb04da2c-5a69-49c3-8f2d-5976a35070ea",
  "event": "chat_predict",
  "_direction": "received"
}
```

#### C — control · `agent_tool_end` (jira, valid credentials)

```json
{
  "type": "agent_tool_end",
  "stream_id": "d16cf456-b5d6-4fcc-a69d-df797ccb7d40",
  "message_id": "4dd1f4ee-b926-4b33-8215-2c245fc941bf",
  "question_id": "5dc388ef-6462-4296-8cee-2f5d0b44b3da",
  "content": "Found 6 projects:\n[{'id': '10165', 'key': 'AIPSDLC', 'name': 'AI PDLC/SDLC Demo ', 'type': 'software', 'style': ''}, {'id': '10066', 'key': 'AT', 'name': 'AI tests', 'type': 'business', 'style': ''}, {'id': '10099', 'key': 'DA', 'name': 'Demo AI', 'type': 'software', 'style': ''}, {'id': '10198', 'key': 'EDP', 'name': 'Elitea Demo Playground', 'type': 'software', 'style': ''}, {'id': '10033', 'key': 'EL', 'name': 'EliteaTest', 'type': 'software', 'style': ''}, {'id': '10000', 'key': 'SCRUM', 'name': 'test_project', 'type': 'software', 'style': ''}]",
  "thinking": null,
  "response_metadata": {
    "tool_name": "list_projects",
    "tool_run_id": "01a042a2-b7a5-7503-a7cb-3721c951ee8a",
    "tool_meta": {
      "name": "list_projects",
      "description": "Jira instance: https://epamelitea.atlassian.net\nToolkit: ProbejiraTK1787824330646\n List all projects in Jira.",
      "metadata": {
        "toolkit_name": "ProbejiraTK1787824330646",
        "toolkit_type": "jira",
        "display_name": "Probe jira TK 1787824330646"
      }
    },
    "metadata": {
      "thread_id": "d16cf456-b5d6-4fcc-a69d-df797ccb7d40",
      "ls_integration": "langgraph",
      "langgraph_step": 2,
      "langgraph_node": "agent",
      "langgraph_triggers": "('branch:to:agent',)",
      "langgraph_path": "('__pregel_pull', 'agent')",
      "langgraph_checkpoint_ns": "agent:dd3d1519-4de7-137a-1bf8-9547d3a61010",
      "checkpoint_ns": "agent:dd3d1519-4de7-137a-1bf8-9547d3a61010",
      "toolkit_name": "ProbejiraTK1787824330646",
      "toolkit_type": "jira",
      "tool_name": "list_projects",
      "display_name": "Probe jira TK 1787824330646"
    },
    "finish_reason": "stop",
    "tool_output": "Found 6 projects:\n[{'id': '10165', 'key': 'AIPSDLC', 'name': 'AI PDLC/SDLC Demo ', 'type': 'software', 'style': ''}, {'id': '10066', 'key': 'AT', 'name': 'AI tests', 'type': 'business', 'style': ''}, {'id': '10099', 'key': 'DA', 'name': 'Demo AI', 'type': 'software', 'style': ''}, {'id': '10198', 'key': 'EDP', 'name': 'Elitea Demo Playground', 'type': 'software', 'style': ''}, {'id': '10033', 'key': 'EL', 'name': 'EliteaTest', 'type': 'software', 'style': ''}, {'id': '10000', 'key': 'SCRUM', 'name': 'test_project', 'type': 'software', 'style': ''}]",
    "timestamp_start": "2026-08-27T09:52:35.238122+00:00",
    "timestamp_finish": "2026-08-27T09:52:35.809375+00:00"
  },
  "references": [],
  "sio_event": "chat_predict",
  "created_at": "2026-08-27T09:52:35.809875Z",
  "parent_message_id": null,
  "agent_name": null,
  "execution_generation": "b372484f-f781-4c59-a30e-490436b61a35",
  "event": "chat_predict",
  "_direction": "received"
}
```

---

### Amendment to § Recommended oracle → Tier 2

The Tier-2 table is replaced by:

| toolkit | pattern | provenance |
|---|---|---|
| `jira` | `r"^Found \d+ projects:"` | **verified live** 2026-08-27, 3 runs (prior pass) — unchanged |
| `github` | `r'^\[\s*\{[^}]*"name"\s*:'` | **verified live** 2026-08-27, 3 runs — captured from a real `list_branches_in_repo` success via an **anonymous** GitHub credential on a public repo. Auth mode is the only unobserved variable (§ Q1 residual gap). |

The prior pass's ⚠️ caveat block (options (a) ship-empty / (b) ship-and-confirm) is
**withdrawn** — both options were framed around an inferred pattern this probe
refuted. The **fallback rule stays** and is still load-bearing for every other
`TOOLKIT_CONFIGS` entry: when `tool_output_success_pattern` is empty, run Tier 1 +
Tier 3 only and classify nothing.

Add to the unit test's pinning set (§ Pinning data):

- **Sample D** — the github success `tool_output` above:
  `tool_output_matches_success(SAMPLE_D, GITHUB_PATTERN)` → **True**; against
  jira's pattern → **False**.
- Sample B (the 401) against `GITHUB_PATTERN` → **False**.
- **The regression pin that matters:** `"error" in SAMPLE_D` → **True** (the array
  contains `tests/ELITEA-1980-credential-error-states` and
  `tests/ELITEA-2392-ai-providers-page-sections-load-without-error`) while
  `tool_output_matches_success(SAMPLE_D, GITHUB_PATTERN)` → **True**. That one pair
  is the whole card in two assertions: the substring scan is wrong on the wire
  channel too, and the anchored positive matcher is right.

### Consequence had BOTH questions failed

Not applicable — Q1 succeeded. For the record, the consequence would have been:
`github` ships with an empty pattern, runs Tier 1 + Tier 3 only, and a genuine 401
in CI passes **green** on every surviving assertion — because the LLM narrates the
failure using the word *"branches"*, which satisfies `chat_response_keywords`
(§ Finding 3). That hole is now closed.

### Evidence

Ephemeral, `/tmp/elitea1140b/`: `github_anon-frames.json` (+ `-run2`, `-run3`),
`github_expired-frames.json`, `jira-frames.json`, `*-summary.json` (frame count +
`get_last_message_text()`), `github_success_tool_output.txt`. Everything
load-bearing is reproduced above, so nothing depends on `/tmp`.

---

## Amendment R1 — the confluence hole, closed by capture (2026-08-27)

Raised by the fresh-session reviewer against the first implementation, resolved
by the implementer with three live captures. **This brief missed it**: it reasoned
about `github` and `jira` and never asked what the *other* CI-wired entry does.

### The hole

Of the five `TOOLKIT_CONFIGS` entries, `gitlab` and `bitbucket` carry an
unconditional `skip_reason`, and `github` / `jira` had captured patterns.
`confluence` had **neither** — and it runs in CI (`CONFLUENCE_API_KEY` is wired
in `test-ui-dev-all.yml:95`, `test-ui-dev-unstable.yml:93`,
`test-ui-stage2.yml:97`). So on an expired Confluence credential: Tier 1 passes
(frame present, output non-empty), Tier 2 classified nothing, Tier 3 passes
because the model narrates the failure using all of `["page", "list", "label"]`.
Net: **GREEN on a broken toolkit** — strictly worse than the false-RED this brief
came to remove.

### Captures (all live, localhost:5173 → DEV backend, space `AT`)

| # | run | `tool_output` (head) | verdict |
|---|---|---|---|
| E | shipped config, label `test` | `[]` | SUCCESS, empty |
| F | label `test-automated` | `[{"id": "182419457", "title": "[DO_NOT_DELETE] TC-003 Page with label"}, …]` | SUCCESS, populated |
| G | credential with a corrupted API key | `Tool execution error!\n\nPossible root causes: Confluence rejected the request …` | FAILURE |

All three are real `list_pages_with_label` calls against the real Confluence
instance; nothing was routed, fulfilled or authored. Capture G's credential
carried a genuinely wrong secret, so Confluence itself produced the rejection —
observation, not simulation. All three are stored as frames under
`tests/unit/data/` and pinned by the unit suite.

**Shipped pattern:** `r'^\[\s*(\]|\{\s*"id"\s*:)'` — both branches of the
alternation were **observed**, neither inferred. The `"id"` anchor is what keeps
it from also matching github's array of `{"name", "protected"}` objects; each
sample now matches only its own toolkit's pattern (a clean diagonal, pinned by
`test_confluence_pattern_does_not_admit_the_other_toolkits_payloads`).

### Two things capture refuted, again

1. **Confluence's failure shape is NOT github's.** The reasonable guess was
   `"Failed to list pages: 401 …"`, by analogy with
   `"Failed to list branches: 401 …"`. The real payload is a prose block
   beginning `Tool execution error!`. Had the pattern been reasoned from the
   github failure instead of captured, it would have been wrong about the very
   payload it exists to reject. Second independent confirmation of § Finding 4's
   rule, now pinned by `test_confluence_failure_shape_is_not_githubs_and_was_not_inferred`.
2. **Tier 1 was only accidentally right for confluence.** `test_tool_result_indicator`
   is documented as *"text expected in result"* and merely *happens* to equal the
   wire `tool_name` for github and jira. Confirmed by capture that the confluence
   wire name really is `list_pages_with_label`, so matching it against
   `response_metadata.tool_name` is correct rather than lucky — pinned by
   `test_confluence_wire_tool_name_really_is_the_configured_indicator`. No config
   or assertion change was needed.

### Observation for the lead — NOT fixed here (out of scope)

The shipped confluence config asks for label **`test`**, which matches **zero**
pages in space `AT` today (confirmed independently via CQL:
`label="test" and space="AT"` → `size 0`; nothing carries that label anywhere on
the instance — the existing labels are `test-automation`, `test-automated`,
`qa-verification`). So the confluence variant of this test verifies *an empty
result*: honest and correctly classified (the tool ran, returned a well-formed
array rather than an error), but weaker end-to-end than it looks.

Changing the label to an existing one would strengthen it — and was deliberately
**not** done here, because `test_tool_params` / `chat_message` are also consumed
by `test_toolkit_test_settings[confluence]`, so it changes *what a second test
verifies*, which is a scope decision, not an implementation detail
(`.agents/role-overrides.md` § declared-improvisation protocol, ceiling 1).
Switching it later needs no oracle change: both the empty and populated shapes
are already pinned.

### Amendment R1 addendum — Tier 1 is sensitive to trigger-side LLM nondeterminism

Observed during R1 verification, worth recording before someone bisects it into a
code defect. In one full 5-parameter invocation, `[jira]` failed Tier 1 with
`got 0 of 39 captured Socket.IO frames` — the harness worked (39 frames), the
model simply answered without calling `list_projects` on that turn. It then
passed **4 consecutive times** (1 standalone + 3 re-runs, 32.60 / 31.83 / 30.03 s,
`reruns.json == {}`).

This is the same trigger-side class `.agents/testing.md` already records for the
HITL specs ("the LLM declining to call the tool on that turn") — it sits
*upstream* of everything the case asserts, so it is never a member of a
sanctioned-RED set and the response is **re-run, never accept 2-of-3**.

It is not a regression introduced by the oracle: before R1 the same turn would
have passed silently (the model's narration satisfies `chat_response_keywords`),
i.e. Tier 1 makes a pre-existing nondeterminism *visible* rather than creating
it. That visibility is the point — a model that never called the tool proves
nothing about the toolkit.

The Tier-1 message is what made this a 5-second diagnosis instead of a bisect:
`0 of 39` separates it from `0 of 0` (a capture/harness failure) without a
re-run. If the rate proves high in CI, the fix is a bounded re-ask of
`cfg.chat_message`, not a weaker assertion.
