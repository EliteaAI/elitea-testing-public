---
name: LLM selector misattribution check — substring collision
description: Model-name substring collisions break the "not attributed to a different model" negative check in LLM selector tests
type: feedback
---

The `test_agent_llm_selector_*_models.py` family (ELITEA-1881 Anthropic,
ELITEA-1882 OpenAI, and any future sibling for another vendor) asserts, per
model, that the chat response transcript is attributed to the SELECTED model
and NOT to any of the OTHER models in the parametrized set (Axis-2 addition,
catches silent misattribution regressions).

**Gotcha:** some model display-name sets contain literal substrings of each
other — e.g. `"GPT-5.4"` is a substring of `"GPT-5.4-mini"`. A naive
`assert other not in full_message_text` for every `other != display_name`
will ALWAYS fail when `display_name` is the longer name and `other` is its
prefix, regardless of actual attribution correctness — this is a test-design
false positive, not a product defect (hit live on ELITEA-1882's first run,
fixed same-session).

**Fix pattern:** exclude from the negative-check loop any `other` that is
itself a substring of `display_name`:

```python
other_models = [
    m for m in MODEL_DISPLAY_NAMES
    if m != display_name and m not in display_name
]
```

The Anthropic set (`"Anthropic Claude 4.5 Sonnet"`, `"...4.6 Sonnet"`,
`"...Haiku 4.5"`) didn't hit this — no member is a substring of another.
Before writing/extending this test family for a new vendor's model list,
check the display names for substring containment first.
