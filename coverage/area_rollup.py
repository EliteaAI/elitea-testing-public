"""Roll up monocart per-file coverage into overall + per-feature-area numbers.

Run from repo root:  .venv/bin/python coverage/area_rollup.py
Reads:  coverage/report/coverage-summary.json  (written by `node coverage/report.mjs`)
        coverage/areas.json                    (path -> area map; first match wins)
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
SUMMARY = HERE / "report" / "coverage-summary.json"
AREAS_FILE = HERE / "areas.json"

if not SUMMARY.exists():
    sys.exit(f"Missing {SUMMARY} — run `node coverage/report.mjs` first")

AREAS = {k: v for k, v in json.loads(AREAS_FILE.read_text()).items() if not k.startswith("_")}
data = json.loads(SUMMARY.read_text())


def area_of(filepath: str) -> str:
    norm = filepath.replace("\\", "/")
    for area, prefixes in AREAS.items():  # dict preserves insertion order; 'shared' is last
        if any(p in norm for p in prefixes):
            return area
    return "other"


METRIC = "branches" if "--branches" in sys.argv else "statements"


def pick_metric(metrics: dict) -> tuple[int, int]:
    st = metrics.get(METRIC) or metrics.get("lines") or {}
    return st.get("covered", 0), st.get("total", 0)


buckets: dict[str, list[int]] = {}
per_file: dict[str, list[tuple[str, int, int]]] = {}
for fp, metrics in data.items():
    if fp == "total":
        continue
    cov, tot = pick_metric(metrics)
    area = area_of(fp)
    b = buckets.setdefault(area, [0, 0])
    b[0] += cov
    b[1] += tot
    per_file.setdefault(area, []).append((fp, cov, tot))

tot_c = sum(b[0] for b in buckets.values())
tot_t = sum(b[1] for b in buckets.values())
print(f"OVERALL  {tot_c}/{tot_t} {METRIC} = {100 * tot_c / max(tot_t, 1):.1f}%\n")
print(f"{'area':16}{'covered':>9}{'total':>9}{'%':>7}")
for a, (c, t) in sorted(buckets.items(), key=lambda x: -x[1][1]):
    print(f"{a:16}{c:>9}{t:>9}{100 * c / max(t, 1):>6.0f}%")

if "--files" in sys.argv:  # optional per-file detail: python coverage/area_rollup.py --files [area]
    want = next((a for a in sys.argv[2:] if not a.startswith("-")), None)
    print()
    for a, rows in sorted(per_file.items()):
        if want and a != want:
            continue
        print(f"\n[{a}]")
        for fp, c, t in sorted(rows, key=lambda r: -r[2]):
            print(f"  {100 * c / max(t, 1):>5.1f}%  {c:>5}/{t:<5}  {fp}")
