---
name: Known-noisy resource — Montserrat webfont 404 from fonts.gstatic.com
description: An intermittent 404 loading the Montserrat font (Google Fonts CDN, app-wide, loaded via index.html on every page) trips "zero console errors" assertions on ANY test that opens the app. Filed EliteaAI/elitea-testing-public#1434. Filter idiom already exists — don't re-diagnose from scratch.
type: feedback
---

## What it is

`EliteaUI/index.html` loads Montserrat via a Google Fonts CSS `<link>` — an
app-wide resource fetch on literally every page render, unrelated to any
specific feature or test. `fonts.gstatic.com` URLs are content-hashed and
essentially never 404 once published, so this reads as a transient CDN/network
blip, not a broken reference. No product-side fix is possible.

Signature:
```
text:         "Failed to load resource: the server responded with a status of 404 ()"
location.url: "https://fonts.gstatic.com/s/montserrat/v31/....woff2"
```

## Frequency (measured, 2026-08-11, issue #1391)

Hit **4 times** across 3 different agent_hub cases (ELITEA-2361, twice on
ELITEA-2353) in one session — roughly 1-in-6 to 1-in-20 fresh runs. Rare
enough that implementer's own 3x local runs and a fresh reviewer's static
review BOTH missed it every time; only the **lead's own independent gate**
(run separately, after review) caught it, 4/4 times.

## The fix — already established, copy it, don't rediscover

`_is_known_1434_montserrat_font_404(msg)` — match on BOTH `msg.text`
containing `"404"` AND `(msg.location or {}).get("url", "")` containing
`fonts.gstatic.com`/`montserrat` (never a blanket "any 404" filter). See
`automation/tests/ui/agent_hub/test_agent_hub_started_conversation_has_agent_as_participant.py`
for the canonical implementation (console-message form) and
`test_agent_hub_started_conversation_has_agent_as_participant.py`'s
`_is_known_1434_montserrat_font_404_response` for the network-response-status
side-channel variant (if the test also listens on `page.on("response", ...)`).

**For dispatch prompts:** tell the implementer to proactively apply this
filter to any new `assert not console_errors`-style side-channel check in the
agent-hub/catalog area, rather than waiting to rediscover the flake from
scratch (ELITEA-2362's implementer did this unprompted after seeing the
ELITEA-2361 fix — worked first try, no lead-gate failure).

## Why this belongs to the lead's gate, not review

Neither the implementer's nor the reviewer's own local runs are the merge
gate (`.agents/testing.md` § Merge gate) — this is the concrete, repeated
proof of why: a rare (~1-in-10) flake will statistically slip past 2 separate
3-run samples before the lead's own (also 3-5 run) sample catches it. Don't
skip your own gate because "implementer and reviewer both ran it clean."
