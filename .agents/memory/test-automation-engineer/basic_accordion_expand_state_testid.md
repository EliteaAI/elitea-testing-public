---
name: BasicAccordion expand state needs items[].testId, not the accordion's data-testid
description: EliteaUI BasicAccordion puts data-testid on an outer Box; aria-expanded lives on the inner summary, reachable only via items[].testId
type: project
aliases: [accordion aria-expanded, BasicAccordion testid, accordion summary testid, expand state accordion]
tags: [area/eliteaui, type/locator]
created: 2026-08-29
updated: 2026-08-29
---

## The trap

`src/[fsd]/shared/ui/accordion/BasicAccordion.jsx` accepts **two** testid inputs
and they land on different nodes:

- the component's own `data-testid` prop -> the **outer wrapper `Box`**;
- each `items[].testId` -> that item's **`StyledAccordionSummary`**, which is the
  node carrying `aria-expanded`.

So `expect(page.get_by_test_id("ai-configurations")).to_have_attribute(
"aria-expanded", "true")` can never pass, even though the accordion IS expanded —
the attribute is one level down. An AFS that says "the accordion's summary carries
aria-expanded" is describing a node with no handle until you pass `items[].testId`.

## What to do

Add `testId: '<section>-accordion-summary'` to the item entry in the *calling*
feature component (e.g. `ProjectGeneralContent.jsx`), not to `BasicAccordion` —
the prop already exists, so it is a pure attribute addition, zero plumbing, and it
passes the zero-functional-impact greps.

Worked instance: `ai-configuration-accordion-summary`, EliteaAI/EliteaUI@2deb9655
(ELITEA-2394 / ELITEA-2393).

Related: [[settings_ai_configuration_surface]]
