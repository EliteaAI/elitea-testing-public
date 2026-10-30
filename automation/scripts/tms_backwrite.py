#!/usr/bin/env python3
"""Validate UI tests' TMS links and back-write the TMS case files they cover.

Every case-derived UI test declares its TMS case twice, and the two must agree:

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-0679_image-creation-internal-tool-happy-path.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.tms("ELITEA-0679")

Parametrized tests follow the toolkit pattern
(``tests/ui/toolkits/test_toolkit_parameterized.py``): one ``@allure.issue`` per case
on the function, ``pytest.param(..., marks=[pytest.mark.tms(<id>)])`` per parameter.

``check`` fails (exit 1) on any of:
  * a test with a TMS link but no ``tms`` marker, or a ``tms`` marker but no link
  * a parameter whose ``tms`` id has no link on its test
  * a test function linking a case none of its parameters declare
  * a link that is not a ``blob/main/...md`` case-file link, or whose file is missing
  * a linked file whose front-matter ``id:`` differs from the id in its file name
  * one case id linked to two different files
  * a linked case that is ``status: deprecated``

``apply`` runs ``check`` first and writes nothing if it fails. Otherwise, for every
linked case it sets ``execution_type: automated``, ``status: ready`` and
``automation_test_id`` (the Form C ids of every test declaring the case — UI refs are
replaced, other refs such as ``tests.api.*`` are kept), and sets ``automation_pr`` to
``--commit-url`` when the case was flipped or its UI refs changed. Cases whose UI refs
point at tests that no longer declare them are reported, never reverted.

Run from automation/ (needs pytest.ini + conftest.py). The TMS checkout must be at the
revision you mean to validate against — in CI a fresh clone of TMS ``main``:
    python scripts/tms_backwrite.py check --tms-root ../../onetest-ai-tm-Elitea
    python scripts/tms_backwrite.py apply --tms-root ../../onetest-ai-tm-Elitea \\
        --commit-url https://github.com/EliteaAI/elitea-testing-public/commit/<sha>
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

CASE_FILE_URL = 'https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/'
CASE_ID = re.compile(r'^ELITEA-\d+$')
FILE_CASE_ID = re.compile(r'^(ELITEA-\d+)')

# automation_test_id refs this script owns: Form C UI refs, plus the two drifted
# forms (node-id, automation.-prefixed) that the canon says to fix on sight.
UI_REF_PREFIXES = ('tests.ui.', 'automation.tests.ui.', 'automation/tests/ui/', 'tests/ui/')


def load_index(path):
    if path:
        with open(path, encoding='utf-8') as f:
            return json.load(f)['tests']
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_test_index import collect
    return collect('tests/ui')


# --- front matter --------------------------------------------------------------

class CaseFile:
    """Line-level editor for a TMS case file's front matter.

    Edits only the keys it is asked to set, leaving every other line byte-for-byte
    intact — the TMS repo's own parser (``onetest-tms/scripts/_tc.py``) is line based.
    """

    def __init__(self, path):
        self.path = path
        self.lines = path.read_text(encoding='utf-8').split('\n')
        if not self.lines or self.lines[0].strip() != '---':
            raise ValueError('no front matter')
        self.end = next((i for i in range(1, len(self.lines)) if self.lines[i].strip() == '---'), None)
        if self.end is None:
            raise ValueError('unterminated front matter')
        self.changed = False

    def _span(self, key):
        """(start, stop) of ``key``'s line plus its indented / list continuation lines."""
        for i in range(1, self.end):
            if re.match(rf'^{re.escape(key)}\s*:', self.lines[i]):
                stop = i + 1
                while stop < self.end and self.lines[stop].startswith((' ', '\t', '-')):
                    stop += 1
                return i, stop
        return None

    def get(self, key):
        span = self._span(key)
        if not span:
            return None
        return _unquote(self.lines[span[0]].split(':', 1)[1].split(' #', 1)[0].strip())

    def get_list(self, key):
        span = self._span(key)
        if not span:
            return []
        value = self.lines[span[0]].split(':', 1)[1].strip()
        if value.startswith('['):
            inner = value[1:value.rindex(']')] if ']' in value else value[1:]
            return [_unquote(v.strip()) for v in inner.split(',') if v.strip()]
        if value:
            return [_unquote(value)]
        return [
            _unquote(ln.strip()[2:].strip())
            for ln in self.lines[span[0] + 1:span[1]]
            if ln.strip().startswith('- ')
        ]

    def set(self, key, rendered, after):
        """Replace ``key`` with ``rendered`` lines, or insert it after the first present key in ``after``."""
        span = self._span(key)
        if span:
            if self.lines[span[0]:span[1]] == rendered:
                return
            self.lines[span[0]:span[1]] = rendered
        else:
            anchor = next((s for s in (self._span(k) for k in after) if s), None)
            at = anchor[1] if anchor else self.end
            self.lines[at:at] = rendered
        self.end = next(i for i in range(1, len(self.lines)) if self.lines[i].strip() == '---')
        self.changed = True

    def save(self):
        if self.changed:
            self.path.write_text('\n'.join(self.lines), encoding='utf-8')


def _unquote(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
        return value[1:-1]
    return value


def _yaml_item(value):
    # Plain scalars cover every Form C ref seen so far ("[param]" included); quote
    # only what YAML would misread.
    if re.search(r'(: | #|^[\s\'"&*!|>%@`{]|\s$)', value):
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return value


def is_ui_ref(ref):
    return ref.startswith(UI_REF_PREFIXES)


# --- check -----------------------------------------------------------------------

def check(tests, tms_root):
    """Validate the index. Returns (errors, case_paths, case_tests).

    case_paths: case id -> TMS-relative path (from the links)
    case_tests: case id -> sorted Form C ids of the tests declaring it
    """
    errors = []
    case_paths = {}
    case_tests = {}
    functions = {}
    file_ids = {}

    def linked_id(test_id, url):
        if not url.startswith(CASE_FILE_URL) or not url.endswith('.md'):
            errors.append(f'{test_id}: TMS link is not a blob/main case-file link: {url}')
            return None
        rel = url[len(CASE_FILE_URL):]
        if rel not in file_ids:
            path = tms_root / rel
            if not path.is_file():
                errors.append(f'{test_id}: linked case file does not exist on TMS main: {rel}')
                file_ids[rel] = None
            else:
                try:
                    case = CaseFile(path)
                except ValueError as e:
                    errors.append(f'{test_id}: linked case file {rel}: {e}')
                    file_ids[rel] = None
                else:
                    fm_id = case.get('id')
                    name = FILE_CASE_ID.match(path.name)
                    if not name or fm_id != name.group(1):
                        errors.append(
                            f'{test_id}: linked case file {rel} has front-matter id {fm_id!r}, '
                            f'file name says {name.group(1) if name else None!r}'
                        )
                        file_ids[rel] = None
                    elif case.get('status') == 'deprecated':
                        errors.append(f'{test_id}: linked case {fm_id} ({rel}) is status: deprecated')
                        file_ids[rel] = None
                    else:
                        file_ids[rel] = fm_id
        case_id = file_ids[rel]
        if case_id:
            other = case_paths.setdefault(case_id, rel)
            if other != rel:
                errors.append(f'{test_id}: {case_id} is linked to two files: {other} and {rel}')
        return case_id

    for test in tests:
        test_id = test['automation_test_id']
        ids = set(test.get('tms_case_ids', []))
        links = test.get('tms_case_links', [])
        for case_id in sorted(ids):
            if not CASE_ID.match(case_id):
                errors.append(f'{test_id}: malformed tms id {case_id!r}')
        if ids and not links:
            errors.append(f'{test_id}: has @pytest.mark.tms{tuple(sorted(ids))} but no TMS @allure.issue link')
        if links and not ids:
            errors.append(f'{test_id}: has a TMS @allure.issue link but no @pytest.mark.tms')
        linked = {cid for cid in (linked_id(test_id, url) for url in links) if cid}
        broken_link = len(linked) < len(links)
        if ids and links and not broken_link and not ids <= linked:
            errors.append(
                f'{test_id}: tms {sorted(ids - linked)} has no @allure.issue link (links: {sorted(linked)})'
            )
        fn = functions.setdefault(test_id.split('[', 1)[0], [set(), set(), broken_link])
        fn[0] |= ids
        fn[1] |= linked
        fn[2] = fn[2] or broken_link
        for case_id in ids:
            case_tests.setdefault(case_id, set()).add(test_id)

    for fn_id, (ids, linked, broken_link) in sorted(functions.items()):
        if ids and not broken_link and not linked <= ids:
            errors.append(f'{fn_id}: links {sorted(linked - ids)} but no test of it declares that tms id')

    return errors, case_paths, {k: sorted(v) for k, v in case_tests.items()}


# --- apply -----------------------------------------------------------------------

def apply(case_paths, case_tests, tms_root, commit_url, dry_run):
    """Back-write every linked case. Returns the list of change descriptions."""
    changes = []
    for case_id in sorted(case_paths):
        rel = case_paths[case_id]
        case = CaseFile(tms_root / rel)
        notes = []

        flipped = False
        for key, value, after in (
            ('status', 'ready', ('id',)),
            ('execution_type', 'automated', ('status', 'id')),
        ):
            current = case.get(key)
            if current != value:
                case.set(key, [f'{key}: {value}'], after)
                notes.append(f'{key}: {current} → {value}')
                flipped = True

        existing = case.get_list('automation_test_id')
        new_ui = case_tests[case_id]
        added = [r for r in new_ui if r not in existing]
        removed = [r for r in existing if is_ui_ref(r) and r not in new_ui]
        if added or removed:
            # Keep surviving refs where they are (no churn from re-sorting), append new ones.
            refs = [r for r in dict.fromkeys(existing) if r not in removed] + added
            case.set(
                'automation_test_id',
                ['automation_test_id:'] + [f'  - {_yaml_item(r)}' for r in refs],
                ('execution_type', 'status', 'id'),
            )
            notes.append(f'automation_test_id: +{len(added)} −{len(removed)}')

        # automation_pr names the commit that automated the case — a pure ref removal is not it.
        if (flipped or added) and commit_url and case.get('automation_pr') != commit_url:
            case.set('automation_pr', [f'automation_pr: {commit_url}'], ('automation_test_id', 'execution_type'))
            notes.append('automation_pr → this commit')

        if case.changed:
            changes.append(f'{case_id} ({rel}): ' + '; '.join(notes))
            if not dry_run:
                case.save()
    return changes


def retirements(case_paths, tests, tms_root):
    """Case files listing UI refs that no test declares for them — reported, never reverted."""
    declared = {(cid, t['automation_test_id']) for t in tests for cid in t.get('tms_case_ids', [])}
    found = []
    for path in sorted((tms_root / 'tests').rglob('*.md')):
        rel = path.relative_to(tms_root).as_posix()
        name = FILE_CASE_ID.match(path.name)
        if not name or case_paths.get(name.group(1), rel) != rel:
            continue
        try:
            refs = CaseFile(path).get_list('automation_test_id')
        except ValueError:
            continue
        stale = [r for r in refs if is_ui_ref(r) and (name.group(1), r) not in declared]
        if stale and name.group(1) not in case_paths:
            found.append(f'{name.group(1)} ({rel}): {len(stale)} UI ref(s) no test declares — e.g. {stale[0]}')
    return found


def report(title, lines):
    out = [f'### {title} ({len(lines)})', ''] + [f'- {ln}' for ln in lines] + ['']
    print('\n'.join(out))
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as f:
            f.write('\n'.join(out) + '\n')


def main():
    parser = argparse.ArgumentParser(description='Validate UI tests\' TMS links and back-write TMS case files')
    parser.add_argument('command', choices=('check', 'apply'))
    parser.add_argument('--tms-root', required=True, type=Path, help='TMS repo checkout (onetest-ai-tm-Elitea)')
    parser.add_argument('--index', help='index.json from build_test_index.py (default: collect tests/ui now)')
    parser.add_argument('--commit-url', help='apply: landed commit URL written to automation_pr')
    parser.add_argument('--dry-run', action='store_true', help='apply: report changes, write nothing')
    args = parser.parse_args()

    if args.command == 'apply' and not args.commit_url and not args.dry_run:
        parser.error('apply needs --commit-url (or --dry-run)')

    tests = load_index(args.index)
    errors, case_paths, case_tests = check(tests, args.tms_root)
    linked_tests = sum(1 for t in tests if t.get('tms_case_links'))
    print(f'{len(tests)} UI tests, {linked_tests} with TMS links, {len(case_paths)} linked cases', file=sys.stderr)
    if errors:
        report('TMS link errors — fix the @pytest.mark.tms / @allure.issue pair', errors)
        sys.exit(1)
    if args.command == 'check':
        print('TMS links OK', file=sys.stderr)
        return

    changes = apply(case_paths, case_tests, args.tms_root, args.commit_url, args.dry_run)
    report('TMS cases back-written' + (' (dry run)' if args.dry_run else ''), changes)
    stale = retirements(case_paths, tests, args.tms_root)
    if stale:
        report('Not reverted — cases whose UI refs no test declares', stale)


if __name__ == '__main__':
    main()
