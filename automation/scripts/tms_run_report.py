#!/usr/bin/env python3
"""Aggregate a run's Allure results into a per-TMS-case result table.

Reads raw ``*-result.json`` files (the allure-results directory, or a directory
holding several suites' worth of them) and groups the outcomes by TMS case id.
Case ids come from the Allure ``tag`` labels that ``utils/tms_case_ids.py``
attaches from each test's ``@pytest.mark.tms(...)`` — so this reads what the
tests themselves declare and needs no TMS index at runtime.

Usage::

    python scripts/tms_run_report.py aggregated-results >> $GITHUB_STEP_SUMMARY
    python scripts/tms_run_report.py reports/allure-results --json cases.json

A case covered by several tests is PASSED only when every one of its tests
passed: the case is the unit the TMS reports on, so one red test makes the case
red. Retries are collapsed the way Allure does it — the LAST result for a given
``historyId`` wins, so a test that passed on rerun counts as passed once, not as
one failure plus one pass.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

#: Case ids look like ELITEA-1234. Other tags (p0, ui, regression, …) are not cases.
CASE_ID_PREFIX = "ELITEA-"

#: Allure statuses in order of severity — the worst one a case sees becomes its verdict.
SEVERITY = ["failed", "broken", "unknown", "skipped", "passed"]

STATUS_ICON = {
    "passed": "✅",
    "failed": "❌",
    "broken": "🔥",
    "skipped": "⏭️",
    "unknown": "❓",
}


def load_results(results_dir: Path) -> list[dict]:
    """Return every Allure test result under ``results_dir`` (recursively).

    Retries are collapsed per ``historyId``, keeping the last-stopped attempt —
    the same rule the Allure report itself applies, so a test that passed on
    rerun is not also counted as a failure.
    """
    latest: dict[str, dict] = {}
    loose: list[dict] = []

    for path in sorted(results_dir.rglob("*-result.json")):
        try:
            result = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"warning: skipping {path.name}: {exc}", file=sys.stderr)
            continue

        history_id = result.get("historyId")
        if not history_id:
            loose.append(result)
            continue
        previous = latest.get(history_id)
        if previous is None or result.get("stop", 0) >= previous.get("stop", 0):
            latest[history_id] = result

    return list(latest.values()) + loose


def case_ids(result: dict) -> list[str]:
    """TMS case ids declared by this test, read from its Allure tag labels."""
    return sorted({
        label["value"]
        for label in result.get("labels", [])
        if label.get("name") == "tag" and str(label.get("value", "")).startswith(CASE_ID_PREFIX)
    })


def group_by_case(results: list[dict]) -> dict[str, list[dict]]:
    """Map each TMS case id to the test results covering it."""
    by_case: dict[str, list[dict]] = defaultdict(list)
    for result in results:
        for case_id in case_ids(result):
            by_case[case_id].append(result)
    return by_case


def case_status(results: list[dict]) -> str:
    """Worst status across a case's tests — one red test makes the case red."""
    statuses = {r.get("status", "unknown") for r in results}
    for status in SEVERITY:
        if status in statuses:
            return status
    return "unknown"


def build_report(results_dir: Path) -> tuple[dict[str, dict], dict[str, int]]:
    """Return ({case_id: {status, tests}}, totals)."""
    results = load_results(results_dir)
    by_case = group_by_case(results)

    report = {
        case_id: {
            "status": case_status(case_results),
            "tests": sorted(
                (
                    {"name": r.get("name", "?"), "status": r.get("status", "unknown")}
                    for r in case_results
                ),
                key=lambda t: t["name"],
            ),
        }
        for case_id, case_results in by_case.items()
    }

    totals = {
        "results": len(results),
        "untagged": sum(1 for r in results if not case_ids(r)),
        "cases": len(report),
    }
    for status in SEVERITY:
        totals[status] = sum(1 for c in report.values() if c["status"] == status)

    return report, totals


def render_markdown(report: dict[str, dict], totals: dict[str, int]) -> str:
    """Render the per-case table for a GitHub step summary / dashboard."""
    lines = ["## 🔗 TMS case results", ""]

    if not report:
        lines += [
            "_No TMS case ids found in this run's Allure results._",
            "",
            "Tests declare their case with `@pytest.mark.tms(\"ELITEA-1234\")` "
            "(see `automation/utils/tms_case_ids.py`).",
            "",
        ]
        return "\n".join(lines)

    covered = totals["cases"]
    lines += [
        "| Metric | Count |",
        "|--------|-------|",
        f"| TMS cases exercised | {covered} |",
        f"| ✅ Passed | {totals['passed']} |",
        f"| ❌ Failed | {totals['failed']} |",
        f"| 🔥 Broken | {totals['broken']} |",
        f"| ⏭️ Skipped | {totals['skipped']} |",
        "",
        "| Case | Result | Tests |",
        "|------|--------|-------|",
    ]

    # Failures first — the reason anyone opens this table.
    def sort_key(item: tuple[str, dict]) -> tuple[int, str]:
        case_id, case = item
        return SEVERITY.index(case["status"]), case_id

    for case_id, case in sorted(report.items(), key=sort_key):
        icon = STATUS_ICON.get(case["status"], "❓")
        tests = case["tests"]
        if len(tests) == 1:
            detail = f"`{tests[0]['name']}`"
        else:
            detail = ", ".join(
                f"{STATUS_ICON.get(t['status'], '❓')} `{t['name']}`" for t in tests
            )
        lines.append(f"| {case_id} | {icon} {case['status']} | {detail} |")

    lines += [
        "",
        f"_From {totals['results']} Allure results; "
        f"{totals['untagged']} not linked to a TMS case._",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "results_dir",
        type=Path,
        help="Allure results directory (or a parent holding several suites')",
    )
    parser.add_argument("--json", type=Path, help="also write the raw mapping here")
    args = parser.parse_args()

    if not args.results_dir.is_dir():
        print(f"warning: {args.results_dir} is not a directory", file=sys.stderr)
        print("## 🔗 TMS case results\n\n_No Allure results to read._\n")
        return 0

    report, totals = build_report(args.results_dir)
    print(render_markdown(report, totals))

    if args.json:
        args.json.write_text(
            json.dumps({"totals": totals, "cases": report}, indent=2) + "\n",
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
