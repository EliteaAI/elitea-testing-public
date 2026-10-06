#!/usr/bin/env node
// issue-tokenomics-backfill.mjs — post the per-run tokenomics blocks for issues
// the factory loop ALREADY worked, wherever the telemetry ledger captured the
// session. The loop derives one conversation id per issue (run.sh `sid_for`:
// md5 of "<tracking repo>#<issue>#<agent|SID_SCOPE>", uuid-shaped) — so the
// candidate set is exact: every issue number whose derived id has ledger lines.
// Each ledger line is one session end, so line i vs line i-1 is one run's
// delta — the same chain the loop posts live. What the loop knew and the
// ledger does not (attempt counter, wall clock start, board outcome) is null.
//
//   node issue-tokenomics-backfill.mjs --tracking-repo owner/repo --agent <agent> \
//        [--loop tal] [--sid-scope <scope>] [--issues 1-2500] [--repo <path>] \
//        [--post] [--gh "env -u GITHUB_TOKEN gh"]
//
//   default = DRY RUN: prints the candidate table (issue, runs in ledger, runs
//   already commented, to post). --post writes the missing comments, in order.
import { createHash } from 'node:crypto';
import { execFileSync, spawnSync } from 'node:child_process';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadLines } from '../../.claude/skills/tokenomics/scripts/team-report.mjs';
import { buildIssueTokenomics, toYaml, parseArgs } from './issue-tokenomics.mjs';

export function sidFor(trackingRepo, issue, scope) {
  const h = createHash('md5').update(`${trackingRepo}#${issue}#${scope}`).digest('hex');
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-4${h.slice(13, 16)}-a${h.slice(17, 20)}-${h.slice(20, 32)}`;
}

/** issue → its ledger lines (capture order), for every issue in the range that has any. */
export function candidates(lines, { trackingRepo, scope, from = 1, to = 2500 }) {
  const byId = new Map();
  for (const l of lines) { if (!byId.has(l.id)) byId.set(l.id, []); byId.get(l.id).push(l); }
  const out = [];
  for (let n = from; n <= to; n++) {
    const sid = sidFor(trackingRepo, n, scope);
    if (byId.has(sid)) out.push({ issue: n, sid, lines: byId.get(sid) });
  }
  return out;
}

export function backfillBlocks(c, { loop, agent }) {
  return c.lines.map((line, i) => buildIssueTokenomics(line, i > 0 ? c.lines[i - 1] : null, {
    issue: c.issue, loop, agent, runsBefore: i, ended: line.endedAt ?? null,
  }));
}

const ghCmd = (o) => (o.gh ? o.gh.split(/\s+/) : ['gh']);
const run = (cmd, args, input) => {
  const r = spawnSync(cmd[0], [...cmd.slice(1), ...args], { encoding: 'utf8', input });
  if (r.status !== 0) throw new Error((r.stderr || r.stdout || `exit ${r.status}`).trim().slice(0, 200));
  return r.stdout;
};

export async function main(argv = process.argv.slice(2)) {
  const o = parseArgs(argv);
  const post = o.post === true;
  if (post && !o.gh) process.stderr.write('issue-tokenomics-backfill: posting with the real `gh` — pass --gh "env -u GITHUB_TOKEN gh" to force the keyring identity\n');
  if (!o.trackingRepo || !o.agent) { process.stderr.write('usage: --tracking-repo owner/repo --agent <agent> [--loop tal] [--sid-scope s] [--issues a-b] [--post]\n'); return 2; }
  const [from, to] = String(o.issues ?? '1-2500').split('-').map(Number);
  const scope = o.sidScope ?? o.agent;
  const loop = o.loop ?? 'tal';
  const lines = loadLines([resolve(o.repo)]);
  const cands = candidates(lines, { trackingRepo: o.trackingRepo, scope, from, to });
  const gh = ghCmd(o);
  let posted = 0, toPost = 0;
  process.stdout.write(`${post ? 'POSTING' : 'DRY RUN'} — ${cands.length} issue(s) with ledger data for agent ${o.agent} in #${from}-#${to}\n`);
  process.stdout.write('issue\truns\tposted\tto-post\tlast run ended\t$ total\n');
  for (const c of cands) {
    let already = 0, comments = '';
    try {
      comments = run(gh, ['issue', 'view', String(c.issue), '-R', o.trackingRepo, '--json', 'comments', '-q', '.comments[].body']);
      already = (comments.match(new RegExp(`^conversation: ${c.sid}`, 'gm')) ?? []).length;
    } catch (e) { process.stdout.write(`#${c.issue}\t${c.lines.length}\t?\t?\tcomments unreadable: ${e.message}\n`); continue; }
    const blocks = backfillBlocks(c, { loop, agent: o.agent });
    const missing = blocks.slice(already);
    toPost += missing.length;
    const last = c.lines[c.lines.length - 1];
    process.stdout.write(`#${c.issue}\t${c.lines.length}\t${already}\t${missing.length}\t${last.endedAt ?? '?'}\t${typeof last.costUsd === 'number' ? last.costUsd.toFixed(2) : 'n/a'}\n`);
    if (!post) continue;
    for (const b of missing) {
      const body = `📊 **Tokenomics** — run ${b.conversation_total.runs} of this conversation (backfilled from the telemetry ledger)\n\n\`\`\`yaml\n${toYaml(b)}\n\`\`\``;
      try { run(gh, ['issue', 'comment', String(c.issue), '-R', o.trackingRepo, '-F', '-'], body); posted++; }
      catch (e) { process.stdout.write(`#${c.issue}: comment failed — ${e.message}\n`); break; }
    }
  }
  process.stdout.write(post ? `posted ${posted} comment(s)\n` : `would post ${toPost} comment(s) — re-run with --post\n`);
  return 0;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().then((code) => process.exit(code), (e) => { process.stderr.write(`issue-tokenomics-backfill: ${e.message}\n`); process.exit(1); });
}
