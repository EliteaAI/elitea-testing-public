import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { rowsForRun, casesFor, parseDay, mergeRows, renderDay, runKey, writeToBranch } from './spent-ledger.mjs';

const line = (o = {}) => ({
  id: 'abcdef12-0000-4000-a000-000000000000', endedAt: '2026-10-22T10:00:00.123Z',
  tokens: { input: 100, output: 50, cacheRead: 849, cacheWrite: 0 }, costUsd: 3, costSource: 'ccusage-metered',
  activeMin: 10, subagents: [], cases: [], ...o,
});

test('runKey: session prefix + second-precision end, same live and backfilled', () => {
  assert.equal(runKey('abcdef12-xyz', '2026-10-22T10:00:00.123Z'), 'abcdef12@2026-10-22T10:00:00Z');
});

test('rowsForRun: split usd and tokens evenly across scope cases, Σ tokens exact', () => {
  const rows = rowsForRun(line({ scope: { intent: 'automation', cases: ['ELITEA-1', 'ELITEA-2', 'ELITEA-3'] } }), null, 2545);
  assert.equal(rows.length, 3);
  assert.deepEqual(rows.map((r) => r.case), ['ELITEA-1', 'ELITEA-2', 'ELITEA-3']);
  assert.ok(rows.every((r) => r.usd === 1 && r.issue === 2545 && r.date === '2026-10-22'));
  assert.equal(rows.reduce((s, r) => s + r.tokens, 0), 999);
});

test('rowsForRun: falls back to mined ids, then to one — row', () => {
  assert.deepEqual(rowsForRun(line({ cases: ['ELITEA-9'] }), null, 1).map((r) => r.case), ['ELITEA-9']);
  const r = rowsForRun(line(), null, 7);
  assert.equal(r.length, 1); assert.equal(r[0].case, '—'); assert.equal(r[0].usd, 3);
});

test('rowsForRun: second run of a conversation is the delta; unmetered → null usd', () => {
  const first = line({ cases: ['ELITEA-1'] });
  const second = line({ endedAt: '2026-10-23T01:00:00Z', cases: ['ELITEA-1'], costUsd: 5,
    tokens: { input: 300, output: 100, cacheRead: 849, cacheWrite: 0 } });
  const [r] = rowsForRun(second, first, 1);
  assert.equal(r.usd, 2); assert.equal(r.tokens, 250); assert.equal(r.date, '2026-10-23');
  const [u] = rowsForRun(line({ costUsd: null }), null, 1);
  assert.equal(u.usd, null);
});

test('casesFor: scope → card title → mined ids filtered to the case shape', () => {
  const l = line({ cases: ['EL-6687', 'ELITEA-1824', 'ELITEA-1824'] });
  assert.deepEqual(casesFor(l, ['ELITEA-5'], '[FIX][ELITEA-9] x'), ['ELITEA-5']);
  assert.deepEqual(casesFor(l, [], '[FIX][ELITEA-2310] assertion-failure'), ['ELITEA-2310']);
  assert.deepEqual(casesFor(l, [], '[FIX][3 cases] timeout'), ['ELITEA-1824']);
  assert.deepEqual(casesFor(line({ cases: ['EL-1'] }), null, ''), []);
});

test('rowsForRun: a run that spent nothing yields no rows', () => {
  const l = line();
  assert.deepEqual(rowsForRun(l, l, 1), []);
});

test('render → parse round-trip; total row counts distinct cases, skips unpriced usd', () => {
  const rows = [
    { case: 'ELITEA-1', usd: 1.5, tokens: 10, issue: 5, run: 'a@1' },
    { case: 'ELITEA-1', usd: null, tokens: 20, issue: 5, run: 'b@2' },
    { case: '—', usd: 0.25, tokens: 5, issue: null, run: 'c@3' },
  ];
  const md = renderDay('2026-10-22', rows);
  assert.match(md, /\| \*\*Total: 1 cases\*\* \| \*\*1\.7500\*\* \| \*\*35\*\* \| \| 1 unpriced \|/);
  assert.deepEqual(parseDay(md), rows);
});

test('mergeRows: a run already on file is never added twice; multi-case run stays whole', () => {
  const existing = [{ case: 'A', run: 'x' }, { case: 'B', run: 'x' }];
  const merged = mergeRows(existing, [{ case: 'A', run: 'x' }, { case: 'B', run: 'x' }, { case: 'C', run: 'y' }, { case: 'D', run: 'y' }]);
  assert.deepEqual(merged.map((r) => r.case), ['A', 'B', 'C', 'D']);
});

test('writeToBranch: creates the day file, appends, dedups, never touches the work tree', () => {
  const g = (cwd, ...a) => execFileSync('git', a, { cwd, encoding: 'utf8' }).trim();
  const root = mkdtempSync(join(tmpdir(), 'spent-git-'));
  const bare = join(root, 'remote.git'); const work = join(root, 'work');
  g(root, 'init', '-q', '--bare', bare);
  g(root, 'clone', '-q', bare, work);
  g(work, 'config', 'user.email', 't@t'); g(work, 'config', 'user.name', 't');
  g(work, 'commit', '-q', '--allow-empty', '-m', 'init');
  g(work, 'push', '-q', 'origin', 'HEAD:refs/heads/automation/maintenance');
  const head = g(work, 'rev-parse', 'HEAD');

  const r1 = writeToBranch(work, [{ date: '2026-10-22', case: 'E-1', usd: 1, tokens: 10, issue: 1, run: 'r1' }]);
  assert.equal(r1.added, 1); assert.deepEqual(r1.files, ['automation/spent/2026-10-22.md']);
  const r2 = writeToBranch(work, [
    { date: '2026-10-22', case: 'E-1', usd: 1, tokens: 10, issue: 1, run: 'r1' },
    { date: '2026-10-22', case: 'E-2', usd: 2, tokens: 20, issue: 2, run: 'r2' },
  ]);
  assert.equal(r2.added, 1);
  assert.equal(writeToBranch(work, [{ date: '2026-10-22', case: 'E-1', usd: 1, tokens: 10, issue: 1, run: 'r1' }]).commit, null);

  const md = g(work, 'show', 'origin/automation/maintenance:automation/spent/2026-10-22.md');
  assert.deepEqual(parseDay(md).map((r) => r.run), ['r1', 'r2']);
  assert.match(md, /\*\*Total: 2 cases\*\* \| \*\*3\.0000\*\* \| \*\*30\*\*/);
  assert.equal(g(work, 'rev-parse', 'HEAD'), head, 'checked-out branch untouched');
  assert.equal(g(work, 'status', '--porcelain'), '', 'work tree untouched');
});
