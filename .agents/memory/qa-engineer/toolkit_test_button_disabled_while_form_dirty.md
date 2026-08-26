---
name: Toolkit/MCP detail Test button is disabled while the form is dirty
description: Load Tools dirties the form, so you must Save and wait before the action bar's Test button becomes clickable
type: project
aliases: [toolkit-test-button disabled, cannot click Test MCP, isTestDisabled, load tools then test]
tags: [area/mcp, area/toolkits, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

`ToolkitForm.jsx` renders the action bar's Test button with
`isTestDisabled={dirty}` (`src/pages/Toolkits/ConfigurationTab.jsx` passes the
form's `dirty`). Clicking **Load Tools** dirties the form.

So this sequence hangs on a permanently disabled element:

```
open /mcps/all/{id} → Load Tools → click toolkit-test-button   ✗ disabled forever
```

The working sequence (confirmed live 2026-08-24, MCP id 2140):

```
open /mcps/all/{id} → Load Tools (wait 3/3) → toolkit-detail-save-button
                    → WAIT for toolkit-test-button to enable → click it
```

## Second async trap on the same page

After a client-side navigation **back** to the detail page, the action bar mounts
asynchronously — `pipeline-history-tab` returned *"does not match any elements"*
on an immediate click and appeared on a later poll. Same class as the known
`toolkit-type-card-mcp` async-mount note. Use framework auto-waiting or an
explicit `wait_for(state="visible")`; never an immediate `query_selector`.

Related: [[mcp_test_settings_route_refactor_el6277]]
