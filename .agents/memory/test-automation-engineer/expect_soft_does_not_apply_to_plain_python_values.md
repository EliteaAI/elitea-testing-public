---
name: expect.soft() is a locator assertion — it cannot soft-assert a parsed value
description: AFS text saying "expect.soft()" on a parsed JSON/XML field is untranslatable; use the repo's soft_failures list + trailing pytest.fail() instead.
type: feedback
aliases: [soft assert parsed json, expect.soft plain value, soft_failures pattern, sanctioned red non-locator]
tags: [area/assertions, area/known-defects]
created: 2026-08-27
updated: 2026-08-27
---

## The gap

`expect.soft(...)` in `playwright.sync_api` takes a **Locator** (or Page/APIResponse). An
AFS that says *"assert X with `expect.soft()` + `# Known defect: #N`"* about a value you
got from `json.loads(body)["key"]` or `ET.fromstring(...)` is describing the INTENT
(sanctioned-RED, one isolated assertion, everything else hard) — not a literal API call.
There is no Playwright locator behind a parsed dict key.

## The project's actual shape

Collect into a list, fail once at the end, outside the `finally:` cleanup:

```python
soft_failures: list[str] = []
...
# Known defect: #1884 — assert the CORRECT value, never the buggy one
if parsed["eliteacode.authToken"] != token_value:
    soft_failures.append(
        f"eliteacode.authToken does not carry the token the generation dialog showed "
        f"(expected the full {len(token_value)}-char value, got "
        f"{parsed['eliteacode.authToken']!r}) — Known defect: #1884"
    )
...
if soft_failures:
    pytest.fail(
        "Known-defect soft failures were recorded (everything else in this case "
        "passed cleanly):\n" + "\n".join(soft_failures)
    )
```

Merged precedent: `tests/ui/settings/test_settings_sidebar_item_navigation.py`,
`tests/ui/chat/test_team_users_mention_and_remove_participants.py`,
`tests/ui/artifacts/test_artifacts_create_bucket_56char_limit_warning_delete_cancel.py`.

## Why the outcome is identical

`.agents/testing.md` § Merge gate already establishes that `expect.soft` failures ARE
pytest FAILEDs. So does `pytest.fail()`. Both make the spec **sanctioned-RED** and both
owe a closure-record entry and an `expected_red[]` declaration. Nothing about the gate
semantics changes — only the mechanism.

Put the `pytest.fail()` AFTER the `finally:` block so cleanup still runs, and keep the
`# Known defect: #N` comment at the assertion site, not only in the message.
