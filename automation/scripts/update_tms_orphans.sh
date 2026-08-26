#!/bin/bash
# Update TMS case files to remove orphan refs that don't exist in automation

set -e

TMS_REPO="../onetest-ai-tm-Elitea"

if [ ! -d "$TMS_REPO" ]; then
    echo "❌ TMS repo not found at $TMS_REPO"
    exit 1
fi

cd "$TMS_REPO"

echo "📋 Scanning for orphan refs in TMS cases..."

# Sample orphan refs - full list would be added here
declare -a ORPHANS=(
    "tests.ui.artifacts.test_artifacts_bucket_name_validation_invalid_formats.TestArtifactBucketNameValidationInvalidFormats.test_bucket_name_validation_rejects_invalid_format:ELITEA-1814"
    "tests.ui.chat.test_agent_hub_create_conversation_via_starter.TestAgentHubCreateConversationViaStarter.test_agent_hub_create_conversation_via_starter:ELITEA-2093"
)

for entry in "${ORPHANS[@]}"; do
    ref="${entry%:*}"
    case_id="${entry##*:}"

    echo "Processing $case_id..."

    # Find case file
    case_file=$(find tests/automated-full-regression-ui -name "${case_id}.md" 2>/dev/null | head -1)

    if [ -z "$case_file" ]; then
        echo "  ⚠️  Case file not found for $case_id"
        continue
    fi

    # Check if this ref exists in the file
    if grep -q "$ref" "$case_file"; then
        echo "  ✓ Found orphan ref in $case_file"
        echo "    Would remove: $ref"
    else
        echo "  ℹ️  Orphan ref not found in $case_file"
    fi
done

echo ""
echo "✅ Analysis complete"
