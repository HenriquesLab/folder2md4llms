#!/bin/bash

# Script to wait for a specific workflow to complete
# Usage: ./wait-for-workflow.sh <workflow-file> <ref> <github-token>

set -e

WORKFLOW_FILE="${1:?Workflow file is required}"
REF="${2:?Git ref is required}"
GITHUB_TOKEN="${3:?GitHub token is required}"
REPO="${GITHUB_REPOSITORY:-}"

# Configuration
MAX_WAIT_TIME=1200  # 20 minutes maximum wait
INITIAL_WAIT=15     # Start with 15 second intervals
MAX_INTERVAL=60     # Cap at 60 second intervals
BACKOFF_FACTOR=1.2  # Slower backoff for workflow polling

if [[ -z "$REPO" ]]; then
    echo "❌ GITHUB_REPOSITORY environment variable is required"
    exit 1
fi

echo "🔍 Waiting for workflow '${WORKFLOW_FILE}' on ref '${REF}' to complete"

start_time=$(date +%s)
wait_interval=$INITIAL_WAIT
attempt=1

get_workflow_status() {
    local workflow_file="$1"
    local ref="$2"
    local token="$3"

    # Get recent workflow runs for this workflow file
    local api_url="https://api.github.com/repos/${REPO}/actions/workflows/${workflow_file}/runs?per_page=10"
    local response=$(curl -s -H "Authorization: token ${token}" \
        -H "Accept: application/vnd.github.v3+json" \
        "$api_url" 2>/dev/null || echo '{"workflow_runs":[]}')

    # Find the most recent run for our ref
    local run_data=$(echo "$response" | jq -r --arg ref "$ref" \
        '.workflow_runs[] | select(.head_branch == $ref or .head_sha == $ref) | {status: .status, conclusion: .conclusion, created_at: .created_at}' | \
        head -1)

    if [[ -n "$run_data" && "$run_data" != "null" ]]; then
        local status=$(echo "$run_data" | jq -r '.status // "unknown"')
        local conclusion=$(echo "$run_data" | jq -r '.conclusion // "null"')
        local created_at=$(echo "$run_data" | jq -r '.created_at // "unknown"')

        echo "$status:$conclusion:$created_at"
    else
        echo "not_found:::"
    fi
}

while true; do
    current_time=$(date +%s)
    elapsed_time=$((current_time - start_time))

    if [[ $elapsed_time -ge $MAX_WAIT_TIME ]]; then
        echo "❌ Timeout: Workflow did not complete after ${MAX_WAIT_TIME} seconds"
        echo "🔄 Proceeding anyway..."
        exit 0
    fi

    echo "🔄 Attempt $attempt: Checking workflow status..."

    status_info=$(get_workflow_status "$WORKFLOW_FILE" "$REF" "$GITHUB_TOKEN")
    IFS=':' read -r status conclusion created_at <<< "$status_info"

    case "$status" in
        "completed")
            case "$conclusion" in
                "success")
                    echo "✅ Workflow completed successfully!"
                    echo "⏱️  Total wait time: ${elapsed_time} seconds"
                    exit 0
                    ;;
                "failure"|"cancelled"|"timed_out")
                    echo "❌ Workflow completed with status: $conclusion"
                    echo "🔄 Proceeding anyway..."
                    exit 0
                    ;;
                *)
                    echo "⚠️  Workflow completed with unknown conclusion: $conclusion"
                    echo "🔄 Proceeding anyway..."
                    exit 0
                    ;;
            esac
            ;;
        "in_progress"|"queued"|"requested"|"waiting")
            echo "⏳ Workflow status: $status (waiting ${wait_interval}s...)"
            ;;
        "not_found")
            echo "🔍 No workflow run found for ref '$REF' yet (waiting ${wait_interval}s...)"
            ;;
        *)
            echo "❓ Unknown workflow status: $status (waiting ${wait_interval}s...)"
            ;;
    esac

    sleep "$wait_interval"

    # Gradual backoff with jitter
    wait_interval=$(echo "$wait_interval * $BACKOFF_FACTOR" | bc -l | cut -d. -f1)
    if [[ $wait_interval -gt $MAX_INTERVAL ]]; then
        wait_interval=$MAX_INTERVAL
    fi

    # Add small random jitter (0-10 seconds)
    jitter=$((RANDOM % 11))
    wait_interval=$((wait_interval + jitter))

    attempt=$((attempt + 1))
done
