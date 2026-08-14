---
name: TMS case-to-issue mapping is not in the case snapshot
description: case snapshots under .agents/automation/<slug>/cases/ don't carry the tracking issue number — capture it at intake, or reconstruct via strict "[Automate][ELITEA-<id>]" title match, never a bare-ID substring match.
type: feedback
---

## The gap

`.agents/automation/<slug>/cases/ELITEA-<id>.md` (the intake snapshot written
before dispatch) carries the case's own TMS frontmatter (id, title, module,
priority...) but **not** the GitHub tracking-issue number it corresponds to.
At closeout — TMS back-write, closure records, board moves — you need that
mapping for every case, and by then it's gone from easy reach.

## Reconstruction, confirmed working 2026-08-04 (39 cases, wave-02-05-merged)

1. The campaign card's "Source" section lists the raw board-order issue
   numbers pulled at intake (e.g. `188, 191, 210, ...`). If earlier waves of
   the same campaign already consumed some of those numbers, subtract them
   first (cross-check against the earlier wave's own report.json `cases[]`).
2. Bulk-fetch remaining candidates' titles:
   `env -u GITHUB_TOKEN gh issue view <n> --repo ... --json number,title -q '.title'`
   (or list+filter for many at once).
3. **Match strictly on the literal `[Automate][ELITEA-<id>]` prefix — never
   a bare `ELITEA-<id>` substring.** A bare-substring match hit a real
   collision this session: issue #994's title was
   `[Clarification][ELITEA-1851] File Preview icon is always visible, not
   hover-gated` — a *different* tracking issue about the same case, filed
   during analysis. A substring match silently returned the wrong issue
   number for the closure record.

## The fix going forward

**Capture the mapping at intake time**, before dispatch — write
`issue: <n>` into the case snapshot's own frontmatter (or a sibling
`cases/_index.json` of `{case_id: issue_number}`) the moment the board sweep
resolves it. This turns closeout from a 30+-minute reconstruction (as it was
this session) into a straight lookup. Flag this to whichever future
intake pass touches the snapshot-writing step.
