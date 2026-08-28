---
name: Chat AI answers — assert the index, never detect "settled"
description: ChatPage.wait_for_ai_response() returns mid-turn; use an auto-retrying assertion on nth(initial_count+1)
type: feedback
---

`ChatPage.wait_for_ai_response(initial_count)` **returns while the turn is still
running**, and then `get_last_message_text()` reads whatever prose is there. Two
independent defects, both confirmed on ELITEA-0500 (board #1888, suite-wide fix
tracked as **#1913**):

1. Its completion signal is "Copy button visible AND the body isn't one of six
   known placeholder strings". The Copy button **flickers on mid-turn** (measured
   at t≈11s, ~0.6s window, in 3 of 3 instrumented runs), and an agentic narration
   like *"Let me read the file directly…"* is not in the placeholder blocklist —
   so the narration scores as a finished answer. That is exactly what turned
   GHA run 33066098636 red.
2. It settles index `initial_count + 1` but `get_last_message_text()` reads
   `.last` — not the same element once the assistant emits more than one message.

**Do not re-implement a better settle detector in a spec.** The whole class of bug
comes from reading the text ONCE at a moment you judged to be the end. Express the
last mile as a web-first assertion on the explicit index instead — it auto-retries,
so a model that narrates first and answers later is handled by construction:

```python
expect(chat.messages_container.nth(initial_count + 1)).to_contain_text(
    expected, ignore_case=True, timeout=ATTACHMENT_ANSWER_TIMEOUT  # 90s
)
```

Established in-repo idiom already (`test_create_agent_via_chat_canvas.py:345`,
`test_pipeline_flow_editor_add_llm_node_from_chat_canvas.py:365`). Measured
send→answer on the attachment flow: ~17.8s, well inside a 90s retry budget.

Corollary: a settle built on `chat-stop-generation-button` is **not** portable —
that testid is on `automation/testids` but **not on EliteaUI `main`**, so it is
green on localhost and red on any deployed env.
