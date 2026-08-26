#!/bin/bash

RUN_ID="32761394529"
REPO="EliteaAI/elitea-testing-public"

echo "Monitoring CI Run: https://github.com/$REPO/actions/runs/$RUN_ID"
echo "Started at: $(date)"
echo "---"

while true; do
    # Get current status
    STATUS=$(env -u GITHUB_TOKEN gh run view $RUN_ID --repo $REPO --json status,conclusion --jq '{status: .status, conclusion: .conclusion}')
    
    echo "[$(date +%H:%M:%S)] $STATUS"
    
    # Check if completed
    if echo "$STATUS" | grep -q '"status":"completed"'; then
        echo "---"
        echo "Run completed!"
        
        # Get final results
        env -u GITHUB_TOKEN gh run view $RUN_ID --repo $REPO --json jobs --jq '.jobs[] | select(.name | contains("pipelines")) | {name: .name, conclusion: .conclusion}'
        
        break
    fi
    
    sleep 30
done
