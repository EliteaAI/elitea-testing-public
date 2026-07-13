#!/usr/bin/env python3
"""Fetch the LIVE ELITEA OpenAPI spec — the ground truth for what endpoints exist.

The bundled `references/openapi-spec.json` is a snapshot and goes stale. This
pulls the current one straight off the platform.

TWO SURFACES — `?all=true` is the flag that matters:

    /shared/openapi/              ->  81 paths  (project/user surface)
    /shared/openapi/?all=true     -> 133 paths  (adds /api/v2/admin/*, support_assistant,
                                                 projects/groups+monitoring, vectorstore,
                                                 the task DELETE, and the 2.0.4 draft generators)

The 81-path view is a strict SUBSET of the 133. This script uses `?all=true` by
default — pass `--user-surface` for the reduced view.

    /shared/openapi/  -> raw JSON  (what this script parses)
    /shared/swagger/  -> the Swagger UI for the same spec (browse it in a browser);
                         takes the same ?all=true flag

`?full=true` is a NO-OP — it returns byte-identical output to the bare path.
It's `?all=true` you want.

HOSTS: works on both `next.elitea.ai` and `dev.elitea.ai`, but each needs ITS OWN
PAT — a next token gets a 302 (login redirect) on dev. Use --base-url for dev.

AUTH: bearer token required; unauthenticated -> 302.

IMPORTANT — even the 133-path spec is authoritative but NOT complete. Known false
negatives (work in production, not declared anywhere in the spec; verified 2026-07-13):

    GET   /api/v2/elitea_core/application_task/{mode}/{pid}/{task_id}          (async-predict poll)
    GET   /api/v2/elitea_core/application/{mode}/{pid}/{app_id}/{version_name} (get version by name)
    PATCH /api/v2/elitea_core/skill/{mode}/{pid}/{skill_id}                    (attach skill to agent)

...and at least one false POSITIVE: the spec declares
`PATCH /skill/{mode}/{pid}/{skill_id}/{version_id}`, which the server REJECTS with
`400 "version_id path segment is not supported for PATCH"`.

So "absent from the spec" is evidence, not proof, that a route is dead. To tell a
missing route from a working-but-undeclared one, call it and compare the failure
against a deliberately bogus path (e.g. /api/v2/elitea_core/totally_bogus_route):
a missing route returns the generic 404 body; a real handler returns something
specific (a 400/500 with a message).

Also check the {mode} segment before declaring something dead — admin-scoped routes
(e.g. vectorstore) live under mode=administration and 404 on prompt_lib/default.

Usage:
    python3 fetch_openapi_spec.py                    # summarize the live spec (133 paths)
    python3 fetch_openapi_spec.py --user-surface     # the reduced 81-path view
    python3 fetch_openapi_spec.py --paths            # list every path
    python3 fetch_openapi_spec.py --grep skill       # paths matching a substring
    python3 fetch_openapi_spec.py --diff             # diff live vs the bundled snapshot
    python3 fetch_openapi_spec.py --update           # overwrite the bundled snapshot
    python3 fetch_openapi_spec.py --show /api/v2/elitea_core/skills/{mode}/{project_id}
    python3 fetch_openapi_spec.py --base-url https://dev.elitea.ai   # needs a DEV token
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

DEFAULT_BASE_URL = "https://next.elitea.ai"
SPEC_PATH = "/shared/openapi/"          # + ?all=true for the full 133-path surface
SNAPSHOT = Path(__file__).resolve().parent.parent / "references" / "openapi-spec.json"


def load_token() -> str:
    for var in ("ELITEA_TOKEN", "ELITEA_API_TOKEN", "ELITEA_NEXT_API_KEY"):
        if os.environ.get(var):
            return os.environ[var]
    # walk up to the nearest .git and read .env
    here = Path.cwd().resolve()
    for d in [here, *here.parents]:
        env = d / ".env"
        if env.is_file():
            for line in env.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                if k.strip() in ("ELITEA_TOKEN", "ELITEA_API_TOKEN", "ELITEA_NEXT_API_KEY"):
                    return v.strip().strip('"').strip("'")
        if (d / ".git").exists():
            break
    sys.exit("No token. Set ELITEA_TOKEN or add it to .env (see .env.example).")


def fetch(base_url: str, full_surface: bool = True) -> dict:
    url = base_url.rstrip("/") + SPEC_PATH + ("?all=true" if full_surface else "")
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {load_token()}",
        "Accept": "application/json",   # never Content-Type on a GET — proxies 400 it
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            if r.status != 200:
                sys.exit(f"GET {url} → {r.status}")
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 401, 403):
            sys.exit(
                f"GET {url} → {e.code}. The spec needs a bearer token for THIS host.\n"
                f"Each environment has its own PAT — a next.elitea.ai token will not "
                f"authenticate against dev.elitea.ai (and vice versa)."
            )
        raise


def summarize(spec: dict, full_surface: bool) -> None:
    paths = spec.get("paths", {})
    v1 = [p for p in paths if "/api/v1/" in p]
    print(f"{spec['info']['title']} v{spec['info']['version']} (OpenAPI {spec['openapi']})")
    print(f"  surface: {'FULL (?all=true)' if full_surface else 'user (reduced)'}")
    print(f"  paths : {len(paths)}")
    print(f"  v1    : {len(v1)}  {'← v1 is retired; any hit here is a surprise' if v1 else '(as expected — v1 is gone)'}")
    print(f"  tags  : {len(spec.get('tags', []))}")
    groups: dict[str, int] = {}
    for p in paths:
        parts = [x for x in p.split("/") if x and not x.startswith("{")]
        key = "/".join(parts[:3]) if len(parts) >= 3 else "/".join(parts)
        groups[key] = groups.get(key, 0) + 1
    print("\n  by group:")
    for k, n in sorted(groups.items(), key=lambda kv: -kv[1]):
        print(f"    {n:3}  {k}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL,
                    help="e.g. https://dev.elitea.ai — needs that host's OWN PAT")
    ap.add_argument("--user-surface", action="store_true",
                    help="reduced 81-path view (omit ?all=true); default is the full 133-path surface")
    ap.add_argument("--paths", action="store_true", help="list every path")
    ap.add_argument("--grep", metavar="SUBSTR", help="list paths containing SUBSTR")
    ap.add_argument("--show", metavar="PATH", help="dump the spec for one path")
    ap.add_argument("--diff", action="store_true", help="diff live vs bundled snapshot")
    ap.add_argument("--update", action="store_true", help="overwrite the bundled snapshot")
    args = ap.parse_args()

    full = not args.user_surface
    spec = fetch(args.base_url, full_surface=full)
    paths = spec.get("paths", {})

    if args.grep:
        hits = sorted(p for p in paths if args.grep.lower() in p.lower())
        for p in hits:
            print(f"{','.join(m.upper() for m in paths[p]):<28} {p}")
        print(f"\n{len(hits)} match(es)", file=sys.stderr)
        return

    if args.show:
        if args.show not in paths:
            near = [p for p in paths if args.show.strip("/").split("/")[-1] in p]
            sys.exit(f"not in spec: {args.show}" + (f"\ndid you mean:\n  " + "\n  ".join(near) if near else ""))
        print(json.dumps(paths[args.show], indent=2))
        return

    if args.paths:
        for p in sorted(paths):
            print(f"{','.join(m.upper() for m in paths[p]):<28} {p}")
        return

    if args.diff or args.update:
        snap = json.loads(SNAPSHOT.read_text())
        lp, sp = set(paths), set(snap.get("paths", {}))
        print(f"live: {len(lp)} paths   snapshot: {len(sp)} paths")
        for p in sorted(lp - sp):
            print(f"  + {p}")
        for p in sorted(sp - lp):
            print(f"  - {p}")
        if not (lp ^ sp):
            print("  (identical path sets)")
        if args.update:
            if not full:
                sys.exit("\nrefusing to write a reduced snapshot — drop --user-surface")
            SNAPSHOT.write_text(json.dumps(spec, separators=(", ", ": ")))
            print(f"\nwrote {SNAPSHOT} ({len(paths)} paths)")
        return

    summarize(spec, full)


if __name__ == "__main__":
    main()
