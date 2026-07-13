#!/usr/bin/env python3
"""Fail if any real secret value from .env.test / .env appears in staged files.

This repo is PUBLIC and .env.test holds a live API token, a test-user password, a
GitHub PAT and a Jira key. An agent memory or a test spec can quote one by accident.

Usage:
    python3 scripts/scan-secrets.py            # scan staged files (pre-push check)
    python3 scripts/scan-secrets.py --all      # scan every tracked file
    python3 scripts/scan-secrets.py --selftest # prove the scanner actually catches a leak

Exit 0 = clean, 1 = leak found (or selftest failed).
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

# Keys whose VALUES are secret. Public URLs (ELITEA_URL, VITE_DEV_SERVER) are not.
SENSITIVE = ("PASSWORD", "TOKEN", "API_KEY", "SECRET", "EMAIL", "USERNAME")
MIN_LEN = 6  # shorter values produce false positives


def repo_root() -> Path:
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True, check=True)
    return Path(out.stdout.strip())


def load_secrets(root: Path) -> list[tuple[str, str]]:
    """Collect (key, value) pairs worth protecting from the env files."""
    secrets: list[tuple[str, str]] = []
    for name in ("automation/.env.test", "../.env", "../.env.test"):
        f = root / name
        if not f.exists():
            continue
        for line in f.read_text(errors="ignore").splitlines():
            m = re.match(r"^([A-Z0-9_]+)\s*=\s*(.*)$", line.strip())
            if not m:
                continue
            key, val = m.group(1), m.group(2).strip().strip("\"'")
            if any(s in key for s in SENSITIVE) and len(val) >= MIN_LEN:
                secrets.append((key, val))
    return secrets


def files_to_scan(root: Path, scan_all: bool) -> list[Path]:
    args = (["git", "ls-files"] if scan_all
            else ["git", "diff", "--cached", "--name-only"])
    out = subprocess.run(args, capture_output=True, text=True, check=True)
    return [root / p for p in out.stdout.split("\n") if p.strip()]


def scan(files, secrets) -> list[str]:
    leaks = []
    for f in files:
        if not f.is_file():
            continue
        try:
            text = f.read_text(errors="ignore")
        except OSError:
            continue
        for key, val in secrets:
            if val in text:
                leaks.append(f"{key} in {f}")
    return leaks


def selftest(root: Path, secrets) -> int:
    """Plant a real secret in a temp file and confirm the scanner finds it."""
    if not secrets:
        print("SELFTEST FAILED: no secrets loaded — scanner would pass everything")
        return 1
    key, val = secrets[0]
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
        fh.write(f"accidentally pasted: {val}\n")
        canary = Path(fh.name)
    try:
        found = scan([canary], secrets)
        if found:
            print(f"SELFTEST PASSED: scanner caught the planted {key}")
            return 0
        print(f"SELFTEST FAILED: scanner MISSED a planted {key} — do not trust it")
        return 1
    finally:
        canary.unlink(missing_ok=True)


def main() -> int:
    root = repo_root()
    secrets = load_secrets(root)

    if "--selftest" in sys.argv:
        return selftest(root, secrets)

    if not secrets:
        print("WARNING: no secret values loaded from .env.test — scan is vacuous")
        return 1

    leaks = scan(files_to_scan(root, "--all" in sys.argv), secrets)
    if leaks:
        print("SECRET LEAK — DO NOT PUSH (this repo is public):")
        for leak in leaks:
            print(f"  {leak}")
        return 1

    scope = "tracked" if "--all" in sys.argv else "staged"
    print(f"clean — no secret values in {scope} files "
          f"(checked {len(secrets)} keys)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
