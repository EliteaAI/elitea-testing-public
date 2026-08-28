# Known issues found while exploring settings-analytics

> Part of the `settings-analytics` exploration digest — index: [`_surface.md`](../_surface.md).
> Handle cache from live exploration, not a source of truth: verify a handle as you use it.

## Case-text clarifications (product is correct, the case text is stale)

| Issue | Case | What drifted |
|---|---|---|
| elitea-testing-public#1185 | ELITEA-2310 | "six tabs" / "Last 24d" — live 8 tabs, `Last 24h` default |
| elitea-testing-public#1188 | ELITEA-2312 | 8 columns incl. non-existent `Events`; ERRORS red at `>0` not `>=0` |
| elitea-testing-public#1191 | ELITEA-2313 | 6 KPI cards on user detail — live 10; panel 3 naming |
| elitea-testing-public#1195 | ELITEA-2320 | tab/chart/table naming, `Events` -> `Runs` |
| elitea-testing-public#1199 | ELITEA-2321 | 5 KPI cards incl. non-existent `Error Rate` — live 8 |
| elitea-testing-public#1948 | ELITEA-2311 | six KPI cards -> eight; `AGENT RUNS` -> `AGENT & PIPELINE RUNS`; adoption badge is conditional |
| elitea-testing-public#1949 | ELITEA-2324 | Health rows are data-driven, not the fixed six (live 5, no `agent`) |
| elitea-testing-public#1950 | ELITEA-2325 | `Calculation`/`Data source` optional (14 and 7 of 43); blue is on the VALUE |

## Product defects

### Product defect found this run
- **elitea-testing-public#1951 (MINOR)** — analytics count labels are not pluralised: a single
  result reads `1 users` / `1 tools` / `1 agents & pipelines`. All specs in this feature should
  assert the literal live format so they stay honest.

- **elitea-testing-public#1192** — a user with no `user_email` renders a BLANK detail-view title
  (no `User {id}` fallback). Pick a row WITH an email for happy-path assertions in that view.
