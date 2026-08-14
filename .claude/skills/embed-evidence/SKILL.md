---
name: embed-evidence
description: Self-healing screenshot-evidence sweep for the issue tracker. Scans open question/bug issues for screenshots referenced by a local path or bare filename (the anti-pattern where evidence is only viewable on the author's machine), uploads each on-disk file to the flat `evidence` prerelease store, and embeds it inline in the issue body. Use when the user asks to attach/embed screenshots to issues, fix local-path evidence references, or schedule a recurring evidence check. Token-free: only dirty issues are written; clean issues cost one bulk read.
---

# embed-evidence

Enforces `.agents/role-overrides.md` § *screenshot evidence ATTACHES* mechanically —
so the rule doesn't depend on every analyst remembering the upload dance.

## Run it

```bash
# from the work-repo root (where .playwright-mcp / test-results/screenshots live)
python3 {skill}/scripts/embed_evidence.py --repo EliteaAI/elitea-testing-public
python3 {skill}/scripts/embed_evidence.py --dry-run     # report only, no writes
```

## What it does (deterministic, no LLM)

1. **One bulk read** per label (`question`, `bug`) — clean issues cost nothing more.
2. For each body, find `.png` references **not already** embedded via the evidence
   store — covers `.playwright-mcp/…`, `test-results/screenshots/…`,
   `automation/screenshots/…`, and **bare filenames**.
3. Each referenced file found on disk → upload to the `evidence` prerelease
   (`--clobber`) → embed `![alt](…/evidence/<file>.png)` inline right after the
   existing reference (local path stays as accompaniment).
4. Only **dirty** issues are edited. Files **not on disk** are reported (can't be
   auto-uploaded — needs re-capture or a human upload), never silently dropped.

Identity: clears `GITHUB_TOKEN` so `gh` runs as the keyring account (the tracker
identity rule).

## Schedule it (the daily sweep)

Not a factory loop — factory loops dispatch an agent per card and would spend
tokens even on clean issues. This is a plain scheduled script instead.

**Local cron** (operator machine, matches the factory's local model):
```cron
# 07:15 daily — self-heal screenshot evidence
15 7 * * *  cd /path/to/elitea-testing-public && python3 .claude/skills/embed-evidence/scripts/embed_evidence.py >> factory/state/last-embed-evidence.log 2>&1
```

Or a scheduled GitHub Actions workflow (`on: schedule:`) — but it must run
screenshots-on-disk-aware and authenticate as an identity with `project`/issue
write; the on-disk requirement makes the local cron the natural home (the
screenshot files live in the operator's work tree, not in CI).

## When an agent IS needed

The script self-heals the mechanical case. The only escalation is its
**MISSING** report — a referenced screenshot no longer on disk. That's a judgment
call (re-run the case to re-capture, or accept the text-only evidence), so hand
those few to an analyst rather than automating them.
