#!/usr/bin/env python3
"""Build index.json from pytest test collection (automation_test_id + markers).

Collects all tests under a given path using pytest's collection hooks,
extracts their markers (including module-level pytestmark), and outputs
a JSON index compatible with the TMS correlation format.

Usage:
    python scripts/build_test_index.py --path tests/ui --out index.json
"""
import argparse
import json
import sys

import pytest


# Markers to exclude from the index (internal/infrastructure markers)
EXCLUDED_MARKERS = frozenset({
    'allure_link',
    'usefixtures',
    'parametrize',
    'filterwarnings',
    'skipif',
    'skip',
    'xfail',
})


class TestCollector:
    """Pytest plugin that collects test metadata during collection phase."""

    def __init__(self):
        self.tests = []

    def pytest_collection_finish(self, session):
        """Called after collection is complete. Extract metadata from all items."""
        for item in session.items:
            # Get all markers, excluding internal ones
            # iter_markers() includes inherited markers from module-level pytestmark
            markers = sorted(set(
                m.name for m in item.iter_markers()
                if m.name not in EXCLUDED_MARKERS
            ))

            # Convert nodeid to automation_test_id format
            # Input:  tests/ui/agents/test_x.py::TestClass::test_method[param]
            # Output: tests.ui.agents.test_x.TestClass.test_method[param]
            nodeid = item.nodeid
            automation_test_id = (
                nodeid
                .replace('.py', '')
                .replace('/', '.')
                .replace('::', '.')
            )

            self.tests.append({
                'automation_test_id': automation_test_id,
                'markers': markers,
            })


def main():
    parser = argparse.ArgumentParser(
        description='Build test index from pytest collection'
    )
    parser.add_argument(
        '--path',
        default='tests/ui',
        help='Test path to collect (default: tests/ui)'
    )
    parser.add_argument(
        '--out',
        default='index.json',
        help='Output file (default: index.json)'
    )
    args = parser.parse_args()

    collector = TestCollector()

    # Run pytest in collection-only mode with our plugin
    # -q for quiet output, --collect-only to skip execution
    # -p no:rerunfailures disables the rerun plugin to avoid missing dependency errors
    # --override-ini clears addopts to avoid picking up rerun options from pytest.ini
    exit_code = pytest.main(
        [
            '--collect-only', '-q',
            '--ignore=tests/unit',
            '-p', 'no:rerunfailures',
            '-o', 'addopts=',
            args.path
        ],
        plugins=[collector]
    )

    if exit_code not in (pytest.ExitCode.OK, pytest.ExitCode.NO_TESTS_COLLECTED):
        print(f'pytest collection failed with exit code {exit_code}', file=sys.stderr)
        sys.exit(1)

    # Sort tests by automation_test_id for stable output
    collector.tests.sort(key=lambda t: t['automation_test_id'])

    output = {'tests': collector.tests}

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write('\n')

    print(f'Indexed {len(collector.tests)} tests to {args.out}', file=sys.stderr)


if __name__ == '__main__':
    main()
