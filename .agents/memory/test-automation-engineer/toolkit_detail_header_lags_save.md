---
name: Toolkit/MCP detail header lags the update PUT
description: toolkit-detail-title still shows the OLD name right after a 200 PUT — assert it with a retrying expect(), never a bare text read
type: feedback
aliases: [detail title stale after save, toolkit-detail-title lag, rename header flake, no toast on toolkit save]
tags: [area/mcp, area/toolkits, type/flake-trap]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

On `/mcps/all/{id}` (and the shared `/toolkits` detail page), the header
`toolkit-detail-title` is fed from the breadcrumb's cached entity data, which is
NOT refreshed synchronously with the update `PUT .../tool/prompt_lib/{p}/{id}`.

Measured live 2026-08-24 (ELITEA-1925), two probes on freshly seeded MCPs:

| Read moment | Header shows |
|---|---|
| immediately after the PUT resolved 200 | **OLD** name |
| ~5 s later (and +2/+5/+10 s, and after a full reload) | new name, stable |

So a bare `get_detail_heading_text() == new_name` right after Save is a coin
flip — it failed on probe 1 and only "passed" on probe 2 because an unrelated
5 s lookup happened to sit in between. Use
`expect(form.detail_title).to_have_text(new_name, timeout=20_000)`.

The name **field** (`toolkit-form-name-input`), the update response body, and
the MCP list are all correct immediately — only the header lags.

## Related gotcha: no success toast on this surface

`ToolkitsTabBarContainer.jsx` calls `toastSuccess('The toolkit has been updated
successfully')`, but `toast-message` never appears within a 5 s wait (confirmed
on two independent probes). Do not wait on a toast to prove a detail-page save —
wait on the PUT 200 (`McpFormPage.save_and_wait_for_updated`).

## And: detail Save/Discard ARE honestly dirty-gated

Unlike the *create* form (#633, where Save ignores required-field validity), the
detail page's Save and Discard both gate on `isFormDirtyExcluding`
(`ToolkitsTabBarContainer.jsx:102-109` and `:157-160`): both disabled pristine,
both enabled after touching one field. A "becomes enabled after editing"
assertion is real here — don't carry the #633 caution across.

Related: [[mcp_toolkit_create_form_implementer_quirks]]
