#!/bin/bash

# Script to wait for package availability on PyPI with intelligent polling
# Usage: ./wait-for-pypi.sh <package-name> <version> <repository-url>

set -e

PACKAGE_NAME="${1:-folder2md4llms}"
VERSION="${2:?Version is required}"
REPOSITORY_URL="${3:-https://pypi.org/simple/}"

# Configuration
MAX_WAIT_TIME=900  # 15 minutes maximum wait
INITIAL_WAIT=10    # Start with 10 second intervals
MAX_INTERVAL=60    # Cap at 60 second intervals
BACKOFF_FACTOR=1.5 # Exponential backoff multiplier

echo "Waiting for ${PACKAGE_NAME} v${VERSION} to be available on ${REPOSITORY_URL}"

start_time=$(date +%s)
wait_interval=$INITIAL_WAIT
attempt=1

check_package_availability() {
    local package_name="$1"
    local version="$2"
    local repo_url="$3"

    if [[ "$repo_url" == *"test.pypi.org"* ]]; then
        # For TestPyPI, check the JSON API
        local api_url="https://test.pypi.org/pypi/${package_name}/json"
        local response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$api_url" 2>/dev/null || echo "HTTPSTATUS:000")
        local http_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
        local body=$(echo "$response" | sed -E 's/HTTPSTATUS:[0-9]*$//')

        if [[ "$http_code" == "200" ]]; then
            # Check if specific version exists
            if echo "$body" | grep -q "\"$version\""; then
                return 0
            fi
        fi
    else
        # For PyPI, check the JSON API
        local api_url="https://pypi.org/pypi/${package_name}/${version}/json"
        local response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$api_url" 2>/dev/null || echo "HTTPSTATUS:000")
        local http_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)

        if [[ "$http_code" == "200" ]]; then
            return 0
        fi
    fi

    return 1
}

while true; do
    current_time=$(date +%s)
    elapsed_time=$((current_time - start_time))

    if [[ $elapsed_time -ge $MAX_WAIT_TIME ]]; then
        echo "Timeout: Package not available after ${MAX_WAIT_TIME} seconds"
        echo "Proceeding with installation attempt anyway..."
        break
    fi

    echo "Attempt $attempt: Checking package availability..."

    if check_package_availability "$PACKAGE_NAME" "$VERSION" "$REPOSITORY_URL"; then
        echo "Package ${PACKAGE_NAME} v${VERSION} is now available!"
        echo "Total wait time: ${elapsed_time} seconds"
        exit 0
    fi

    echo "Package not yet available. Waiting ${wait_interval} seconds..."
    sleep "$wait_interval"

    # Exponential backoff with jitter
    wait_interval=$(echo "$wait_interval * $BACKOFF_FACTOR" | bc -l | cut -d. -f1)
    if [[ $wait_interval -gt $MAX_INTERVAL ]]; then
        wait_interval=$MAX_INTERVAL
    fi

    # Add small random jitter (0-5 seconds) to avoid thundering herd
    jitter=$((RANDOM % 6))
    wait_interval=$((wait_interval + jitter))

    attempt=$((attempt + 1))
done

echo "Proceeding without confirmation of package availability"
exit 0
