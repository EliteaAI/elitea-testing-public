---
name: Run Details 'messages' After value is a real JSON array of stringified LangChain messages
description: Run Details STATES panel renders `messages`' After value as JSON.stringify([...]); confirmed live shape `["content='...' ...", ...]` -- assert isinstance(json.loads(v), list), not just non-empty/non-identical
type: reference
---

## What

The Run Details panel's `messages` state-variable After value (`RunStateDialog.jsx`
/ `StateItemView`, same rendering path as any custom `list`/`dict`-typed
variable) is a genuine JSON array — confirmed live via debug print on
`test_pipeline_run_details_state_before_after.py` (ELITEA-2452 pipeline,
`pipeline_with_two_llm_nodes_id`):

```
["content='User asked: Say hello in exactly three words.' additional_kwargs={} response_metadata={} id='...'",
 "content='Hello to you' additional_kwargs={} response_metadata={} id='...' tool_calls=[] invalid_tool_calls=[]"]
```

Each array element is the Python `str()` repr of a LangChain message object
(NOT a nested JSON object) — `json.loads(value)` parses cleanly as a `list`
of `str` elements.

## Why this mattered (ELITEA-2453 review round 2)

ELITEA-2452's shipped test only asserted `messages_before != messages_after`
+ non-emptiness for Step 8 — never a shape check. ELITEA-2453's AFS cited
those exact assertions as proof of "MESSAGES: shows list representation"
(its own case step 8), which a reviewer correctly flagged as an overclaim:
non-equality + non-emptiness doesn't prove "list representation" for any
value type. Fixed by adding a real `isinstance(json.loads(messages_after),
list)` + non-empty shape assertion to ELITEA-2452's Step 8 block (additive,
verified live first via a throwaway `print()` debug patch before committing
to the shape) — this is now the correct citation target for any future
case needing to prove `messages` renders as a list.

## Reusable pattern

Before asserting/citing a value's "shape" (list/array, JSON object, quoted
string, bare number) in an AFS Coverage Map, verify the LIVE value with a
throwaway debug print in a scratch run (`json.loads(value)` + `type()`) —
don't infer the render shape from the variable's semantic role. `messages`
"looks like" a list of message *objects*, but each array element is
actually a `str`, not a nested `dict` — get it wrong and an `isinstance`
assertion either false-fails or asserts the wrong thing.
