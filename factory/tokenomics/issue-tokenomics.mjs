#!/usr/bin/env node
// issue-tokenomics.mjs — one factory run's tokenomics as a YAML block for the
// issue thread that triggered it. Derived ENTIRELY from the ledger line the
// SessionEnd hook wrote for that session (tokens, ccusage dollars, per-dispatch
// sub-agent rollup, declared scope) — never from anything the agent reported.
//
// The factory loop resumes ONE conversation per issue across attempts, and a
// ledger line is cumulative for the conversation's whole life (a re-captured
// session supersedes its earlier line). So the block carries THIS RUN's delta
// (latest line − the latest line that existed before the run) plus the
// running conversation total (the latest line itself).
//
// Ledger convention (telemetry-capture.mjs:754-756, 719): `costUsd` and
// `activeMin` INCLUDE sub-agents; `tokens`, `turns`, `toolCalls`, `toolErrors`
// are the PARENT thread only — sub-agent figures live in `subagents[]`. The
// block reports the whole run (parent + dispatches) and names the lead thread
// as its own by_role row.
//
//   node issue-tokenomics.mjs --session <id> --baseline-count <N> \
//        --issue 2294 --loop tal --agent test-automation-lead --attempt 1/3 \
//        --started <ISO> --ended <ISO> --board-after Ready --verdict left-queue \
//        [--runs-before 0] [--wait 30] [--repo <path>] [--json]
//
//   --baseline-count N  how many ledger lines carried this session id BEFORE
//                       the run (the loop counts them); the delta is taken
//                       against line N-1, or against nothing when N is 0
//   --wait S            poll up to S seconds for the post-run line to appear
//                       (the SessionEnd hook writes it ~1 s after exit)
//   exit 3              no new ledger line — the caller logs and moves on
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
// Lives in factory/ (loop glue, repo-owned) — the tokenomics skill folder is a
// bundle drop-in that `init --update` overwrites. Reads the skill's own report
// helpers so the numbers stay the skill's numbers.
import { loadLines, realWork, cacheHitRate } from '../../.claude/skills/tokenomics/scripts/team-report.mjs';

const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : 0);
const r2 = (v) => Math.round(v * 100) / 100;
const r1 = (v) => Math.round(v * 10) / 10;
const TOK = ['input', 'output', 'cacheRead', 'cacheWrite'];
const zeroTok = () => ({ input: 0, output: 0, cacheRead: 0, cacheWrite: 0 });
const totalTok = (t) => TOK.reduce((s, k) => s + num(t?.[k]), 0);
const subTok = (a, b) => Object.fromEntries(TOK.map((k) => [k, Math.max(0, num(a?.[k]) - num(b?.[k]))]));
const addTok = (a, b) => Object.fromEntries(TOK.map((k) => [k, num(a?.[k]) + num(b?.[k])]));
// A dollar delta is a dollar only when BOTH sides are metered — an unpriced
// baseline makes the difference meaningless, and we never estimate. With no
// baseline at all (first run) the line's own figure is the delta.
const subUsd = (a, b, hasBaseline) => {
  if (typeof a !== 'number') return null;
  if (!hasBaseline) return r2(a);
  return typeof b === 'number' ? r2(Math.max(0, a - b)) : null;
};
const hitPct = (t) => { const h = cacheHitRate(t); return h == null ? null : r1(h * 100); };

// Stage of a dispatch, from the HEAD of its label — the same head-only rule
// batch-cost.mjs uses (labels routinely MENTION other stages further on).
// batch-cost's four overhead kinds, plus the three per-unit slots the
// pipeline dispatches; `fix` first, because "Fix round 2 — implementer" is rework.
const STAGE_HEAD = 48;
export const STAGE_KIND = [
  ['fix', /^fix[:\s]|fix round|\brework\b/i],
  ['triage', /\btriage\b/i],
  ['gate', /hardening gate|mini-gate|gate for batch|^gate[:\s]/i],
  ['report', /report writer|write the report|^report[:\s]/i],
  ['analyst', /\banalys(t|e|is)\b/i],
  ['implementer', /\bimplement(er|ation)?\b|\bbuild(er)?\b/i],
  ['reviewer', /\breview(er)?\b/i],
];
export const stageOf = (label) => {
  const head = String(label || '').slice(0, STAGE_HEAD);
  return STAGE_KIND.find(([, re]) => re.test(head))?.[0] ?? 'other';
};

const LABEL_MAX = 80;
const clip = (s) => { s = String(s ?? ''); return s.length > LABEL_MAX ? `${s.slice(0, LABEL_MAX - 1)}…` : s; };

/** Ledger lines for one session id, in capture order (file order = append order). */
export function sessionLines(repo, session) {
  return loadLines([repo]).filter((l) => l.id === session);
}

/**
 * This run's dispatches: entries of `after.subagents` that are new since
 * `before`, or whose transcript grew (a resumed agent is re-recorded under the
 * same id — its delta counts, flagged `resumed`).
 */
export function dispatchDeltas(after, before) {
  const prev = new Map((before?.subagents ?? []).map((s) => [s.id, s]));
  const out = [];
  for (const s of after?.subagents ?? []) {
    const b = prev.get(s.id);
    const tok = b ? subTok(s.tokens, b.tokens) : { ...zeroTok(), ...s.tokens };
    if (b && totalTok(tok) === 0) continue;
    out.push({
      id: s.id, role: s.role ?? null, label: clip(s.label), stage: stageOf(s.label),
      usd: subUsd(s.costUsd, b?.costUsd, !!b), tokens: tok,
      activeMin: Math.max(0, num(s.activeMin) - num(b?.activeMin)),
      toolCalls: Math.max(0, num(s.toolCalls) - num(b?.toolCalls)),
      toolErrors: Math.max(0, num(s.toolErrors) - num(b?.toolErrors)),
      cases: s.cases ?? [], ...(b ? { resumed: true } : {}),
    });
  }
  return out;
}

/** The whole-session delta (parent + dispatches) between two ledger lines. */
export function sessionDelta(after, before) {
  const tokens = before ? subTok(after.tokens, before.tokens) : { ...zeroTok(), ...after.tokens };
  const sub = (k) => Math.max(0, num(after[k]) - num(before?.[k]));
  const had = new Set(before?.skills ?? []);
  return {
    tokens, usd: subUsd(after.costUsd, before?.costUsd, !!before),
    activeMin: sub('activeMin'), turns: sub('turns'), toolCalls: sub('toolCalls'), toolErrors: sub('toolErrors'),
    dispatches: sub('dispatches'), skills: (after.skills ?? []).filter((s) => !had.has(s)),
  };
}

const roleRow = (role, b) => ({
  role, usd: b.usd, dispatches: b.dispatches, real_work: realWork(b.tokens) ?? 0,
  cache_hit_rate_pct: hitPct(b.tokens), active_min: b.activeMin, tool_calls: b.toolCalls, tool_errors: b.toolErrors,
});

/**
 * The block. `after` = the latest ledger line for the session; `before` = the
 * latest line that existed before the run (null on a first run); `meta` = what
 * only the loop knows (issue, attempt, wall clock, board outcome).
 */
export function buildIssueTokenomics(after, before, meta = {}) {
  const d = sessionDelta(after, before);          // parent-only tokens/tools; inclusive usd/activeMin
  const disp = dispatchDeltas(after, before);
  const dispTok = disp.reduce((a, x) => addTok(a, x.tokens), zeroTok());
  const dispUsd = disp.every((x) => typeof x.usd === 'number') ? disp.reduce((s, x) => s + x.usd, 0) : null;
  const sum = (k) => disp.reduce((s, x) => s + x[k], 0);
  // Lead thread: tokens/tools are the parent's own; dollars and minutes are
  // the inclusive figures net of the dispatches. Dollars only when every
  // dispatch is metered — one unpriced dispatch makes the remainder a guess.
  const lead = {
    tokens: d.tokens, dispatches: 0,
    usd: typeof d.usd === 'number' && dispUsd != null ? r2(Math.max(0, d.usd - dispUsd)) : null,
    activeMin: Math.max(0, d.activeMin - sum('activeMin')),
    toolCalls: d.toolCalls, toolErrors: d.toolErrors,
  };
  const runTok = addTok(d.tokens, dispTok);       // the whole run — what the batch report calls "Tokens"
  const byRole = new Map();
  for (const x of disp) {
    const b = byRole.get(x.role) ?? { tokens: zeroTok(), usd: 0, priced: true, dispatches: 0, activeMin: 0, toolCalls: 0, toolErrors: 0 };
    b.tokens = addTok(b.tokens, x.tokens); b.dispatches += 1; b.activeMin += x.activeMin;
    b.toolCalls += x.toolCalls; b.toolErrors += x.toolErrors;
    if (typeof x.usd === 'number') b.usd += x.usd; else b.priced = false;
    byRole.set(x.role, b);
  }
  const rework = disp.filter((x) => x.stage === 'fix');
  const reworkUsd = rework.length && rework.every((x) => typeof x.usd === 'number') ? r2(rework.reduce((s, x) => s + x.usd, 0)) : rework.length ? null : 0;
  const total = totalTok(runTok);
  const models = [...new Set([...Object.keys(after.tokensByModel ?? {}), ...(after.subagents ?? []).flatMap((x) => Object.keys(x.tokensByModel ?? {}))])];
  const scope = after.scope ?? null;
  return {
    tokenomics: 'v1',
    issue: meta.issue ?? null, loop: meta.loop ?? null, agent: meta.agent ?? after.role ?? null,
    conversation: after.id, attempt: meta.attempt ?? null,
    run: {
      started: meta.started ?? null, ended: meta.ended ?? after.endedAt ?? null,
      wall_min: meta.started && meta.ended ? Math.max(0, Math.round((Date.parse(meta.ended) - Date.parse(meta.started)) / 60000)) : null,
      active_min: d.activeMin, board_after: meta.boardAfter ?? null, loop_verdict: meta.verdict ?? null,
    },
    cost: {
      usd: d.usd, source: typeof d.usd === 'number' ? (after.costSource ?? 'metered') : 'tokens-only',
      overhead_usd: lead.usd, overhead_pct: typeof d.usd === 'number' && d.usd > 0 && lead.usd != null ? Math.round((lead.usd / d.usd) * 100) : null,
      rework_usd: reworkUsd,
    },
    tokens: {
      total, real_work: realWork(runTok) ?? 0,
      input: runTok.input, output: runTok.output, cache_read: runTok.cacheRead, cache_write: runTok.cacheWrite,
      cache_hit_rate_pct: hitPct(runTok),
    },
    models: models.length ? models : (after.models ?? []),
    activity: {
      turns: d.turns, tool_calls: d.toolCalls + sum('toolCalls'), tool_errors: d.toolErrors + sum('toolErrors'),
      dispatches: disp.length, skills: d.skills,
    },
    by_role: [
      roleRow(after.role ?? 'lead', lead),
      ...[...byRole.entries()].map(([role, b]) => roleRow(role, { ...b, usd: b.priced ? r2(b.usd) : null })),
    ],
    dispatches: disp.map((x) => ({
      role: x.role, label: x.label, stage: x.stage, usd: x.usd, active_min: x.activeMin,
      tool_calls: x.toolCalls, tool_errors: x.toolErrors, cases: x.cases, ...(x.resumed ? { resumed: true } : {}),
    })),
    scope: scope ? { intent: scope.intent ?? null, cases: scope.cases ?? [], outcomes: scope.outcomes ?? {} } : null,
    conversation_total: (() => {
      const all = (after.subagents ?? []).reduce((a, x) => addTok(a, x.tokens), { ...zeroTok(), ...after.tokens });
      return {
        runs: num(meta.runsBefore) + 1,
        usd: typeof after.costUsd === 'number' ? r2(after.costUsd) : null,
        active_min: num(after.activeMin), real_work: realWork(all) ?? 0,
        tokens_total: totalTok(all), dispatches: num(after.dispatches),
      };
    })(),
  };
}

// ---- YAML ------------------------------------------------------------------
// A small emitter — the block is flat enough that a dependency would be more
// code than this. Scalars that could be mistaken for YAML types are quoted.
const BARE = /^[A-Za-z0-9_][A-Za-z0-9_./-]*$/;
const NUMERIC = /^[0-9][0-9_.]*$/;              // looks like a number → quote it
const YAML_WORD = /^(true|false|null|yes|no|on|off|~)$/i;
const scalar = (v) => {
  if (v == null) return 'null';
  if (typeof v === 'number') return Number.isFinite(v) ? String(v) : 'null';
  if (typeof v === 'boolean') return String(v);
  const s = String(v);
  return BARE.test(s) && !YAML_WORD.test(s) && !NUMERIC.test(s) ? s : JSON.stringify(s);
};
const isObj = (v) => v && typeof v === 'object' && !Array.isArray(v);
const COMMENT = {
  conversation: 'claude --resume <id> to take over',
  attempt: "the loop's retry counter (MAX_ATTEMPTS)",
  'run.active_min': 'sub-agents included (they overlap the lead thread)',
  'activity.turns': 'lead thread only',
  'run.loop_verdict': 'left-queue | retry | escalated | deferred',
  cost: 'THIS RUN — delta vs the conversation before it',
  'cost.source': 'metered at capture, or tokens-only — never estimated',
  'cost.overhead_usd': 'lead thread — the orchestration share',
  'cost.rework_usd': 'fix-round dispatches',
  'tokens.real_work': 'input + output — what actually costs',
  by_role: 'lead thread first, then dispatched roles',
  dispatches: "this run's, in order",
  scope: 'declared by the session (work-scope.mjs), not inferred',
  conversation_total: 'every run on this issue so far',
};
export function toYaml(v, indent = 0, path = '') {
  const pad = ' '.repeat(indent);
  if (Array.isArray(v)) {
    if (!v.length) return `${pad}[]`;
    if (v.every((x) => !isObj(x) && !Array.isArray(x))) return `${pad}[${v.map(scalar).join(', ')}]`;
    return v.map((x) => {
      const body = toYaml(x, indent + 2, path).replace(/^ {2}/, '');
      return `${pad}- ${body.trimStart()}`;
    }).join('\n');
  }
  if (isObj(v)) {
    const keys = Object.keys(v);
    if (!keys.length) return `${pad}{}`;
    return keys.map((k) => {
      const p = path ? `${path}.${k}` : k;
      const c = COMMENT[p] ? `  # ${COMMENT[p]}` : '';
      const x = v[k];
      if (isObj(x) && Object.keys(x).length) return `${pad}${k}:${c}\n${toYaml(x, indent + 2, p)}`;
      if (Array.isArray(x) && x.length && x.some((e) => isObj(e))) return `${pad}${k}:${c}\n${toYaml(x, indent + 2, p)}`;
      if (isObj(x)) return `${pad}${k}: {}${c}`;
      return `${pad}${k}: ${toYaml(x, 0, p)}${c}`;
    }).join('\n');
  }
  return `${pad}${scalar(v)}`;
}

// ---- CLI -------------------------------------------------------------------
const sleep = (ms) => new Promise((res) => setTimeout(res, ms));
const FLAGS = new Set(['json', 'post', 'dryRun', 'help']);
export function parseArgs(argv) {
  const o = { wait: 30, baselineCount: 0, runsBefore: 0, repo: process.cwd() };
  const key = (k) => k.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) continue;
    const k = key(a.slice(2));
    // Boolean flags never consume the next argument — `--post --gh <cmd>`
    // once swallowed `--gh` as --post's value and fell back to the REAL gh.
    if (FLAGS.has(k) || argv[i + 1] === undefined || String(argv[i + 1]).startsWith('--')) { o[k] = true; continue; }
    o[k] = argv[++i];
  }
  for (const k of ['wait', 'baselineCount', 'runsBefore', 'issue']) if (o[k] != null) o[k] = Number(o[k]);
  return o;
}

export async function main(argv = process.argv.slice(2)) {
  const o = parseArgs(argv);
  if (!o.session) { process.stderr.write('issue-tokenomics: --session <id> is required\n'); return 2; }
  const repo = resolve(o.repo);
  if (!existsSync(repo)) { process.stderr.write(`issue-tokenomics: no such repo ${repo}\n`); return 2; }
  const deadline = Date.now() + num(o.wait) * 1000;
  let lines = sessionLines(repo, o.session);
  while (lines.length <= num(o.baselineCount) && Date.now() < deadline) { await sleep(2000); lines = sessionLines(repo, o.session); }
  if (lines.length <= num(o.baselineCount)) {
    process.stderr.write(`issue-tokenomics: no new ledger line for ${o.session} (have ${lines.length}, baseline ${o.baselineCount}) — SessionEnd capture missing?\n`);
    return 3;
  }
  const after = lines[lines.length - 1];
  const before = num(o.baselineCount) > 0 ? lines[Math.min(num(o.baselineCount), lines.length) - 1] : null;
  const block = buildIssueTokenomics(after, before, o);
  process.stdout.write(o.json ? `${JSON.stringify(block, null, 2)}\n` : `${toYaml(block)}\n`);
  return 0;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().then((code) => process.exit(code), (e) => { process.stderr.write(`issue-tokenomics: ${e.message}\n`); process.exit(1); });
}
