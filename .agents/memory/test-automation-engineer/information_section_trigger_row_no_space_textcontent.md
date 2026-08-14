---
name: Information section Trigger row no-space textContent
description: ApplicationInformation.jsx's pipeline Trigger row concatenates label+value with no space in DOM textContent; also async-populated like the node combobox
type: feedback
---

`ApplicationInformation.jsx` (shared Information accordion, Agents + Pipelines) renders the
pipeline-only "Trigger:" row as two sibling `<Typography>` elements inside one `<Box
sx={styles.pipelineLink}>`. Confirmed live (2026-08-08/09, ELITEA-2041): `element.textContent` on
that Box is `"Trigger:Chat Message"` — **no space** between label and value. The visual gap
between them is CSS flexbox `gap`, not a text character. Any assertion against this row's text
must use the no-space form (`f"Trigger:{value}"`), not `"Trigger: {value}"` — the latter is a
case-text artifact, not the live product.

Also confirmed: this row is driven by the SAME `useGetPipelineTriggerQuery` RTK-Query hook as the
entry-point node's own Trigger combobox (`TriggerTypeSelector.jsx`) — one shared data source, and
subject to the identical async-population gap already documented for the combobox
(`test-specs/pipelines/_surface.md` § Entry point node — Trigger control): absent on the very
first paint after page load/reload, present ~1-2s later. Always wait for visibility
(`expect(locator).to_be_visible()`) before reading text; never read immediately.

The row had NO testid before ELITEA-2041 — added `information-trigger-row` on the wrapping `<Box>`
(`EliteaAI/EliteaUI@28dbc5e4`, pushed to `automation/testids`). Named generically (not
`agent-information-trigger-row` / `pipeline-information-trigger-row`) per the shared-component
naming ruling — same style as the pre-existing generic `copy-id`/`copy-version-id` testids in the
same component.
