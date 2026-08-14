#!/usr/bin/env python3
"""embed_evidence.py — self-healing screenshot-evidence sweep (token-free).

Scans OPEN `question`/`bug` issues for screenshots referenced by a local path or
bare filename (the #51/#526/#595 anti-pattern), uploads each file that exists on
disk to the flat `evidence` prerelease store, and rewrites the issue body to embed
the image inline — leaving the original local path in place as accompaniment.

Zero LLM. Only DIRTY issues are written; clean issues cost one bulk read and
nothing else. Referenced files NOT found on disk are reported for human/agent
follow-up (they can't be auto-uploaded).

Run daily (cron / scheduled workflow):
    python3 embed_evidence.py --repo EliteaAI/elitea-testing-public
Dry run (no writes):
    python3 embed_evidence.py --dry-run

Requires: `gh` authenticated as the keyring account (script clears GITHUB_TOKEN,
matching the identity rule).
"""
import argparse, json, os, re, subprocess, sys

REPO_DEFAULT = "EliteaAI/elitea-testing-public"
# where screenshots may live on disk, searched in order
SEARCH_DIRS = [".playwright-mcp", "test-results/screenshots", "automation/screenshots", "."]
PNG_RE = re.compile(r'([A-Za-z0-9_./-]+\.png)', re.I)


def gh(args, repo, capture=True):
    env = {**os.environ}
    env.pop("GITHUB_TOKEN", None)  # identity rule: keyring account, not shared token
    return subprocess.run(["gh", *args], env=env, capture_output=capture, text=True)


def base_url(repo):
    return f"https://github.com/{repo}/releases/download/evidence/"


def ensure_release(repo, dry):
    r = gh(["release", "view", "evidence", "--repo", repo, "--json", "tagName"], repo)
    if r.returncode == 0:
        return True
    print("evidence release missing — creating" + (" (dry-run: skipped)" if dry else ""))
    if not dry:
        gh(["release", "create", "evidence", "--prerelease", "--title", "Evidence store",
            "--notes", "Flat store for screenshot evidence embedded in issues.", "--repo", repo], repo)
    return not dry


def find_on_disk(basename, root):
    for d in SEARCH_DIRS:
        p = os.path.join(root, d, basename)
        if os.path.isfile(p):
            return p
    # last resort: recursive (bounded)
    for dirpath, _, files in os.walk(root):
        if any(seg in dirpath for seg in ("node_modules", ".venv", ".git")):
            continue
        if basename in files:
            return os.path.join(dirpath, basename)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO_DEFAULT)
    ap.add_argument("--root", default=".", help="work-repo root where screenshots live")
    ap.add_argument("--labels", default="question,bug")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    BASE = base_url(a.repo)

    # one bulk read per label (cheap); union by number
    issues = {}
    for lbl in a.labels.split(","):
        r = gh(["issue", "list", "--repo", a.repo, "--state", "open", "--label", lbl.strip(),
                "--limit", "800", "--json", "number,body,title"], a.repo)
        if r.returncode != 0:
            print(f"WARN: could not list label {lbl}: {r.stderr[:120]}", file=sys.stderr); continue
        for i in json.loads(r.stdout):
            issues[i["number"]] = i

    dirty = missing = clean = 0
    missing_report = []
    have_release = None

    for n in sorted(issues):
        body = issues[n]["body"] or ""
        # candidate png tokens NOT already embedded via the evidence store
        tokens, seen = [], set()
        for tok in PNG_RE.findall(body):
            b = os.path.basename(tok)
            already = f"releases/download/evidence/{b}" in body
            if not already and b not in seen:
                seen.add(b); tokens.append((tok, b))
        if not tokens:
            clean += 1; continue

        # resolve each on disk; build inline embeds
        lines = body.split("\n"); out = []
        embedded_here = []
        for line in lines:
            out.append(line)
            for tok in PNG_RE.findall(line):
                b = os.path.basename(tok)
                if f"releases/download/evidence/{b}" in body:  # already embedded elsewhere
                    continue
                path = find_on_disk(b, a.root)
                if not path:
                    if b not in [m[1] for m in missing_report]:
                        missing_report.append((n, b)); missing += 1
                    continue
                if have_release is None:
                    have_release = ensure_release(a.repo, a.dry_run)
                if not a.dry_run and have_release:
                    up = gh(["release", "upload", "evidence", path, "--clobber", "--repo", a.repo], a.repo)
                    if up.returncode != 0:
                        print(f"  #{n}: upload {b} FAILED: {up.stderr[:100]}", file=sys.stderr); continue
                alt = b[:-4].replace("-", " ")
                out.append(f"  ![{alt}]({BASE}{b})")
                embedded_here.append(b)
        if not embedded_here:
            continue
        newbody = "\n".join(out)
        dirty += 1
        if a.dry_run:
            print(f"  #{n}: WOULD embed {len(embedded_here)}: {', '.join(embedded_here)}")
            continue
        with open(f"/tmp/_evbody_{n}.md", "w") as fh:
            fh.write(newbody)
        ed = gh(["issue", "edit", str(n), "--repo", a.repo, "--body-file", f"/tmp/_evbody_{n}.md"], a.repo)
        print(f"  #{n}: {'embedded '+str(len(embedded_here)) if ed.returncode==0 else 'EDIT FAILED: '+ed.stderr[:100]}")

    print(f"\nscanned {len(issues)} {a.labels} issues | clean {clean} | "
          f"{'would-fix' if a.dry_run else 'fixed'} {dirty} | files-missing-on-disk {missing}")
    if missing_report:
        print("MISSING (referenced but not on disk — needs re-capture or human upload):")
        for n, b in missing_report:
            print(f"  #{n}  {b}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
