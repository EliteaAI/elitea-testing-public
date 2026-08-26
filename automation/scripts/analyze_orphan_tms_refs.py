#!/usr/bin/env python3
"""
Analyze orphan TMS references and suggest automation_test_id updates.

This script:
1. Extracts orphan TMS references from the dashboard
2. Searches for likely moved/renamed tests in the automation codebase
3. Identifies high-confidence matches that can be updated
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict

# Patterns to extract from orphan references
ORPHAN_PATTERN = r'`([^`]+)`\s+\(([^)]+)\)'

# Root paths
AUTOMATION_ROOT = Path(__file__).parent.parent / "tests" / "ui"
TMS_ROOT = Path(__file__).parent.parent.parent.parent / "onetest-ai-tm-Elitea" / "tests" / "automated-full-regression-ui"


def parse_test_id(test_id: str) -> dict:
    """Parse a test ID into components."""
    # Format: suite.module.Class.method
    parts = test_id.split('.')
    if len(parts) >= 4:
        return {
            'suite': parts[0],
            'module': parts[1],
            'class': parts[2] if len(parts) > 2 else None,
            'method': parts[-1],
            'full': test_id
        }
    return None


def find_test_in_codebase(module_name: str, class_name: str, method_name: str) -> list:
    """Search for a test in the automation codebase."""
    matches = []

    # Search for files matching the module name
    for suite_dir in AUTOMATION_ROOT.iterdir():
        if not suite_dir.is_dir() or suite_dir.name.startswith('__'):
            continue

        for test_file in suite_dir.glob(f"**/{module_name}.py"):
            # Read file and check for class and method
            try:
                content = test_file.read_text()

                # Check if class exists
                class_match = re.search(rf'class\s+{class_name}\b', content)
                if not class_match:
                    continue

                # Check if method exists
                method_match = re.search(rf'def\s+{method_name}\s*\(', content)
                if not method_match:
                    continue

                # Build the new test ID
                relative_path = test_file.relative_to(AUTOMATION_ROOT.parent)
                suite = test_file.parent.name
                module = test_file.stem

                new_test_id = f"tests.ui.{suite}.{module}.{class_name}.{method_name}"

                matches.append({
                    'file': str(test_file.relative_to(AUTOMATION_ROOT.parent.parent)),
                    'suite': suite,
                    'new_test_id': new_test_id
                })
            except Exception as e:
                continue

    return matches


def extract_orphan_refs(dashboard_path: Path) -> list:
    """Extract orphan TMS references from dashboard."""
    content = dashboard_path.read_text()

    # Find the Orphan TMS References section
    orphan_section = re.search(
        r'### Orphan TMS References.*?<summary>Show (\d+) orphan refs</summary>(.*?)</details>',
        content,
        re.DOTALL
    )

    if not orphan_section:
        return []

    orphan_text = orphan_section.group(2)
    orphans = []

    for match in re.finditer(ORPHAN_PATTERN, orphan_text):
        test_id = match.group(1)
        case_id = match.group(2)
        orphans.append({
            'old_test_id': test_id,
            'case_id': case_id
        })

    return orphans


def analyze_orphans(orphans: list) -> dict:
    """Analyze orphans and categorize by confidence."""
    results = {
        'high_confidence': [],  # Exact match found in different suite
        'medium_confidence': [],  # Similar match found
        'low_confidence': [],  # No clear match
    }

    for orphan in orphans:
        old_test_id = orphan['old_test_id']
        case_id = orphan['case_id']

        parsed = parse_test_id(old_test_id)
        if not parsed:
            results['low_confidence'].append({
                **orphan,
                'reason': 'Invalid test ID format'
            })
            continue

        # Search for the test in the codebase
        matches = find_test_in_codebase(
            parsed['module'],
            parsed['class'],
            parsed['method']
        )

        if not matches:
            results['low_confidence'].append({
                **orphan,
                'reason': 'No matching test found in codebase'
            })
            continue

        if len(matches) == 1:
            match = matches[0]
            # High confidence: exact match in different suite
            if match['suite'] != parsed['suite']:
                results['high_confidence'].append({
                    **orphan,
                    'new_test_id': match['new_test_id'],
                    'new_suite': match['suite'],
                    'old_suite': parsed['suite'],
                    'file': match['file'],
                    'reason': f"Exact match found - moved from {parsed['suite']}/ to {match['suite']}/"
                })
            else:
                # Same suite - might be a rename
                results['medium_confidence'].append({
                    **orphan,
                    'new_test_id': match['new_test_id'],
                    'file': match['file'],
                    'reason': 'Same suite, possible module rename'
                })
        else:
            # Multiple matches - medium confidence
            results['medium_confidence'].append({
                **orphan,
                'matches': [m['new_test_id'] for m in matches],
                'reason': f'Multiple matches found ({len(matches)})'
            })

    return results


def print_results(results: dict):
    """Print analysis results."""
    print("=" * 80)
    print("ORPHAN TMS REFERENCE ANALYSIS")
    print("=" * 80)
    print()

    # High confidence matches
    print(f"HIGH CONFIDENCE MATCHES ({len(results['high_confidence'])})")
    print("-" * 80)
    print("These can be updated with high confidence:\n")

    for item in results['high_confidence']:
        print(f"Case ID: {item['case_id']}")
        print(f"  Old: {item['old_test_id']}")
        print(f"  New: {item['new_test_id']}")
        print(f"  Reason: {item['reason']}")
        print(f"  File: {item['file']}")
        print()

    # Summary by suite move
    if results['high_confidence']:
        print("\nSUITE MIGRATION SUMMARY:")
        suite_moves = defaultdict(list)
        for item in results['high_confidence']:
            key = f"{item['old_suite']} → {item['new_suite']}"
            suite_moves[key].append(item['case_id'])

        for move, cases in sorted(suite_moves.items()):
            print(f"  {move}: {len(cases)} tests")
            print(f"    Cases: {', '.join(cases)}")
        print()

    print("=" * 80)
    print(f"\nMEDIUM CONFIDENCE MATCHES ({len(results['medium_confidence'])})")
    print("-" * 80)
    if results['medium_confidence']:
        print("These may need manual verification:\n")
        for item in results['medium_confidence'][:5]:  # Show first 5
            print(f"Case ID: {item['case_id']}")
            print(f"  Old: {item['old_test_id']}")
            if 'new_test_id' in item:
                print(f"  New: {item['new_test_id']}")
            if 'matches' in item:
                print(f"  Matches: {', '.join(item['matches'][:3])}")
            print(f"  Reason: {item['reason']}")
            print()
        if len(results['medium_confidence']) > 5:
            print(f"  ... and {len(results['medium_confidence']) - 5} more\n")

    print("=" * 80)
    print(f"\nLOW CONFIDENCE / NOT FOUND ({len(results['low_confidence'])})")
    print("-" * 80)
    if results['low_confidence']:
        print("These tests were not found or have issues:\n")
        reasons = defaultdict(list)
        for item in results['low_confidence']:
            reasons[item['reason']].append(item['case_id'])

        for reason, cases in reasons.items():
            print(f"  {reason}: {len(cases)} cases")
            print(f"    {', '.join(cases[:10])}")
            if len(cases) > 10:
                print(f"    ... and {len(cases) - 10} more")
            print()


def generate_update_script(results: dict, output_path: Path):
    """Generate a script to update TMS case files."""
    high_conf = results['high_confidence']

    if not high_conf:
        print("No high-confidence matches to generate update script.")
        return

    script_lines = [
        "#!/bin/bash",
        "# Auto-generated script to update orphan TMS references",
        "# HIGH CONFIDENCE updates only",
        "",
        "set -e",
        "",
        "TMS_ROOT='../onetest-ai-tm-Elitea/tests/automated-full-regression-ui'",
        "",
        "echo 'Updating TMS case automation_test_id fields...'",
        "echo ''",
        ""
    ]

    for item in high_conf:
        case_id = item['case_id']
        old_id = item['old_test_id']
        new_id = item['new_test_id']

        # Find the TMS case file
        case_files = list(TMS_ROOT.rglob(f"*{case_id.lower()}*.md"))
        if case_files:
            case_file = case_files[0].relative_to(TMS_ROOT.parent.parent)

            script_lines.append(f"# {case_id}: {item['old_suite']} → {item['new_suite']}")
            script_lines.append(f"echo 'Updating {case_id}...'")
            script_lines.append(f"sed -i.bak 's|{old_id}|{new_id}|g' '{case_file}'")
            script_lines.append("")

    script_lines.extend([
        "echo ''",
        "echo 'Done! Updated ' $(find \"$TMS_ROOT\" -name '*.bak' | wc -l) ' files'",
        "echo 'Backup files (.bak) created for safety'",
        "echo ''",
        "echo 'Review changes with: git diff'",
        "echo 'Remove backups with: find \"$TMS_ROOT\" -name \"*.bak\" -delete'",
    ])

    output_path.write_text('\n'.join(script_lines))
    output_path.chmod(0o755)
    print(f"\n✅ Update script generated: {output_path}")
    print(f"   This will update {len(high_conf)} TMS case files")


if __name__ == '__main__':
    # Path to latest dashboard
    dashboard_path = Path(__file__).parent.parent.parent.parent / \
                     "onetest-ai-tm-Elitea" / "reports" / "dashboards" / \
                     "dashboard-RUN-ELITEA-2026-08-21-35-DEV-STABLE-ALL-FAILED.md"

    if not dashboard_path.exists():
        print(f"❌ Dashboard not found: {dashboard_path}")
        exit(1)

    print(f"📊 Analyzing dashboard: {dashboard_path.name}")
    print()

    # Extract orphan references
    orphans = extract_orphan_refs(dashboard_path)
    print(f"Found {len(orphans)} orphan TMS references")
    print()

    # Analyze orphans
    results = analyze_orphans(orphans)

    # Print results
    print_results(results)

    # Generate update script for high-confidence matches
    if results['high_confidence']:
        output_script = Path(__file__).parent / "update_tms_orphans.sh"
        generate_update_script(results, output_script)

        # Save detailed JSON report
        json_output = Path(__file__).parent / "orphan_analysis.json"
        json_output.write_text(json.dumps(results, indent=2))
        print(f"📄 Detailed JSON report: {json_output}")
