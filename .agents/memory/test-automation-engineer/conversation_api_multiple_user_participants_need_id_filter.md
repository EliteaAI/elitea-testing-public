---
name: ConversationAPI participants list can have MULTIPLE entity_name=="user" rows — filter by entity_meta.id, not entity type alone
description: Cross-verifying the conversation OWNER via ConversationAPI.get_conversation()'s participants list (the ELITEA-2095 pattern) assumes exactly one "user"-entity participant. That's only true for a single-owner conversation. Once real users are invited (ELITEA-2167's Invite Users flow), invited users ALSO carry entity_name=="user" — a bare `next(p for p in participants if entity_name=="user")` non-deterministically grabs an invited user instead of the owner. Filter on `entity_meta.id == author_id` directly.
type: feedback
---

## What happened

ELITEA-2167's fix-only round (PR #988, reviewer Finding 1) added a hard
assertion that the conversation's actual OWNER — not just "some third
participant" — appears in PARTICIPANTS USERS after the first Send. The
established technique for this in the suite is
`test_open_conversation_today_section.py` (ELITEA-2095) Step 10: fetch
`ConversationAPI.get_conversation(conv_id)`, read `author_id`, then find
the participant with `entity_name == "user"` and confirm its
`entity_meta.id == author_id`.

Copied verbatim, the first draft used:

```python
owner_participant = next(
    (p for p in conv_data.get("participants", []) if p.get("entity_name") == "user"),
    None,
)
assert owner_participant.get("entity_meta", {}).get("id") == owner_id, (...)
```

First local run failed immediately:
```
AssertionError: The conversation's 'user' participant should be its actual
owner (author_id=659), got participant entity_meta={'id': 7}
```

`entity_meta={'id': 7}` was **Levon Dadayan** (one of the two invited
users), not the owner. `next()` grabbed the FIRST "user"-entity row in
API response order, which is not owner-first.

## Why the copied technique broke

ELITEA-2095's conversation is single-owner — its API response has
EXACTLY one `entity_name == "user"` participant (the owner), so
`next(... if entity_name == "user")` and "the owner" were the same thing
by construction. ELITEA-2167's conversation has invited users, and
invited users are real platform accounts too — they ALSO get
`entity_name == "user"` participant rows (as opposed to `entity_name ==
"agent"` for an AI participant). The moment a conversation has 2+ human
participants, "the user-entity participant" stops uniquely identifying
the owner.

## The fix

Filter on the ID directly instead of entity type alone — entity type
narrows the candidate set, `entity_meta.id == author_id` picks the
specific one:

```python
owner_participant = next(
    (
        p for p in conv_data.get("participants", [])
        if p.get("entity_name") == "user" and p.get("entity_meta", {}).get("id") == owner_id
    ),
    None,
)
assert owner_participant is not None, (
    f"...participant entry matching the owner (author_id={owner_id})..."
)
owner_name = owner_participant.get("meta", {}).get("user_name", "")
```

Confirmed green (2 consecutive clean runs, 0 reruns) after the fix.

## Actionable pattern

When reusing the ELITEA-2095 "cross-verify owner via ConversationAPI"
idiom on ANY conversation that may have invited/multiple human
participants (not just the owner): never assume `entity_name == "user"`
is unique. Always add the `entity_meta.id == author_id` filter up front
— it's strictly more correct even in the single-owner case (a no-op
there) and is the only correct form once invited users exist. Don't
special-case "well THIS test only has 2 invited users so I'll just check
count==3" — the ID filter is the same one-line cost and generalizes to N
invited users, group conversations, or future participant types.
