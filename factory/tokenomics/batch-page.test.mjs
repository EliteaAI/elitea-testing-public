import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { receiptFromScope, ensureReceipt, readScope } from './batch-page.mjs';

const scope = { v: 1, session: 's1', intent: 'automation', batch: 'fix-2145', cases: ['ELITEA-1869'], outcomes: { 'ELITEA-1869': { outcome: 'automated', at: 'T' } } };

test('receiptFromScope: cases[] with id + outcome, marked as synthesized', () => {
  const r = receiptFromScope({ ...scope, cases: ['ELITEA-1869', 'ELITEA-1870'] }, 'NOW');
  assert.equal(r.source, 'scope'); assert.equal(r.batch, 'fix-2145'); assert.equal(r.generatedAt, 'NOW');
  assert.deepEqual(r.cases, [{ id: 'ELITEA-1869', outcome: 'automated' }, { id: 'ELITEA-1870', outcome: 'not-started' }]);
});

test('ensureReceipt: writes once, never overwrites a real receipt, skips without outcomes', () => {
  const repo = mkdtempSync(join(tmpdir(), 'bp-'));
  assert.equal(ensureReceipt(repo, { ...scope, outcomes: {} }), 'no-outcomes');
  assert.equal(ensureReceipt(repo, scope), 'written');
  const p = join(repo, '.agents', 'automation', 'fix-2145', 'report.json');
  assert.ok(existsSync(p));
  writeFileSync(p, '{"cases":[{"id":"X","outcome":"delivered"}]}');
  assert.equal(ensureReceipt(repo, scope), 'exists');
  assert.match(readFileSync(p, 'utf8'), /"X"/, 'the workflow receipt is untouched');
});

test('readScope: missing → null', () => {
  const repo = mkdtempSync(join(tmpdir(), 'bp-'));
  assert.equal(readScope(repo, 'nope'), null);
  mkdirSync(join(repo, '.agents', 'telemetry', 'automation', 'scopes'), { recursive: true });
  writeFileSync(join(repo, '.agents', 'telemetry', 'automation', 'scopes', 's1.json'), JSON.stringify(scope));
  assert.equal(readScope(repo, 's1').batch, 'fix-2145');
});
