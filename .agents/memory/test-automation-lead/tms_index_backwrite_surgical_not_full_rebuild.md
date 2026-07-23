---
name: TMS index.json back-write must be a surgical single-entry edit, not a full rebuild
description: Rebuilding onetest index.json for a one-case back-write produces a huge multi-case diff (the index is 300+ cases behind disk); edit only the delivered case's entry and flag the systemic drift separately
type: feedback
---

Post-merge TMS back-write for a single case (#370/ELITEA-2167) requires the case's
`automation_test_id` to reach `index.json` (what `correlate_results` reads). But the
committed `index.json` is chronically stale — 2226 indexed vs 2542 `.md` files on disk
(the "build-index CI is a stub" gap, `.agents/test-automation.yaml`). Running the full
rebuild (`onetest-tms/scripts/_index.py --dir tests --out index.json`) reindexes ALL
cases → a +7039/-984-line diff spanning ~283 OTHER cases.

**Do NOT commit a full rebuild in a single-case back-write.** It's scope creep, and it
would silently absorb other cases' contradictory metadata into your delivery commit.

**Surgical approach that yields a clean 1-entry diff:**
```python
# revert any full rebuild first: git checkout HEAD -- index.json
import json
idx = json.load(open("index.json", encoding="utf-8"))
for c in idx["cases"]:
    if c["id"] == "ELITEA-XXXX":
        c["status"] = "ready"; c["execution_type"] = "automated"
        c["automation_test_id"] = ["tests.<...>.Form.C.id"]   # LIST, even for one ref
        break
open("index.json","w",encoding="utf-8").write(json.dumps(idx, indent=2, ensure_ascii=False)+"\n")
```
Re-dumping the SAME structure (same `indent=2, ensure_ascii=False`, trailing `\n` — the
script's exact format) with one entry changed gives a diff of only that entry. Verify
`git diff --numstat index.json` is small before committing. (The case whose entry you
edit must already be IN the index; a brand-new case not yet indexed genuinely needs a
rebuild — but then flag the drift, don't bundle it.)

**Flag the systemic drift separately** — I filed #991 (316 unindexed cases → all
invisible to correlation). It's a factory-wide infra gap, not one case's job to fix.

Also: self-check the Form C id against the real junit BEFORE committing —
`grep 'classname="<pkg.Class>".*name="<method>"' reports/junit.xml` must MATCH (it's the
exact `classname + "." + name` correlate_results compares against).
