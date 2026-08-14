---
name: CredentialsSelect mismatch trap and group-header testid
description: ToolkitAPI.create_github_toolkit() hardcodes private=False (mismatches a personal-project credential); SELECT_OPTION values need single-quoted CSS attribute selectors; new select-group-header-{title} testid
type: feedback
---

## `ToolkitAPI.create_github_toolkit()` hardcodes `github_configuration.private=False`

If the linked credential was itself created in the identity's OWN
(`personal_project_id`) project, `CredentialsSelect.jsx`'s `selectedOption`
lookup (`availableSavedData = savedCredentialsMenuData.find(opt =>
opt.elitea_title === value.elitea_title && opt.private === value.private)`)
requires an EXACT match on both `elitea_title` AND `private`. A saved
personal credential always has `private: true` (computed from
`configuration.project_id === personal_project_id`), so pairing it with a
toolkit whose `github_configuration.private` is hardcoded `false` produces
NO match — the toolkit shows the RED mismatch state
(`credential-select-mismatch-footer` visible, `aria-invalid="true"` on the
combobox) **immediately after creation**, before any deletion/breakage
step ever runs. Confirmed live via a scratch diagnostic (dump
`[data-tour="shared-tool-configuration-form"]`'s `innerHTML`, grep
`data-testid`).

**Fix for a personal-project credential:** don't use
`create_github_toolkit()` — use `toolkit_api.create_toolkit(toolkit_type=
"github", settings={"github_configuration": {"elitea_title": ...,
"private": True}, "repository": ..., "active_branch": ..., "base_branch":
...})` instead. Don't touch the shared helper itself — other merged callers
(`github_toolkit` fixture, etc.) may rely on the `False` default for their
own scenarios; this is a per-test choice, not a shared-file fix.

## `select-option-{value}` testid values are JSON — CSS selector needs single quotes

`SingleSelectMenuItem`/`SingleSelect` action options carry
`data-testid="select-option-{JSON.stringify(...)}"`, e.g.
`select-option-{"kind":"create_action","private":true}`. Building the
Python-side locator template as `'[data-testid="select-option-{}"]'`
(double-quoted attribute value) breaks — the JSON payload's own double
quotes terminate the CSS attribute selector early
(`SyntaxError: ... is not a valid selector`). Use single quotes for the
attribute value instead: `"[data-testid='select-option-{}']"`. Build the
Python-side JSON string with `json.dumps(obj, separators=(",", ":"))` to
match JS's compact `JSON.stringify` output exactly (no spaces), and match
the app's own key order (`kind` before `private` for CREATE actions; `kind`,
`elitea_title`, `private` for saved rows — see `CredentialsSelect.jsx`'s
`createActionToSelectValue`/`savedRowToSelectValue`).

## New testid: `select-group-header-{group.key}` (SingleSelect.jsx)

The dropdown's `ListSubheader` title text ("CREATE" / "Saved {type}
Credentials") had no testid before ELITEA-1976 — added
`data-testid={`select-group-header-${groupKey}`}` on the header
`Typography` (`SingleSelect.jsx` `renderMenuItems`), where `groupKey =
group.key ?? `ss-grp-${groupIndex}``. `CredentialsSelect.jsx` sets
`group.key` to the raw title string, so values can contain spaces
(`select-group-header-Saved github Credentials`) — quote the CSS selector
value, same as above. Generic/data-driven (keyed by whatever `group.title`
the call site supplies), not feature-hardcoded — compliant with the
shared-component testid rule.

See also `fork_wizard_and_projectselect_testid_passthrough.md` — the
`SingleSelect.jsx` prop for a trigger testid is literally named
`data-testid` (not `dataTestId`); I re-hit that exact trap on
`CredentialsSelect.jsx`'s `<Select.SingleSelect>` call before catching it
via the same diagnostic-dump technique. Grep memory for `SingleSelect`
BEFORE wiring a new testid onto it, not after.
