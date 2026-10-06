#!/usr/bin/env python3
"""Write an authenticated Playwright storage state for the target env.

The factory analyses and builds tests against the DEV env (`ELITEA_URL` in
`.env.test`). Agents explore it through the Playwright MCP, which is started
with `--isolated --storage-state .playwright-mcp/dev-storage-state.json` —
this script produces that file via the same API (Keycloak) login the pytest
`auth_state` fixture uses, so agents never type credentials into a browser.

Keycloak sessions expire: run it at the start of every analyst / implementer
session, before the first browser call (the MCP reads the file when it
launches the browser, not when the server starts).

Prints only the output path, the cookie count and the origin — never cookie
values or credentials. The output directory is gitignored (`.playwright-mcp`).

Usage (from automation/):
    ../.venv/bin/python scripts/dev_storage_state.py [--out PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

AUTOMATION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTOMATION_ROOT.parent
DEFAULT_OUT = REPO_ROOT / ".playwright-mcp" / "dev-storage-state.json"

sys.path.insert(0, str(AUTOMATION_ROOT))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    from api_auth import get_playwright_storage_state
    from config import settings

    if "localhost" in settings.elitea_url or "127.0.0.1" in settings.elitea_url:
        print(
            f"ELITEA_URL points at {settings.elitea_url} — the factory targets the DEV env. "
            "Set ELITEA_URL / APP_PREFIX in automation/.env.test (see .env.test.example).",
            file=sys.stderr,
        )
        return 2

    state = get_playwright_storage_state(
        base_url=settings.elitea_auth_url,
        username=settings.test_user_email,
        password=settings.test_user_password,
    )
    if not state.get("cookies"):
        print("Login returned no cookies — check TEST_USER_EMAIL / TEST_USER_PASSWORD.", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    args.out.chmod(0o600)
    origins = ", ".join(o["origin"] for o in state.get("origins", [])) or "-"
    print(f"Wrote {args.out}  ({len(state['cookies'])} cookies, origin {origins}, app {settings.app_base_url})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
