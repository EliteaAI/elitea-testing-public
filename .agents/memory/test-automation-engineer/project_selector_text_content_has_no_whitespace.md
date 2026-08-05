---
name: project selector text_content has no whitespace
description: get_selected_project_text() raw text is "PProject:Private" (avatar-initial span + no-space divs), never "Project: Private" — assert substring, not equality
type: feedback
---

`ChatPage.project_selector_trigger` (`project-selector-trigger-combobox`)
renders three sibling nodes with **zero whitespace between them**: an
avatar-initial `<span>` (e.g. "P" for a project starting with P), then two
`<div>`s ("Project:" / "<name>"). `element.textContent` / Playwright
`text_content()` therefore concatenates to `"PProject:Private"`, never the
human-readable `"Project: Private"`.

`ChatPage.get_selected_project_text()` does no cleanup — it returns this raw
concatenation verbatim.

**Confirmed live via `browser_evaluate` innerHTML dump** (ELITEA-2350,
2026-08-05):
```json
{"text": "PProject:Private", "html": "<div ...><span ...>P</span></div><div ...><div>Project:</div><div>Private</div></div>"}
```

**Implication:** never assert `get_selected_project_text() == "Project: <name>"`
— it will fail on a non-defect (reverse-masking guard). Assert substring
membership instead: `"<name>" in chat.get_selected_project_text()`. This
matches the existing idiom in `test_open_conversation_today_section.py` /
`test_credential_create_private_from_toolkit_dropdown.py` — they already avoid
exact equality, apparently for exactly this reason (not documented until now).

An AFS that specs an exact `"Project: X"` match against this element is
stale — amend it in-place rather than writing the test to the stale string.
