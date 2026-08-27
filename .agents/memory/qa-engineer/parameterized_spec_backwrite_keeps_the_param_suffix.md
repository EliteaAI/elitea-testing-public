---
name: Parameterized spec back-write keeps the [param] suffix
description: A family spec's automation_test_id must carry the pytest param id, because junit's name attribute does
type: reference
aliases: [automation_test_id parametrize, family AFS back-write, param id correlation]
tags: [area/tms, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## The fact

`_junit.py` builds the correlation `code_ref` as `classname + "." + name`, and for a
parameterized test pytest's junit `name` attribute **includes the bracketed param id**
(`test_x[ELITEA-2289-vscode]`). So the Form C ref for a family spec is:

```
tests.ui.admin.test_personal_token_ide_config_download.TestPersonalTokenIdeConfigDownload.test_ide_download_icon_generates_config_file[ELITEA-2289-vscode]
```

Dropping the suffix fails correlation **silently** (🟥 gap, never an error), exactly like
the `automation.`-prefix and node-id drifts in `.agents/test-automation.yaml`
§ backwrite_on_done.

Precedent in the TMS repo (verified 2026-08-27, `grep automation_test_id` in
`onetest-ai-tm-Elitea/tests/`): ELITEA-2107 / ELITEA-2108 both back-write
`…test_rename_checkmark_inactive_click_has_no_effect[ELITEA-2107-1-char]` — quoted,
because the brackets need YAML quoting.

## Why the param id shape matters to the reviewer

This is the reason a family spec's param ids should start with the TMS case id
(`pytest.param(..., id="ELITEA-2289-vscode")`): one case id ⇒ one param ⇒ one greppable
back-write ref, and a failing param names its own case in the pytest tail.

Related: [[afs_filed_issue_claims_need_tracker_verification]]
