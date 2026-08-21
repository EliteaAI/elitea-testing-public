# Test Suite Distribution Strategy

## Overview

The GitHub Actions workflow now uses **weighted load-balancing** instead of round-robin to distribute test suites across parallel executors.

## Algorithm: Greedy Bin-Packing

The distribution uses a greedy bin-packing algorithm:

1. **Count test files per suite** (at workflow runtime from the checked-out codebase)
2. **Sort suites by size** (largest first)
3. **Assign each suite to the executor with minimum current load**

This minimizes load imbalance and reduces wasted executor time.

## Example Distribution

Given 13 suites with varying sizes (1-66 test files), the algorithm produces:

```
Executor 1:  66 files - pipelines
Executor 2:  34 files - chat
Executor 3:  31 files - skills
Executor 4:  30 files - agents
Executor 5:  24 files - toolkits
Executor 6:  22 files - artifacts
Executor 7:  20 files - admin
Executor 8:  19 files - agent_hub
Executor 9:   7 files - settings,voice,support_assistant,smoke,help_center
```

**Key characteristics:**
- All 9 executors are utilized (no idle workers)
- Load variance is minimized (7-66 files vs round-robin's 1-66)
- Small suites are bundled together (executor 9)

## When This Helps

The weighted distribution provides the most benefit when:

1. **Suite sizes vary significantly** (some suites are 10× larger than others)
2. **Multiple executors are used** (parallelism > 3)
3. **Full suite runs** (not single-suite runs)

### Comparison: Round-Robin vs Weighted

| Distribution | Min Load | Max Load | Variance | Idle Executors |
|--------------|----------|----------|----------|----------------|
| Round-Robin  | 1 file   | 66 files | 65 files | 0              |
| Weighted     | 7 files  | 66 files | 59 files | 0              |

**Improvement:** 9% reduction in load variance

## Current Bottleneck

**The pipelines suite (66 test files) is the system bottleneck.** Even with perfect distribution, wall-clock time is limited by this single large suite.

### To Further Improve Performance

1. **Split pipelines suite** into smaller sub-suites (e.g., `pipelines-core`, `pipelines-advanced`)
2. **Enable pytest-xdist** to run tests within each suite in parallel (requires `-n 2` flag)
3. **Collect historical timing data** to weight by actual execution time instead of file count

See the main optimization plan for details on these strategies.

## Testing Locally

Verify the distribution algorithm:

```bash
# See the distribution for your current codebase
bash .github/scripts/test-distribution.sh

# Compare round-robin vs weighted
bash .github/scripts/compare-distributions.sh
```

## Implementation Details

- **Location:** `.github/workflows/test-ui-custom.yml` lines 340-405
- **Zero stored data required** - counts are computed at runtime
- **Fallback behavior:** If checkout is unavailable (single suite or custom list), uses equal weights
- **Language:** Pure bash (no Python dependencies)

## Maintenance

The algorithm is **self-updating**:
- New test files are automatically counted
- Suite additions/removals are handled without changes
- No manual configuration needed

If suite execution times diverge significantly from file counts (e.g., some tests are 10× slower), consider upgrading to historical-data-based distribution (see main optimization plan, Strategy 1).
