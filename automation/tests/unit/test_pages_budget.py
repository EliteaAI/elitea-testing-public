"""Unit tests for `scripts/pages_budget.py` — gh-pages per-file limit and site budget."""

import importlib.util
import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "pages_budget.py"
_spec = importlib.util.spec_from_file_location("pages_budget", SCRIPT)
budget_mod = importlib.util.module_from_spec(_spec)
sys.modules["pages_budget"] = budget_mod
_spec.loader.exec_module(budget_mod)

MB = budget_mod.MB


def _make_report(root: Path, label: str, published_at: int, videos: dict, run_url: str = "") -> Path:
    """Build a minimal Allure report dir: one test case per video, video attached in afterStages."""
    run_dir = root / label
    (run_dir / "data" / "attachments").mkdir(parents=True)
    (run_dir / "data" / "test-cases").mkdir(parents=True)
    (run_dir / "index.html").write_text("<html></html>")
    (run_dir / ".published-at").write_text(str(published_at))
    if run_url:
        (run_dir / ".run-url").write_text(run_url)
    for uid, size_mb in videos.items():
        (run_dir / "data" / "attachments" / f"{uid}.webm").write_bytes(b"\0" * int(size_mb * MB))
        case = {
            "uid": f"case-{uid}",
            "afterStages": [
                {
                    "name": "context::0",
                    "steps": [
                        {
                            "name": "Failure Evidence",
                            "attachments": [
                                {
                                    "uid": f"att-{uid}",
                                    "name": "Video recording",
                                    "source": f"{uid}.webm",
                                    "type": "video/webm",
                                    "size": int(size_mb * MB),
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        (run_dir / "data" / "test-cases" / f"case-{uid}.json").write_text(json.dumps(case))
    return run_dir


def _attachment(run_dir: Path, uid: str) -> dict:
    case = json.loads((run_dir / "data" / "test-cases" / f"case-{uid}.json").read_text())
    return case["afterStages"][0]["steps"][0]["attachments"][0]


def test_file_over_limit_is_dropped_and_repointed(tmp_path):
    run = _make_report(tmp_path, "dev/329", 2_000, {"big": 3, "small": 1}, run_url="https://gh/run/1")

    result = budget_mod.enforce(tmp_path, "dev/329", max_file_mb=2, budget_mb=100)

    assert not (run / "data" / "attachments" / "big.webm").exists()
    assert (run / "data" / "attachments" / "small.webm").exists()
    entry = _attachment(run, "big")
    assert entry["type"] == "text/plain"
    assert entry["source"] == "big-removed.txt"
    note = (run / "data" / "attachments" / "big-removed.txt").read_text()
    assert "https://gh/run/1" in note
    assert entry["size"] == len(note.encode())
    assert _attachment(run, "small")["source"] == "small.webm"
    assert [d[1] for d in result["dropped"]] == ["big.webm"]
    assert result["oversize"] == []


def test_budget_drops_oldest_run_first_and_current_run_last(tmp_path):
    old = _make_report(tmp_path, "dev-vm/9", 1_000, {"old_a": 2, "old_b": 1})
    mid = _make_report(tmp_path, "next/50", 2_000, {"mid_a": 2})
    cur = _make_report(tmp_path, "dev/329", 3_000, {"cur_a": 2})

    # 7 MB of video (+ a few KB of report files); budget 4.1 MB → drop old_a (2) + old_b (1), nothing else.
    result = budget_mod.enforce(tmp_path, "dev/329", max_file_mb=95, budget_mb=4.1)

    assert [d[1] for d in result["dropped"]] == ["old_a.webm", "old_b.webm"]
    assert (mid / "data" / "attachments" / "mid_a.webm").exists()
    assert (cur / "data" / "attachments" / "cur_a.webm").exists()
    assert not result["over_budget"]
    assert _attachment(old, "old_a")["type"] == "text/plain"


def test_current_run_goes_last_even_when_it_is_older(tmp_path):
    # A re-published old run number must not be pruned of videos before the others.
    cur = _make_report(tmp_path, "dev/329", 1_000, {"cur_a": 2})
    other = _make_report(tmp_path, "next/50", 2_000, {"other_a": 2})

    budget_mod.enforce(tmp_path, "dev/329", max_file_mb=95, budget_mb=3)

    assert not (other / "data" / "attachments" / "other_a.webm").exists()
    assert (cur / "data" / "attachments" / "cur_a.webm").exists()


def test_within_limits_is_a_no_op(tmp_path):
    run = _make_report(tmp_path, "dev/329", 1_000, {"a": 1})

    result = budget_mod.enforce(tmp_path, "dev/329", max_file_mb=95, budget_mb=100)

    assert result["dropped"] == []
    assert _attachment(run, "a")["source"] == "a.webm"


def test_git_dir_is_ignored(tmp_path):
    _make_report(tmp_path, "dev/329", 1_000, {"a": 1})
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "pack").write_bytes(b"\0" * (3 * MB))

    result = budget_mod.enforce(tmp_path, "dev/329", max_file_mb=2, budget_mb=100)

    assert result["dropped"] == []
    assert (tmp_path / ".git" / "pack").exists()


def test_main_exit_code_and_summary(tmp_path, capsys):
    _make_report(tmp_path, "dev/329", 1_000, {"big": 3})

    assert budget_mod.main([str(tmp_path), "--current", "dev/329", "--max-file-mb", "2"]) == 0

    out = capsys.readouterr()
    assert "dropped 1 attachment(s)" in out.out
    assert "`dev/329` big.webm" in out.out
    assert "::warning::1 attachment(s) of dev/329" in out.err
