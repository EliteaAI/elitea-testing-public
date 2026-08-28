# Never fix a TMS ref with a full `build_index` rebuild — it silently drops cases

**Learned:** 2026-08-28 (#1890 / ELITEA-1955), while correcting one stale
`automation_test_id` in `EliteaAI/onetest-ai-tm-Elitea`.

## What happened

The case file's ref was wrong (`tests.ui.pipelines.*` for a spec living in
`tests/ui/pipelines_2/`). Editing the case file is not enough — `correlate_results`
reads **`index.json` and `index_automated.json`**, which do not self-heal. The obvious
move is the `build_index` MCP verb. It reported:

```
✓ wrote index.json
2789 cases indexed
```

`index.json` held **3073**. A full rebuild would have dropped ~284 cases — and it writes
**server-side**, so the local clone showed no diff and `git status` stayed clean. The gap
is invisible unless you compare the reported count against the file yourself.

`git log` then showed this had already happened once: EliteaAI/onetest-ai-tm-Elitea@312b5a8
— *"revert(index): replace full rebuild with the surgical ELITEA-2020 edit"* — backing out
`fd9d457` ("rebuild index.json (3097 cases)") at 51 insertions / 699 deletions.

## The rule

**Back-write the index surgically. Never bulk-rebuild it.**

```bash
cd ../onetest-ai-tm-Elitea
sed -i '' 's|"<old.dotted.ref>"|"<new.dotted.ref>"|' index.json index_automated.json
python3 -c "import json;[json.load(open(f)) for f in ('index.json','index_automated.json')];print('valid')"
git diff --stat        # expect exactly 1 changed line per file
```

Both files — the ref appears in each. Validate the JSON afterwards; a `sed` that eats a
quote is a silently corrupt index.

## Related, and also true

The TMS repo's **`build-index` CI is failing** (3 consecutive failures as of 2026-08-28),
so the #1776 closure note's claim that it "auto-rebuilt `index_automated.json`" is stale.
Assume the index is only as correct as your own edit. Tracked on #1777 (64 refs still stale).

## The general shape

A verb that reports a count is offering you a checksum. Compare it against the artifact
before letting it overwrite one — especially when it writes somewhere you cannot `git diff`.
