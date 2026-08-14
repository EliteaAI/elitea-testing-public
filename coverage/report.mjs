// V8 coverage fragments -> per-src-file coverage report (monocart-coverage-reports).
// Run from repo root: node coverage/report.mjs
// Fragments are written by the COVERAGE=1 page fixture (automation/conftest.py)
// into coverage/.v8/*.json — each an array of V8 ScriptCoverage entries with
// `source` attached (captured via CDP Debugger.getScriptSource; Vite dev serves
// modules with inline sourcemaps, so remap works offline).
import MCR from 'monocart-coverage-reports';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));

// Full-codebase denominator: EliteaUI sibling clone's src tree. Files the browser
// never loaded are added with 0% coverage (monocart `all` option), so the
// denominator is the whole codebase and stays constant across campaigns.
const uiSrc = path.resolve(here, '..', '..', 'EliteaUI', 'src');
// Untested .jsx needs a JSX->JS transform for branch counting; reuse EliteaUI's
// own esbuild (no new dependency). Degrade gracefully if unavailable.
let esbuild = null;
try {
  const esbuildMain = path.resolve(here, '..', '..', 'EliteaUI', 'node_modules', 'esbuild', 'lib', 'main.js');
  esbuild = (await import(pathToFileURL(esbuildMain).href)).default;
} catch {
  console.warn('[warn] esbuild not found in ../EliteaUI/node_modules — untested JSX files get byte/line metrics only');
}
let transformFailures = 0;
const v8dir = path.join(here, '.v8');
const files = fs.existsSync(v8dir) ? fs.readdirSync(v8dir).filter(f => f.endsWith('.json')) : [];
if (!files.length) {
  console.error(`No V8 fragments in ${v8dir} — run the tests with COVERAGE=1 first (Stage 3)`);
  process.exit(1);
}

const mcr = MCR({
  name: 'Elitea automation runtime coverage',
  outputDir: path.join(here, 'report'),
  // Vite dev's per-module sourcemaps carry only bare filenames (no dirs), but
  // Vite serves each source file unbundled at its own URL — so the served path
  // (info.distFile, e.g. "localhost-5173/src/[fsd]/.../X.jsx") IS the original
  // source path. Restore it from there; strip Vite query suffixes (?import&react).
  // NOTE: monocart normalises the served URL into a filesystem-safe distFile,
  // which turns "?" into "-". So Vite's HMR cache-buster arrives as a trailing
  // "-t=<epoch-ms>" and split('?') never sees it. Left unstripped, every file
  // touched by an HMR reload mid-run becomes a SECOND entry, splitting its
  // coverage and inflating the denominator (2026-08-09 campaign: 569 dupes,
  // +18,892 phantom branches). Strip it so both halves merge into one file.
  sourcePath: (filePath, info) => {
    const base = ((info && info.distFile) || filePath)
      .split('?')[0]
      .replace(/-t=\d+$/, '');
    const i = base.indexOf('src/');
    return i >= 0 ? base.slice(i) : filePath;
  },
  // Keep only EliteaUI's own source; drop node_modules, vite client/deps, HMR
  // runtime, and asset stubs (svg-as-component modules — icon noise the breadth
  // report also excludes, keeps denominators comparable).
  sourceFilter: (sourcePath) =>
    sourcePath.startsWith('src/') &&
    !sourcePath.includes('node_modules') &&
    !sourcePath.startsWith('src/assets/'),
  // Add every never-loaded source file at 0% -> fixed, full-codebase denominator.
  all: {
    dir: [uiSrc],
    filter: {
      '**/assets/**': false,
      '**/stories/**': false,
      '**/*.stories.*': false,
      '**/*.test.*': false,
      '**/*.{css,scss,svg,png,json,md}': false,
      '**/*.{js,jsx,ts,tsx}': true,
      '**/*': false,
    },
    transformer: async (entry) => {
      if (!esbuild) return;
      const ext = entry.url.split('.').pop();
      const loader = ext === 'ts' ? 'ts' : ext === 'tsx' ? 'tsx' : 'jsx';
      try {
        const { code, map } = await esbuild.transform(entry.source, {
          loader, sourcemap: true, sourcefile: entry.url,
        });
        entry.source = code;
        entry.sourceMap = JSON.parse(map);
      } catch {
        transformFailures += 1; // leave untransformed -> byte/line metrics only
      }
    },
  },
  reports: ['v8', 'json-summary', 'console-summary'],
});

let entries = 0;
for (const f of files) {
  const data = JSON.parse(fs.readFileSync(path.join(v8dir, f), 'utf8'));
  const list = Array.isArray(data) ? data : data.result;
  if (Array.isArray(list) && list.length) {
    entries += list.length;
    await mcr.add(list);
  }
}
console.log(`Merged ${files.length} fragment(s), ${entries} script entries`);
await mcr.generate();
if (transformFailures) console.warn(`[warn] ${transformFailures} untested file(s) failed JSX transform (byte/line metrics only)`);

// Guard: a duplicate-entry bug is INVISIBLE in the numbers — it presents as a
// plausible-looking regression (the 2026-08-09 campaign read 32.7% instead of
// 47.1%). If any per-file key still carries a Vite query suffix, sourcePath()
// above failed to normalise it and the denominator is inflated. Fail loudly.
try {
  const summaryFile = path.join(here, 'report', 'coverage-summary.json');
  const summary = JSON.parse(fs.readFileSync(summaryFile, 'utf8'));
  const keys = Object.keys(summary).filter((k) => k !== 'total');
  const suspect = keys.filter((k) => !/\.(jsx?|tsx?|css|scss)$/.test(k));
  if (suspect.length) {
    console.warn(`[warn] ${suspect.length} entr(ies) do not end in a source extension — likely un-normalised Vite suffixes, which SPLIT a file's coverage and inflate the denominator:`);
    for (const k of suspect.slice(0, 5)) console.warn(`         ${k}`);
    console.warn('       Extend sourcePath() above to strip the suffix, then re-run this script (no test re-run needed).');
  }
  console.log(`${keys.length} source files in the report`);
} catch { /* summary unreadable — nothing to assert */ }

console.log(`HTML report -> ${path.join(here, 'report', 'index.html')}`);
console.log('Next: node coverage/campaign.mjs compare <baselineDir>   (canonical %, both sides re-bucketed)');
