#!/usr/bin/env python3
"""Locator inventory, locator-debt metric and testid-migration ledger.

Static (AST) scan of the page objects — no browser, no Playwright import — so
it runs anywhere, including CI and the weekly testid-migrator session.

What it counts
  * declared locators: class-level LocatorDescriptor / OptionalLocatorDescriptor /
    ScopedLocator fields, plus UPPER_CASE `[data-testid="…"]` string constants
    (scoped / template testid selectors)
  * unmanaged handles: raw `page.locator(` / `get_by_*(` calls inside method
    bodies and non-testid `*_SELECTOR` string constants — legacy debt the
    migrator cannot swap mechanically (no suggested_testid)

Locator debt = non-testid declared locators / all declared locators.

Ledger (git-tracked JSON, owned by the testid migrator) tracks every
non-testid declaration through:  raw → testid-proposed → on-dev → migrated

Usage (from automation/):
    ../.venv/bin/python scripts/locator_inventory.py scan [--json out.json]
    ../.venv/bin/python scripts/locator_inventory.py sync-ledger
    ../.venv/bin/python scripts/locator_inventory.py queue [--limit 25]
    ../.venv/bin/python scripts/locator_inventory.py check-ui-ref --ui-repo ../../EliteaUI --ref origin/main
    ../.venv/bin/python scripts/locator_inventory.py mark <id> <state> --evidence "…"
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

AUTOMATION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTOMATION_ROOT.parent
DEFAULT_PAGES = AUTOMATION_ROOT / "pages"
DEFAULT_LEDGER = REPO_ROOT / ".agents" / "locator-migration" / "ledger.json"

DESCRIPTOR_CLASSES = {"LocatorDescriptor", "OptionalLocatorDescriptor", "ScopedLocator"}
KINDS = ("testid", "role", "label", "css", "xpath")
STATES = ("raw", "testid-proposed", "on-dev", "migrated", "removed")
# Allowed forward moves for `mark`; sync-ledger alone sets migrated/removed.
TRANSITIONS = {
    "raw": {"testid-proposed"},
    "testid-proposed": {"on-dev", "raw"},
    "on-dev": {"migrated", "testid-proposed"},
    "migrated": set(),
    "removed": {"raw"},
}
RAW_CALLS = {
    "locator",
    "get_by_role",
    "get_by_label",
    "get_by_text",
    "get_by_placeholder",
    "get_by_title",
    "get_by_alt_text",
    "get_by_test_id",
    "query_selector",
    "query_selector_all",
}
UPPER_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
TESTID_SELECTOR_RE = re.compile(r"^\s*\[data-testid")


@dataclass
class Declaration:
    id: str
    file: str
    line: int
    cls: str
    attr: str
    descriptor: str
    kind: str
    selector: str
    suggested_testid: str | None
    description: str = ""


@dataclass
class Unmanaged:
    file: str
    line: int
    cls: str
    where: str
    call: str


@dataclass
class Inventory:
    declarations: list[Declaration] = field(default_factory=list)
    unmanaged: list[Unmanaged] = field(default_factory=list)

    def metric(self) -> dict:
        total = len(self.declarations)
        by_kind: dict[str, int] = {}
        for d in self.declarations:
            by_kind[d.kind] = by_kind.get(d.kind, 0) + 1
        non_testid = total - by_kind.get("testid", 0)
        hinted = sum(1 for d in self.declarations if d.kind != "testid" and d.suggested_testid)
        return {
            "declared_total": total,
            "declared_testid": by_kind.get("testid", 0),
            "declared_non_testid": non_testid,
            "non_testid_with_hint": hinted,
            "non_testid_without_hint": non_testid - hinted,
            "by_kind": dict(sorted(by_kind.items())),
            "locator_debt": round(non_testid / total, 4) if total else 0.0,
            "unmanaged_handles": len(self.unmanaged),
        }


def _const_str(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value if isinstance(v, ast.Constant) else "{}" for v in node.values)
    return None


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _declaration_from_call(call: ast.Call, rel: str, cls: str, attr: str) -> Declaration:
    kw = {k.arg: k.value for k in call.keywords if k.arg}
    positional = ["testid", "locator", "description", "fallback"]
    for i, arg in enumerate(call.args[: len(positional)]):
        kw.setdefault(positional[i], arg)
    kind = next((k for k in KINDS if _const_str(kw.get(k))), None)
    if kind is None:
        kind = "locator" if "locator" in kw else ("fallback" if "fallback" in kw else "unknown")
    selector = _const_str(kw.get(kind)) or (ast.unparse(kw[kind]) if kind in kw else "")
    if kind == "role" and _const_str(kw.get("name")) is not None:
        selector = f"{selector}[name={_const_str(kw['name'])!r}]"
    return Declaration(
        id=f"{rel}::{cls}.{attr}",
        file=rel,
        line=call.lineno,
        cls=cls,
        attr=attr,
        descriptor=_call_name(call) or "",
        kind=kind,
        selector=selector,
        suggested_testid=_const_str(kw.get("suggested_testid")),
        description=_const_str(kw.get("description")) or "",
    )


def scan_file(path: Path, root: Path) -> Inventory:
    rel = path.relative_to(root.parent).as_posix() if root.parent in path.parents else path.as_posix()
    inv = Inventory()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
        for stmt in cls.body:
            if isinstance(stmt, ast.Assign | ast.AnnAssign):
                targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
                names = [t.id for t in targets if isinstance(t, ast.Name)]
                value = stmt.value
                if not names or value is None:
                    continue
                attr = names[0]
                if isinstance(value, ast.Call) and _call_name(value) in DESCRIPTOR_CLASSES:
                    inv.declarations.append(_declaration_from_call(value, rel, cls.name, attr))
                elif UPPER_RE.match(attr) and (text := _const_str(value)) is not None:
                    if TESTID_SELECTOR_RE.match(text):
                        inv.declarations.append(
                            Declaration(
                                id=f"{rel}::{cls.name}.{attr}",
                                file=rel,
                                line=stmt.lineno,
                                cls=cls.name,
                                attr=attr,
                                descriptor="const",
                                kind="testid",
                                selector=text,
                                suggested_testid=None,
                            )
                        )
                    elif attr.endswith(("_SELECTOR", "_LOCATOR")):
                        inv.unmanaged.append(Unmanaged(rel, stmt.lineno, cls.name, attr, f"const {text!r}"))
            elif isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef):
                for node in ast.walk(stmt):
                    if isinstance(node, ast.Call) and _call_name(node) in RAW_CALLS:
                        first = _const_str(node.args[0]) if node.args else None
                        if first is not None and TESTID_SELECTOR_RE.match(first):
                            continue  # literal [data-testid=…] scoped selector — testid-keyed
                        if first is None and node.args and _is_class_constant_ref(node.args[0]):
                            continue  # self.UPPER_CONST / Class.UPPER_CONST — counted at its declaration
                        inv.unmanaged.append(Unmanaged(rel, node.lineno, cls.name, stmt.name, ast.unparse(node)[:160]))
    return inv


def _is_class_constant_ref(node: ast.AST) -> bool:
    """`self.X` / `Cls.X` / `self.X.format(...)` with an UPPER_CASE X."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "format":
        node = node.func.value
    return isinstance(node, ast.Attribute) and bool(UPPER_RE.match(node.attr))


def scan(pages_dir: Path) -> Inventory:
    inv = Inventory()
    for path in sorted(pages_dir.rglob("*.py")):
        if path.name in {"__init__.py", "locator_descriptor.py"}:
            continue
        part = scan_file(path, pages_dir)
        inv.declarations.extend(part.declarations)
        inv.unmanaged.extend(part.unmanaged)
    return inv


# ── ledger ────────────────────────────────────────────────────────────────


def _today() -> str:
    return dt.date.today().isoformat()


def load_ledger(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"schema": 1, "entries": {}}


def save_ledger(path: Path, ledger: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ledger["entries"] = dict(sorted(ledger["entries"].items()))
    path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sync_ledger(inv: Inventory, ledger: dict) -> dict:
    """Reconcile the ledger with the current source. Returns a change summary."""
    entries = ledger["entries"]
    current = {d.id: d for d in inv.declarations}
    added, migrated, removed, revived = [], [], [], []
    for d in inv.declarations:
        e = entries.get(d.id)
        if d.kind == "testid":
            if e and e["state"] != "migrated":
                e.update(state="migrated", testid=_testid_of(d), updated=_today())
                e.setdefault("history", []).append({"state": "migrated", "date": _today(), "by": "sync"})
                migrated.append(d.id)
            continue
        snapshot = {
            "file": d.file,
            "line": d.line,
            "kind": d.kind,
            "selector": d.selector,
            "suggested_testid": d.suggested_testid,
            "description": d.description,
        }
        if e is None:
            entries[d.id] = {**snapshot, "state": "raw", "added": _today(), "updated": _today(), "history": []}
            added.append(d.id)
        else:
            if e["state"] in ("removed", "migrated"):
                revived.append(d.id)
                e["state"] = "raw"
                e.setdefault("history", []).append({"state": "raw", "date": _today(), "by": "sync"})
            e.update(snapshot)
    for eid, e in entries.items():
        if eid not in current and e["state"] not in ("removed", "migrated"):
            e.update(state="removed", updated=_today())
            e.setdefault("history", []).append({"state": "removed", "date": _today(), "by": "sync"})
            removed.append(eid)
    ledger["last_sync"] = _today()
    ledger["metric"] = inv.metric()
    return {"added": added, "migrated": migrated, "removed": removed, "revived": revived}


def _testid_of(d: Declaration) -> str:
    m = re.search(r'data-testid="([^"]+)"', d.selector)
    return m.group(1) if m else d.selector


def mark(ledger: dict, entry_id: str, state: str, evidence: str, ref: str | None = None) -> dict:
    if state not in STATES:
        raise SystemExit(f"unknown state {state!r}; one of {STATES}")
    e = ledger["entries"].get(entry_id)
    if e is None:
        raise SystemExit(f"no ledger entry {entry_id!r} — run sync-ledger first")
    if state not in TRANSITIONS[e["state"]]:
        raise SystemExit(f"illegal transition {e['state']} → {state} for {entry_id}")
    if not evidence:
        raise SystemExit("--evidence is required (commit SHA, PR URL, dev run id …)")
    e["state"] = state
    e["updated"] = _today()
    if ref:
        e["ref"] = ref
    e.setdefault("history", []).append({"state": state, "date": _today(), "evidence": evidence})
    return e


def queue(ledger: dict, limit: int) -> dict:
    """Next weekly batch: phase A swaps (on-dev), phase B testid additions (raw, hinted)."""

    def pick(state: str, need_hint: bool) -> list[dict]:
        rows = [
            {"id": eid, **{k: e[k] for k in ("file", "kind", "selector", "suggested_testid")}}
            for eid, e in ledger["entries"].items()
            if e["state"] == state and (e.get("suggested_testid") or not need_hint)
        ]
        rows.sort(key=lambda r: (r["file"], r["id"]))
        return rows[:limit]

    return {
        "phase_a_swap": pick("on-dev", need_hint=True),
        "phase_b_add_testid": pick("raw", need_hint=True),
        "awaiting_deploy": pick("testid-proposed", need_hint=True),
        # Legacy declarations with no suggested_testid — the migrator names them first.
        "needs_hint": [
            {"id": eid, **{k: e[k] for k in ("file", "kind", "selector")}}
            for eid, e in sorted(ledger["entries"].items())
            if e["state"] == "raw" and not e.get("suggested_testid")
        ][:limit],
    }


def check_ui_ref(ledger: dict, ui_repo: Path, ref: str) -> list[dict]:
    """Which testid-proposed entries' testids already exist on `ref` of the UI repo (src/ only)."""
    out = []
    for eid, e in ledger["entries"].items():
        tid = e.get("suggested_testid")
        if e["state"] != "testid-proposed" or not tid:
            continue
        needle = tid.removesuffix("-{}")
        res = subprocess.run(
            ["git", "-C", str(ui_repo), "grep", "-l", "-F", needle, ref, "--", "src/"],
            capture_output=True,
            text=True,
            check=False,
        )
        out.append({"id": eid, "suggested_testid": tid, "on_ref": res.returncode == 0})
    return out


# ── CLI ───────────────────────────────────────────────────────────────────


def _print_metric(inv: Inventory) -> None:
    m = inv.metric()
    print(f"Declared locators : {m['declared_total']}")
    print(f"  testid          : {m['declared_testid']}")
    print(
        f"  non-testid      : {m['declared_non_testid']}  (hinted {m['non_testid_with_hint']}, "
        f"no hint {m['non_testid_without_hint']})"
    )
    print(f"  by kind         : {m['by_kind']}")
    print(f"Locator debt      : {m['locator_debt']:.2%}")
    print(f"Unmanaged handles : {m['unmanaged_handles']}  (raw calls in methods / non-testid *_SELECTOR consts)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pages", type=Path, default=DEFAULT_PAGES)
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan", help="print the locator-debt metric")
    s.add_argument("--json", type=Path, help="write the full inventory as JSON")
    s.add_argument("--max-debt", type=float, help="exit 1 if locator debt exceeds this ratio")
    sub.add_parser("sync-ledger", help="reconcile the ledger with the source")
    q = sub.add_parser("queue", help="print the next migration batch as JSON")
    q.add_argument("--limit", type=int, default=25)
    c = sub.add_parser("check-ui-ref", help="report testid-proposed entries present on a UI ref")
    c.add_argument("--ui-repo", type=Path, required=True)
    c.add_argument("--ref", default="origin/main")
    mk = sub.add_parser("mark", help="move one ledger entry to a new state")
    mk.add_argument("id")
    mk.add_argument("state", choices=STATES)
    mk.add_argument("--evidence", required=True)
    mk.add_argument("--ref")
    args = ap.parse_args(argv)

    if args.cmd == "scan":
        inv = scan(args.pages)
        _print_metric(inv)
        if args.json:
            args.json.write_text(
                json.dumps(
                    {
                        "metric": inv.metric(),
                        "declarations": [asdict(d) for d in inv.declarations],
                        "unmanaged": [asdict(u) for u in inv.unmanaged],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        if args.max_debt is not None and inv.metric()["locator_debt"] > args.max_debt:
            print(f"FAIL: locator debt above {args.max_debt:.2%}", file=sys.stderr)
            return 1
        return 0

    ledger = load_ledger(args.ledger)
    if args.cmd == "sync-ledger":
        inv = scan(args.pages)
        changes = sync_ledger(inv, ledger)
        save_ledger(args.ledger, ledger)
        _print_metric(inv)
        print(json.dumps({k: len(v) for k, v in changes.items()}))
        return 0
    if args.cmd == "queue":
        print(json.dumps(queue(ledger, args.limit), indent=2))
        return 0
    if args.cmd == "check-ui-ref":
        print(json.dumps(check_ui_ref(ledger, args.ui_repo, args.ref), indent=2))
        return 0
    if args.cmd == "mark":
        e = mark(ledger, args.id, args.state, args.evidence, args.ref)
        save_ledger(args.ledger, ledger)
        print(json.dumps({args.id: e["state"]}))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
