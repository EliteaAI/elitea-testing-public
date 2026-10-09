#!/usr/bin/env python3
"""One-time backfill of ``@pytest.mark.tms(...)`` markers from the TMS index.

Reads the TMS case→test mapping and writes the case ids into the test sources,
so that from then on the ids are hardcoded and no index lookup happens at
runtime. Intended to be run ONCE; afterwards new tests get the marker by hand
(and `scripts/check_tms_markers.py` reports any drift).

Usage (from automation/)::

    python scripts/backfill_tms_markers.py \
        --tms-index ../../onetest-ai-tm-Elitea/index_automated_short.json --dry-run
    python scripts/backfill_tms_markers.py \
        --tms-index ../../onetest-ai-tm-Elitea/index_automated_short.json --apply

The marker is inserted at the scope the TMS ref names:

* ``tests.ui.x.test_y.TestY.test_z``    → on the ``test_z`` method
* ``tests.ui.x.test_y.test_z``          → on the ``test_z`` function
* ``…test_z[param]``                    → reported, never auto-applied: a
  per-parameter case id must be attached to the ``pytest.param(marks=...)``,
  which cannot be done safely by line insertion. Apply those by hand.

Decorators are inserted directly above ``def``, below any existing decorators,
matching the target's indentation. Tests that already carry a ``tms`` marker are
left alone, so re-running is safe.
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

TESTS_ROOT = Path("tests")


def load_mapping(tms_index: Path) -> tuple[dict[str, list[str]], list[tuple[str, list[str]]]]:
    """Return ({test_ref: [case_id, ...]}, [(param_ref, case_ids), ...]).

    Parametrized refs are split out: they need a ``pytest.param(marks=...)`` edit
    that this script deliberately does not attempt.
    """
    data = json.loads(tms_index.read_text(encoding="utf-8"))

    plain: dict[str, list[str]] = defaultdict(list)
    parametrized: dict[str, list[str]] = defaultdict(list)

    for case in data.get("cases", []):
        case_id = case["id"]
        refs = case.get("automation_test_id") or []
        if isinstance(refs, str):  # a bare scalar is a 1-item list
            refs = [refs]
        for ref in refs:
            target = parametrized if "[" in ref else plain
            target[ref].append(case_id)

    return (
        {ref: sorted(dict.fromkeys(ids)) for ref, ids in plain.items()},
        sorted((ref, sorted(dict.fromkeys(ids))) for ref, ids in parametrized.items()),
    )


def resolve_source(ref: str) -> tuple[Path, str] | None:
    """Map a dotted test ref to (file_path, target_name).

    ``tests.ui.x.test_y.TestY.test_z`` → (tests/ui/x/test_y.py, "test_z").
    The module boundary is found by walking the dotted path until the longest
    prefix that is an existing .py file — class names and the test name follow.
    """
    parts = ref.split(".")
    for split_at in range(len(parts) - 1, 0, -1):
        candidate = Path(*parts[:split_at]).with_suffix(".py")
        if candidate.is_file():
            trailing = parts[split_at:]
            if not trailing:
                return None
            return candidate, trailing[-1]
    return None


def already_marked(lines: list[str], def_index: int) -> bool:
    """True if a tms marker already decorates the def at ``def_index``."""
    i = def_index - 1
    while i >= 0:
        stripped = lines[i].strip()
        if stripped.startswith("@"):
            if re.match(r"@pytest\.mark\.tms\b", stripped):
                return True
            i -= 1
            continue
        if not stripped or stripped.startswith("#"):
            i -= 1
            continue
        break
    return False


def find_def(lines: list[str], name: str) -> int | None:
    """Index of the line defining ``name`` (def or async def). None if absent."""
    pattern = re.compile(rf"^\s*(async\s+)?def\s+{re.escape(name)}\s*\(")
    for index, line in enumerate(lines):
        if pattern.match(line):
            return index
    return None


def decorator_insert_index(lines: list[str], def_index: int) -> int:
    """Where to insert so the new decorator sits just above ``def``.

    Walks up past the def's own decorator stack — including multi-line
    decorators such as a wrapped @pytest.mark.parametrize(...) — and returns the
    line directly below the topmost one, keeping existing decorator order intact.
    """
    insert_at = def_index
    i = def_index - 1
    depth = 0
    while i >= 0:
        stripped = lines[i].strip()
        if not stripped or stripped.startswith("#"):
            i -= 1
            continue
        depth += stripped.count(")") - stripped.count("(")
        if stripped.startswith("@") and depth <= 0:
            insert_at = i
            depth = 0
            i -= 1
            continue
        if depth > 0:  # inside a wrapped decorator's parentheses
            i -= 1
            continue
        break
    return insert_at


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tms-index", required=True, type=Path)
    parser.add_argument("--apply", action="store_true", help="write changes to disk")
    parser.add_argument("--dry-run", action="store_true", help="report only (default)")
    args = parser.parse_args()

    if not args.apply and not args.dry_run:
        args.dry_run = True

    plain, parametrized = load_mapping(args.tms_index)

    # Group edits per file so each file is read and written exactly once.
    per_file: dict[Path, list[tuple[str, list[str], str]]] = defaultdict(list)
    unresolved: list[tuple[str, list[str]]] = []

    for ref, case_ids in sorted(plain.items()):
        resolved = resolve_source(ref)
        if resolved is None:
            unresolved.append((ref, case_ids))
            continue
        path, target = resolved
        per_file[path].append((target, case_ids, ref))

    applied = skipped = missing = 0

    for path in sorted(per_file):
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        # Insert bottom-up so earlier insertions don't shift later line numbers.
        edits = []
        for target, case_ids, ref in per_file[path]:
            def_index = find_def(lines, target)
            if def_index is None:
                print(f"  MISSING  {ref} — no 'def {target}' in {path}")
                missing += 1
                continue
            if already_marked(lines, def_index):
                skipped += 1
                continue
            edits.append((decorator_insert_index(lines, def_index), case_ids, target))

        for insert_at, case_ids, target in sorted(edits, reverse=True):
            indent = re.match(r"\s*", lines[insert_at]).group(0)
            args_text = ", ".join(f'"{cid}"' for cid in case_ids)
            lines.insert(insert_at, f"{indent}@pytest.mark.tms({args_text})\n")
            applied += 1
            print(f"  + {path}: {target} → {', '.join(case_ids)}")

        if edits and args.apply:
            path.write_text("".join(lines), encoding="utf-8")

    print("\n--- summary ---")
    print(f"markers inserted : {applied}{'' if args.apply else ' (dry-run, nothing written)'}")
    print(f"already marked   : {skipped}")
    print(f"def not found    : {missing}")
    print(f"unresolved refs  : {len(unresolved)} (no such module)")
    for ref, case_ids in unresolved:
        print(f"  ? {ref} → {', '.join(case_ids)}")
    print(f"parametrized     : {len(parametrized)} — apply by hand on pytest.param(marks=...)")
    for ref, case_ids in parametrized:
        print(f"  ! {ref} → {', '.join(case_ids)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
