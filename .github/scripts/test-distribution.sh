#!/bin/bash
# Test script to verify weighted distribution logic locally
# Usage: bash .github/scripts/test-distribution.sh

set -e

cd "$(dirname "$0")/../.."

MAX_USERS=9

echo "Testing weighted distribution algorithm..."
echo ""

# Discover suites
SUITES=$(ls -d automation/tests/ui/*/ 2>/dev/null \
  | xargs -n1 basename \
  | grep -v -E '^(__pycache__|__init__)' \
  | sort \
  | tr '\n' ',' \
  | sed 's/,$//')

if [ -z "$SUITES" ]; then
  echo "ERROR: No test suites found"
  exit 1
fi

# Convert to array
IFS=',' read -ra SUITE_ARRAY <<< "$SUITES"
SUITE_COUNT=${#SUITE_ARRAY[@]}
echo "Total suites: $SUITE_COUNT"
echo ""

# Step 1: Count test files per suite
declare -A SUITE_SIZES
echo "Counting test files per suite..."
for suite in "${SUITE_ARRAY[@]}"; do
  count=$(find "automation/tests/ui/$suite" -type f -name 'test_*.py' 2>/dev/null | wc -l | tr -d ' ')
  SUITE_SIZES[$suite]=$count
  printf "  %-20s %3d test files\n" "$suite:" "$count"
done
echo ""

# Step 2: Sort suites by size (largest first)
SORTED_SUITES=()
while IFS= read -r line; do
  SORTED_SUITES+=("$line")
done < <(
  for suite in "${SUITE_ARRAY[@]}"; do
    echo "${SUITE_SIZES[$suite]} $suite"
  done | sort -rn | awk '{print $2}'
)

echo "Sorted order (largest first):"
for suite in "${SORTED_SUITES[@]}"; do
  printf "  %-20s %3d files\n" "$suite" "${SUITE_SIZES[$suite]}"
done
echo ""

# Step 3: Assign each suite to executor with minimum load
declare -A USER_SUITES
declare -A EXECUTOR_LOADS
for i in $(seq 1 $MAX_USERS); do
  EXECUTOR_LOADS[$i]=0
done

for suite in "${SORTED_SUITES[@]}"; do
  # Find executor with minimum load
  min_load=999999
  min_executor=1
  for i in $(seq 1 $MAX_USERS); do
    load=${EXECUTOR_LOADS[$i]:-0}
    if [ $load -lt $min_load ]; then
      min_load=$load
      min_executor=$i
    fi
  done

  # Assign suite to that executor
  if [ -z "${USER_SUITES[$min_executor]}" ]; then
    USER_SUITES[$min_executor]="$suite"
  else
    USER_SUITES[$min_executor]="${USER_SUITES[$min_executor]},$suite"
  fi
  EXECUTOR_LOADS[$min_executor]=$(( ${EXECUTOR_LOADS[$min_executor]} + ${SUITE_SIZES[$suite]} ))
done

# Log final distribution
echo "=========================================="
echo "FINAL DISTRIBUTION"
echo "=========================================="
total_files=0
for i in $(seq 1 $MAX_USERS); do
  if [ -n "${USER_SUITES[$i]}" ]; then
    printf "Executor %d: %3d files - %s\n" "$i" "${EXECUTOR_LOADS[$i]}" "${USER_SUITES[$i]}"
    total_files=$(( total_files + ${EXECUTOR_LOADS[$i]} ))
  else
    printf "Executor %d: %3d files - (empty)\n" "$i" "0"
  fi
done
echo "=========================================="
printf "Total:      %3d files\n" "$total_files"

# Calculate statistics
min_load=999999
max_load=0
active_executors=0
for i in $(seq 1 $MAX_USERS); do
  load=${EXECUTOR_LOADS[$i]:-0}
  if [ $load -gt 0 ]; then
    active_executors=$(( active_executors + 1 ))
  fi
  if [ $load -lt $min_load ]; then
    min_load=$load
  fi
  if [ $load -gt $max_load ]; then
    max_load=$load
  fi
done

avg_load=$(( total_files / active_executors ))
echo ""
echo "Statistics:"
echo "  Min load:        $min_load files"
echo "  Max load:        $max_load files"
echo "  Avg load:        $avg_load files"
echo "  Active executors: $active_executors / $MAX_USERS"
echo "  Load difference: $(( max_load - min_load )) files (max - min)"
echo ""

# Build JSON matrix (for verification)
JSON="["
FIRST=true
for user_idx in $(echo "${!USER_SUITES[@]}" | tr ' ' '\n' | sort -n); do
  suites="${USER_SUITES[$user_idx]}"
  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    JSON="$JSON,"
  fi
  JSON="$JSON{\"user_idx\":\"$user_idx\",\"suites\":\"$suites\"}"
done
JSON="$JSON]"

echo "JSON matrix output:"
echo "$JSON" | python3 -m json.tool 2>/dev/null || echo "$JSON"
