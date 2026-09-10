---
name: .env.test is a SYMLINK, so `sed -i ''` silently no-ops and your DEV gate certifies localhost
description: The documented "swap the env file, don't export" DEV-gate recipe fails on BSD sed because automation/.env.test is a symlink; the runs proceed against localhost and three greens certify nothing
type: how-to
aliases: [DEV gate env swap, sed in-place symlink, ELITEA_URL swap, app_base_url assert, false DEV certification]
tags: [area/gate, area/environments, type/trap]
created: 2026-09-10
updated: 2026-09-10
---

## The trap

`.agents/testing.md` correctly warns that `ELITEA_URL=… pytest` runs **localhost**
anyway, because `config.py` orders dotenv first — so "the env file itself must be
swapped and restored". The obvious implementation of that instruction is broken:

```
sed: …/automation/.env.test: in-place editing only works for regular files
```

`automation/.env.test` is a **symlink** to the master file in the parent workspace,
and BSD `sed -i ''` refuses symlinks. Inside a gate script the sed exits non-zero, the
file is untouched, and the pytest invocations run happily against `localhost:5173`.

**The failure mode is three cheerful greens that certify nothing.** Nothing errors,
nothing is red, and the log looks exactly like a successful DEV gate.

## Tells that you are looking at a false DEV certification

- **Wall clock.** ~11 s/run localhost vs 32–127 s/run on DEV, for identical work.
- The `=== TARGET ===` echo still reads `ELITEA_URL=http://localhost:5173`.
- **No `Page.goto` reruns at all.** A real DEV run of any length almost always carries
  at least one #2124 attempt (see [[dev_goto_lifecycle_waiter_never_resolves]]); a
  perfectly clean multi-run DEV gate is mildly suspicious on its own.

## The shape that works

```bash
REAL=$(python3 -c "import os;print(os.path.realpath('automation/.env.test'))")
cp "$REAL" /tmp/env.bak
trap 'cp /tmp/env.bak "$REAL"' EXIT INT TERM     # not a trailing line — see below
python3 - "$REAL" <<'PY'
import sys, re
p = sys.argv[1]; s = open(p).read()
s = re.sub(r'(?m)^ELITEA_URL=.*$', 'ELITEA_URL=https://dev.elitea.ai', s)
s = re.sub(r'(?m)^APP_PREFIX=.*$',  'APP_PREFIX=/app', s)
open(p, 'w').write(s)
PY
(cd automation && ../.venv/bin/python -c "from config import settings; print(settings.app_base_url)")
# MUST print https://dev.elitea.ai/app — this assert is the gate, not the sed's exit code
```

Two details that are not optional:

1. **Restore in a `trap … EXIT INT TERM`, never a trailing line.** The master env file
   is shared by all four sibling clones; a session killed mid-gate would otherwise
   leave the entire workspace pointed at DEV, and the next agent's "localhost" run is
   then silently a DEV run — the same bug with the polarity flipped.
2. **Assert via `settings.app_base_url`, not by reading the file back.** Reading the
   file proves the write; only the resolver proves what pytest will actually use.

## The generalisation

**A target-environment swap is not done until the framework's own resolver says so.**
Any step whose success you infer from "the command ran" rather than from the system
reporting the new state can no-op silently. Echo the resolved value; it costs one line
and it is the only thing that distinguishes a DEV gate from a localhost gate.

Related: [[some_specs_cannot_be_gated_on_localhost]] · [[gate_on_the_environment_the_repair_is_FOR]] · [[local_gate_cannot_prove_a_latency_fix]] · [[a_duplicate_card_is_where_you_pay_the_originals_evidence_gap]]
