#!/usr/bin/env python3
"""Fit the gh-pages tree of Allure reports inside GitHub's size limits.

GitHub rejects a push that contains any file over 100 MB, and one such file
loses the whole report (run 329: a 200 MB failure video → push rejected → the
report URL 404s). GitHub Pages also caps a published site at 1 GB. Videos are
almost all of the weight (1348 of 1499 MB on 2026-10-30), so this script drops
videos — never the report itself — until both limits hold:

1. Any file larger than ``--max-file-mb`` is dropped, wherever it is.
2. While the tree is over ``--budget-mb``, videos are dropped from the OLDEST
   run first, largest first within a run. The run being published goes last,
   so the newest report keeps as many of its videos as the budget allows.

A dropped attachment is not left as a dead link: its entry in the report's
``data/test-cases/*.json`` is repointed at a small text file that says what was
removed and where the original lives (the run's ``allure-results`` artifact,
whose URL the publish job stamps into ``<run>/.run-url``).

Usage (from the publish job, after the prune step)::

    python scripts/pages_budget.py gh-pages --current dev/329 >> "$GITHUB_STEP_SUMMARY"

Exit code is 0 unless a file over ``--max-file-mb`` survives (it cannot, by
construction — the check is a guard against a future edit breaking that).
"""

import argparse
import json
import os
import sys
from pathlib import Path

MB = 1024 * 1024

#: Attachment types / extensions treated as droppable video.
VIDEO_EXTENSIONS = {".webm", ".mp4"}


def _published_at(run_dir: Path) -> float:
    """Publish time of a run in epoch seconds; 0 (= oldest) when unknown."""
    try:
        return float((run_dir / ".published-at").read_text().strip())
    except (OSError, ValueError):
        pass
    try:
        started = json.loads((run_dir / "widgets" / "summary.json").read_text())["time"]["start"]
        if isinstance(started, (int, float)) and started > 0:
            return started / 1000.0
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return 0.0


def _tree_size(root: Path) -> int:
    total = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in filenames:
            path = os.path.join(dirpath, name)
            if not os.path.islink(path):
                try:
                    total += os.path.getsize(path)
                except OSError:
                    pass
    return total


def _iter_attachment_entries(node):
    """Yield every attachment dict in an Allure test-case JSON document."""
    if isinstance(node, dict):
        for item in node.get("attachments") or []:
            if isinstance(item, dict) and "source" in item:
                yield item
        for value in node.values():
            if isinstance(value, (dict, list)):
                yield from _iter_attachment_entries(value)
    elif isinstance(node, list):
        for value in node:
            yield from _iter_attachment_entries(value)


class Report:
    """One published Allure report directory (``<env>/<run>``)."""

    def __init__(self, path: Path, label: str):
        self.path = path
        self.label = label
        self.attachments_dir = path / "data" / "attachments"
        self.published_at = _published_at(path)
        run_url_file = path / ".run-url"
        self.run_url = run_url_file.read_text().strip() if run_url_file.is_file() else ""
        self._refs = None  # source file name -> [test-case json path, ...]

    def refs(self) -> dict:
        if self._refs is None:
            self._refs = {}
            for case_file in sorted((self.path / "data" / "test-cases").glob("*.json")):
                try:
                    doc = json.loads(case_file.read_text())
                except (OSError, ValueError):
                    continue
                for entry in _iter_attachment_entries(doc):
                    self._refs.setdefault(entry["source"], []).append(case_file)
        return self._refs

    def videos(self) -> list:
        if not self.attachments_dir.is_dir():
            return []
        return [p for p in self.attachments_dir.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS]

    def drop(self, file: Path, reason: str) -> int:
        """Delete ``file`` and repoint its report entries at a text placeholder.

        Returns the number of bytes freed.
        """
        size = file.stat().st_size
        size_mb = size / MB
        where = (
            f"the allure-results artifact of {self.run_url} (artifacts are kept for 14 days)"
            if self.run_url
            else "the allure-results artifact of the CI run that produced this report"
        )
        note = (
            f"This attachment ({file.name}, {size_mb:.1f} MB) was removed from the GitHub Pages copy "
            f"of this report: {reason}.\nThe original is in {where}.\n"
        )
        placeholder = file.with_name(f"{file.stem}-removed.txt")
        placeholder.write_text(note)
        for case_file in self.refs().get(file.name, []):
            doc = json.loads(case_file.read_text())
            for entry in _iter_attachment_entries(doc):
                if entry["source"] == file.name:
                    entry["name"] = f"{entry.get('name') or 'Attachment'} — removed, {size_mb:.0f} MB (see note)"
                    entry["source"] = placeholder.name
                    entry["type"] = "text/plain"
                    entry["size"] = len(note.encode())
            case_file.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))
        file.unlink()
        return size - placeholder.stat().st_size


def find_reports(root: Path) -> dict:
    """Map ``env/run`` label → Report for every published report under ``root``."""
    reports = {}
    for env_dir in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")):
        for run_dir in sorted(p for p in env_dir.iterdir() if p.is_dir() and p.name.isdigit()):
            if (run_dir / "data").is_dir():
                label = f"{env_dir.name}/{run_dir.name}"
                reports[label] = Report(run_dir, label)
    return reports


def enforce(root: Path, current: str, max_file_mb: float, budget_mb: float) -> dict:
    """Apply both limits to ``root`` in place. Returns a summary dict."""
    reports = find_reports(root)
    before = _tree_size(root)
    dropped = []  # (label, file name, MB, reason)

    # 1. Per-file hard limit — anything GitHub would reject outright.
    limit = max_file_mb * MB
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in filenames:
            path = Path(dirpath) / name
            if path.is_symlink() or path.stat().st_size <= limit:
                continue
            owner = next((r for r in reports.values() if r.attachments_dir == path.parent), None)
            reason = f"larger than the {max_file_mb:g} MB per-file limit for the gh-pages push"
            size_mb = path.stat().st_size / MB
            if owner is not None:
                owner.drop(path, reason)
                dropped.append((owner.label, name, size_mb, "file limit"))
            else:
                path.unlink()
                dropped.append((str(path.relative_to(root)), name, size_mb, "file limit"))

    # 2. Site budget — videos, oldest run first, the run being published last.
    total = _tree_size(root)
    budget = budget_mb * MB
    if total > budget:
        order = sorted(reports.values(), key=lambda r: (r.label == current, r.published_at, r.label))
        reason = f"the GitHub Pages site is kept under {budget_mb:g} MB and videos are dropped oldest-run-first"
        for report in order:
            for video in sorted(report.videos(), key=lambda p: p.stat().st_size, reverse=True):
                if total <= budget:
                    break
                size_mb = video.stat().st_size / MB
                total -= report.drop(video, reason)
                dropped.append((report.label, video.name, size_mb, "site budget"))
            if total <= budget:
                break

    after = _tree_size(root)
    oversize = [
        str(Path(d) / f)
        for d, dn, fs in os.walk(root)
        if ".git" not in Path(d).parts
        for f in fs
        if not os.path.islink(os.path.join(d, f)) and os.path.getsize(os.path.join(d, f)) > limit
    ]
    return {
        "before_mb": before / MB,
        "after_mb": after / MB,
        "budget_mb": budget_mb,
        "dropped": dropped,
        "over_budget": after > budget,
        "oversize": oversize,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("root", type=Path, help="gh-pages working tree")
    parser.add_argument("--current", default="", help="env/run being published, e.g. dev/329 (its videos go last)")
    parser.add_argument("--max-file-mb", type=float, default=95.0, help="per-file limit (GitHub rejects >100 MB)")
    parser.add_argument("--budget-mb", type=float, default=900.0, help="site budget (GitHub Pages caps sites at 1 GB)")
    args = parser.parse_args(argv)

    result = enforce(args.root, args.current, args.max_file_mb, args.budget_mb)

    print(
        f"- gh-pages content: {result['before_mb']:.0f} MB → {result['after_mb']:.0f} MB "
        f"(budget {result['budget_mb']:g} MB, per-file limit {args.max_file_mb:g} MB)"
    )
    if result["dropped"]:
        freed = sum(mb for _, _, mb, _ in result["dropped"])
        print(f"- dropped {len(result['dropped'])} attachment(s), {freed:.0f} MB, to fit:")
        for label, name, mb, why in result["dropped"]:
            print(f"  - `{label}` {name} ({mb:.1f} MB, {why})")
        current_drops = [d for d in result["dropped"] if d[0] == args.current]
        if current_drops:
            print(
                f"::warning::{len(current_drops)} attachment(s) of {args.current} were removed from the "
                f"published report (full copies are in the run's allure-results artifacts)",
                file=sys.stderr,
            )
    if result["over_budget"]:
        print(
            f"::warning::gh-pages is still {result['after_mb']:.0f} MB after dropping every video — "
            f"above the {result['budget_mb']:g} MB budget. Lower KEEP_RUNS / MAX_AGE_DAYS.",
            file=sys.stderr,
        )
    if result["oversize"]:
        print(f"::error::files over the per-file limit survived: {result['oversize']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
