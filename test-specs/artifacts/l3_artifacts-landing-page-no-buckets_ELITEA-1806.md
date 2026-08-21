# Test Case: Artifacts Landing Page – UI Elements with No Buckets

## Metadata
- **TMS ID**: ELITEA-1806
- **Linked Story**: none
- **Priority**: l3 (TMS `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot, artifacts-w01 cluster ELITEA-1803/1804/1805/1806, 2026-08-21)
- **Status**: blocked

## Blocked Steps

**What could not be produced honestly: the case's single precondition — "the
project has no buckets."**

Every project the automation user can reach contains buckets. Measured live via
`GET {ELITEA_API_BASE}/artifacts/buckets/default/{project_id}` for all five
projects offered by the UI's project selector (2026-08-21):

| Project | Id | Buckets |
|---|---|---|
| Private | 399 | 759 |
| Bugs & Features | 406 | 4 |
| Elitea Development | 25 | 19 |
| Elitea Testing Team | 471 | 13 |
| UI Testing | 400 | 2 |

None is empty, and none can be *made* empty honestly:

- **Emptying an existing project is destructive to shared data.** Projects 400 /
  471 / 399 are live test fixtures for other suites (e.g.
  `test_bucket_permissions_api.py`), and 399 carries 759 accumulated buckets
  (the `#636` teardown leak). Deleting them to satisfy a rendering case would be
  a far larger mutation than the case is worth, and unrepeatable.
- **Creating a throw-away project is outside the suite's capability.** There is
  no project-create/delete client in `automation/api/` and no fixture for it;
  project lifecycle is an account-level, human-scoped operation here.
- **The empty state cannot be reached any other way.** `BucketsPanel.jsx` gates
  it on `buckets.length === 0` for the *selected* project. The visually similar
  filtered-empty state ("No buckets found" / "Try adjusting your search terms",
  reachable via the bucket search) is a **different** branch with different text
  — asserting the case against it would be a substitution of the subject.

Faking it — intercepting the buckets response, or injecting state — would be a
**terminal substitution**: every observable this case asserts (both empty-state
messages, the placeholder, the zero-count footer) is exactly the thing that
would be fabricated. Forbidden by `.agents/testing.md` § Fidelity policy, and
the case text does not ask for simulation. So this is routed to a human rather
than engineered around.

**What would unblock it (human decision, one of):**
1. Provision a dedicated, bucket-free project for the automation user (and keep
   it bucket-free) — then this case is `ready-for-automation` as written, with
   `BasePage.switch_project()` selecting it; or
2. Sanction adding project create/delete API support to the suite so the test
   can provision its own empty project per run; or
3. Re-scope the case as manual-only.

## Case-text findings (source-verified, NOT live-verified — the state was unreachable)

- **Step 3** claims the LEFT panel shows `No buckets created yet` **and** a
  subtitle `Create your first bucket to get started`. In
  `Components/BucketsListContent.jsx` the `BUCKET_TYPES.EMPTY` branch renders
  **one** Typography, `No buckets created yet.` (with a trailing period) and
  **no subtitle**. The only subtitle-like text lives in the MAIN area's
  `EmptyStatePage` and reads differently:
  `Create your first bucket to organize and manage your artifacts in one place.`
  (`Artifacts.jsx`).
- **Steps 4-5** (main area) match the source: `EmptyStatePage` renders the
  `EmptyArtifactBucketsIcon`, then the title `No buckets created yet`
  (`data-testid="empty-state-title"`), then the description above, then a
  `Create` button the case text does not mention.

These are stated as **source reads, not live observations** — the state could
not be reached — and should be re-verified before the case text is edited.

## Testids
**None added for this case.** The left-panel empty-state Typography has no
testid; adding one for a case that cannot run would be a blanket add
(`.agents/testing.md` § Locator policy — testids go only on elements tests
actually touch). It is deliberately left for whoever unblocks this case.

## Coverage Map
Not applicable — the case never reached execution. No step was verified live.
