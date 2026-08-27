---
name: A green CI run can mean zero tests ran
description: pytest exits 0 when everything skips, so a dev-stable run that skipped 259/259 on auth failure reported success — always open the JUnit before trusting a gate
type: feedback
aliases: [false green, 100% skip, all tests skipped, CI success but nothing ran, auth skip, dev-stable green]
tags: [area/ci, type/gotcha]
created: 2026-08-26
updated: 2026-08-26
---

## The trap

`pytest` exits **0** when every test SKIPs, so `test-ui-dev-stable.yml` (via
`test-ui-custom.yml`) concludes **`success`** on a run that verified nothing.
Every job green, Allure report published, badge green.

Observed 2026-08-26 while gating #1810/ELITEA-2016:

| Run | Scope | Reported | Reality |
|---|---|---|---|
| 32998986791 | `pipelines,pipelines_2` | ✅ success | 102 tests, **102 skipped** |
| 32999476644 | `all`, 9 executors | ✅ success | 259 tests, **259 skipped**, 155s wall |

Cause both times: `Authentication failed — check TEST_USER_EMAIL and TEST_USER_PASSWORD`
against the Keycloak `dev` realm. I nearly merged on the first green.

## The tells

- **Wall time.** A full `all` suite that normally takes ~30 min finished in **155 s**.
  Absurdly fast is the loudest signal.
- The GHA job summary does not surface skip counts — you must open the artifact.

## Always do this before treating a CI run as a gate

```bash
gh run download <id> --repo EliteaAI/elitea-testing-public --dir /tmp/x
# then, per test-results-*/junit.xml, check tests vs skipped:
python3 -c "
import xml.etree.ElementTree as ET,glob,collections
t=collections.Counter()
for p in glob.glob('/tmp/x/test-results-*/junit.xml'):
    r=ET.parse(p).getroot()
    for s in ([r] if r.tag=='testsuite' else r.iter('testsuite')):
        for k in ('tests','failures','errors','skipped'): t[k]+=int(s.get(k) or 0)
print(dict(t))"
```
`skipped == tests` ⇒ the run is worthless as evidence, whatever its conclusion says.
Also grab the skip *message*: an infrastructure skip (auth, provisioning) is never a
legitimate skip; a missing-credential feature guard (e.g. `GIT_HUB_TOKEN` unset) is.

Filed as [#1822](https://github.com/EliteaAI/elitea-testing-public/issues/1822) — proposed
fix is to hard-fail when `skipped == tests` or when the skip reason is an infra one.

Related: [[gating_a_fix_on_dev_via_workflow_dispatch]]

## 2026-08-27 — this is now a SUSTAINED OUTAGE, and the nightly is affected

Not a one-off any more. Measured by `grep -c` over each run's `agents` job log:

| Run | UTC | SKIPPED | PASSED |
|---|---|---|---|
| 32931571484 | 08-26 **04:48** | 0 | **27** |
| 32999476644 | 08-26 **18:23** | **33** | 1 |
| 33039314963 | 08-27 04:24 — **scheduled nightly, `main`** | all | 0 |
| 33043606347 | 08-27 05:47 — my own verification run | all | 0 |

DEV Keycloak rejects **every** automation user (`autotest_user_1`, `autotest_user_5`
confirmed) with `Login failed: 200 .../realms/dev/login-` — the `200` means the login
page re-renders, i.e. credentials rejected, not a service outage. Broke between
08-26 04:48 and 18:23. Filed **#1850**; the masking half is **#1845** (occurrence +
timeline added there).

**The consequence that actually bites this role:** the `[Fix]` cards this factory works
are generated from these runs. A silently-skipped test can never be reported as failing,
so **"no new [Fix] cards" reads as "the suite got healthier" when it means "the suite
stopped running."** Absence of red is not evidence of green. Before treating a quiet
period as improvement, check a recent run's SKIPPED-vs-PASSED counts.

**Operational rule, reinforced:** the 04:48 control run is what made the diagnosis
airtight — same workflow, same realm, same users, 27 tests genuinely executed. When a
run looks empty, find the last run that wasn't and diff the conditions; don't reason
from the failing run alone.
