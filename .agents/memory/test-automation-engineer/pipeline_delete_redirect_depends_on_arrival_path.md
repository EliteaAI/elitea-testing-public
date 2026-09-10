---
name: Post-delete redirect is navigate(-1) — the arrival path decides whether it fires
description: EliteaUI history-backs after delete, so a page.goto() precondition manufactures a redirect "bug"
type: feedback
aliases: [navigate(-1) redirect, delete pipeline redirect, deep link stranded after delete, "#1332"]
tags: [area/ui, type/fidelity]
created: 2026-09-10
updated: 2026-09-10
---

## Fact

EliteaUI's post-delete redirect (`DeleteApplicationButton.jsx`, fired from the success
toast's `onCloseToast`) is `navigate(-1)` — React Router **history-back**, not a
navigate-to-route. So it fires when the detail page was reached in-app (dashboard card
click, or landing there after Save) and no-ops on a `page.goto()` deep link with empty
history. The same `useDeleteApplication` hook backs **Agents**, so expect it there too.

Measured on `dev.elitea.ai` (board #2139): in-app arrival redirects 3/3 (0.1-1.7 s after
`delete_pipeline_via_menu()` returns), deep-link arrival 0/3.

## Why it matters beyond one case

`PipelineDetailPage.navigate(pid)` in a precondition is a **wrong-interface substitution**
that is *observable-changing*, not transit — it manufactures the exact condition the
case's own observable cannot survive, and the resulting red was filed and carried as a
sanctioned-RED defect (`#1332`) for a month. `#1332` is still a real bug for real
deep-link users; it just is not what the case tests.

**Rule:** a case whose observable is a *redirect, a back-navigation, or anything reading
browser history* must reach its starting page the way the case's user does. Ask "does the
product read history here?" before choosing a `goto` precondition for speed.
