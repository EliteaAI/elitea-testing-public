#!/usr/bin/env node
// batch-page.mjs — make sure the session's batch has a receipt and a page,
// however the job was done (batch Workflow, direct dispatches, or solo).
//
// The batch page (`telemetry/reports/<batch>.html`) is rendered from a receipt
// (`.agents/automation/<batch>/report.json`). The batch Workflow writes one;
// a lead working a card conversationally usually does not (fix-2287 got its
// page only because the lead typed report.json by hand). But every session
// records its outcomes via `work-scope outcome` — so when no receipt exists,
// one is SYNTHESIZED from the declared scope (marked `source: scope`), and the
// page is rendered either way. No scope, or no batch in it → nothing to do.
//
//   node batch-page.mjs --session <id> [--repo <path>]
//   prints one line; exit 0 always (the loop must never die on a report).
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const SKILL = '.claude/skills/tokenomics/scripts';

export function readScope(repo, session) {
  const p = join(repo, '.agents', 'telemetry', 'automation', 'scopes', `${session}.json`);
  if (!existsSync(p)) return null;
  try { return JSON.parse(readFileSync(p, 'utf8')); } catch { return null; }
}

/** Receipt from a scope: `cases[]` with id + outcome — the reader's whole contract. */
export function receiptFromScope(scope, now = new Date().toISOString()) {
  const outcomes = scope.outcomes ?? {};
  const ids = [...new Set([...(scope.cases ?? []), ...Object.keys(outcomes)])].sort();
  return {
    batch: scope.batch, source: 'scope', session: scope.session, generatedAt: now,
    note: 'synthesized by factory/tokenomics/batch-page.mjs from the session\'s declared scope — no workflow receipt existed',
    cases: ids.map((id) => ({ id, outcome: outcomes[id]?.outcome ?? 'not-started' })),
  };
}

/** Write the receipt only when none exists. Returns 'written' | 'exists' | 'no-outcomes'. */
export function ensureReceipt(repo, scope, now) {
  const dir = join(repo, '.agents', 'automation', ...scope.batch.split('/'));
  const path = join(dir, 'report.json');
  if (existsSync(path)) return 'exists';
  if (!Object.keys(scope.outcomes ?? {}).length) return 'no-outcomes';
  mkdirSync(dir, { recursive: true });
  writeFileSync(path, `${JSON.stringify(receiptFromScope(scope, now), null, 2)}\n`);
  return 'written';
}

export function renderPage(repo, batch) {
  const out = join(repo, '.agents', 'telemetry', 'automation', 'reports', `${batch.replace(/\//g, '__')}.html`);
  mkdirSync(join(repo, '.agents', 'telemetry', 'automation', 'reports'), { recursive: true });
  const r = spawnSync('node', [join(repo, SKILL, 'team-report.mjs'), '--batch', batch, '--html', '--out', out], { cwd: repo, encoding: 'utf8' });
  if (r.status !== 0) throw new Error((r.stderr || r.stdout || `exit ${r.status}`).trim().slice(0, 200));
  return out;
}

export function main(argv = process.argv.slice(2)) {
  const o = {}; for (let i = 0; i < argv.length; i++) if (argv[i].startsWith('--')) o[argv[i].slice(2)] = argv[++i];
  const repo = resolve(o.repo ?? process.cwd());
  if (!o.session) { process.stdout.write('batch-page: no --session\n'); return 0; }
  const scope = readScope(repo, o.session);
  if (!scope?.batch) { process.stdout.write(`batch-page: ${o.session.slice(0, 8)} has no batch in its scope — nothing to render\n`); return 0; }
  try {
    const r = ensureReceipt(repo, scope);
    if (r === 'no-outcomes') { process.stdout.write(`batch-page: ${scope.batch} — no receipt and no declared outcomes yet — skipped\n`); return 0; }
    const page = renderPage(repo, scope.batch);
    process.stdout.write(`batch-page: ${scope.batch} — receipt ${r}, page ${page.replace(`${repo}/`, '')}\n`);
  } catch (e) { process.stdout.write(`batch-page: ${scope.batch} — failed: ${e.message}\n`); }
  return 0;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) process.exit(main());
