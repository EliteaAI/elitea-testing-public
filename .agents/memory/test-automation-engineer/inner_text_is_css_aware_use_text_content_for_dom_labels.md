---
name: inner_text is CSS-aware — use text_content for DOM label assertions
description: Playwright inner_text() applies text-transform, so an uppercase-looking assertion silently conflates DOM text with CSS casing
type: feedback
aliases: [inner_text vs text_content, text-transform uppercase assertion, CSS-rendered casing, uppercase column labels]
tags: [area/playwright, type/assertion-strength]
created: 2026-08-28
updated: 2026-08-28
---

## The trap

`Locator.inner_text()` returns the **CSS-rendered** text; `text_content()` returns the raw DOM text.
Where a stylesheet carries `text-transform: uppercase`, `inner_text()` gives `EVENT TYPE` while the
JSX literally says `Event Type`.

Asserting the uppercase string alone is a **weaker** assertion than it looks: it passes equally if
the DOM label were hardcoded `EVENT TYPE` and the transform dropped. It also silently contradicts an
AFS that specced the title-case DOM text.

## The compliant shape

Assert the two halves separately:

- `text_content()` per cell -> the DOM labels (title case)
- `el => window.getComputedStyle(el).textTransform` -> `"uppercase"`

That needs a **per-cell handle**, so a repeated testid on the cells is the work
(`analytics-health-table-header-cell`, EliteaAI/EliteaUI@1a1fa5f4) — the parent container only
yields a concatenated (`text_content`) or CSS-rendered (`inner_text`) string.

The computed-style `evaluate()` is **not** a fidelity substitution: it OBSERVES what the product's
own stylesheet computed. Playwright has no computed-style accessor, and the suite already does this
(`notification_center_page.COMPUTED_COLOR_JS`, `agent_form_page`). Keep the JS in an UPPER_CASE
class constant, not inline in a method.

## Where it bites

Anywhere a case text writes a label capitalised because the UI *looks* capitalised. Known in-repo
precedents: `ArtifactsPage.buckets_heading` ('Buckets' vs case's 'BUCKETS'),
`ToolkitDetailPage.SELECT_GROUP_HEADER`, the whole `settings-analytics` table-header family.

Related: [[base_page_capture_console_errors_is_url_less]]
