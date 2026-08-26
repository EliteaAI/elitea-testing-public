---
name: Console-noise filters must pair a status with a URL, never the URL alone
description: A URL-only known-noise filter drops every future status on that resource — masking; pair (status text, URL marker) and pin it with a unit test
type: feedback
aliases: [console noise filter scope, known background noise, secrets 403 filter]
tags: [area/console-errors, type/review-finding]
created: 2026-08-26
updated: 2026-08-26
---

## The correction (PR #1787 review, fix round 1)

ELITEA-2261/2263 shipped `KNOWN_BACKGROUND_NOISE_URL_MARKERS` matched by URL substring
alone, so the Axis-2 console assertion dropped **every** error naming
`/secrets/secrets/default/` or `/project_info/prompt_lib/` at **any** status. The
signatures actually observed live were a `403` on the secrets probe and a `500` on
project-info; the URL-only shape would also have swallowed a future `500` on the secrets
probe — a genuine backend regression shipping green.

`.agents/testing.md` § Merge gate is explicit: "Do NOT widen the #1753 filter (or any
filter) to swallow 400s — that is masking, not noise handling."

## The compliant shape (what every sibling spec already does)

```python
KNOWN_BACKGROUND_NOISE_SIGNATURES = (
    ("status of 403", "/secrets/secrets/default/"),
    ("status of 500", "/project_info/prompt_lib/"),
)
# both halves must match
```

Precedents to copy rather than re-derive: `_is_known_secrets_403` (chat suite,
`"403" in msg.text and "secrets/secrets/default" in (text + location_url)`) and
`_is_known_554_warning` (credentials suite, status + exact URL shape).

## And pin it

`tests/unit/test_credentials_console_filters_scope.py` is the template: a unit test that
(a) asserts the unscoped symbol name can never come back by copy-forward, and (b) feeds
status-swapped and resource-swapped messages through the filter expecting `False`. Build
the message strings via `utils.console_errors.format_console_message` so the test exercises
the real `"<type>: <text> @ <url>"` shape.

Related: [[artifacts_rest_calls_carry_project_id_as_query_param]]
