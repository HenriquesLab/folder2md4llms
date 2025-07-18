#!/bin/bash

# monitor-ci.sh - CI Status Monitor for rxiv-maker and related repositories
# Monitors CI status for the main project and package manager repositories

set -eo pipefail

# Check if we're running in bash (associative arrays require bash 4+)
if [ -z "${BASH_VERSION:-}" ]; then
    echo "Error: This script requires bash" >&2
    exit 1
fi

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
readonly GITHUB_API_BASE="https://api.github.com"

# Repository configurations (using arrays since macOS has old bash)
REPO_KEYS=("main" "homebrew" "scoop")
REPO_NAMES=("HenriquesLab/folder2md4llms" "HenriquesLab/homebrew-folder2md4llms" "HenriquesLab/scoop-folder2md4llms")
REPO_BRANCHES=("dev" "main" "main")

# GitHub API token (optional, for higher rate limits)
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

# Function to print colored output
print_status() {
    local status="$1"
    local message="$2"
    local color=""

    case "$status" in
        "SUCCESS"|"PASS") color="$GREEN" ;;
        "FAILURE"|"FAIL") color="$RED" ;;
        "PENDING"|"RUNNING") color="$YELLOW" ;;
        "INFO") color="$BLUE" ;;
        *) color="$NC" ;;
    esac

    echo -e "${color}[$status]${NC} $message"
}

# Function to make GitHub API request
github_api_request() {
    local endpoint="$1"
    local headers=()

    if [[ -n "$GITHUB_TOKEN" ]]; then
        headers=("-H" "Authorization: token $GITHUB_TOKEN")
    fi

    curl -s "${headers[@]}" "$GITHUB_API_BASE/$endpoint" 2>/dev/null || echo "{}"
}

# Function to get repository CI status
get_repo_ci_status() {
    local repo="$1"
    local branch="${2:-main}"

    print_status "INFO" "Checking CI status for $repo (branch: $branch)"

    # Get workflow runs for the repository
    local workflow_runs
    workflow_runs=$(github_api_request "repos/$repo/actions/runs?branch=$branch&per_page=10")

    if [[ "$workflow_runs" == "{}" ]]; then
        print_status "FAIL" "Failed to fetch workflow runs for $repo"
        return 1
    fi

    # Parse the JSON response to get the latest workflow run
    local latest_status
    latest_status=$(echo "$workflow_runs" | python3 -c "
import json
import sys
try:
    data = json.load(sys.stdin)
    runs = data.get('workflow_runs', [])
    if runs:
        latest = runs[0]
        print(f\"{latest['status']}:{latest['conclusion']}:{latest['html_url']}:{latest['workflow_id']}:{latest['name']}\")
    else:
        print('no_runs')
except:
    print('error')
" 2>/dev/null)

    if [[ "$latest_status" == "error" ]]; then
        print_status "FAIL" "Failed to parse workflow data for $repo"
        return 1
    elif [[ "$latest_status" == "no_runs" ]]; then
        print_status "INFO" "No workflow runs found for $repo"
        return 0
    fi

    # Parse the status
    IFS=':' read -r status conclusion url workflow_id workflow_name <<< "$latest_status"

    local display_status="$status"
    if [[ "$status" == "completed" ]]; then
        display_status="$conclusion"
    fi

    case "$display_status" in
        "success") print_status "SUCCESS" "$repo - $workflow_name" ;;
        "failure") print_status "FAILURE" "$repo - $workflow_name" ;;
        "cancelled") print_status "FAIL" "$repo - $workflow_name (cancelled)" ;;
        "in_progress"|"queued") print_status "PENDING" "$repo - $workflow_name (running)" ;;
        *) print_status "INFO" "$repo - $workflow_name ($display_status)" ;;
    esac

    echo "    URL: $url"
    echo ""
}

# Function to check if repository exists
check_repo_exists() {
    local repo="$1"
    local repo_info
    repo_info=$(github_api_request "repos/$repo")

    if [[ "$repo_info" == "{}" ]] || echo "$repo_info" | grep -q '"message": "Not Found"'; then
        return 1
    fi
    return 0
}

# Function to get repository branch
get_repo_branch() {
    local repo="$1"
    local default_branch="$2"

    # Try to get the actual default branch
    local repo_info
    repo_info=$(github_api_request "repos/$repo")

    if [[ "$repo_info" != "{}" ]]; then
        local actual_branch
        actual_branch=$(echo "$repo_info" | python3 -c "
import json
import sys
try:
    data = json.load(sys.stdin)
    print(data.get('default_branch', '$default_branch'))
except:
    print('$default_branch')
" 2>/dev/null)
        echo "$actual_branch"
    else
        echo "$default_branch"
    fi
}

# Function to show help
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Monitor CI status for rxiv-maker and related repositories.

OPTIONS:
    -h, --help          Show this help message
    -t, --token TOKEN   GitHub API token (or set GITHUB_TOKEN env var)
    -w, --watch         Watch mode - continuously monitor every 30 seconds
    -r, --repo REPO     Monitor specific repository only (main|homebrew|scoop)
    -v, --verbose       Verbose output

EXAMPLES:
    $0                  # Check all repositories once
    $0 -w               # Watch mode
    $0 -r main          # Check only main repository
    $0 -t ghp_xxxx      # Use specific GitHub token

ENVIRONMENT:
    GITHUB_TOKEN        GitHub API token for higher rate limits
EOF
}

# Function to monitor in watch mode
watch_mode() {
    local repo_filter="$1"

    print_status "INFO" "Starting watch mode (press Ctrl+C to stop)"
    echo ""

    while true; do
        clear
        echo "=== rxiv-maker CI Status Monitor ==="
        echo "Last updated: $(date)"
        echo ""

        monitor_repositories "$repo_filter"

        echo ""
        print_status "INFO" "Refreshing in 30 seconds..."
        sleep 30
    done
}

# Function to get repository info by key
get_repo_info() {
    local repo_key="$1"
    local info_type="$2"  # "name" or "branch"

    for i in "${!REPO_KEYS[@]}"; do
        if [[ "${REPO_KEYS[$i]}" == "$repo_key" ]]; then
            if [[ "$info_type" == "name" ]]; then
                echo "${REPO_NAMES[$i]}"
            elif [[ "$info_type" == "branch" ]]; then
                echo "${REPO_BRANCHES[$i]}"
            fi
            return 0
        fi
    done
    return 1
}

# Function to monitor all repositories
monitor_repositories() {
    local repo_filter="$1"

    local failed_repos=()
    local total_repos=0
    local checked_repos=0

    for repo_key in "${REPO_KEYS[@]}"; do
        if [[ -n "$repo_filter" && "$repo_key" != "$repo_filter" ]]; then
            continue
        fi

        local repo
        local default_branch
        repo=$(get_repo_info "$repo_key" "name")
        default_branch=$(get_repo_info "$repo_key" "branch")

        ((total_repos++))

        # Check if repository exists
        if ! check_repo_exists "$repo"; then
            print_status "FAIL" "Repository $repo not found (may not be created yet)"
            failed_repos+=("$repo")
            echo ""
            continue
        fi

        # Use configured branch instead of querying GitHub API
        local branch="$default_branch"

        # Check CI status
        if ! get_repo_ci_status "$repo" "$branch"; then
            failed_repos+=("$repo")
        fi

        ((checked_repos++))
    done

    # Summary
    echo "=== Summary ==="
    print_status "INFO" "Checked $checked_repos/$total_repos repositories"

    if [[ ${#failed_repos[@]} -gt 0 ]]; then
        print_status "FAIL" "Failed repositories: ${failed_repos[*]}"
        return 1
    else
        print_status "SUCCESS" "All available repositories checked successfully"
        return 0
    fi
}

# Main function
main() {
    local watch=false
    local repo_filter=""
    local verbose=false

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -t|--token)
                GITHUB_TOKEN="$2"
                shift 2
                ;;
            -w|--watch)
                watch=true
                shift
                ;;
            -r|--repo)
                repo_filter="$2"
                # Check if repo_filter is valid
                local valid_repo=false
                for key in "${REPO_KEYS[@]}"; do
                    if [[ "$key" == "$repo_filter" ]]; then
                        valid_repo=true
                        break
                    fi
                done
                if [[ "$valid_repo" != true ]]; then
                    print_status "FAIL" "Invalid repository: $repo_filter"
                    echo "Valid repositories: ${REPO_KEYS[*]}"
                    exit 1
                fi
                shift 2
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            *)
                print_status "FAIL" "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Check dependencies
    if ! command -v python3 &> /dev/null; then
        print_status "FAIL" "python3 is required but not installed"
        exit 1
    fi

    if ! command -v curl &> /dev/null; then
        print_status "FAIL" "curl is required but not installed"
        exit 1
    fi

    # Show configuration if verbose
    if [[ "$verbose" == true ]]; then
        print_status "INFO" "Configuration:"
        echo "  GitHub Token: ${GITHUB_TOKEN:+SET}"
        echo "  Repositories: ${REPO_KEYS[*]}"
        echo "  Repository filter: ${repo_filter:-all}"
        echo ""
    fi

    if [[ "$watch" == true ]]; then
        watch_mode "$repo_filter"
    else
        monitor_repositories "$repo_filter"
    fi
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
