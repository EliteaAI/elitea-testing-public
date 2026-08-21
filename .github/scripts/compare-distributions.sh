#!/bin/bash
# Compare round-robin vs weighted distribution
# Shows the improvement from the new algorithm

set -e

cd "$(dirname "$0")/../.."

MAX_USERS=9

# Discover suites
SUITES=$(ls -d automation/tests/ui/*/ 2>/dev/null \
  | xargs -n1 basename \
  | grep -v -E '^(__pycache__|__init__)' \
  | sort \
  | tr '\n' ',' \
  | sed 's/,$//')

IFS=',' read -ra SUITE_ARRAY <<< "$SUITES"

# Count test files per suite
declare -A SUITE_SIZES
for suite in "${SUITE_ARRAY[@]}"; do
  count=$(find "automation/tests/ui/$suite" -type f -name 'test_*.py' 2>/dev/null | wc -l | tr -d ' ')
  SUITE_SIZES[$suite]=$count
done

echo "=========================================="
echo "DISTRIBUTION COMPARISON"
echo "=========================================="
echo ""

# ===== OLD: Round-Robin =====
echo "OLD METHOD: Round-Robin"
echo "------------------------------------------"
declare -A RR_USER_SUITES
declare -A RR_LOADS
for i in $(seq 1 $MAX_USERS); do
  RR_LOADS[$i]=0
done

for i in "${!SUITE_ARRAY[@]}"; do
  suite="${SUITE_ARRAY[$i]}"
  user_idx=$(( (i % MAX_USERS) + 1 ))
  if [ -z "${RR_USER_SUITES[$user_idx]}" ]; then
    RR_USER_SUITES[$user_idx]="$suite"
  else
    RR_USER_SUITES[$user_idx]="${RR_USER_SUITES[$user_idx]},$suite"
  fi
  RR_LOADS[$user_idx]=$(( ${RR_LOADS[$user_idx]} + ${SUITE_SIZES[$suite]} ))
done

rr_min=999999
rr_max=0
for i in $(seq 1 $MAX_USERS); do
  load=${RR_LOADS[$i]:-0}
  printf "Executor %d: %3d files - %s\n" "$i" "$load" "${RR_USER_SUITES[$i]}"
  if [ $load -gt 0 ]; then
    if [ $load -lt $rr_min ]; then rr_min=$load; fi
    if [ $load -gt $rr_max ]; then rr_max=$load; fi
  fi
done
echo ""
echo "Round-robin stats:"
echo "  Min: $rr_min files  |  Max: $rr_max files  |  Difference: $(( rr_max - rr_min )) files"
echo ""
echo ""

# ===== NEW: Weighted =====
echo "NEW METHOD: Weighted Load-Balancing"
echo "------------------------------------------"

# Sort suites by size
SORTED_SUITES=()
while IFS= read -r line; do
  SORTED_SUITES+=("$line")
done < <(
  for suite in "${SUITE_ARRAY[@]}"; do
    echo "${SUITE_SIZES[$suite]} $suite"
  done | sort -rn | awk '{print $2}'
)

# Greedy assignment
declare -A WB_USER_SUITES
declare -A WB_LOADS
for i in $(seq 1 $MAX_USERS); do
  WB_LOADS[$i]=0
done

for suite in "${SORTED_SUITES[@]}"; do
  min_load=999999
  min_executor=1
  for i in $(seq 1 $MAX_USERS); do
    load=${WB_LOADS[$i]:-0}
    if [ $load -lt $min_load ]; then
      min_load=$load
      min_executor=$i
    fi
  done

  if [ -z "${WB_USER_SUITES[$min_executor]}" ]; then
    WB_USER_SUITES[$min_executor]="$suite"
  else
    WB_USER_SUITES[$min_executor]="${WB_USER_SUITES[$min_executor]},$suite"
  fi
  WB_LOADS[$min_executor]=$(( ${WB_LOADS[$min_executor]} + ${SUITE_SIZES[$suite]} ))
done

wb_min=999999
wb_max=0
for i in $(seq 1 $MAX_USERS); do
  load=${WB_LOADS[$i]:-0}
  printf "Executor %d: %3d files - %s\n" "$i" "$load" "${WB_USER_SUITES[$i]}"
  if [ $load -gt 0 ]; then
    if [ $load -lt $wb_min ]; then wb_min=$load; fi
    if [ $load -gt $wb_max ]; then wb_max=$load; fi
  fi
done
echo ""
echo "Weighted load-balancing stats:"
echo "  Min: $wb_min files  |  Max: $wb_max files  |  Difference: $(( wb_max - wb_min )) files"
echo ""
echo ""

# ===== COMPARISON =====
echo "=========================================="
echo "IMPROVEMENT SUMMARY"
echo "=========================================="

rr_diff=$(( rr_max - rr_min ))
wb_diff=$(( wb_max - wb_min ))
improvement=$(( rr_diff - wb_diff ))
improvement_pct=$(( 100 * improvement / rr_diff ))

echo "Load balance (max - min):"
echo "  Round-robin:     $rr_diff files"
echo "  Weighted:        $wb_diff files"
echo "  Improvement:     $improvement files reduction (${improvement_pct}%)"
echo ""

# Estimate time improvement (assuming 17s per test on average)
AVG_TIME_PER_FILE=17
rr_time=$(( rr_max * AVG_TIME_PER_FILE ))
wb_time=$(( wb_max * AVG_TIME_PER_FILE ))
time_saved=$(( rr_time - wb_time ))

echo "Estimated wall-clock time (@ ${AVG_TIME_PER_FILE}s/file):"
echo "  Round-robin:     $(( rr_time / 60 )) min $(( rr_time % 60 )) sec (bottleneck executor)"
echo "  Weighted:        $(( wb_time / 60 )) min $(( wb_time % 60 )) sec (bottleneck executor)"
echo "  Time saved:      $(( time_saved / 60 )) min $(( time_saved % 60 )) sec"
echo ""

# Idle executor analysis
echo "Idle executor usage:"
rr_empty_count=0
wb_empty_count=0
for i in $(seq 1 $MAX_USERS); do
  if [ ${RR_LOADS[$i]:-0} -eq 0 ]; then
    rr_empty_count=$(( rr_empty_count + 1 ))
  fi
  if [ ${WB_LOADS[$i]:-0} -eq 0 ]; then
    wb_empty_count=$(( wb_empty_count + 1 ))
  fi
done
echo "  Round-robin:     $rr_empty_count idle executors"
echo "  Weighted:        $wb_empty_count idle executors"
echo ""

if [ $wb_time -lt $rr_time ]; then
  echo "✅ Weighted distribution is FASTER and MORE BALANCED"
else
  echo "⚠️  No improvement (but suite distribution is more balanced)"
fi
