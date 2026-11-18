---
name: batch elitea-4716-4717 lessons (2026-11-18)
type: project
---
- Sandbox lacks automation/.env.test: export `APP_PREFIX=/app` on the pytest command line, else every pipelines spec 404s ("Page Not Found"). A fixer reported "blocked" for this reason; lead re-ran green.
- haiku slots (triage/report/merge) 403 for this team — report.json is written by the lead; pass an allowed model for mergeModel/reporterModel/triageModel next run.
- CodeMirror `.cm-line:text-is()` never matches (spans split text) — use `:has-text()`.
- Case-text drift on Save-disabled/button label/canvas drag step → question #2980.
