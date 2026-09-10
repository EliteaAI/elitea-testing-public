---
name: Removing a manual navigate exposes the absence check it was hiding
description: Dropping a fallback list_page.navigate() turns a sampled absence assert into a race and a toast false-positive
type: feedback
aliases: [absence check after delete, pipeline_exists_in_list race, deleted card still listed, vacuous to_have_count zero, delete success toast carries the name]
tags: [area/ui, type/flake]
created: 2026-09-10
updated: 2026-09-10
---

## The trap

A repair that removes a manual `navigate()`/reload has a **second-order effect nobody
specs**: every assertion downstream of it silently loses the settle that `goto` +
networkidle was providing. ELITEA-2022 (board #2139) replaced a deep-link arrival with
an in-app one and asserted the post-delete redirect. The AFS said Step 5's absence check
was unchanged. It was not — it failed **0.03 s** into the step, three ways at once:

1. **`pipeline_exists_in_list()` samples; it does not wait.** It only waits for the name
   to APPEAR and returns True the instant it sees it. The post-delete redirect is a
   history-back, so the dashboard repaints its **cached** list — deleted card still on
   it — and drops the card only when the refetch lands. The old `list_page.navigate()`
   absorbed that refetch.
2. **The success toast carries the entity name** ("The `<name>` pipeline has been
   successfully deleted.") and is still on screen, so any page-wide `text="<name>"`
   match conflates "gone from the list" with "named in the toast". Scope absence to the
   list's own card testid.
3. **A mid-refetch grid renders skeletons and ZERO card-name nodes**, so a bare
   `to_have_count(0)` on the card handle passes **vacuously** — the negative-direction
   twin of the board #2118 / ELITEA-2024 trap.

## The shape that survives all three

```python
card = self.entity_card_name.filter(has_text=name)
expect(card).to_have_count(0, timeout=t)                                    # wait it OUT
expect(self.entity_card_name.first.or_(self.empty_state_title)).to_be_visible(timeout=t)  # grid RENDERED
expect(card).to_have_count(0, timeout=t)                                    # re-assert on it
```

`.or_()` keeps the settle check a single strict match whether the list has content or is
legitimately empty. Shipped as `PipelinesListPage.wait_for_pipeline_absent()`.

## Transferable rule

When a repair deletes a navigation/reload, **re-derive every assertion after it** — ask
what that call was settling, not just what it was navigating to. And read the failure
SCREENSHOT before theorising: this one showed the skeleton grid and the name-bearing
toast in a single frame, which is all three causes at once.

Related: [[pipeline_delete_redirect_depends_on_arrival_path]]
