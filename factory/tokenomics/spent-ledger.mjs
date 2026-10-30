#!/usr/bin/env node
// spent-ledger.mjs — the factory's daily spend ledger: one markdown table per
// UTC day, `automation/spent/<YYYY-MM-DD>.md` on the `automation/maintenance`
// branch of the work repo. One row per (run, case): a run's dollars and tokens
// are split evenly across the cases it worked; a run with no named case keeps
// its spend as one `—` row, so nothing paid for disappears. A trailing Total
// row (distinct cases · Σ usd · Σ tokens) is rebuilt on every write.
//
// Numbers come from the SAME derivation as the per-card tokenomics comment
// (issue-tokenomics.mjs: this run's delta from the session's ledger lines) —
// never from anything the agent reported. `run` = <session-8>@<ledger endedAt>:
// identical whether the row is written live by the loop or replayed by
// backfill, so re-runs never duplicate a row.
//
// Writes with git plumbing (temp index + commit-tree + push of a sha), so the
// loop's working tree — a live batch trunk, maybe — is never touched. A
// rejected push re-fetches and rebuilds (3 tries); never --force.
//
//   node spent-ledger.mjs append --session <id> --baseline-count <N> --issue <n> \
//        [--tracking-repo owner/repo] [--title "<card title>"] [--wait 30] [--repo <path>] [--dry-run]
//   node spent-ledger.mjs backfill --tracking-repo owner/repo --agent <agent> \
//        [--sid-scope s] [--issues 1-5000] [--repo <path>] [--push]
//   common: [--branch automation/maintenance] [--dir automation/spent] [--remote origin]
//
//   append exits 3 when no new ledger line exists (the caller logs and moves on).
//   backfill is a DRY RUN unless --push. Both read the card title with `gh`
//   when --tracking-repo is given (`--gh "env -u GITHUB_TOKEN gh"` off the pod).
//
// Cases of a run, strongest source first: the session's declared scope → case
// ids in the card title ([FIX][ELITEA-2310] …) → ids the ledger mined from the
// transcript, filtered to the case shape → one `—` row. Mined ids alone are
// noisy (app-bug keys, issue numbers read as cases), hence the order.
// Case shape: SPENT_CASE_RE (default ELITEA-<digits>).
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadLines } from '../../.claude/skills/tokenomics/scripts/team-report.mjs';
import { buildIssueTokenomics, parseArgs, sessionLines } from './issue-tokenomics.mjs';
import { candidates } from './issue-tokenomics-backfill.mjs';

const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : 0);
const NO_CASE = '—';
const caseRe = () => new RegExp(`\\b(?:${process.env.SPENT_CASE_RE || 'ELITEA-\\d+'})\\b`, 'g');
const isCase = (id) => { const m = String(id).match(caseRe()); return !!m && m[0] === String(id); };

/** Case ids for one run — scope → card title → filtered mined ids. */
export function casesFor(after, scopeCases, title) {
  if (scopeCases?.length) return [...new Set(scopeCases)];
  const fromTitle = String(title ?? '').match(caseRe()) ?? [];
  if (fromTitle.length) return [...new Set(fromTitle)];
  return [...new Set((after.cases ?? []).filter(isCase))];
}
const HEADER = ['| case | usd | tokens | issue | run |', '|---|---|---|---|---|'];

/** Stable run key: same value live and in backfill. */
export const runKey = (session, endedAt) => `${String(session).slice(0, 8)}@${String(endedAt ?? '').replace(/\.\d+Z$/, 'Z')}`;

/**
 * Rows for one run — `after` is the run's ledger line, `before` the one that
 * existed before it (null on a first run). Cases: the session's declared scope,
 * else the ids the ledger mined from it. A run that spent nothing yields none.
 */
export function rowsForRun(after, before, issue, title) {
  const b = buildIssueTokenomics(after, before, { issue });
  const tokens = num(b.tokens?.total);
  const usd = typeof b.cost?.usd === 'number' ? b.cost.usd : null;
  if (!tokens && !usd) return [];
  const cases = casesFor(after, b.scope?.cases, title);
  const ids = cases.length ? cases : [NO_CASE];
  const n = ids.length;
  const base = Math.floor(tokens / n);
  const date = String(after.endedAt ?? after.capturedAt ?? '').slice(0, 10);
  const run = runKey(after.id, after.endedAt ?? after.capturedAt);
  return ids.map((id, i) => ({
    date, case: id, run, issue: issue ?? null,
    usd: usd == null ? null : Math.round((usd / n) * 10000) / 10000,
    tokens: base + (i === 0 ? tokens - base * n : 0),   // remainder on the first row: Σ stays exact
  }));
}

const fmtUsd = (v) => (v == null ? 'n/a' : v.toFixed(4));
const fmtIssue = (v) => (v ? `#${v}` : NO_CASE);

/** Parse a day file back into rows (header, separator and Total row skipped). */
export function parseDay(md) {
  const rows = [];
  for (const line of String(md ?? '').split('\n')) {
    if (!line.startsWith('| ') || line.startsWith('| case ') || line.startsWith('| **')) continue;
    const c = line.split('|').slice(1, -1).map((s) => s.trim());
    if (c.length < 5) continue;
    rows.push({
      case: c[0], usd: c[1] === 'n/a' ? null : Number(c[1]), tokens: Number(c[2]) || 0,
      issue: c[3].startsWith('#') ? Number(c[3].slice(1)) : null, run: c[4],
    });
  }
  return rows;
}

/** Existing rows + new rows, a run already on file is never written twice. */
export function mergeRows(existing, incoming) {
  const seen = new Set(existing.map((r) => r.run));
  return [...existing, ...incoming.filter((r) => !seen.has(r.run))];
}

export function renderDay(date, rows) {
  const cases = new Set(rows.map((r) => r.case).filter((c) => c !== NO_CASE));
  const priced = rows.filter((r) => typeof r.usd === 'number');
  const usd = priced.reduce((s, r) => s + r.usd, 0);
  const tokens = rows.reduce((s, r) => s + num(r.tokens), 0);
  const unpriced = rows.length - priced.length;
  return [
    `# Factory spent — ${date} (UTC)`,
    '',
    'One row per (factory run, case); a run\'s cost is split evenly across its cases.',
    'Source: telemetry ledger via factory/tokenomics/spent-ledger.mjs — `usd` n/a = not metered (excluded from the total).',
    '',
    ...HEADER,
    ...rows.map((r) => `| ${r.case} | ${fmtUsd(r.usd)} | ${num(r.tokens)} | ${fmtIssue(r.issue)} | ${r.run} |`),
    `| **Total: ${cases.size} cases** | **${usd.toFixed(4)}** | **${tokens}** | | ${unpriced ? `${unpriced} unpriced` : ''} |`,
    '',
  ].join('\n');
}

export function groupByDate(rows) {
  const m = new Map();
  for (const r of rows) { if (!m.has(r.date)) m.set(r.date, []); m.get(r.date).push(r); }
  return m;
}

// ---- git plumbing ------------------------------------------------------------
const git = (repo, args, { env, input } = {}) =>
  execFileSync('git', args, { cwd: repo, encoding: 'utf8', input, env: env ? { ...process.env, ...env } : process.env, stdio: ['pipe', 'pipe', 'pipe'] }).trim();

/**
 * Merge `rows` into the day files on `branch` and push ONE commit. Returns
 * { commit, files, added } — commit null when every run was already on file.
 */
export function writeToBranch(repo, rows, { branch = 'automation/maintenance', dir = 'automation/spent', remote = 'origin', tries = 3, push = true } = {}) {
  const byDate = groupByDate(rows);
  let lastErr;
  for (let attempt = 1; attempt <= tries; attempt++) {
    const tracking = `refs/remotes/${remote}/${branch}`;
    git(repo, ['fetch', '-q', remote, `+refs/heads/${branch}:${tracking}`]);
    const parent = git(repo, ['rev-parse', tracking]);
    const tmp = mkdtempSync(join(tmpdir(), 'spent-'));
    const env = { GIT_INDEX_FILE: join(tmp, 'index') };
    try {
      git(repo, ['read-tree', parent], { env });
      const files = []; let added = 0;
      for (const [date, incoming] of [...byDate.entries()].sort()) {
        const path = `${dir}/${date}.md`;
        let existing = [];
        try { existing = parseDay(git(repo, ['show', `${parent}:${path}`])); } catch { /* new day */ }
        const merged = mergeRows(existing, incoming);
        if (merged.length === existing.length) continue;
        added += merged.length - existing.length;
        const blob = git(repo, ['hash-object', '-w', '--stdin'], { input: renderDay(date, merged) });
        git(repo, ['update-index', '--add', '--cacheinfo', `100644,${blob},${path}`], { env });
        files.push(path);
      }
      if (!files.length) return { commit: null, files, added: 0 };
      const tree = git(repo, ['write-tree'], { env });
      const commit = git(repo, ['commit-tree', tree, '-p', parent, '-m', `chore(spent): ${added} row(s) — ${files.map((f) => f.split('/').pop()).join(', ')}`]);
      if (!push) return { commit, files, added, pushed: false };
      try {
        git(repo, ['push', '-q', remote, `${commit}:refs/heads/${branch}`]);
        return { commit, files, added, pushed: true };
      } catch (e) { lastErr = e; }            // non-fast-forward: the branch moved — rebuild on the new tip
    } finally { rmSync(tmp, { recursive: true, force: true }); }
  }
  throw new Error(`push to ${branch} failed after ${tries} tries — ${String(lastErr?.stderr || lastErr?.message || '').trim().slice(0, 200)}`);
}

// ---- CLI -------------------------------------------------------------------
const sleep = (ms) => new Promise((res) => setTimeout(res, ms));
const opts = (o) => ({ branch: o.branch ?? 'automation/maintenance', dir: o.dir ?? 'automation/spent', remote: o.remote ?? 'origin' });
const table = (rows) => rows.map((r) => `${r.date}\t${r.case}\t${fmtUsd(r.usd)}\t${r.tokens}\t${fmtIssue(r.issue)}\t${r.run}`).join('\n');

function titleReader(o) {
  const gh = o.gh ? String(o.gh).split(/\s+/) : ['gh'];
  return (n) => {
    if (!o.trackingRepo || !n) return '';
    const r = spawnSync(gh[0], [...gh.slice(1), 'issue', 'view', String(n), '-R', o.trackingRepo, '--json', 'title', '-q', '.title'], { encoding: 'utf8' });
    return r.status === 0 ? r.stdout.trim() : '';
  };
}

async function append(o) {
  if (!o.session) { process.stderr.write('spent-ledger append: --session <id> is required\n'); return 2; }
  const repo = resolve(o.repo);
  const base = num(o.baselineCount);
  const deadline = Date.now() + num(o.wait ?? 30) * 1000;
  let lines = sessionLines(repo, o.session);
  while (lines.length <= base && Date.now() < deadline) { await sleep(2000); lines = sessionLines(repo, o.session); }
  if (lines.length <= base) { process.stderr.write(`spent-ledger: no new ledger line for ${o.session}\n`); return 3; }
  const after = lines[lines.length - 1];
  const before = base > 0 ? lines[Math.min(base, lines.length) - 1] : null;
  const issue = Number.isFinite(o.issue) ? o.issue : null;
  const title = typeof o.title === 'string' ? o.title : titleReader(o)(issue);
  const rows = rowsForRun(after, before, issue, title);
  if (!rows.length) { process.stdout.write('spent-ledger: run spent nothing — no rows\n'); return 0; }
  if (o.dryRun) { process.stdout.write(`${table(rows)}\n`); return 0; }
  const r = writeToBranch(repo, rows, opts(o));
  process.stdout.write(r.commit ? `spent-ledger: +${r.added} row(s) → ${r.files.join(', ')} @ ${r.commit.slice(0, 9)}\n` : 'spent-ledger: run already on file\n');
  return 0;
}

async function backfill(o) {
  if (!o.trackingRepo || !o.agent) { process.stderr.write('usage: spent-ledger backfill --tracking-repo owner/repo --agent <agent> [--sid-scope s] [--issues a-b] [--push]\n'); return 2; }
  const repo = resolve(o.repo);
  const [from, to] = String(o.issues ?? '1-5000').split('-').map(Number);
  const cands = candidates(loadLines([repo]), { trackingRepo: o.trackingRepo, scope: o.sidScope ?? o.agent, from, to });
  const titleOf = titleReader(o);
  const rows = cands.flatMap((c) => {
    const title = titleOf(c.issue);
    return c.lines.flatMap((l, i) => rowsForRun(l, i > 0 ? c.lines[i - 1] : null, c.issue, title));
  });
  const days = groupByDate(rows);
  process.stdout.write(`${o.push ? 'PUSHING' : 'DRY RUN'} — ${cands.length} issue(s), ${rows.length} row(s), ${days.size} day(s)\n`);
  process.stdout.write(`date\tcase\tusd\ttokens\tissue\trun\n${table(rows)}\n`);
  if (!o.push) { process.stdout.write('re-run with --push to write\n'); return 0; }
  const r = writeToBranch(repo, rows, opts(o));
  process.stdout.write(r.commit ? `+${r.added} row(s) in ${r.files.length} file(s) @ ${r.commit.slice(0, 9)}\n` : 'every run already on file\n');
  return 0;
}

export async function main(argv = process.argv.slice(2)) {
  const [cmd, ...rest] = argv;
  const o = parseArgs(rest);
  o.repo = o.repo ?? process.cwd();
  if (cmd === 'append') return append(o);
  if (cmd === 'backfill') return backfill(o);
  process.stderr.write('usage: spent-ledger.mjs append|backfill …  (see the header)\n');
  return 2;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().then((code) => process.exit(code), (e) => { process.stderr.write(`spent-ledger: ${e.message}\n`); process.exit(1); });
}
