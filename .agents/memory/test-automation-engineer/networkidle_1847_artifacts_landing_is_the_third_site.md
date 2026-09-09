---
name: Artifacts landing is #1847's third networkidle site — the endpoint is unpaginated
description: navigate_to_artifacts waited networkidle 15s against a 12-44s unpaginated bucket list; wait on the response instead
type: feedback
aliases: [navigate_to_artifacts timeout, artifacts/s3 slow, #1847, networkidle artifacts, bucket list 1217]
tags: [area/artifacts, type/flake-mechanism]
created: 2026-09-09
updated: 2026-09-09
---

## Mechanism

`ArtifactsPage.navigate_to_artifacts()` → `wait_for_page_load(15000)` →
`BasePage.wait_for_network()` → `page.wait_for_load_state("networkidle")`.
`networkidle` needs 500 ms of zero connections and this app holds a persistent
`/socket.io/` poll open — issue **#1847**, already confirmed on
`SkillsListPage.navigate_to_create` and `AdminUsersPage.ensure_team_project_selected`.

The Artifacts landing adds an amplifier the other two sites don't have: the
bucket-list request is **unpaginated**. Measured live 2026-09-09 on project 399
(**1217 buckets**): a healthy `GET /artifacts/s3/` took **12.4–43.8 s** (502/503
under load) against a **15 000 ms** budget. So it did not flake — it failed
deterministically whenever the backend was anything but fast, including on a
pristine page.

## The fix that worked

#1847's own prescription — wait on what the caller needs:

```python
with self.page.expect_response(
    lambda r: "/artifacts/s3/" in r.url and r.status == 200,
    timeout=self.BUCKET_LIST_RESPONSE_TIMEOUT,   # 60_000
):
    super().navigate("/artifacts")
expect(self.buckets_heading).to_be_visible(timeout=self.BUCKETS_HEADING_TIMEOUT)
```

`expect_response` **must wrap** the triggering navigation — it cannot be applied
after the fact. Use the class-level `buckets_heading` descriptor, not the inline
`get_by_test_id` that `wait_for_page_load` still uses (locator policy).

**Do not** wait on a bucket row (wrong for a genuinely empty project) or on the
empty-state element — product defect **#2073** renders a false
"No buckets created yet" for ~12 s while the list loads, so it is useless as a
settle signal.

Scoped to `navigate_to_artifacts()` only: `wait_for_page_load()` has ~14 direct
spec callers passing their own budgets, and `BasePage.wait_for_network()` has
~143 call sites. Result: Step 32 of ELITEA-1866 measured **18.3 s** and passed;
3 blast-radius artifacts specs stayed 5/5 green.

Related: [[tool_result_text_content_has_no_newlines]]
