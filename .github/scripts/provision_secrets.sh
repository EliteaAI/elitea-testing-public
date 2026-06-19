#!/usr/bin/env bash
# provision_secrets.sh — Sets or deletes GitHub secrets from a .env file.
#
# Usage:
#   ./provision_secrets.sh                               # provision shared secrets (no suffix)
#   ./provision_secrets.sh --env dev                     # provision env-specific secrets with _DEV suffix
#   ./provision_secrets.sh --env stage                   # provision env-specific secrets with _STAGE suffix
#   ./provision_secrets.sh --delete                      # delete all secrets listed in .env
#   ./provision_secrets.sh --env-file path/to/.env --repo owner/repo
#
# When --env is provided, each key is suffixed with the uppercased env name:
#   ELITEA_API_TOKEN → ELITEA_API_TOKEN_DEV  (with --env dev)
#   ELITEA_API_TOKEN → ELITEA_API_TOKEN_STAGE  (with --env stage)
#
# Defaults:
#   --env-file  automation/.env.test
#   --repo      EliteaAI/elitea-testing

set -euo pipefail

ENV_FILE="automation/.env.test"
REPO="EliteaAI/elitea-testing"
DELETE_MODE=false
ENV_SUFFIX=""   # empty = no suffix (shared secrets)

# Parse optional arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --env-file) ENV_FILE="$2"; shift 2 ;;
    --repo)     REPO="$2";     shift 2 ;;
    --env)      ENV_SUFFIX="$(echo "$2" | tr '[:lower:]' '[:upper:]')"; shift 2 ;;
    --delete)   DELETE_MODE=true; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

# Validate prerequisites
if ! command -v gh &>/dev/null; then
  echo "Error: gh CLI is not installed." >&2
  exit 1
fi

if ! gh auth status &>/dev/null; then
  echo "Not authenticated with GitHub CLI."
  read -rp "Run 'gh auth login' now? [y/N] " answer
  if [[ "$answer" =~ ^[Yy]$ ]]; then
    gh auth login
    if ! gh auth status &>/dev/null; then
      echo "Error: authentication failed." >&2
      exit 1
    fi
  else
    echo "Aborted. Run 'gh auth login' first." >&2
    exit 1
  fi
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Error: env file not found: $ENV_FILE" >&2
  exit 1
fi

# Collect all valid keys from the .env file (with suffix applied)
keys=()
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
  line="${line#export }"
  [[ "$line" != *=* ]] && continue
  key="${line%%=*}"
  [[ -z "$key" || "$key" =~ [[:space:]] ]] && continue
  keys+=("${key}${ENV_SUFFIX:+_${ENV_SUFFIX}}")
done < "$ENV_FILE"

if [[ ${#keys[@]} -eq 0 ]]; then
  echo "No valid keys found in '$ENV_FILE'." >&2
  exit 1
fi

# ── DELETE MODE ──────────────────────────────────────────────────────────────
if [[ "$DELETE_MODE" == true ]]; then
  echo "The following ${#keys[@]} secrets will be DELETED from $REPO:"
  echo ""
  for key in "${keys[@]}"; do
    echo "  - $key"
  done
  echo ""
  read -rp "This cannot be undone. Continue? [y/N] " confirm
  if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
  fi
  echo ""

  deleted=0
  failed=0
  for key in "${keys[@]}"; do
    if gh secret delete "$key" --repo "$REPO" 2>/dev/null; then
      echo "  DELETED  $key"
      ((++deleted))
    else
      echo "  FAIL     $key" >&2
      ((++failed))
    fi
  done

  echo ""
  echo "Done: $deleted deleted, $failed failed"
  [[ $failed -eq 0 ]]
  exit
fi

# ── PROVISION MODE ───────────────────────────────────────────────────────────
if [[ -n "$ENV_SUFFIX" ]]; then
  echo "Provisioning secrets from '$ENV_FILE' → $REPO (suffix: _${ENV_SUFFIX})"
else
  echo "Provisioning secrets from '$ENV_FILE' → $REPO (no suffix)"
fi
echo ""

success=0
skipped=0
failed=0

while IFS= read -r line || [[ -n "$line" ]]; do
  # Skip blank lines and comments
  [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue

  # Strip leading 'export ' if present
  line="${line#export }"

  # Must contain '='
  [[ "$line" != *=* ]] && continue

  key="${line%%=*}"
  value="${line#*=}"

  # Strip trailing carriage return (handles CRLF files edited on Windows)
  value="${value%$'\r'}"

  # Strip surrounding quotes from value (single or double)
  if [[ "$value" =~ ^\"(.*)\"$ ]] || [[ "$value" =~ ^\'(.*)\'$ ]]; then
    value="${BASH_REMATCH[1]}"
  fi

  # Skip if key is empty or contains spaces (malformed line)
  if [[ -z "$key" || "$key" =~ [[:space:]] ]]; then
    echo "  SKIP (malformed): $line"
    ((++skipped))
    continue
  fi

  secret_name="${key}${ENV_SUFFIX:+_${ENV_SUFFIX}}"
  if gh secret set "$secret_name" --body "$value" --repo "$REPO" 2>/dev/null; then
    echo "  OK  $secret_name"
    ((++success))
  else
    echo "  FAIL $secret_name" >&2
    ((++failed))
  fi

done < "$ENV_FILE"

echo ""
echo "Done: $success set, $skipped skipped, $failed failed"

[[ $failed -eq 0 ]]
