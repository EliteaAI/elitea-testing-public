#!/usr/bin/env node
// coverage/campaign.mjs — lifecycle helpers around report.mjs.
//
// A runtime-coverage campaign is a multi-hour, easy-to-get-wrong operation. Each
// subcommand here exists because doing it by hand produced a WRONG NUMBER at
// least once (see coverage/README.md § Gotchas):
//
//   preflight    Refuse to start a 4h run that will die on a missing prereq.
//   lint-areas   Catch areas.json drift — a moved feature silently re-buckets.
//   archive      Snapshot report + rollups + provenance BEFORE wiping. Without
//                this there is nothing to compare the next campaign against.
//   compare      Diff two campaigns re-bucketed with the SAME (current) map.
//                Diffing the two printed tables is wrong when the map drifted.
//
// Usage (from repo root):
//   node coverage/campaign.mjs preflight [--tests N]
//   node coverage/campaign.mjs lint-areas
//   node coverage/campaign.mjs archive <label> [--wipe]
//   node coverage/campaign.mjs compare <baselineDirOrJson> [--json]
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, '..');
const workspace = path.resolve(repoRoot, '..');
const uiRoot = path.join(workspace, 'EliteaUI');
const uiSrc = path.join(uiRoot, 'src');
const archiveRoot = path.join(workspace, 'coverage-archive');
const v8dir = path.join(here, '.v8');
const reportDir = path.join(here, 'report');
const summaryOf = (dir) => path.join(dir, 'coverage-summary.json');

const OK = '  ok  ', BAD = ' FAIL ', WARN = ' warn ';
let failures = 0;
const say = (tag, msg) => console.log(`[${tag}] ${msg}`);
const ok = (m) => say(OK, m);
const bad = (m) => { failures++; say(BAD, m); };
const warn = (m) => say(WARN, m);

const sh = (cmd, args, opts = {}) => {
  try {
    return execFileSync(cmd, args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], ...opts }).trim();
  } catch { return null; }
};
const dirBytes = (d) => {
  if (!fs.existsSync(d)) return 0;
  return fs.readdirSync(d).reduce((s, f) => {
    const st = fs.statSync(path.join(d, f));
    return s + (st.isDirectory() ? 0 : st.size);
  }, 0);
};
const gb = (b) => (b / 1024 ** 3).toFixed(1) + ' GB';

// ---------------------------------------------------------------- areas map
const loadAreas = () => JSON.parse(fs.readFileSync(path.join(here, 'areas.json'), 'utf8'));
const areaOrder = (areas) =>
  Object.keys(areas).filter((a) => a !== 'shared' && Array.isArray(areas[a]));
// Mirrors area_rollup.py: substring match, FIRST match wins, 'shared' last.
const makeBucket = (areas) => {
  const order = areaOrder(areas);
  const shared = Array.isArray(areas.shared) ? areas.shared : [];
  return (p) => {
    for (const a of order) if (areas[a].some((pre) => p.includes(pre))) return a;
    if (shared.some((pre) => p.includes(pre))) return 'shared';
    return 'other';
  };
};

// ---------------------------------------------------------------- preflight
async function preflight(args) {
  const n = Number((args.find((a) => a.startsWith('--tests=')) || '').split('=')[1]) ||
    Number(args[args.indexOf('--tests') + 1]) || 0;
  console.log('Preflight — runtime coverage campaign\n');

  fs.existsSync(path.join(here, 'node_modules', 'monocart-coverage-reports'))
    ? ok('monocart-coverage-reports installed')
    : bad('monocart missing — run: cd coverage && npm install');

  fs.existsSync(uiSrc) ? ok(`EliteaUI src found (${uiSrc})`)
    : bad(`EliteaUI src NOT found at ${uiSrc} — the full-codebase denominator needs it`);

  fs.existsSync(path.join(uiRoot, 'node_modules', 'esbuild', 'lib', 'main.js'))
    ? ok('esbuild present (untested JSX gets branch metrics)')
    : warn('esbuild missing in ../EliteaUI/node_modules — untested JSX degrades to byte/line only, DEFLATING the branch denominator vs prior campaigns');

  const branch = sh('git', ['rev-parse', '--abbrev-ref', 'HEAD'], { cwd: uiRoot });
  if (branch) {
    branch === 'automation/testids'
      ? ok(`EliteaUI on ${branch}`)
      : warn(`EliteaUI on '${branch}', expected 'automation/testids' — testids may be missing`);
  }

  const url = process.env.ELITEA_URL || 'http://localhost:5173';
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(5000) });
    res.ok ? ok(`dev server responding at ${url} (HTTP ${res.status})`)
      : bad(`dev server at ${url} returned HTTP ${res.status}`);
  } catch {
    bad(`dev server NOT reachable at ${url} — start it: cd ../EliteaUI && npm run dev`);
  }

  const df = sh('df', ['-k', repoRoot]);
  if (df) {
    const avail = Number(df.trim().split('\n').pop().split(/\s+/)[3]) * 1024;
    const need = (n || 400) * 25 * 1024 ** 2; // ~25 MB of fragments per test
    avail > need * 1.3
      ? ok(`disk headroom ${gb(avail)} (campaign of ${n || 400} tests needs ~${gb(need)})`)
      : bad(`disk headroom ${gb(avail)} too tight — ${n || 400} tests need ~${gb(need)} of fragments`);
  }

  const frags = fs.existsSync(v8dir) ? fs.readdirSync(v8dir).filter((f) => f.endsWith('.json')).length : 0;
  if (frags) {
    warn(`${frags} fragment(s) already in coverage/.v8 (${gb(dirBytes(v8dir))}) — the next report MERGES them in.`);
    warn('  Intentional across waves; otherwise archive + wipe first:  node coverage/campaign.mjs archive <label> --wipe');
  } else ok('coverage/.v8 empty — clean slate');

  console.log(failures ? `\n${failures} blocking problem(s). Fix before starting.` : '\nAll clear.');
  return failures ? 1 : 0;
}

// -------------------------------------------------------------- lint-areas
function lintAreas() {
  const areas = loadAreas();
  console.log('Checking areas.json against the real EliteaUI src tree\n');
  // A mapping may legitimately point into a CONNECTED first-party repo (the
  // Support Assistant is aliased into the dev server via VITE_ASSISTANT_LOCAL),
  // so resolve against every source root we serve from — not EliteaUI alone.
  const sourceRoots = [uiRoot, path.join(workspace, 'elitea_assistant')].filter((r) => fs.existsSync(r));
  const existsSomewhere = (p) => sourceRoots.some((r) => fs.existsSync(path.join(r, p)));
  const dead = [];
  for (const [area, prefixes] of Object.entries(areas)) {
    if (!Array.isArray(prefixes)) continue;
    for (const pre of prefixes) if (!existsSomewhere(pre)) dead.push([area, pre]);
  }
  console.log(`source roots: ${sourceRoots.map((r) => path.basename(r)).join(', ')}\n`);
  if (dead.length) {
    bad(`${dead.length} mapped path(s) no longer exist — files that moved are now bucketed elsewhere (silently):`);
    for (const [a, p] of dead) console.log(`         ${a.padEnd(16)} ${p}`);
    console.log('       Fix: repoint or delete the key. A dead mapping made `analytics`');
    console.log('       vanish into `settings` in the 2026-08-10 campaign.');
  } else ok('every mapped path exists');

  // Anything under src/ that no prefix claims lands in `other`.
  const bucket = makeBucket(areas);
  const unmapped = new Map();
  const walk = (d, rel = 'src') => {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const r = `${rel}/${e.name}`;
      if (e.isDirectory()) { if (e.name !== 'assets') walk(path.join(d, e.name), r); }
      else if (/\.(jsx?|tsx?)$/.test(e.name) && bucket(r) === 'other') {
        const key = r.split('/').slice(0, 3).join('/');
        unmapped.set(key, (unmapped.get(key) || 0) + 1);
      }
    }
  };
  if (fs.existsSync(uiSrc)) walk(uiSrc);
  if (unmapped.size) {
    warn(`${[...unmapped.values()].reduce((a, b) => a + b, 0)} source file(s) fall into 'other' — add to areas.json if they matter:`);
    for (const [k, c] of [...unmapped].sort((a, b) => b[1] - a[1]).slice(0, 12)) {
      console.log(`         ${String(c).padStart(4)} file(s)  ${k}`);
    }
  } else ok("nothing lands in 'other'");

  // The scan above only sees EliteaUI/src. Code from a CONNECTED repo (the
  // Support Assistant, aliased in via VITE_ASSISTANT_LOCAL) never appears there
  // — it reaches the browser at runtime only. So also inspect the last report,
  // where such files show up in 'other' with real branches.
  if (fs.existsSync(summaryOf(reportDir))) {
    const j = JSON.parse(fs.readFileSync(summaryOf(reportDir), 'utf8'));
    const runtime = new Map();
    for (const [k, v] of Object.entries(j)) {
      if (k === 'total' || !v || !v.branches || bucket(k) !== 'other') continue;
      if (fs.existsSync(path.join(uiRoot, k))) continue; // already covered by the tree scan
      const key = k.split('/').slice(0, 3).join('/');
      const e = runtime.get(key) || { files: 0, br: 0 };
      e.files++; e.br += v.branches.total || 0;
      runtime.set(key, e);
    }
    if (runtime.size) {
      warn("'other' also holds files NOT in EliteaUI/src — a connected repo served at runtime. These sit in the denominator:");
      for (const [k, e] of [...runtime].sort((a, b) => b[1].br - a[1].br)) {
        console.log(`         ${String(e.br).padStart(5)} branches, ${e.files} file(s)  ${k}`);
      }
      console.log('       Decide deliberately: map them in areas.json, or exclude them in');
      console.log('       report.mjs sourceFilter. Either is fine — drifting is not.');
    }
  }
  return dead.length ? 1 : 0;
}

// ----------------------------------------------------------------- archive
function archive(args) {
  const label = args.find((a) => !a.startsWith('--'));
  if (!label) { console.error('usage: campaign.mjs archive <label> [--wipe]'); return 2; }
  if (!fs.existsSync(summaryOf(reportDir))) {
    console.error(`No report at ${reportDir} — run: node coverage/report.mjs`);
    return 1;
  }
  const dest = path.join(archiveRoot, label);
  fs.mkdirSync(dest, { recursive: true });
  fs.cpSync(reportDir, path.join(dest, 'report'), { recursive: true });

  const py = path.join(repoRoot, '.venv', 'bin', 'python');
  if (fs.existsSync(py)) {
    for (const [file, flags] of [['rollup-branches.txt', ['--branches']], ['rollup-statements.txt', []]]) {
      const out = sh(py, [path.join('coverage', 'area_rollup.py'), ...flags], { cwd: repoRoot });
      if (out) fs.writeFileSync(path.join(dest, file), out + '\n');
    }
    ok('rollup tables captured');
  } else warn('.venv/bin/python not found — rollup tables not captured');

  const frags = fs.existsSync(v8dir) ? fs.readdirSync(v8dir).filter((f) => f.endsWith('.json')).length : 0;
  const summary = JSON.parse(fs.readFileSync(summaryOf(reportDir), 'utf8'));
  const t = summary.total || {};
  fs.writeFileSync(path.join(dest, 'PROVENANCE.txt'), [
    `label:        ${label}`,
    `archived:     ${new Date().toISOString()}`,
    `branches:     ${t.branches ? `${t.branches.covered}/${t.branches.total} = ${t.branches.pct}%` : 'n/a'}`,
    `statements:   ${t.statements ? `${t.statements.covered}/${t.statements.total} = ${t.statements.pct}%` : 'n/a'}`,
    `entries:      ${Object.keys(summary).length - 1}`,
    `fragments:    ${frags} (${gb(dirBytes(v8dir))})`,
    `test repo:    ${sh('git', ['rev-parse', '--abbrev-ref', 'HEAD'], { cwd: repoRoot })} @ ${sh('git', ['rev-parse', '--short', 'HEAD'], { cwd: repoRoot })}`,
    `EliteaUI:     ${sh('git', ['rev-parse', '--abbrev-ref', 'HEAD'], { cwd: uiRoot })} @ ${sh('git', ['rev-parse', '--short', 'HEAD'], { cwd: uiRoot })}`,
    '',
  ].join('\n'));
  ok(`archived -> ${dest}`);

  if (args.includes('--wipe')) {
    fs.rmSync(v8dir, { recursive: true, force: true });
    fs.rmSync(reportDir, { recursive: true, force: true });
    ok('wiped coverage/.v8 and coverage/report — clean slate for the next campaign');
  } else {
    console.log(`[note ] fragments kept (${gb(dirBytes(v8dir))}). Re-slice without re-running tests, or free the disk with --wipe.`);
  }
  return 0;
}

// ----------------------------------------------------------------- compare
function resolveSummary(p) {
  const tries = [p, summaryOf(p), path.join(p, 'report', 'coverage-summary.json')];
  for (const t of tries) if (fs.existsSync(t) && fs.statSync(t).isFile()) return t;
  return null;
}
function tally(file, bucket) {
  const j = JSON.parse(fs.readFileSync(file, 'utf8'));
  const out = {};
  let dupes = 0;
  for (const [k, v] of Object.entries(j)) {
    if (k === 'total' || !v || !v.branches) continue;
    if (/-t=\d+$/.test(k)) dupes++;
    const a = bucket(k);
    const o = out[a] ??= { c: 0, t: 0 };
    o.c += v.branches.covered || 0;
    o.t += v.branches.total || 0;
  }
  return { out, dupes };
}
function compare(args) {
  const target = args.find((a) => !a.startsWith('--'));
  if (!target) { console.error('usage: campaign.mjs compare <baselineDirOrJson> [--json]'); return 2; }
  const bFile = resolveSummary(target);
  if (!bFile) { console.error(`No coverage-summary.json under ${target}`); return 1; }
  const nFile = summaryOf(reportDir);
  if (!fs.existsSync(nFile)) { console.error(`No current report — run: node coverage/report.mjs`); return 1; }

  // Both sides bucketed with the CURRENT map, so a moved feature cannot fake a delta.
  const bucket = makeBucket(loadAreas());
  const B = tally(bFile, bucket), N = tally(nFile, bucket);
  for (const [label, r] of [['baseline', B], ['current', N]]) {
    if (r.dupes) warn(`${label} contains ${r.dupes} Vite HMR duplicate entr(ies) ("-t=<epoch>") — its denominator is inflated and its coverage split across pairs. Regenerate it with a report.mjs that strips the suffix.`);
  }

  const pct = (c, t) => (t ? (100 * c) / t : 0);
  const areas = [...new Set([...Object.keys(B.out), ...Object.keys(N.out)])];
  const rows = areas.map((a) => {
    const b = B.out[a] || { c: 0, t: 0 }, n = N.out[a] || { c: 0, t: 0 };
    return { a, bc: b.c, bt: b.t, nc: n.c, nt: n.t, bp: pct(b.c, b.t), np: pct(n.c, n.t) };
  }).sort((x, y) => y.nt - x.nt);
  const sum = (k) => rows.reduce((s, r) => s + r[k], 0);
  const [TBC, TB, TNC, TN] = [sum('bc'), sum('bt'), sum('nc'), sum('nt')];

  if (args.includes('--json')) {
    console.log(JSON.stringify({ baseline: bFile, current: nFile, rows, total: { TBC, TB, TNC, TN } }, null, 1));
    return 0;
  }
  console.log(`baseline: ${bFile}\ncurrent : ${nFile}\n`);
  console.log('| area | base br% | new br% | Δpp | base cov | new cov | Δ cov | denom Δ |');
  console.log('|---|---:|---:|---:|---:|---:|---:|---:|');
  const s = (n) => (n >= 0 ? '+' : '') + n;
  for (const r of rows) {
    console.log(`| ${r.a} | ${r.bp.toFixed(0)}% | ${r.np.toFixed(0)}% | ${s((r.np - r.bp).toFixed(0))} | ${r.bc} | ${r.nc} | ${s(r.nc - r.bc)} | ${s(r.nt - r.bt)} |`);
  }
  console.log(`| **OVERALL** | **${pct(TBC, TB).toFixed(1)}%** | **${pct(TNC, TN).toFixed(1)}%** | **${s((pct(TNC, TN) - pct(TBC, TB)).toFixed(1))}** | **${TBC}** | **${TNC}** | **${s(TNC - TBC)}** | **${s(TN - TB)}** |`);

  const drift = TB ? (100 * (TN - TB)) / TB : 0;
  console.log('');
  Math.abs(drift) > 10
    ? warn(`denominator moved ${drift.toFixed(1)}% (${TB} -> ${TN}). Expect only real source growth (a few %). A jump this size usually means HMR duplicates, a missing esbuild, or an areas.json change — verify before quoting the %.`)
    : ok(`denominator moved ${drift.toFixed(1)}% (${TB} -> ${TN}) — consistent with source growth`);
  return 0;
}

// -------------------------------------------------------------------- main
const [cmd, ...rest] = process.argv.slice(2);
const table = {
  preflight, 'lint-areas': lintAreas, archive, compare,
};
if (!cmd || !table[cmd]) {
  console.log(`coverage/campaign.mjs — runtime-coverage campaign helpers

  preflight [--tests N]        check prereqs BEFORE a multi-hour run
  lint-areas                   verify areas.json still matches the src tree
  archive <label> [--wipe]     snapshot report+rollups+provenance, optionally wipe
  compare <baseline> [--json]  diff two campaigns, both re-bucketed with the current map

Archives live in ${archiveRoot} (outside the repo — coverage/report is gitignored,
and an in-repo archive dir would not be).`);
  process.exit(cmd ? 2 : 0);
}
process.exit((await table[cmd](rest)) || 0);
