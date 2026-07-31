// Canonical batch workflow for the test-automation pipeline.
// Claude Code only — invoked by the orchestrator via
//   Workflow({ scriptPath: '<installed skill>/scripts/workflows/batch-build.workflow.mjs',
//              args: { slug, base, cases: [{id, title?}, …], clusters?, … } })
//
// ONE workflow, ONE report. It runs the whole batch — analyse, implement,
// review, merge, gate — and returns a single status the lead acts on:
// land what is `automated`, classify what is `blocked`, replan the rest.
//
//   for each unit, IN ORDER, on the batch trunk:
//     analyse   → live exploration; commits its AFS + digest to the trunk
//     implement → on a unit branch cut FROM the trunk
//     review    → static, reads the diff of that branch
//     fix       → rounds until APPROVED (see loopVerdict)
//     merge     → the unit branch into the trunk, then the tree RETURNS to it
//   gate        → the batch's specs together, N consecutive green + affected specs
//   report      → one writer, at close
//
// ONE TREE, ONE MASTER — the invariant everything else rests on. There is no
// concurrency here at all, and that is the design, not a limitation:
//
//   Always return the tree to a known state, and always branch from it.
//
// A single working tree has ONE state at a time, but concurrent slots need
// DIFFERENT states — an analyst wants base, a reviewer wants the branch it is
// judging, an implementer wants its own. No rule can reconcile that; only
// ordering can. An earlier revision ran analysts in parallel with builds and
// paid for it in the field: eight `local changes would be overwritten by
// checkout` aborts (the analyst's `_surface.md` against a build's branch
// switch), merge conflicts concentrated in shared page objects, 90 conflict
// hits and three git-surgery rescues in one session.
//
// Serialising buys back everything those hazards cost us in rules. Analysts may
// now run git, commit, and push like anyone else, because nothing else is in
// the tree while they do. Deleted with the concurrency: browser lanes, the
// per-unit AFS handoff, the integrator's orphan sweep, and the separate
// integrate phase — units merge as they finish, so integration is continuous
// and conflicts surface small, early, and while their author is still live.
//
// THROUGHPUT COMES FROM CLUSTERING, NOT CONCURRENCY. Units are the wall clock,
// so a cluster of 5 is one unit rather than five — a 4x reduction against the 2x
// that analyst concurrency bought, and without any of the hazards.
//
// WHY NO BOARD. Earlier revisions kept a `.agents/automation-board/` state
// machine — 15 statuses, legal transitions, a serialized clerk applying every
// flip. It existed to record PROGRESS, and progress only needs recording if
// something reads it mid-run. Nothing does: the runtime already persists every
// agent's full return to the run's `journal.jsonl` as it completes, and
// `resumeFromRunId` replays completed calls from cache. The board was a second,
// hand-maintained copy of that — and it drifted: 4 of 12 merged cases in one
// campaign ended mis-stated, one sitting at `analysis` despite a merge commit,
// which would have bought a full re-analysis of shipped work. What survives an
// interruption now: the journal (every return), git (AFS on base, branches,
// PRs), and the report once it lands. Recovery turns the first two into the
// third by hand — playbook § Interruption and resumption.
//
// OUTCOMES, NOT STATUSES. A case ends somewhere; it does not travel through a
// state machine. `outcome` says where it ended; `findings` — orthogonal — say
// what turned up on the way. A case can be `automated` AND have filed two
// defects and raised a question: the work completed, and there is still
// something to tell. The old vocabulary forced that into the exception status
// `defect-found`, which read as "this case failed".
//
// UNITS & CLUSTERS: work flows in units of 1..k cases. A cluster (args.clusters,
// declared by the plan per campaign-planning.md) is a pack of genuinely similar
// same-surface cases analysed by ONE analyst in ONE live session — every case
// still executed individually (per-case evidence mandatory) — and implemented
// as ONE branch (family AFS → parameterized spec, one row per case). Unlisted
// cases run as solo units. With builds sequenced, UNITS are the wall clock, so
// clustering is the main throughput lever a batch has.
//
// PROMPT DETERMINISM IS THE RESUME CONTRACT (field lesson, 2026-07-24 — it cost
// one campaign ~2x). `resumeFromRunId` caches every agent() call keyed on the
// EXACT (prompt, opts) pair, so any value interpolated into a prompt that
// depends on RUN TIMING rather than on the args breaks the cache on every
// resume and the agent re-runs live. An earlier revision handed out browser
// lanes from a counting semaphore (completion order): measured, 20 of 28
// analysed cases were dispatched under >=2 distinct lane numbers and 35 of 53
// were re-analysed from scratch. Serialising removed that whole class: every
// unit branches from the TRUNK, whose name comes from args, so no prompt
// depends on who finished first. When editing: interpolate args and worker
// RESULTS, never anything derived from completion order.

export const meta = {
  name: 'ta-batch-build',
  description: 'One batch, one report: units run in order on the batch trunk — analyse (commits its AFS) → implement on a branch cut from the trunk → static review → fix to APPROVED → merge back, tree returns to the trunk — then one hardening gate (N consecutive green plus the specs the batch could have broken), returning per-case outcomes and findings for the lead to land, classify and replan from',
  whenToUse: 'Orchestrator (test-automation-lead) on Claude Code once a batch of cases has been planned and clustered — it runs the batch end to end; the lead (or a closer) lands it per seeded policy, classifies anything red, and replans the remainder',
  phases: [
    { title: 'Analysis', detail: 'per unit, live exploration on the trunk; commits its AFS + surface digest' },
    { title: 'Build', detail: 'per unit: implement green-once on a branch cut from the trunk, static review, fix rounds, merge back' },
    { title: 'Gate', detail: 'the batch specs together N consecutive green, plus one run of the specs the batch could have broken — its own agent, never the implementer' },
    { title: 'Report', detail: 'one writer: per-case outcomes + findings to disk' },
  ],
}

// ---- args ------------------------------------------------------------------
// Tolerate stringified args (observed 2026-07-20).
const A = typeof args === 'string' ? JSON.parse(args) : (args ?? {})
if (!A.slug || !A.base || !Array.isArray(A.cases) || A.cases.length === 0 || A.cases.some((c) => !c?.id)) {
  throw new Error(
    'args required: { slug, base, cases: [{id, title?}, …] (every case needs an id), clusters?: [[id,…],…], ' +
    'analyzeOnly?, preAnalyzed?: [{id, afs_path, surface_key}], root?, reportDir?, ' +
    'agentTypes?, workerModel?, workerEffort?, reviewerModel?, mergeModel?, reporterModel?, ' +
    'extendImplementerModel?, fixRounds?, gateN?, gateCmd?, integrationBranch?, skipGate?, ' +
    'reviewPanel?, breakerThreshold?, extendRateThreshold?, budgetReserve? }'
  )
}
{
  // Args removed by the serialisation redesign. Silently ignoring one changes
  // behaviour without saying so — `skipIntegrate: true` used to stop before
  // integrate+gate and would now run a full gate.
  const gone = ['analystConcurrency', 'skipIntegrate', 'integratorModel', 'integrateScriptPath']
    .filter((k) => A[k] !== undefined)
  if (gone.length) {
    throw new Error(
      `removed arg(s): ${gone.join(', ')}. Units are strictly sequential now, integration happens per unit, `
      + 'and the integrator is not a separate slot. Use `skipGate` to stop after review; drop the rest.'
    )
  }
}
{
  // A duplicate id would build twice and collapse into one OUTCOME row; a
  // missing id would file snapshots and outcomes under 'undefined'.
  const dup = A.cases.map((c) => c.id).filter((id, i, arr) => arr.indexOf(id) !== i)
  if (dup.length) throw new Error(`duplicate case id(s) in args.cases: ${[...new Set(dup)].join(', ')}`)
}
// analyzeOnly: stop after the analyst front (campaign heads pass — the
// conductor analyzes breadth-first heads to source the foundation inventory).
// preAnalyzed: cases already analyzed in an earlier analyzeOnly run — their
// units skip the analyst dispatch and go straight to build.
const ANALYZE_ONLY = A.analyzeOnly === true
const PRE = new Map((Array.isArray(A.preAnalyzed) ? A.preAnalyzed : []).map((p) => [p.id, p]))
const SLUG = A.slug
const BASE = A.base
const CASES = A.cases
const ROOT = A.root ? `${String(A.root).replace(/\/+$/, '')}/` : ''
// ALWAYS dispatch named agent types: the SubagentStart hook resolves role
// memory from the agent name; an anonymous workflow agent gets none.
const TYPES = {
  analyst: 'qa-engineer',
  implementer: 'test-automation-engineer',
  reviewer: 'qa-engineer',
  gate: 'test-automation-engineer',
  // Every dispatch that touches the repository is named. Anonymous ones resolve
  // to no role and therefore get no role memory or project briefing.
  reporter: 'test-automation-engineer',
  ...(A.agentTypes ?? {}),
}
// No model opt = the agent definition's frontmatter `model:` governs (agentType
// resolves from the same registry as the Agent tool: explicit opt > frontmatter
// > inherit). Analyst, implementer, and gate deliberately pass NO model so the
// installed AGENT.md stays the configuration surface; args override per run.
const WORKER = {
  ...(A.workerModel ? { model: A.workerModel } : {}),
  ...(A.workerEffort ? { effort: A.workerEffort } : {}),
}
// Reviewer: same rule — frontmatter governs unless an arg overrides. (An
// earlier hardcoded 'sonnet' floor here silently overrode a project's tuned
// qa-engineer frontmatter; the gate backstops review quality regardless.)
const REV = {
  ...(A.workerEffort ? { effort: A.workerEffort } : {}),
  ...((A.reviewerModel ?? A.workerModel) ? { model: A.reviewerModel ?? A.workerModel } : {}),
}
// Opt-in per-case tiering for extend-existing gap-fills (gate catches weakness).
const EXTEND_MODEL = A.extendImplementerModel ?? null
const BREAKER = A.breakerThreshold ?? 3
const PANEL = A.reviewPanel === true
// Extend-rate quality flag (flag, never halt — mature suites legitimately run
// high extend rates): when extend+covered conclusions exceed this share of
// analyzed cases, the return carries a quality flag → the lead blind-audits a
// sample (re-analysis by a second analyst) before trusting the batch.
const EXTEND_RATE = A.extendRateThreshold ?? 0.5
const RESERVE = A.budgetReserve ?? 60_000
// RUNAWAY BACKSTOP, not the working control. The loop is meant to run until the
// reviewer approves; what ends it early is the reviewer saying the remaining
// blockers cannot be moved by another round (see loopVerdict). A low number
// here was itself the bug: at 2, a unit whose fixer merely FORGOT an item got
// shipped as `blocked` with the work nearly done, which is the one outcome
// nobody wants — neither finished nor honestly stuck. This number exists so a
// pathological review/fix pair cannot spend the budget, and nothing else.
const FIX_ROUNDS = A.fixRounds ?? 8
const GATE_N = A.gateN ?? 3
const GATE_CMD = A.gateCmd ?? null          // project's suite command; null → the gate agent resolves it from .agents/testing.md
// THE TRUNK — the "known state" the whole run returns to. Every unit branches
// from it and merges back into it, so it accumulates the batch's work in order
// and is the single thing the gate proves and the lead lands.
const TRUNK = A.integrationBranch ?? `tests/batch-${SLUG}`
const SKIP_GATE = A.skipGate === true
// Intake writes each case body here (fetch-once-to-disk); workers read the
// snapshot instead of re-fetching the TMS.
const SRC = (id) => `${ROOT}.agents/automation/${SLUG}/cases/${id}.md`
// reportDir: the campaign conductor gives every wave (and the heads pass) its
// own dir — waves share this SLUG for the snapshot dir, and without a distinct
// report location each wave's report.json would overwrite the previous one's.
const REPORT_DIR = `${ROOT}${A.reportDir ?? `.agents/automation/${SLUG}`}`

// ---- units: clusters (plan-declared) + solos, in caller order --------------
const byId = new Map(CASES.map((c) => [c.id, c]))
const clustered = new Set()
const UNITS = []
for (const cl of (Array.isArray(A.clusters) ? A.clusters : [])) {
  const members = cl.filter((id) => byId.has(id) && !clustered.has(id)).map((id) => byId.get(id))
  if (members.length >= 2) { UNITS.push(members); members.forEach((m) => clustered.add(m.id)) }
}
for (const c of CASES) if (!clustered.has(c.id)) UNITS.push([c])
UNITS.sort((a, b) => CASES.findIndex((c) => c.id === a[0].id) - CASES.findIndex((c) => c.id === b[0].id))
const label = (unit) => unit.map((c) => c.id).join('+')

// Field lesson, 2026-07-30 (lazy-modal foundation): an implementer backgrounded
// the full suite, wrote "I'll wait for this full-suite run to complete", and
// ended its turn. Nothing woke it. Twelve minutes later the output file was
// still empty, the conductor still held a `pending` journal entry, no error was
// raised anywhere, and finishing a nearly-done branch took a human noticing and
// dispatching a rescue. There is no timer, and no operator watches an
// individual slot — an agent that idles is an agent that died quietly.
//
// This goes to EVERY worker, not just implementers: the gate is the most
// exposed slot of all, because running the suite N consecutive times is its
// whole contract.
const FOREGROUND_RULE =
  'RUN LONG JOBS IN THE FOREGROUND — test suites especially. Let the call block. ' +
  'If you background one you own it until it exits: poll it every turn until you ' +
  'have the result. NEVER end a turn waiting for a background job to finish — ' +
  'nothing will wake you, this workflow blocks on your return, and your silence ' +
  'is indistinguishable from thinking. If a job is genuinely too long for one ' +
  'call, say so in findings[] and run the narrower selection you actually need.'

// FOREIGN TEXT GOES THROUGH HERE. Case titles come from the TMS, blocking items
// and notes are written by other agents, tickets by the implementer — none of
// it is authored by this script, and all of it lands inside a prompt that IS
// instructions. Two failure modes, one guard: an unbounded blob crowds out the
// contract it was pasted into, and text carrying prompt structure (a heading, a
// fence, a role line) reads as structure rather than as the datum it is. So:
// clamp, defuse the markers, and keep it a quoted value.
const quote = (s, max = 400) => String(s ?? '')
  .replace(/```+/g, "'''")                 // cannot close a fence it sits inside
  .replace(/^\s{0,3}#{1,6}\s+/gm, '')      // cannot pose as a prompt heading
  .trim()
  .slice(0, max)

// Hook insurance: injection verified for named agentTypes but undocumented —
// every worker self-heals if it arrives cold.
const PREAMBLE =
  'You are dispatched from the batch workflow. If your role memory / project ' +
  'briefing / .agents/*.md digests are not already in your context, load them ' +
  'now (memory skill; read the files). Confirm your slot skill / contract file ' +
  'is loaded (Skill tool / Read) before touching anything. ' +
  // The findings channel: a durable gotcha has somewhere to go that is read.
  'Anything worth telling someone that did NOT stop you — a product defect you ' +
  'filed, a place the case text disagrees with the live product, an open ' +
  'question, a gotcha another agent would want — goes in your result\'s ' +
  'findings[] with the right kind. Do not write it to memory yourself: the run\'s ' +
  'report is what gets read, and memory belongs to the lead at close. ' +
  // Context economy: the bill is resident-context × turns — every turn re-sends
  // your whole context, so turn count and payload size ARE the cost. Field
  // measurement: workers averaged ~30 turns at ~1 tool call per turn.
  'Context economy (hard rules): batch independent tool calls into ONE message ' +
  '(issue non-dependent reads/greps together, never one tool per turn); read a ' +
  'file once and work from what you read (ranged reads for big files; no ' +
  're-reads to double-check what is already in context); keep runner output ' +
  'lean (line/dot reporter, tail long failures — never dump a full HTML report ' +
  'or trace into the transcript); screenshots only when a step fails or visual ' +
  'judgment is the task — save to disk and cite the path instead of re-emitting ' +
  'pixels. Soft budget, a self-check not a cap: ~15 tool turns per case in ' +
  'your unit (batching makes turns dense — 15 batched turns carry what ~40 ' +
  'single-call turns did). A genuinely long case — 30 steps, a deep debug — ' +
  'may exceed it; what the check catches is CIRCLING: re-reading what is ' +
  'already in context, retrying the same probe, exploring without acting. At ' +
  'each ~15-turn mark ask: did the last stretch advance the case, or circle? ' +
  'Advance -> continue. Circle -> act on what you have and record the gap in ' +
  'findings/notes. ' +
  // Denials block an EFFECT, not the task. Same effect via another shape =
  // evasion; a different allowed route to the goal = adaptation — take it,
  // but on the record, so a human can veto a substitution that broke intent.
  'A PERMISSION DENIAL BLOCKS AN EFFECT, NOT THE TASK. Never re-achieve the ' +
  'SAME blocked effect through a different shape (a script instead of the ' +
  'denied command, an alternate binary, a broader allowed command) — that ' +
  'evades a pattern, not a policy. But a genuinely different allowed route to ' +
  'the task goal — one that does NOT produce the blocked effect — is ' +
  'legitimate: take it and record the substitution in findings/notes (what ' +
  'was denied, what you did instead). No such route -> the case goes blocked ' +
  'with the denial recorded, and you continue with what remains. ' +
  FOREGROUND_RULE

// ---- worker schemas --------------------------------------------------------
// findings[] rides every worker return: orthogonal to whether the work landed.
const FINDINGS = {
  type: 'array',
  items: {
    type: 'object', additionalProperties: false,
    required: ['kind', 'note'],
    properties: {
      kind: { type: 'string', enum: ['defect', 'clarification', 'question', 'note'] },
      note: { type: 'string' },
      ref: { type: ['string', 'null'] },   // tracker id for a filed defect
    },
  },
}
const ANALYST_VERDICT = ['ready-for-automation', 'extend-existing', 'blocked', 'un-automatable', 'already-covered', 'out-of-scope-by-author']
const ANALYST_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['surface_key', 'family_afs', 'cases', 'notes', 'findings'],
  properties: {
    surface_key: { type: 'string' },
    // True only when every member shares ONE AFS file — cases that differ only
    // in DATA. Cases differing in STEPS get one AFS each and this stays false.
    // The workflow verifies it against the paths you actually wrote.
    family_afs: { type: 'boolean' },
    cases: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['case_id', 'verdict', 'afs_path', 'notes'],
        properties: {
          case_id: { type: 'string' },
          verdict: { type: 'string', enum: ANALYST_VERDICT },
          afs_path: { type: 'string' },
          notes: { type: 'string' },
        },
      },
    },
    notes: { type: 'string' },
    findings: FINDINGS,
  },
}
const IMPL_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['status', 'branch', 'pr', 'reruns', 'notes', 'findings'],
  properties: {
    status: { type: 'string', enum: ['built', 'blocked', 'needs-analyst-rerun', 'needs-escalation'] },
    branch: { type: 'string' },
    pr: { type: ['integer', 'null'] },
    reruns: { type: 'integer' },
    // Tests that are RED BY DESIGN: the doctrine's answer to a ticketed product
    // defect is `expect.soft()` with a `// Known defect: <TICKET>` comment, which
    // fails loudly and stays failing until the product ships. Correct — and it
    // makes the batch gate unpassable, taking every healthy case down with it
    // (measured: one such case blocked four others). Declaring them lets the gate
    // run them without counting them, and lets a case be reported honestly as
    // `blocked` on a ticket rather than `automated`.
    expected_red: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['spec', 'ticket', 'why'],
        properties: {
          spec: { type: 'string' },
          test_id: { type: 'string' },
          ticket: { type: 'string' },
          why: { type: 'string' },
          // Which of the unit's cases the red test belongs to. Omitted/empty =
          // the whole unit. Without this, one ticketed defect in case A's spec
          // would demote every OTHER case on the branch to `blocked` too.
          case_ids: { type: 'array', items: { type: 'string' } },
        },
      },
    },
    notes: { type: 'string' },
    findings: FINDINGS,
  },
}
const REVIEW_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['verdict', 'findings', 'blocking', 'notes'],
  properties: {
    verdict: { type: 'string', enum: ['APPROVED', 'CHANGES_REQUESTED'] },
    blocking: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
    // WHY a blocking item is still here, per item, on a re-review. This is the
    // loop's real control, and the distinction it encodes is the whole point:
    //
    //   unaddressed     — nobody acted on it. The fixer skipped it, half-did
    //                     it, or forgot it. That is NOT a reason to stop; it is
    //                     the reason to go round again. A loop that quits here
    //                     ships work everyone knew was unfinished.
    //   persists        — a real attempt was made against the right code and
    //                     the problem is still there. THAT is the "can't"
    //                     signal: another round by the same actor cannot help,
    //                     because the obstacle is not effort.
    //   external        — it cannot be resolved on this branch at all (AFS
    //                     drift, a missing framework primitive, a product
    //                     defect, a broken environment). Stop and escalate.
    //
    // Only the reviewer can tell these apart — it is the party that saw both
    // rounds and the diff between them. Comparing finding TEXT across rounds
    // measures phrasing, and counting findings measures neither.
    blocking_detail: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['item', 'status'],
        properties: {
          item: { type: 'string' },
          status: { type: 'string', enum: ['unaddressed', 'persists', 'external'] },
        },
      },
    },
    findings: FINDINGS,
  },
}

// ---- outcome recording (in memory; one writer at close) --------------------
// Every input case gets exactly one row. `outcome` is where it ended — there is
// no transition table, nothing to validate, and no second copy to drift from.
//
// Notes and finding notes are CLIPPED at the source: the report is a routing
// record, not an archive — agents sometimes return essays, and unbounded rows
// inflated one field batch's report-writer prompt to 74k chars, then rode into
// every downstream context that touched the report. The full text is not lost:
// each worker's complete return sits in its receipt under
// `.agents/automation/_returns/` (SubagentStop hook) and in the run journal.
const CLIP = 400
const clip = (s) => {
  const t = String(s ?? '')
  return t.length <= CLIP ? t : `${t.slice(0, CLIP)}… [clipped; full text in the unit's receipt under .agents/automation/_returns/]`
}
const OUTCOME = {}                          // id -> row
for (const c of CASES) OUTCOME[c.id] = { id: c.id, outcome: 'not-started', note: '', findings: [] }
const record = (id, patch) => {
  const p = { ...patch }
  if (typeof p.note === 'string') p.note = clip(p.note)
  OUTCOME[id] = { ...OUTCOME[id], ...p }
}
// A worker handles a whole UNIT, so its findings are recorded against every case
// in it — a finding about the shared flow really does apply to all of them.
// But a unit is dispatched ONCE, so the same finding arrives once and would be
// copied verbatim per member: a family of 2 turned 10 findings into 20 identical
// rows in the report a human reads. Attach one copy per case, and never the same
// (kind, note, ref) twice — a re-review after a fix round legitimately repeats
// what it already said, and the report should show it once.
const addFindings = (ids, list) => {
  for (const f of (Array.isArray(list) ? list : [])) {
    if (!f?.note) continue
    const entry = { kind: f.kind ?? 'note', note: clip(f.note), ...(f.ref ? { ref: f.ref } : {}) }
    const key = `${entry.kind}\u0000${entry.note}\u0000${entry.ref ?? ''}`
    for (const id of ids) {
      const seen = (OUTCOME[id]._findingKeys ??= new Set())
      if (seen.has(key)) continue
      seen.add(key)
      OUTCOME[id].findings.push(entry)
    }
  }
}
// Analyst verdicts that mean "no automation work is needed here" map straight
// to a terminal outcome; the rest advance or stop.
const VERDICT_OUTCOME = {
  'already-covered': 'already-covered',
  'out-of-scope-by-author': 'out-of-scope',
  'un-automatable': 'un-automatable',
  blocked: 'blocked',
}
const IMPL_STOP = {
  blocked: 'blocked',
  'needs-analyst-rerun': 'blocked',
  'needs-escalation': 'blocked',
}

// ---- circuit breaker + account ceiling -------------------------------------
// The breaker exists for a DEAD ENVIRONMENT — causes where case N+1 fails
// exactly like case N, so stopping after three saves the rest of the batch. It
// must never fire on an ACCOUNT ceiling: three consecutive session-limit hits
// once tripped it inside a 109-case dispatch and cascaded ~100 healthy cases to
// not-started. A quota ceiling is a clock, not a batch defect.
let breakerCause = null
let breakerRun = 0
let breakerTripped = false
let quotaHalted = false
const QUOTA_RE = /(session limit|usage limit|rate.?limit|quota|resets? (at|in) )/i
function noteQuotaHalt(why) {
  if (quotaHalted) return
  quotaHalted = true
  log(`ACCOUNT CEILING reached — halting admission (not a batch failure): ${why}. ` +
      'Re-invoke with the same args plus resumeFromRunId once the limit resets; completed units replay from cache.')
}
function breakerCount(cause, why = '') {
  if (QUOTA_RE.test(why)) { noteQuotaHalt(why.slice(0, 160)); return }
  if (cause === breakerCause) breakerRun++
  else { breakerCause = cause; breakerRun = 1 }
  if (!breakerTripped && breakerRun >= BREAKER) {
    breakerTripped = true
    log(`circuit breaker TRIPPED — ${breakerRun} consecutive '${cause}' analysis stops; remaining units stay not-started` +
      (cause === 'agent-died'
        ? ' (agents dying without a return is ALSO what an account ceiling looks like from here — check the last transcript before treating this as a batch defect)'
        : ''))
  }
}

// ---- slot dispatches -------------------------------------------------------
let analyzedCount = 0
let extendishCount = 0
const extendCases = []

async function runAnalyst(unit) {
  const ids = unit.map((c) => c.id)
  // Pre-analyzed unit (conductor heads pass): reconstruct from data, no dispatch.
  if (ids.every((id) => PRE.has(id))) {
    const members = ids.map((id) => PRE.get(id))
    members.forEach((m) => record(m.id, { outcome: 'analysed', afs: m.afs_path }))
    return {
      surface_key: PRE.get(ids[0]).surface_key || 'default',
      // Non-empty path required: two members with afs_path '' share a value,
      // not an AFS file — an empty "family" would demand a parameterized spec
      // triangulated against a file that does not exist.
      family_afs: members.length > 1 && Boolean(members[0].afs_path) && new Set(members.map((m) => m.afs_path)).size === 1,
      members: members.map((p) => ({ id: p.id, afs_path: p.afs_path })),
    }
  }
  if (quotaHalted) {
    ids.forEach((id) => record(id, { note: 'account ceiling — admission halted before analysis' }))
    log(`${label(unit)} not started — account ceiling`)
    return null
  }
  if (breakerTripped) {
    ids.forEach((id) => record(id, { note: `circuit breaker: ${breakerRun} consecutive '${breakerCause}' stops` }))
    log(`${label(unit)} not started — circuit breaker (${breakerCause})`)
    return null
  }
  if (budget.total && budget.remaining() < RESERVE) {
    ids.forEach((id) => record(id, { note: 'token budget reserve reached' }))
    log(`${label(unit)} not started — budget reserve reached`)
    return null
  }

  const clusterNote = unit.length > 1
    ? `This is a CLUSTER dispatch: ${unit.length} similar cases, ONE live session. Shared login/navigation/discovery is the point — but you MUST execute EVERY case's steps individually and record per-case observations; "executed the first, assumed the rest" is forbidden. A case that diverges from the family mid-exploration: return it with its own verdict and note (it will run solo). Where the cases are true variants of one flow, write ONE family AFS (parameter table, one row per case, per-case Coverage Map rows; family_afs=true, same afs_path for members). `
    : ''
  const a = await agent(
    `${PREAMBLE}\n\nAnalyst slot — analyse ${unit.map((c) => `${c.id}${c.title ? ` (${quote(c.title, 120)})` : ''}`).join(', ')} per the test-case-analysis skill § Analyst slot contract. ` +
    clusterNote +
    `Read each case's snapshot first: ${ids.map((id) => SRC(id)).join(' , ')} (written at intake); ONLY if missing, fetch via the project's TMS adapter (.agents/test-automation.yaml) and note the gap. ` +
    'Before exploring, read the feature\'s exploration digest test-specs/<feature>/_surface.md if present (verify handles as you use them); create or update it after your run. ' +
    // ANALYZE-ONLY runs (the campaign heads pass) have no build after them and
    // no branch switching at all, so there is nothing to protect the files
    // from — and the next stage (the foundation) reads them straight out of
    // this tree. Committing there would put doc commits on a branch nothing
    // merges. So: commit on a real batch, leave on disk for a heads pass.
    (ANALYZE_ONLY
      ? 'YOU OWN THE TREE RIGHT NOW and nothing else runs. This is an ANALYSIS-ONLY pass: write your AFS and the digest to disk and LEAVE them there uncommitted — run no git command and do not switch branches. The next stage reads them out of this same tree. '
      : `YOU OWN THE TREE RIGHT NOW and nothing else runs, so ordinary git is yours. FIRST make sure you are on the batch trunk, because everything in this batch branches from it: \`git rev-parse --verify ${TRUNK}\` — if it exists (locally or on the remote), check it out; if it exists NOWHERE, create and push it: \`git checkout -B ${TRUNK} ${BASE} && git push -u origin ${TRUNK}\`. Never -B a trunk that already exists — that discards units already merged into it. ` +
        `THEN write your AFS and the digest, \`git add\` them BY PATH, commit, and push. Do NOT switch to any other branch — leave the tree on ${TRUNK} when you finish. ` +
        'Committing your own analysis is the point: it lands the moment it exists, so a case that turns out already-covered or blocked still has its AFS on the trunk, and an interrupted run loses nothing. Stage by exact path rather than `git add -A` — that is ordinary hygiene: the tree may hold artifacts from a previous unit that are not yours to commit. ') +
    'READ THE NEIGHBOURS FIRST, before you execute: grep test-specs/ and the suite dir BY BEHAVIOUR (the observable, the UI label, the endpoint) — never by case id — to arrive knowing the handles, the flow that reaches the screen, the fixtures and the conventions. That is what makes analysis cheap. This is REUSE, not a duplicate hunt: reading a spec that turns out to be unrelated costs minutes, but wrongly calling a case already-covered means it is never automated and the hole is invisible. So the normal outcome here is ready-for-automation WITH better context. already-covered is the rare exception and needs a spec merged to ' + BASE + ' proving the SAME observable with the SAME expected result, cited at file:line — same screen, same page object or a similar title is NOT coverage. When in doubt, ready-for-automation and say what you checked in notes. ' +
    'FAST-REACH: reuse the suite to travel — authenticate via the framework\'s auth state/fixture and drive deep navigation via existing specs/page-object scratch runs; transit is NOT execution (the case\'s own steps you still run and observe live), and a failing transit path falls back to manual navigation AND gets flagged in notes (possible regression). ' +
    'You are the only analyst running, so the shared Playwright MCP browser is yours — no lane, no isolated instance, no port juggling. ' +
    // The two verdicts have different exposure, so they get different targets.
    // `extend-existing` produces work that rides this batch and shares its fate,
    // so a target on the trunk is safe. `already-covered` is TERMINAL — it drops
    // the case out of the remainder — so it needs a fact that has already
    // landed, or a red gate later would close a case whose "coverage" never
    // shipped, invisibly.
    `MERGED-TARGET RULE: \`extend-existing\` may target a spec merged to ${BASE} OR already on this batch's trunk ${TRUNK} (earlier units in this batch have merged into it). \`already-covered\` is stricter: it may target ONLY a spec merged to ${BASE}, because it CLOSES the case — a terminal verdict needs coverage that has already landed. Never target a same-batch AFS that is not yet merged; when in doubt classify ready-for-automation. ` +
    'Execute against the live system per your contract — do not skip execution. Prefer scripted probes over full-page snapshots (browser-tools.md § Probe first). ' +
    'Write AFS files to the project\'s test-specs/ convention. ' +
    'surface_key: one stable kebab-case identifier for the page/component family this unit exercises (cluster members share it by construction). ' +
    'If you cannot proceed because of an ACCOUNT/USAGE LIMIT (not a problem with the app or the case), say exactly that in notes — it stops the batch cleanly instead of stopping healthy cases. ' +
    'Return one cases[] entry per case id, afs_path relative to the project root ("" if none written).',
    { label: `analyst:${label(unit)}`, phase: 'Analysis', agentType: TYPES.analyst, ...WORKER, schema: ANALYST_SCHEMA }
  )
  if (!a || !Array.isArray(a.cases) || a.cases.length === 0) {
    // A null return is an agent that DIED (skipped, interrupted, terminal API
    // error) — which is also exactly what an account ceiling looks like from
    // here. Its own breaker cause, so a trip names that ambiguity instead of
    // reading as a batch defect.
    breakerCount('agent-died', '')
    ids.forEach((id) => record(id, { outcome: 'blocked', note: 'analyst agent died without a return — if several did in a row, suspect the account ceiling before the environment' }))
    return null
  }
  addFindings(ids, a.findings)
  const byCase = new Map(a.cases.map((c) => [c.case_id, c]))
  // Count only rows about THIS unit's ids: the schema cannot stop an analyst
  // returning a foreign case_id, and a confabulated row must not skew the
  // extend-rate flag or leak into extend_cases.
  const unitRows = a.cases.filter((c) => ids.includes(c.case_id))
  analyzedCount += unitRows.length
  for (const c of unitRows) {
    if (c.verdict === 'extend-existing' || c.verdict === 'already-covered') {
      extendishCount += 1
      if (c.verdict === 'extend-existing') extendCases.push(c.case_id)
    }
  }
  const adv = ids.filter((id) => ['ready-for-automation', 'extend-existing'].includes(byCase.get(id)?.verdict))
  const rest = ids.filter((id) => !adv.includes(id))
  if (rest.length) {
    // Only environment-shaped stops feed the breaker. already-covered /
    // out-of-scope / un-automatable are HEALTHY terminal verdicts — a mature
    // suite legitimately produces runs of them (see the extend-rate comment:
    // "flag, never halt") — and any completed analysis proves the environment
    // is alive, whatever it concluded.
    const blockedRest = rest.filter((id) => (VERDICT_OUTCOME[byCase.get(id)?.verdict] ?? 'blocked') === 'blocked')
    if (blockedRest.length) {
      const first = byCase.get(blockedRest[0])
      breakerCount('blocked', first?.notes ?? '')
    }
    for (const id of rest) {
      const c = byCase.get(id)
      record(id, { outcome: VERDICT_OUTCOME[c?.verdict] ?? 'blocked', note: c?.notes || c?.verdict || 'no analyst verdict', afs: c?.afs_path || undefined })
      log(`${id} → ${OUTCOME[id].outcome}: ${OUTCOME[id].note}`)
    }
  }
  // Any completed verdict that is not 'blocked' resets the streak — the
  // breaker is for an unbroken run of environment-shaped stops only.
  if (adv.length || rest.some((id) => (VERDICT_OUTCOME[byCase.get(id)?.verdict] ?? 'blocked') !== 'blocked')) {
    breakerCause = null; breakerRun = 0
  }
  if (!adv.length) return null
  adv.forEach((id) => record(id, { outcome: 'analysed', afs: byCase.get(id).afs_path }))
  const members = adv.map((id) => ({ id, verdict: byCase.get(id).verdict, afs_path: byCase.get(id).afs_path }))
  // A family is DEFINED by the members sharing one AFS file, not by the analyst
  // saying so. Trusting the claim let the two disagree, and the disagreement
  // reached the implementer as a contradiction: "FAMILY UNIT — write ONE
  // parameterized spec" pointing at three different AFS paths, or the reverse.
  // The paths are an observable fact; the flag is a self-report. Prefer the fact
  // (the same rule the rest of this pipeline runs on) and say so when they part.
  // Non-empty path required: two members whose afs_path is '' (allowed for
  // extend-existing) share a VALUE, not a file, and must not read as a family.
  const sharesOneAfs = members.length > 1 && Boolean(members[0].afs_path) && new Set(members.map((m) => m.afs_path)).size === 1
  if (a.family_afs === true && !sharesOneAfs && members.length > 1) {
    log(`${adv.join('+')}: analyst returned family_afs=true but wrote ${new Set(members.map((m) => m.afs_path)).size} AFS files — treating as separate specs (the files decide)`)
  }
  return {
    surface_key: a.surface_key || 'default',
    family_afs: sharesOneAfs,
    members,
  }
}

const REVIEW_LENSES = [
  'assertion strength & per-step coverage (every case-side expected result asserted AT its step, not only end-state)',
  'defect masking & error swallowing (test.fail/skip/soft-pass patterns, catch-and-ignore, weakened assertions)',
  'coverage fidelity (case ↔ AFS ↔ diff triangulation: every Coverage Map row disposition holds in the code)',
]

function reviewOnce(u, impl, fixNote, lens) {
  const ids = u.members.map((m) => m.id)
  return agent(
    `${PREAMBLE}\n\nReviewer slot — STATIC review of ${ids.join(', ')} per the test-automation-workflow skill's references/reviewer-contract.md ` +
    '(do not execute the spec; the hardening gate does). ' +
    `Branch: ${impl.branch}. PR: ${impl.pr ?? 'n/a'}. AFS: ${[...new Set(u.members.map((m) => m.afs_path))].join(', ')}. ` +
    'Read the diff via `git diff <base>...<branch>` — do NOT check the branch out (the tree is shared and a build may follow yours). ' +
    `FIRST read each case snapshot (${ids.map((id) => SRC(id)).join(' , ')}; fetch via the TMS adapter only if missing), then triangulate case ↔ AFS ↔ diff FOR EVERY CASE. ` +
    (u.family_afs ? 'This is a FAMILY spec: per-ROW triangulation — every case id maps to a data-table row whose DISTINCT expected values are actually asserted; a shared flattened assertion is CHANGES_REQUESTED. ' : '') +
    'For every Coverage-Map row claiming covered-by/extend, verify the disposition against the covering spec\'s ACTUAL assertions (does that assertion really exist, at that step?) — never against its mere existence. ' +
    (lens ? `Your assigned review lens — judge ONLY through it: ${lens}. ` : 'Cover per-step assertions and the masking hunt. ') +
    (fixNote
      ? `This is the re-review after a fix round. Prior blocking findings:\n${fixNote}\n` +
        'For EVERY item you still block on, put an entry in blocking_detail[] with the status that is TRUE OF THE DIFF, not of your patience:\n' +
        '  - `unaddressed` — you can see no serious attempt against it. Nothing in the diff touches the code it names, or the change is cosmetic/partial. Forgotten and half-done both count here.\n' +
        '  - `persists` — a genuine attempt was made against the right code and the problem is still present. Say in notes what was tried and why it did not work.\n' +
        '  - `external` — it cannot be resolved on this branch at all: the AFS is wrong, a framework primitive is missing, it is a product defect, the environment is broken.\n' +
        'This decides whether the case gets another round. `unaddressed` sends it back — that is the point, and you must not use `persists` to end a loop you are tired of. Reserve `persists` for a real attempt that really failed; the difference is whether more effort could plausibly fix it. A NEW item you are raising for the first time is not in this list at all — new ground is progress and needs no status.\n'
      : '') +
    'blocking[] is what must change before this can land; anything else worth saying goes in findings[].',
    { label: `review:${ids.join('+')}${lens ? `:${lens.split(' ')[0]}` : ''}`, phase: 'Build', agentType: TYPES.reviewer, ...REV, schema: REVIEW_SCHEMA }
  )
}

async function review(u, impl, fixNote) {
  if (!PANEL) return reviewOnce(u, impl, fixNote, null)
  const rs = (await parallel(REVIEW_LENSES.map((l) => () => reviewOnce(u, impl, fixNote, l)))).filter(Boolean)
  if (!rs.length) return null
  // blocking_detail unions across the panel. No voting: one lens reporting
  // `unaddressed` is enough to earn another round, because it is a claim about
  // the diff — either something was acted on or it wasn't — and a lens that
  // looked closer is not outvoted by two that didn't.
  return {
    verdict: rs.every((r) => r.verdict === 'APPROVED') ? 'APPROVED' : 'CHANGES_REQUESTED',
    blocking: rs.flatMap((r) => r.blocking ?? []),
    notes: rs.map((r) => r.notes).filter(Boolean).join(' | '),
    findings: rs.flatMap((r) => r.findings ?? []),
    blocking_detail: rs.flatMap((r) => r.blocking_detail ?? []),
  }
}

/**
 * Should the loop go round again?
 *
 * Keep going while ANY blocking item is `unaddressed` — work nobody attempted
 * is not a reason to stop, it is the reason to continue. Stop only when every
 * remaining blocker is one the same actor cannot move: attempted and still
 * failing (`persists`), or not resolvable on this branch (`external`).
 *
 * A re-review that classifies nothing is treated as "keep going": the items are
 * new ground, and new ground is progress. The runaway backstop still binds.
 */
function loopVerdict(review) {
  const detail = review?.blocking_detail ?? []
  // Unclassified. Default to going again — the bias belongs on the side of
  // finishing the work — but say it was unclassified so the caller can stop if
  // it keeps happening. A reviewer that never classifies would otherwise burn
  // every round of the backstop and report nothing about why.
  if (!detail.length) return { go: true, why: null, unclassified: true }
  const unaddressed = detail.filter((d) => d.status === 'unaddressed')
  if (unaddressed.length) return { go: true, why: null, unaddressed: unaddressed.map((d) => d.item) }
  const external = detail.filter((d) => d.status === 'external').map((d) => d.item)
  const persists = detail.filter((d) => d.status === 'persists').map((d) => d.item)
  return {
    go: false,
    why: external.length
      ? `not resolvable on this branch: ${external.join('; ').slice(0, 160)}`
      : `attempted and still failing: ${persists.join('; ').slice(0, 160)}`,
  }
}

// Tests the batch KNOWS are red: ticketed product defects the doctrine says to
// assert softly rather than hide. The gate runs them and reports them, but they
// do not count against its green requirement — otherwise one ticketed defect
// makes the batch unpassable forever.
const EXPECTED_RED = []
const merged = []            // [{ ids, branch, pr }] — units landed on the trunk
const parked = []            // [{ ids, branch, why }] — reviewed but not merged

async function buildUnit(u) {
  const ids = u.members.map((m) => m.id)
  const ul = ids.join('+')
  if (budget.total && budget.remaining() < RESERVE) {
    ids.forEach((id) => record(id, { note: 'token budget reserve reached before implementation' }))
    return null
  }
  if (quotaHalted) {
    ids.forEach((id) => record(id, { note: 'account ceiling — halted before implementation' }))
    return null
  }

  const workspaceNote =
    'You work in the project\'s ONE working tree — its real checkout, with its installed dependencies and its env files. No worktree is created for you and you must not create one. NOTHING else runs while you do: units are strictly sequential, so the tree is yours alone for the whole dispatch. Two rules keep it usable for whoever comes next: stay on your own feature branch (never switch the tree to anything else), and stage ONLY your own paths (`git add <paths>`, never `-A`/`.`) so a stray artifact does not ride in on your commit. Leave the tree on your branch when you finish — the merge step takes it from there and returns it to the trunk. '
  const familyNote = u.family_afs
    ? `FAMILY implementation: these ${ids.length} cases share one AFS with a parameter table — implement ONE parameterized spec (one data row per case, each row asserting its OWN expected values, tagged with its case id). One branch, one PR for the family. `
    : (ids.length > 1 ? `Implement all ${ids.length} cases on ONE branch (separate specs are fine when the AFS files are separate). ` : '')

  const impl = await agent(
    `${PREAMBLE}\n\nImplementer slot — implement ${ids.join(', ')} per the test-automation-workflow skill's references/implementer-contract.md. ` +
    `AFS: ${[...new Set(u.members.map((m) => m.afs_path))].join(', ')}. Read the FULL case snapshot(s) for the coverage cross-check (Phase 1 Absorb): ${ids.map((id) => SRC(id)).join(' , ')}. ` +
    workspaceNote +
    // TWO BRANCH LEVELS, and the trunk is the KNOWN STATE. Every unit cuts from
    // the trunk and merges back into it, so the trunk accumulates the batch in
    // order and the tree is always somewhere named between units. Cutting from
    // the PREVIOUS unit's tip (an earlier revision) made the base of each build
    // depend on completion order — which broke resume caching — and deferred
    // every merge to one big integration step: 63 git commands, 90 conflict
    // hits and three git-surgery rescues in one measured session. Merging as we
    // go costs the same merges, smaller and while their author is still live.
    `The tree is on ${TRUNK} and that is where you start. Cut your feature branch FROM ${TRUNK} — it already carries every unit that finished before you, so page-object and fixture work accumulates and you are never rebasing onto a surprise. ` +
    `If ${TRUNK} does not exist anywhere yet (you are the first unit of a fresh batch), create it: \`git checkout -B ${TRUNK} ${BASE} && git push -u origin ${TRUNK}\`. Never -B an existing trunk — that discards the units already merged into it. ` +
    `Open your PR against ${TRUNK}, NOT against ${BASE} — case PRs land on the batch trunk, and one PR takes the trunk to ${BASE} after the gate. `+
    // A retried unit can arrive at a feature branch a previous attempt already
    // built on. Whether that work is usable is a judgement about the diff, so
    // it is yours — a script cannot tell "half-finished and coherent" from
    // "abandoned and wrong", and both look identical to `git rev-parse`.
    'If YOUR feature branch already exists, read it before writing anything (`git log <base>..<branch>`, `git status`): coherent work in progress → continue it and say in notes what you inherited; wrong or contradicting the AFS → rebuild those parts and say so. Never silently restart on a branch that already has work, and never assume it is finished because it exists. ' +
    // A multi-case unit is NOT automatically one spec. Clustering buys a shared
    // LIVE SESSION (one login, one discovery pass) — merging the output is a
    // separate judgement the analyst already made: one AFS means true
    // flow-variants, several means the cases only shared a surface. Without
    // saying so, the implementer has to infer the shape from a path count.
    (u.members.length > 1
      ? (u.family_afs
        ? `FAMILY UNIT: the analyst judged these true variants of ONE flow and wrote a single AFS with a parameter table, one row per case. Implement ONE parameterized spec — a data table with a row per case id, each row carrying its OWN expected values, and the case id tagged on its row's test so it fails by itself. Never flatten distinct expected values into a shared assertion: that is how a case silently stops being tested. `
        : `NOT a family: the analyst wrote a SEPARATE AFS per case (${u.members.length} of them), because these cases shared a surface but not a flow. Implement them as SEPARATE specs, one per case, exactly as if they had arrived alone. They ride ONE branch and ONE PR only because they were analysed together — that is a dispatch economy, not a reason to merge test code. Shared page objects and fixtures are of course reused. `)
      : '') +
    'If any assertion is red for a PRODUCT reason with a ticket (the `expect.soft()` + `// Known defect: <TICKET>` case), that test is RED BY DESIGN and stays red until the product ships. Do NOT weaken it — declare it in expected_red[] with the spec path, the test id, the ticket, one line of why, and (in a multi-case unit) the case_ids the red test belongs to, so only THOSE cases are held on the ticket and not their healthy neighbours on the same branch. The gate then runs it without counting it against the batch, and the affected case is reported blocked-on-that-ticket instead of automated. An undeclared red-by-design test makes the gate unpassable and blocks every healthy case beside it. ' +
    `YOUR AFS IS ALREADY COMMITTED on ${TRUNK}: ${[...new Set(u.members.map((m) => m.afs_path))].join(', ')} — the analyst committed it before you started, so read it from the branch you just cut. If your exploration finds it has drifted from the live product (a selector, an observable), AMEND it and commit the amendment on YOUR branch with the spec it belongs to, so the change is reviewed with the code that motivated it. Stage by exact path, never \`git add -A\`. `+
    familyNote +
    'The feature\'s `_surface.md` digest is the analyst\'s: read it, and report drift in findings[] rather than editing it — it describes the surface, not your case, and the next analyst owns keeping it true. ' +
    'Implement inside the existing framework, run it green ONCE locally (determinism is the gate\'s job, not repeated local runs), retry budget ≤ 2 reruns on the same root cause, then open the PR per your Phase 6 handoff. ' +
    'Return the actual branch name, the PR number (null if none), and your rerun count.',
    {
      label: `implement:${ul}`, phase: 'Build', agentType: TYPES.implementer,
      ...WORKER,
      ...(EXTEND_MODEL && u.members.every((m) => m.verdict === 'extend-existing') ? { model: EXTEND_MODEL } : {}),
      schema: IMPL_SCHEMA,
    }
  )
  if (!impl) { ids.forEach((id) => record(id, { outcome: 'blocked', note: 'implementer agent failed' })); return null }
  addFindings(ids, impl.findings)
  if (impl.reruns > 2) {
    ids.forEach((id) => record(id, { outcome: 'blocked', note: `R2 cap exceeded (${impl.reruns} reruns) — classify architectural vs AFS-drift vs product-change` }))
    return null
  }
  if (impl.status !== 'built') {
    ids.forEach((id) => record(id, { outcome: IMPL_STOP[impl.status] ?? 'blocked', note: impl.notes || impl.status }))
    return null
  }
  // Red-by-design declarations arrive from the INITIAL implement AND from any
  // fix round (a fixer restoring a weakened assertion declares it here too —
  // dropping those made the gate unpassable for exactly the case the mechanism
  // exists for). Attribution is per entry: an entry naming case_ids holds only
  // those cases; one naming none holds the whole unit.
  const noteRed = (list) => {
    const reds = Array.isArray(list) ? list : []
    if (!reds.length) return
    for (const r of reds) EXPECTED_RED.push({ ...r, unit: ul })
    log(`${ul}: ${reds.length} test(s) red by design — ${reds.map((r) => r.ticket).join(', ')}`)
    for (const id of ids) {
      const mine = reds.filter((r) => !Array.isArray(r.case_ids) || r.case_ids.length === 0 || r.case_ids.includes(id))
      if (mine.length) OUTCOME[id]._expectedRed = [...(OUTCOME[id]._expectedRed ?? []), ...mine]
    }
  }
  noteRed(impl.expected_red)
  ids.forEach((id) => record(id, { outcome: 'built', branch: impl.branch, pr: impl.pr ?? undefined }))

  let r = await review(u, impl, null)
  if (r) addFindings(ids, r.findings)

  // The loop runs until the reviewer APPROVES. It is not a budget for how much
  // quality a unit is allowed — it ends when going round again cannot help:
  //
  //   * any blocker still `unaddressed` → GO AGAIN. Something was skipped or
  //     half-done, and stopping there ships work everyone knew was unfinished.
  //     This is the case the old 2-round cap got wrong.
  //   * every blocker `persists` (real attempt, still failing) or `external`
  //     (not resolvable on this branch) → STOP. The obstacle is not effort, and
  //     the same actor repeating itself cannot move it. That is a real
  //     `blocked`, and it goes to the lead with the reason.
  //   * FIX_ROUNDS → backstop only, for a review/fix pair that has gone
  //     pathological. Reaching it is a defect worth reporting, not a normal end.
  //   * budget floor → the run stops spending before it strands the batch.
  let round = 0
  let stopped = null
  let unclassified = 0
  while (r && r.verdict === 'CHANGES_REQUESTED' && (r.blocking ?? []).length) {
    if (round > 0) {
      const v = loopVerdict(r)
      if (!v.go) { stopped = v.why; break }
      unclassified = v.unclassified ? unclassified + 1 : 0
      if (unclassified >= 2) { stopped = 'reviewer left surviving blockers unclassified twice — cannot tell unaddressed from unfixable, so the loop cannot judge whether another round would help'; break }
    }
    if (round >= FIX_ROUNDS) { stopped = `fix-round backstop (${FIX_ROUNDS}) reached — review/fix pair is not converging`; break }
    if (budget.total && budget.remaining() < RESERVE) { stopped = 'budget floor reached mid-fix'; break }
    round++
    const prior = r.blocking.map((b) => quote(b)).join('\n- ')
    // Name what was skipped, explicitly. A fixer told only "here are the
    // blockers" reads the list as new work; told "you did not touch this one",
    // it has no room to skip it twice.
    const skipped = (r.blocking_detail ?? []).filter((d) => d.status === 'unaddressed').map((d) => quote(d.item))
    const fix = await agent(
      `${PREAMBLE}\n\nImplementer slot — fix round ${round} for ${ids.join(', ')} on branch ${impl.branch} per references/implementer-contract.md. ` +
      workspaceNote +
      'Address EACH blocking finding (verify against the code first) and add the regression test that would have caught it, re-run the affected spec green once, update the PR:\n- ' +
      prior +
      (skipped.length
        ? `\n\nTHE REVIEWER SAYS THESE WERE NOT ADDRESSED LAST ROUND — no attempt was visible in the diff:\n- ${skipped.join('\n- ')}\n`
          + 'Do them. If one genuinely cannot be done on this branch, say so in notes with the reason (missing primitive, AFS wrong, product defect) instead of leaving it silent — an unexplained gap reads as another skip and costs the unit another round.'
        : ''),
      { label: `fix:${ul}:${round}`, phase: 'Build', agentType: TYPES.implementer, ...WORKER, schema: IMPL_SCHEMA }
    )
    if (fix) { addFindings(ids, fix.findings); noteRed(fix.expected_red) }
    if (!fix || fix.status !== 'built') { r = null; break }
    r = await review(u, impl, prior)
    if (r) addFindings(ids, r.findings)
  }

  if (!r) { ids.forEach((id) => record(id, { outcome: 'blocked', note: `review/fix round ${round} failed` })); return null }
  if (r.verdict !== 'APPROVED') {
    const why = stopped ?? 'review CHANGES_REQUESTED'
    ids.forEach((id) => record(id, { outcome: 'blocked', note: `${why} after ${round} fix round(s): ${(r.blocking ?? []).join('; ').slice(0, 200)}` }))
    return null
  }
  ids.forEach((id) => record(id, { outcome: 'reviewed', branch: impl.branch, pr: impl.pr ?? undefined }))

  // ---- merge back, and RETURN THE TREE TO THE TRUNK ------------------------
  // No budget/quota guard here on purpose: the unit is BUILT and REVIEWED, and
  // abandoning it unmerged would strand finished work on a branch. Merging is
  // the cheapest agent in the run and the one that makes everything before it
  // count, so it runs even at the reserve.
  // The unit lands the moment it is approved, rather than waiting for one big
  // integration step at the end. Three things that buys: the trunk is a known
  // state for the next unit to branch from, conflicts surface small and while
  // the author of the change is still in flight, and an interrupted run leaves
  // the trunk carrying exactly the units that finished — which is what makes
  // recovery a `git log` rather than an archaeology exercise.
  const landed = await agent(
    `${PREAMBLE}\n\nMerge unit ${ids.join(', ')} into the batch trunk. You own the tree; nothing else runs.\n` +
    `1. \`git checkout ${TRUNK}\` and make sure it is current (\`git pull --ff-only\` if it tracks a remote).\n` +
    `2. \`git merge --no-ff ${impl.branch} -m "merge ${ids.join(', ')} into ${TRUNK}"\`.\n` +
    'On a conflict, classify EVERY conflicted file before touching anything. MECHANICAL (resolve by union/addition only): both sides added distinct imports/exports, distinct methods or locators on a page object or fixture, independent files or independent spec blocks — keep BOTH sides, stage, conclude the merge. SEMANTIC (never resolve): the same function/method/locator edited on both sides, assertion or expected-value differences, fixture signature drift, or anything you cannot resolve as a pure union — `git merge --abort`, report merged=false with the conflict files and a one-line reason, and STOP.\n' +
    'HARD RULES: never delete, `rm`, or `checkout --ours/--theirs` a file away to make a merge pass; never edit test logic, assertions or expected values while resolving; never run the suite (the gate does that).\n' +
    `3. Push: \`git push origin ${TRUNK}\` — the gate reads the trunk from the remote, so an unpushed merge is invisible to it. Say so in notes if the push fails.\n` +
    `4. LEAVE THE TREE ON ${TRUNK}. The next unit branches from it and assumes it is there.\n` +
    'Return whether the merge landed, the trunk head sha, and any conflict files.',
    {
      label: `merge:${ul}`, phase: 'Build', agentType: TYPES.implementer, ...WORKER,
      // Mechanical slot tiering: checkout/merge/push with a classify-or-abort
      // rule — the semantic backstop is the gate running the suite on the
      // trunk, so a cheap model here trades nothing for ~1/3 the price.
      model: A.mergeModel ?? A.workerModel ?? 'haiku',
      effort: A.workerEffort ?? 'low',
      schema: {
        type: 'object', additionalProperties: false,
        // findings[] is in the PREAMBLE every dispatch gets, so it has to be
        // declarable here — `additionalProperties: false` plus a preamble that
        // asks for a field the schema forbids means an obedient agent returns
        // schema-invalid output and its unit gets parked on a clean merge.
        required: ['merged', 'head_sha', 'conflict_files', 'notes'],
        properties: {
          merged: { type: 'boolean' },
          head_sha: { type: 'string' },
          conflict_files: { type: 'array', items: { type: 'string' } },
          notes: { type: 'string' },
          findings: FINDINGS,
        },
      },
    }
  )
  if (!landed || landed.merged !== true) {
    const why = landed
      ? `${landed.notes || 'semantic conflict'}${landed.conflict_files?.length ? ` (${landed.conflict_files.slice(0, 4).join(', ')})` : ''}`
      : 'merge agent failed'
    parked.push({ ids, branch: impl.branch, why })
    ids.forEach((id) => record(id, { outcome: 'blocked', note: `reviewed but NOT merged — ${why}; resolve on the case branch and re-enter` }))
    log(`${ul} reviewed but parked: ${why}`)
    return null
  }
  merged.push({ ids, branch: impl.branch, pr: impl.pr ?? null })
  addFindings(ids, landed.findings)
  log(`${ul} merged into ${TRUNK} (${String(landed.head_sha).slice(0, 8)})`)
  return impl.branch
}

// ---- runaway-cap accounting ------------------------------------------------
// The runtime caps a workflow at 1000 agents for its whole LIFETIME, and
// nothing degrades gracefully there — the 1001st agent() simply throws, in
// whatever phase happens to reach it, which on this pipeline means a batch that
// dies somewhere between review and gate with its work unreported. The worst
// case is knowable up front (it is a function of units, fix rounds and panel
// width), so say it before anything runs rather than discovering it at agent
// 1000. This is a WARNING, not a refusal: the worst case assumes every unit
// burns every fix round, which a healthy batch never does.
{
  const perUnit = 3 + FIX_ROUNDS + (FIX_ROUNDS + 1) * (PANEL ? REVIEW_LENSES.length : 1)
  const worst = UNITS.length * perUnit + 2        // + gate, reporter
  if (worst > 900) {
    log(`HEADROOM: worst case ~${worst} agents for ${UNITS.length} unit(s) — the runtime's lifetime cap is 1000. `
      + 'A batch that actually burns its fix rounds would die mid-run. Split it into smaller batches (or lower '
      + `fixRounds${PANEL ? '/turn reviewPanel off' : ''}) before this becomes a rescue.`)
  }
}

// ---- the unit loop: strictly one at a time ---------------------------------
// ONE tree, ONE master. A plain `for … await` and nothing else: no lanes, no
// chains, no locks. Every hazard those existed to manage came from two slots
// wanting the tree in different states at once, and ordering is the only thing
// that actually reconciles that (see ONE TREE, ONE MASTER above).
//
// Do NOT reach for parallel()/pipeline() here. It looks like free throughput
// and it is not: it puts two `git checkout` in one tree, which is precisely
// what produced the eight checkout aborts and the conflict pile-up we measured.
// Throughput comes from CLUSTERING — fewer, larger units — not from overlap.
const analyzed = []

for (const unit of UNITS) {
  phase('Analysis')
  const u = await runAnalyst(unit)
  if (!u) continue
  if (ANALYZE_ONLY) {
    u.members.forEach((m) => analyzed.push({ id: m.id, afs_path: m.afs_path, surface_key: u.surface_key }))
    continue
  }
  // A thrown build costs its own unit and nothing else — the trunk is where it
  // was, so the next unit starts from a known state regardless.
  try {
    phase('Build')
    await buildUnit(u)
  } catch (e) {
    const ids = u.members.map((m) => m.id)
    ids.forEach((id) => record(id, { outcome: 'blocked', note: `build failed: ${String(e?.message ?? e).slice(0, 160)}` }))
    log(`${ids.join('+')} build threw — continuing with the next unit`)
  }
}

// ---- integration already happened -------------------------------------------
// There is no integrate PHASE. Each unit merged into the trunk the moment its
// review approved (see buildUnit), so by the time we get here the trunk already
// carries everything that passed and the tree is sitting on it. `merged` is the
// record of what landed; `parked` is what reviewed but could not be merged.
// batch-integrate.workflow.mjs survives as a REPAIR tool — for re-merging a
// parked unit by hand, or integrating a batch that was built without this
// workflow — not as a stage of the normal run.

// ---- Phase 4: the hardening gate -------------------------------------------
// Its own agent — never the implementer, never the reviewer. It runs the
// batch's specs TOGETHER, N consecutive green: stronger than a per-case gate
// because it surfaces the parallel-interaction flakes a per-case run never
// sees. It does NOT merge, does NOT classify a red, does NOT fix. A red goes to
// the report; the lead classifies (product defect / flake / architectural) and
// may dispatch the stabilize workflow for the batch.
const GATE_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['verdict', 'runs', 'green_specs', 'failures', 'notes'],
  properties: {
    verdict: { type: 'string', enum: ['green', 'red', 'not-run'] },
    runs: { type: 'integer' },
    seconds: { type: 'array', items: { type: 'number' } },
    green_specs: { type: 'array', items: { type: 'string' } },
    failures: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['spec', 'signature'],
        properties: {
          spec: { type: 'string' },
          signature: { type: 'string' },
          case_ids: { type: 'array', items: { type: 'string' } },
        },
      },
    },
    notes: { type: 'string' },
  },
}
let gate = null
const gateBranch = TRUNK
if (!ANALYZE_ONLY && !SKIP_GATE && merged.length) {
  phase('Gate')
  gate = await agent(
    `${PREAMBLE}\n\nHardening gate for batch ${SLUG}. You did not write this code and you do not fix it — you PROVE it, and you report exactly what you saw.\n` +
    `Branch: ${gateBranch} (the batch trunk — every approved unit is already merged into it). Base: ${BASE}.\n` +
    `Run the batch's new/changed specs TOGETHER, ${GATE_N} CONSECUTIVE deterministic green runs, each a clean process against the live env. ` +
    'Use `scripts/gate/gate-case.mjs` for the mechanics (it merges the base FIRST — a run against a branch that lacks base proves nothing about what will land — refuses a dirty tree, and returns timings), ' +
    (GATE_CMD ? `with --cmd '${GATE_CMD}'. ` : 'resolving the suite command from .agents/testing.md § run commands. ') +
    'A red anywhere ENDS the attempt — N CONSECUTIVE is the contract, not best-of-N. ' +
    // TWO PROOFS, TWO COUNTS. The batch's own specs are unproven, so they need
    // repetition — that is what catches a flake. Everything else was already
    // proven, so ONE run is enough to reveal a regression, and repeating it
    // would be paying N× for a question already answered. Scope the second run
    // by BLAST RADIUS rather than running the whole suite: a full suite is
    // hours, and the specs that can plausibly break are the ones that share the
    // code this batch touched.
    `THEN, ONCE (not ${GATE_N}×), run the specs this batch could have BROKEN. Find them mechanically, do not guess: \`git diff --name-only ${BASE}...${gateBranch}\` and keep the NON-spec files (page objects, fixtures, helpers, config); the affected specs are the ones importing them. If the batch only ADDED spec files and touched nothing shared, there is no blast radius and this run is unnecessary — say so in notes. A red here is a REGRESSION and belongs in failures[] like any other, flagged in notes as pre-existing-code rather than new-code. ` +
    'Report both scopes in notes: how many specs the N× run covered, and how many the regression run covered. ' +
    `When you are done, LEAVE THE TREE ON ${gateBranch} — \`git checkout ${gateBranch}\` after the script's detached run — because the next step assumes it is there. ` +
    'On red: read the runner\'s STRUCTURED report (JSON/HTML) for per-spec verdicts rather than log-diving, and return one failures[] entry per failing spec with its failure signature and, where the spec names them, the case ids it covers. ' +
    'One distinction you MUST make, because only you see the runner output: a spec that FAILED (an assertion, a timeout, an error inside the test) versus a spec that never ran (module not found, worker crash, 0ms duration, collection error). The second is an infrastructure fact — a file missing from the merge, a dependency not installed — and reporting it as a red case sends the lead hunting a bug that does not exist. Put such failures in `failures` with the signature verbatim AND say in notes that the spec did not execute. ' +
    (EXPECTED_RED.length
      ? `RED BY DESIGN — do not count these against the green requirement:\n${EXPECTED_RED.map((r) => `  - ${quote(r.spec, 200)}${r.test_id ? ` :: ${quote(r.test_id, 120)}` : ''} — ticket ${quote(r.ticket, 60)} (${quote(r.why, 200)})`).join('\n')}\nRun them like everything else and report exactly what they did, but the N-consecutive-green contract covers only the OTHER specs. These carry a ticketed product defect the implementer asserted softly rather than hid — a permanently failing test is the correct signal, and counting it would make this batch unpassable while blocking every healthy case in it. If one of them comes back GREEN, say so loudly in notes: the product shipped a fix and the ticket can close. `
      : '') +
    'Do NOT merge anything. Do NOT classify the failure (product defect vs flake vs architectural — that is the lead\'s call). Do NOT fix. ' +
    FOREGROUND_RULE +
    'Return verdict=green only if you observed ' + GATE_N + ' consecutive green runs.',
    { label: `gate:${SLUG}`, phase: 'Gate', agentType: TYPES.gate, ...WORKER, schema: GATE_SCHEMA }
  )
  if (gate) addFindings(merged.flatMap((r) => r.ids), gate.findings ?? [])
  // The gate proves the TRUNK, so it speaks for exactly the units on it.
  const integratedIds = new Set(merged.flatMap((r) => r.ids))
  if (gate?.verdict === 'green') {
    // A green gate proves the specs it COUNTED. A case carrying a red-by-design
    // test was deliberately excluded from that count, so the gate says nothing
    // about it — reporting it `automated` would claim proof the run never had.
    // It is blocked on its ticket, and re-enters a batch when the product ships.
    let autoCount = 0
    for (const id of integratedIds) {
      const red = OUTCOME[id]._expectedRed
      if (red?.length) {
        record(id, { outcome: 'blocked', note: `red by design pending ${red.map((r) => r.ticket).join(', ')} — the gate ran it but could not count it; re-enter once the product ships` })
        continue
      }
      record(id, { outcome: 'automated', gate: { runs: gate.runs, seconds: gate.seconds ?? [] } })
      autoCount++
    }
    log(`gate GREEN ${gate.runs}/${GATE_N} — ${autoCount} case(s) automated` + (EXPECTED_RED.length ? `, ${integratedIds.size - autoCount} held on ticketed defects` : ''))
  } else {
    const failedIds = new Set((gate?.failures ?? []).flatMap((f) => f.case_ids ?? []))
    for (const id of integratedIds) {
      const why = failedIds.has(id)
        ? `gate red: ${(gate.failures.find((f) => (f.case_ids ?? []).includes(id))?.signature ?? '').slice(0, 200)}`
        : 'gate red for the batch — this spec did not itself fail; the batch is not proven until the red is resolved'
      record(id, { outcome: 'blocked', note: why })
    }
    log(`gate ${gate?.verdict ?? 'not-run'} — classify (product defect / flake / architectural), then consider batch-stabilize`)
  }
}

// ---- Phase 5: the report — ONE writer, at close -----------------------------
phase('Report')
// `_findingKeys` is dedup bookkeeping, not part of the report contract.
const rows = CASES.map((c) => { const { _findingKeys, _expectedRed, ...row } = OUTCOME[c.id]; return row })
const totals = rows.reduce((acc, r) => { acc[r.outcome] = (acc[r.outcome] ?? 0) + 1; return acc }, {})
const qualityFlags = []
if (analyzedCount >= 4 && extendishCount / analyzedCount > EXTEND_RATE) {
  qualityFlags.push(`extend-rate ${extendishCount}/${analyzedCount} exceeds ${EXTEND_RATE} — blind-audit a sample of the extend/covered conclusions (a second analyst re-analyzing 1-2) before trusting this batch's coverage`)
}
// There is deliberately NO mirror flag for a batch with zero already-covered /
// extend-existing. Zero is the normal, healthy result: reading the neighbouring
// specs (§ 2b) exists to make ANALYSIS cheaper — handles, flows, conventions —
// not to close cases. A flag on "too little dedup" would push analysts toward
// calling cases covered, and the two errors are not symmetric: a redundant test
// is visible and cheap to delete, while a wrongly-deduped case is never
// automated and the hole never surfaces. Only the dangerous direction — too
// MANY extend/covered conclusions — is flagged, above.
const report = {
  batch: SLUG,
  base: BASE,
  integration_branch: merged.length ? gateBranch : null,
  gate: gate ? { verdict: gate.verdict, runs: gate.runs, seconds: gate.seconds ?? [], failures: (gate.failures ?? []).map((f) => ({ ...f, ...(typeof f?.signature === 'string' ? { signature: clip(f.signature) } : {}) })) } : null,
  cases: rows,
  totals,
  quality_flags: qualityFlags,
  quota_halted: quotaHalted,
  expected_red: EXPECTED_RED,
  // Units that passed review but could NOT be merged into the trunk. They are
  // `blocked` in cases[] too; naming them here keeps the merge failure visible
  // as its own class rather than buried among product-defect blocks.
  parked: parked.map((p) => ({ ids: p.ids, branch: p.branch, why: clip(p.why) })),
}

// The only disk write in the whole run. Everything else that must survive an
// interruption is already persisted by the runtime (journal.jsonl) or by git.
const WRITE_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['written'], properties: { written: { type: 'boolean' }, detail: { type: 'string' } },
}
const wrote = await agent(
  'You are the report writer — the single disk write of this run.\n' +
  `Create the directory ${REPORT_DIR} if needed, then Write TWO files:\n` +
  `1. ${REPORT_DIR}/report.json — EXACTLY this JSON, byte for byte, no edits, no commentary:\n` +
  // Five-backtick fence: notes and findings are agent-authored free text and
  // frequently contain ``` themselves, which would end a three-backtick fence.
  '`````json\n' + JSON.stringify(report, null, 2) + '\n`````\n' +
  `2. ${REPORT_DIR}/report.md — a readable rendering of the same data for a human: a totals line, then a table of case id / outcome / note, then any findings grouped by kind, then the gate verdict with its timings.\n` +
  'Change NOTHING about the data — you are rendering it, not judging it. ' +
  `If the project commits automation artifacts, commit both — then RETURN THE TREE TO ${gateBranch} before you finish (\`git checkout ${gateBranch}\`), because the next thing to run assumes it is there. Otherwise leave them on disk, touch no branch, and say so.`,
  // Named, not anonymous: it writes into the repository and may commit, so it
  // needs the project's conventions from its role briefing. An `agent()` without
  // `agentType` reaches SubagentStart as `workflow-subagent` and resolves to no
  // role at all — measured on one campaign, 1004 of 2123 units arrived that way.
  // Pure rendering (byte-exact JSON copy + a markdown table): the cheapest
  // capable tier. Override via reporterModel if a project's renderer needs more.
  { label: `report:${SLUG}`, phase: 'Report', agentType: TYPES.reporter, model: A.reporterModel ?? 'haiku', effort: 'low', schema: WRITE_SCHEMA }
)

return {
  ...report,
  report_written: wrote?.written === true,
  report_path: `${REPORT_DIR}/report.json`,
  analyzed,                                  // analyzeOnly runs feed this back as preAnalyzed
  extend_cases: extendCases,
  next: quotaHalted
    ? 'ACCOUNT CEILING — nothing to repair. Re-invoke with the SAME args plus resumeFromRunId once the limit resets; completed units replay from cache.'
    : gate?.verdict === 'green'
      // ONE PR takes the whole trunk to base — the units already merged into it,
      // so what was gated and what lands are the same object.
      ? `Gate green on ${gateBranch}. LAND IT: one PR from ${gateBranch} to ${BASE} per .agents/profile.md § Automation PR policy (auto-merge / human-approved / manual decides who presses it), then mirror to the TMS and run the close sweep. Replan anything not 'automated'.`
      : `Classify each blocked case (product defect → tracker; flake/test-code bug → batch-stabilize on ${gateBranch}; architectural → § Framework architecture), then replan the remainder. ${gateBranch} is NOT landed — nothing reaches ${BASE} until it is green.`,
}
