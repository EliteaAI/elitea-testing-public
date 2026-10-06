// Tests for issue-tokenomics.mjs — one factory run's tokenomics as a YAML block.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { stageOf, dispatchDeltas, sessionDelta, buildIssueTokenomics, toYaml, sessionLines, parseArgs, main } from './issue-tokenomics.mjs';

const tok = (input, output, cacheRead, cacheWrite) => ({ input, output, cacheRead, cacheWrite });
const sub = (id, role, label, t, usd, extra = {}) => ({ id, role, label, n: 1, tokens: t, tokensByModel: { m: t }, activeMin: 5, toolCalls: 10, toolErrors: 1, cases: ['TC-1'], costUsd: usd, ...extra });

// A conversation after run 1 (one dispatch) and after run 2 (that dispatch
// resumed + one new one). Ledger convention: costUsd/activeMin inclusive,
// tokens/turns/toolCalls parent-only.
const run1 = {
  v: 1, host: 'claude', id: 's1', role: 'test-automation-lead', endedAt: '2026-09-15T07:00:00Z',
  tokens: tok(10, 1000, 100000, 5000), tokensByModel: { 'claude-opus-5': tok(10, 1000, 100000, 5000) },
  costUsd: 10, costSource: 'ccusage-metered', activeMin: 12, turns: 20, toolCalls: 30, toolErrors: 1, dispatches: 1,
  skills: ['memory'], scope: { intent: 'automation', cases: ['TC-1'], outcomes: {} },
  subagents: [sub('a1', 'qa-engineer', 'Analyst — TC-1 (do not execute; the implementer builds later)', tok(5, 500, 50000, 2000), 4)],
};
const run2 = {
  ...run1, endedAt: '2026-09-15T08:00:00Z',
  tokens: tok(30, 3000, 300000, 9000), costUsd: 30, activeMin: 40, turns: 50, toolCalls: 70, toolErrors: 3, dispatches: 2,
  skills: ['memory', 'sync-base-branches'], scope: { intent: 'automation', cases: ['TC-1'], outcomes: { 'TC-1': 'delivered' } },
  subagents: [
    sub('a1', 'qa-engineer', 'Analyst — TC-1 (do not execute; the implementer builds later)', tok(6, 600, 60000, 2500), 5),
    sub('a2', 'test-automation-engineer', 'Fix round 1 — implementer, TC-1', tok(8, 800, 80000, 3000), 7),
  ],
};

test('stageOf: head-only match, fix wins over the role words it mentions', () => {
  assert.equal(stageOf('Analyst — TC-1 (do not execute; the implementer builds later)'), 'analyst');
  assert.equal(stageOf('Implementer — TC-1 repair'), 'implementer');
  assert.equal(stageOf('Reviewer — TC-1 repair'), 'reviewer');
  assert.equal(stageOf('Fix round 1 — implementer, TC-1'), 'fix');
  assert.equal(stageOf('Hardening gate for batch x'), 'gate');
  assert.equal(stageOf('Report writer — batch x'), 'report');
  assert.equal(stageOf('Port TC-1 repair to main'), 'other');
  assert.equal(stageOf(undefined), 'other');
});

test('dispatchDeltas: first run = whole entries; second run = new ids + resumed growth only', () => {
  const first = dispatchDeltas(run1, null);
  assert.equal(first.length, 1);
  assert.equal(first[0].usd, 4);
  assert.equal(first[0].resumed, undefined);
  const second = dispatchDeltas(run2, run1);
  assert.deepEqual(second.map((x) => x.id), ['a1', 'a2']);
  assert.equal(second[0].resumed, true, 'a1 grew → re-recorded as a resumed delta');
  assert.deepEqual(second[0].tokens, tok(1, 100, 10000, 500));
  assert.equal(second[0].usd, 1);
  assert.equal(second[1].usd, 7);
  // an unchanged dispatch is not repeated
  assert.equal(dispatchDeltas(run1, run1).length, 0);
});

test('sessionDelta: subtracts every additive field; skills are the new ones', () => {
  const d = sessionDelta(run2, run1);
  assert.deepEqual(d.tokens, tok(20, 2000, 200000, 4000));
  assert.equal(d.usd, 20);
  assert.equal(d.activeMin, 28);
  assert.equal(d.turns, 30);
  assert.deepEqual(d.skills, ['sync-base-branches']);
  const first = sessionDelta(run1, null);
  assert.equal(first.usd, 10);
});

test('sessionDelta: a tokens-only side never yields a dollar', () => {
  assert.equal(sessionDelta({ ...run2, costUsd: null }, run1).usd, null);
  assert.equal(sessionDelta(run2, { ...run1, costUsd: null }).usd, null);
});

test('buildIssueTokenomics: whole-run tokens = parent + dispatches; lead row nets dollars and minutes; by_role sums to the run', () => {
  const b = buildIssueTokenomics(run2, run1, { issue: 7, loop: 'tal', attempt: '2/3', started: '2026-09-15T07:30:00Z', ended: '2026-09-15T08:00:00Z', boardAfter: 'Ready', verdict: 'left-queue', runsBefore: 1 });
  assert.equal(b.tokenomics, 'v1');
  assert.equal(b.run.wall_min, 30);
  assert.equal(b.run.active_min, 28);
  // run tokens: parent delta (20/2000/200000/4000) + a1 delta (1/100/10000/500) + a2 (8/800/80000/3000)
  assert.deepEqual([b.tokens.input, b.tokens.output, b.tokens.cache_read, b.tokens.cache_write], [29, 2900, 290000, 7500]);
  assert.equal(b.tokens.real_work, 2929);
  assert.equal(b.cost.usd, 20);
  assert.equal(b.cost.overhead_usd, 12, '20 − (1 + 7)');
  assert.equal(b.cost.overhead_pct, 60);
  assert.equal(b.cost.rework_usd, 7, 'the fix-round dispatch');
  assert.equal(b.activity.turns, 30);
  assert.equal(b.activity.tool_calls, 40 + 0 + 10, 'parent delta + resumed a1 (no new calls) + a2');
  assert.equal(b.activity.dispatches, 2);
  const lead = b.by_role[0];
  assert.equal(lead.role, 'test-automation-lead');
  assert.equal(lead.real_work, 2020, 'parent-only tokens, not a subtraction');
  assert.equal(lead.active_min, 23, '28 − 0 (resumed a1, no new minutes) − 5');
  const roleUsd = b.by_role.reduce((s, r) => s + r.usd, 0);
  assert.equal(Math.round(roleUsd * 100) / 100, b.cost.usd, 'by_role dollars add up to the run');
  assert.equal(b.dispatches[1].stage, 'fix');
  assert.deepEqual(b.scope.outcomes, { 'TC-1': 'delivered' });
  assert.equal(b.conversation_total.runs, 2);
  assert.equal(b.conversation_total.usd, 30);
  assert.equal(b.conversation_total.tokens_total, 30 + 3000 + 300000 + 9000 + (6 + 600 + 60000 + 2500) + (8 + 800 + 80000 + 3000));
});

test('buildIssueTokenomics: one unpriced dispatch → lead dollars null, never a guess', () => {
  const r = { ...run1, subagents: [{ ...run1.subagents[0], costUsd: undefined }] };
  const b = buildIssueTokenomics(r, null, {});
  assert.equal(b.cost.usd, 10);
  assert.equal(b.cost.overhead_usd, null);
  assert.equal(b.by_role[1].usd, null);
});

test('buildIssueTokenomics: tokens-only session', () => {
  const b = buildIssueTokenomics({ ...run1, costUsd: null }, null, {});
  assert.equal(b.cost.usd, null);
  assert.equal(b.cost.source, 'tokens-only');
});

test('toYaml: quotes what YAML would mistype, keeps ids and case keys bare, comments the marked keys', () => {
  const y = toYaml({ tokenomics: 'v1', conversation: '98c7-abc', attempt: '1/3', n: '42', when: '2026-09-15T07:00:00Z', ok: 'yes', e: [], m: {}, list: ['ELITEA-1', 'x'], rows: [{ a: 1, b: 'two words' }], scope: { outcomes: { 'ELITEA-1': 'delivered' } } });
  assert.match(y, /^tokenomics: v1$/m);
  assert.match(y, /^conversation: 98c7-abc  # claude --resume/m);
  assert.match(y, /^attempt: 1\/3  # the loop/m, "1/3 is bare — YAML reads it as a string, not a number");
  assert.match(y, /^n: "42"$/m, 'numeric-looking string stays a string');
  assert.match(y, /^when: "2026-09-15T07:00:00Z"$/m);
  assert.match(y, /^ok: "yes"$/m);
  assert.match(y, /^e: \[\]$/m);
  assert.match(y, /^m: \{\}$/m);
  assert.match(y, /^list: \[ELITEA-1, x\]$/m);
  assert.match(y, /^rows:\n  - a: 1\n    b: "two words"$/m);
  assert.match(y, /^scope:  # declared by the session/m);
  assert.match(y, /^    ELITEA-1: delivered$/m);
});

test('toYaml of a real block round-trips its own scalars (keys and values survive as strings/numbers)', () => {
  const y = toYaml(buildIssueTokenomics(run2, run1, { issue: 7 }));
  for (const line of y.split('\n')) assert.doesNotMatch(line, /: undefined$/);
  assert.match(y, /^issue: 7$/m);
});

test('parseArgs: --key value pairs, numeric coercion, --json flag', () => {
  const o = parseArgs(['--session', 's1', '--baseline-count', '2', '--attempt', '1/3', '--json', '--wait', '0']);
  assert.equal(o.session, 's1'); assert.equal(o.baselineCount, 2); assert.equal(o.attempt, '1/3'); assert.equal(o.json, true); assert.equal(o.wait, 0);
  const p = parseArgs(['--post', '--gh', '/tmp/fakegh', '--issues', '1-9']);
  assert.equal(p.post, true); assert.equal(p.gh, '/tmp/fakegh', 'a boolean flag never swallows the next option'); assert.equal(p.issues, '1-9');
});

const repoWith = (lines) => {
  const repo = mkdtempSync(join(tmpdir(), 'issue-tok-'));
  const dir = join(repo, '.agents', 'telemetry', 'automation');
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, 'usage-u.jsonl'), lines.map((l) => JSON.stringify(l)).join('\n') + '\n');
  return repo;
};

test('main: no new line since the baseline → exit 3, nothing on stdout', async () => {
  const repo = repoWith([run1]);
  const out = []; const orig = process.stdout.write; process.stdout.write = (s) => { out.push(s); return true; };
  try {
    assert.equal(await main(['--repo', repo, '--session', 's1', '--baseline-count', '1', '--wait', '0']), 3);
    assert.equal(out.length, 0);
    assert.equal(await main(['--repo', repo, '--session', 'nope', '--wait', '0']), 3);
  } finally { process.stdout.write = orig; }
});

test('main: delta against line N-1 when N lines existed before the run', async () => {
  const repo = repoWith([run1, run2]);
  assert.equal(sessionLines(repo, 's1').length, 2);
  const out = []; const orig = process.stdout.write; process.stdout.write = (s) => { out.push(s); return true; };
  try {
    assert.equal(await main(['--repo', repo, '--session', 's1', '--baseline-count', '1', '--issue', '7', '--json', '--wait', '0']), 0);
    const b = JSON.parse(out.join(''));
    assert.equal(b.cost.usd, 20, 'run2 − run1');
    assert.equal(b.issue, 7);
    out.length = 0;
    assert.equal(await main(['--repo', repo, '--session', 's1', '--baseline-count', '0', '--json', '--wait', '0']), 0);
    assert.equal(JSON.parse(out.join('')).cost.usd, 30, 'no baseline → the whole latest line');
  } finally { process.stdout.write = orig; }
});
