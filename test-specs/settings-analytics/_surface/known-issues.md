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
| elitea-testing-public#1954 | ELITEA-2326 | Overview Daily Activity tooltip has FOUR series (three on a personal project), none named `Events` |
| elitea-testing-public#1955 | ELITEA-2327 | chart is `Most Active Agents & Pipelines`; tooltip metric is `Runs`, not an "event count" (sibling of #1195) |
| elitea-testing-public#1950 | ELITEA-2325 | `Calculation`/`Data source` optional (14 and 7 of 43); blue is on the VALUE |

## Product defects

### Product defect found this run
- **elitea-testing-public#1951 (MINOR)** — analytics count labels are not pluralised: a single
  result reads `1 users` / `1 tools` / `1 agents & pipelines`. All specs in this feature should
  assert the literal live format so they stay honest.

- **elitea-testing-public#1192** — a user with no `user_email` renders a BLANK detail-view title
  (no `User {id}` fallback). Pick a row WITH an email for happy-path assertions in that view.

### Known noise — a wide-range analytics query can return `502`, and the suite's rerun filter does NOT catch it

During ELITEA-2314's fix round 1, one of five invocations of
`test_presets_update_pickers_and_refresh_content` failed on
`AssertionError: Last 30d: analytics request returned 502 / assert 502 == 200` after 38 s; it passed
standalone immediately after (42.77 s) and in the full-set run that followed (14 passed,
`reruns.json == {}`). Same family as the "wide-range queries are SLOW" entry in
[`date-filter.md`](date-filter.md) — a gateway giving up on the 30-day query, not a code defect.

⚠️ `pytest.ini`'s `--only-rerun="502 Server Error"` matches the **requests/HTTPError** wording; an
assertion that formats the status itself (`returned 502`, `assert 502 == 200`) does not contain that
phrase, so pytest-rerunfailures does **not** retry it. Any spec asserting `response.status == 200`
on a slow analytics range is exposed to a hard red from this. Raised to the lead as a finding rather
than fixed in a fix round — widening a shared rerun filter is a suite-wide blast radius.
