#!/usr/bin/env python3
"""testid_coverage.py — map automation UI-test coverage via data-testids.

Compares the testids PRESENT in a React UI repo against the testids REFERENCED by
a Playwright/pytest automation repo, then reports:
  - binding health   (used testids that actually exist in the UI)
  - no-backing set   (used testids absent from the UI — classified)
  - orphans          (UI testids no test references)
  - dead fields      (page-object LocatorDescriptor fields no test method uses)
  - segmented coverage of interactive UI elements, by area and class

Stdlib only. Static analysis => interaction BREADTH, not flow/branch execution
(use runtime JS coverage for that). See SKILL.md for the method + caveats.

Usage:
  python3 testid_coverage.py --ui ../EliteaUI/src --auto automation [--out report.md]
"""
import re, glob, os, argparse, datetime

Q = "['\"]"
KEBAB = re.compile(r'^[a-z0-9]+(-[a-z0-9*]+)+$')          # section-element-type
TESTID_ATTR = re.compile(r'[Tt]est[Ii]d' + Q + r'?\s*[=:]')  # data-testid=, titleTestId=, 'data-testid':
HANDLER = re.compile(r'\bon[A-Z]\w+\s*=')
INTERACTIVE_TAGS = {
    'button','input','a','select','textarea','form','Button','IconButton','LoadingButton','TextField',
    'OutlinedInput','FilledInput','Input','InputBase','Select','NativeSelect','MenuItem','Checkbox','Switch',
    'Radio','Autocomplete','Link','Tab','ToggleButton','Slider','Fab','Chip','ListItemButton','Menu','Dialog','Modal'}
# testids that legitimately live OUTSIDE the UI repo (external pages, e.g. Keycloak login)
EXTERNAL = {'login-button', 'username', 'password', 'kc-login'}


def norm(t):
    t = re.sub(r'\$\{[^}]*\}', '*', t)   # ${expr} first
    t = re.sub(r'\{[^}]*\}', '*', t)     # {expr}
    return t


def _literals(expr):
    out = re.findall(r"'([^']+)'", expr) + re.findall(r'"([^"]+)"', expr)
    out += re.findall(r'`([^`]+)`', expr)  # template literals
    return out


def scan_open_tags(s):
    """Yield (tag, attr_window) for every JSX opening tag — brace/string aware, multiline."""
    i, n = 0, len(s)
    while i < n:
        if s[i] == '<' and i + 1 < n and s[i + 1].isalpha():
            m = re.match(r'<([A-Za-z][A-Za-z0-9.]*)', s[i:])
            if not m:
                i += 1; continue
            tag = m.group(1); j = i + m.end(); depth = 0; qc = None; w = []
            while j < n:
                c = s[j]
                if qc:
                    if c == qc: qc = None
                elif c in '"\'`': qc = c
                elif c in '{[(': depth += 1
                elif c in '}])': depth -= 1
                elif c == '>' and depth <= 0: break
                w.append(c); j += 1
            yield tag, ''.join(w); i = j + 1
        else:
            i += 1


def testids_in(window):
    """All normalized testid values inside a JSX attribute window (all forms)."""
    ids = set()
    for m in re.finditer(r'[Tt]est[Ii]d' + Q + r'?\s*[=:]\s*(' + Q + r')([^\'"]+)\1', window):
        ids.add(norm(m.group(2)))                       # attribute/object literal
    for m in re.finditer(r'[Tt]est[Ii]d' + Q + r'?\s*[=:]\s*\{(.*?)\}', window, re.DOTALL):
        for lit in _literals(m.group(1)):               # braced expr: ternary strings + templates
            ids.add(norm(lit))
    for m in re.finditer(r'[Tt]est[Ii]d' + Q + r'?\s*:\s*[^,}\n]*\?[^,}\n]*', window):
        for lit in _literals(m.group(0)):               # object-form ternary w/o braces
            ids.add(norm(lit))
    return {t for t in ids if KEBAB.match(t)}


def ui_files(ui_dirs):
    # ui_dirs: a single dir (str) or several (list) — e.g. ../EliteaUI/src plus connected repos
    # like ../elitea_assistant/src (Support Assistant). Union their .jsx/.tsx files.
    if isinstance(ui_dirs, str):
        ui_dirs = [ui_dirs]
    files = []
    for d in ui_dirs:
        files += [f for f in glob.glob(os.path.join(d, '**', '*.*'), recursive=True)
                  if f.endswith(('.jsx', '.tsx'))]
    return files


def extract_ui(ui_dir):
    present = set()
    for f in ui_files(ui_dir):
        try:
            s = open(f, encoding='utf-8').read()
        except Exception:
            continue
        present |= testids_in(s)          # whole-file pass catches non-JSX (helpers, object maps)
    return present


def extract_auto(auto_dir):
    """testids referenced by page objects + tests, and per-field usage for dead-field detection."""
    used = set()
    po_fields = {}     # fieldname -> testid (from page objects)
    field_used = set()  # fieldnames referenced (as .field) anywhere in tests
    po_files = glob.glob(os.path.join(auto_dir, 'pages', '**', '*.py'), recursive=True)
    test_files = glob.glob(os.path.join(auto_dir, 'tests', '**', '*.py'), recursive=True)
    for f in po_files + test_files:
        s = open(f, encoding='utf-8').read()
        for m in re.finditer(r'testid\s*=\s*f?(' + Q + r')([^\'"]+)\1', s):
            v = norm(m.group(2))
            if KEBAB.match(v): used.add(v)
    # page-object field -> testid (field name is the assignment target near a LocatorDescriptor)
    for f in po_files:
        lines = open(f, encoding='utf-8').read().splitlines()
        cur = None
        for ln in lines:
            fm = re.match(r'\s*([a-z_][a-z0-9_]*)\s*=\s*LocatorDescriptor\(', ln)
            if fm: cur = fm.group(1)
            tm = re.search(r'testid\s*=\s*(' + Q + r')([^\'"]+)\1', ln)
            if tm and cur:
                po_fields[cur] = tm.group(2); cur = None
    # a field is LIVE if referenced via .field anywhere in page objects (methods) OR tests —
    # the definition line uses `field =` (no dot), so it won't self-match.
    all_src = '\n'.join(open(f, encoding='utf-8').read() for f in po_files + test_files)
    for fld in po_fields:
        if re.search(r'\.' + re.escape(fld) + r'\b', all_src):
            field_used.add(fld)
    return used, po_fields, field_used


def classify(path):
    """(class, area). Admin here = platform/instance-admin ONLY (usually a separate app)."""
    q = path.lower()
    if 'icons/' in q or q.endswith('icon.jsx') or q.endswith('icon.tsx'):
        return ('PRESENTATIONAL', 'icons')
    if '/admin/' in q or 'admin-app' in q or 'adminconsole' in q:
        return ('ADMIN', 'admin')                       # platform admin (rare in a user app)
    rules = [
        ('agents', ('application', '/agent/', '/agents/')),
        ('skills', ('skill',)),
        ('chat', ('chat', 'newchat')),
        ('toolkits/mcp', ('toolkit', '/mcp', 'mcp/')),
        ('credentials', ('credential',)),
        ('pipelines', ('pipeline',)),
        ('artifacts', ('artifact',)),
        ('notifications', ('notification',)),
        ('onboarding', ('onboarding', 'userpublic')),
        ('settings', ('settings', 'user-settings', 'secret', 'token', 'ai-provider')),  # per-user config = user-facing
    ]
    for area, keys in rules:
        if any(k in q for k in keys):
            return ('FEATURE', area)
    if 'componentslib' in q or '/shared/' in q or '/components/' in q or 'formik' in q or 'datadisplay' in q:
        return ('SHARED-UI', 'shared')
    return ('OTHER', 'other')


def segment(ui_dir, used):
    from collections import defaultdict
    area = defaultdict(lambda: [0, 0, 0])   # interactive, instrumented, covered
    klass = defaultdict(lambda: [0, 0, 0])
    comp_files = routes = branches = defs = 0
    for f in ui_files(ui_dir):
        comp_files += 1
        try:
            s = open(f, encoding='utf-8').read()
        except Exception:
            continue
        defs += len(re.findall(r'(?:function\s+[A-Z]\w*\s*\(|const\s+[A-Z]\w*\s*=\s*(?:React\.)?(?:memo\()?\()', s))
        branches += len(re.findall(r'&&\s*[\(<]', s)) + len(re.findall(r'\?\s*[\(<]', s))
        routes += len(re.findall(r'<Route\b', s)) + len(re.findall(r"path:\s*" + Q, s))
        kl, ar = classify(f)
        for tag, w in scan_open_tags(s):
            if not (tag in INTERACTIVE_TAGS or HANDLER.search(w)):
                continue
            tids = testids_in(w)
            for D in (area[ar], klass[kl]):
                D[0] += 1
                if tids: D[1] += 1
                if tids & used: D[2] += 1
    return dict(area), dict(klass), dict(files=comp_files, defs=defs, routes=routes, branches=branches)


def pct(a, b):
    return f"{a / b * 100:.1f}%" if b else "n/a"


def build_report(ui_dir, auto_dir):
    present = extract_ui(ui_dir)
    used, po_fields, field_used = extract_auto(auto_dir)
    matched = used & present
    no_backing = sorted(used - present)
    orphans = sorted(present - used)
    dead = sorted(f for f in po_fields if f not in field_used)
    area, klass, dims = segment(ui_dir, used)
    today = os.environ.get('REPORT_DATE', datetime.date.today().isoformat())

    L = []
    w = L.append
    w(f"# UI test-automation coverage — testid map\n")
    w(f"_Generated {today}. UI: `{', '.join(ui_dir) if isinstance(ui_dir, list) else ui_dir}` · Automation: `{auto_dir}`. "
      f"Method: static testid cross-reference — measures interaction **breadth**, not flow/branch execution._\n")
    w("## Summary\n")
    w("| Metric | Value |")
    w("|---|--:|")
    w(f"| testids present in UI (normalized) | {len(present)} |")
    w(f"| testids referenced by automation | {len(used)} |")
    w(f"| matched (binding health) | {len(matched)} = {pct(len(matched), len(used))} of referenced |")
    w(f"| referenced but not in UI (no-backing) | {len(no_backing)} |")
    w(f"| orphan UI testids (present, unused) | {len(orphans)} |")
    w(f"| dead page-object fields (no test uses them) | {len(dead)} |")
    w("")
    w("## Interactive-element coverage (breadth)\n")
    w(f"Denominators — component files: {dims['files']} · component defs: {dims['defs']} · "
      f"routes: {dims['routes']} · conditional branches: {dims['branches']}\n")
    w("### By class\n| Class | Interactive | Instrumented | Covered | Coverage |")
    w("|---|--:|--:|--:|--:|")
    for k in sorted(klass, key=lambda x: -klass[x][0]):
        i, ins, c = klass[k]
        w(f"| {k} | {i} | {ins} | {c} | {pct(c, i)} |")
    w("\n> **User-facing coverage** = the FEATURE row. Shared-UI is exercised *indirectly*; "
      "presentational (icons) & infra are excluded from the meaningful denominator. "
      "Platform/instance ADMIN, if any, is a separate app — track separately.\n")
    w("### By area (user-facing features)\n| Area | Interactive | Instrumented | Covered | Coverage |")
    w("|---|--:|--:|--:|--:|")
    for a in sorted(area, key=lambda x: -area[x][0]):
        i, ins, c = area[a]
        w(f"| {a} | {i} | {ins} | {c} | {pct(c, i)} |")
    w("")
    w("## No-backing testids (referenced by automation, absent from UI)\n")
    w("Classify each before acting — most are NOT real bugs:\n")
    w("- **dynamic template** (UI renders `x-${k}`, test uses concrete `x-foo`) → normalize mismatch, actually covered.")
    w("- **external page** (e.g. `login-button` on Keycloak) → legitimately outside this UI repo.")
    w("- **dead page-object field** (see below) → inert, never resolved.")
    w("- **genuine** → broken locator: test would fail if the field were exercised. Confirm at runtime.\n")
    ext = [t for t in no_backing if t in EXTERNAL]
    rest = [t for t in no_backing if t not in EXTERNAL]
    if ext:
        w(f"External (expected): {', '.join(f'`{t}`' for t in ext)}\n")
    w("Remaining (investigate):\n")
    for t in rest:
        w(f"- `{t}`")
    w("")
    w("## Dead page-object fields (no test references them)\n")
    w("`LocatorDescriptor` fields defined in page objects that no test method uses. "
      "Inert (never resolved, never fail) but they're cruft and can mask missing testids.\n")
    for f in dead:
        w(f"- `{f}` → testid `{po_fields[f]}`" + (" *(also absent in UI)*" if norm(po_fields[f]) not in present else ""))
    w("")
    w("## Orphan UI testids (present, unreferenced)\n")
    for t in orphans:
        w(f"- `{t}`")
    w("")
    w("## Caveats\n")
    w("- **Breadth, not execution.** A testid means a test *can reach* a control, not which of the "
      f"{dims['branches']} branches / {dims['routes']} routes actually ran. Use runtime JS coverage "
      "(Playwright `page.coverage` / Istanbul) for flow/branch depth.")
    w("- **Interactive denominator undercounts** custom wrappers (handler passed as a prop), so absolute "
      "%s are order-of-magnitude; the *relative* per-area ranking is reliable.")
    w("- **Normalization** collapses `${..}`/`{..}` → `*`; concrete-vs-template can still mismatch — verify "
      "no-backing entries against the live UI before calling them gaps.")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ui', required=True, nargs='+',
                    help='UI src dir(s) — e.g. ../EliteaUI/src ../elitea_assistant/src (connected repos)')
    ap.add_argument('--auto', required=True, help='automation repo root (with pages/ and tests/)')
    ap.add_argument('--out', help='write markdown report here (else stdout)')
    a = ap.parse_args()
    md = build_report(a.ui, a.auto)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        open(a.out, 'w').write(md)
        print(f"wrote {a.out} ({len(md)} bytes)")
    else:
        print(md)


if __name__ == '__main__':
    main()
