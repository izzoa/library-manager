#!/bin/bash
# auto-fix-issues.sh - Automatically handle GitHub issues with Claude Code
#
# This script opens Claude Code interactively (uses your Max subscription)
# and feeds it the issue context.
#
# Usage:
#   ./auto-fix-issues.sh              # Process all open issues
#   ./auto-fix-issues.sh --issue 5    # Process specific issue
#   ./auto-fix-issues.sh --dry-run    # Just show what would be processed
#   ./auto-fix-issues.sh --cli        # Use CLI mode instead of interactive
#
# Cron (check every 30 min):
#   */30 * * * * cd /path/to/library-manager && ./scripts/auto-fix-issues.sh >> /var/log/issue-bot.log 2>&1

set -e

REPO="deucebucket/library-manager"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PROMPT_FILE="$SCRIPT_DIR/issue-bot-prompt.md"
STATE_FILE="/tmp/library-manager-processed-issues.txt"
LOCK_FILE="/tmp/library-manager-issue-bot.lock"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check for lock file (prevent multiple instances)
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        log "Another instance is running (PID: $PID). Exiting."
        exit 0
    else
        rm -f "$LOCK_FILE"
    fi
fi

# Create lock file
echo $$ > "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

# Parse arguments
DRY_RUN=false
SPECIFIC_ISSUE=""
USE_CLI=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --issue)
            SPECIFIC_ISSUE="$2"
            shift 2
            ;;
        --cli)
            USE_CLI=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Make sure we're in the project directory
cd "$PROJECT_DIR"

# Check dependencies
for cmd in gh jq; do
    if ! command -v $cmd &> /dev/null; then
        log "Error: $cmd is not installed"
        exit 1
    fi
done

if ! command -v claude &> /dev/null; then
    log "Error: claude is not installed"
    exit 1
fi

# Get open issues
log "Checking for open issues on $REPO..."

if [ -n "$SPECIFIC_ISSUE" ]; then
    ISSUE_DATA=$(gh issue view "$SPECIFIC_ISSUE" --repo "$REPO" --json number,title,body,comments 2>/dev/null || echo "")
    if [ -z "$ISSUE_DATA" ]; then
        log "Issue #$SPECIFIC_ISSUE not found"
        exit 1
    fi
    ISSUE_NUMBERS="$SPECIFIC_ISSUE"
else
    ISSUES=$(gh issue list --repo "$REPO" --state open --json number,title,body,createdAt,comments 2>/dev/null)

    if [ -z "$ISSUES" ] || [ "$ISSUES" = "[]" ]; then
        log "No open issues. All clear!"
        exit 0
    fi

    ISSUE_NUMBERS=$(echo "$ISSUES" | jq -r '.[].number')
fi

# Track state to avoid reprocessing
touch "$STATE_FILE"

for NUM in $ISSUE_NUMBERS; do
    # Skip if already processed (unless specifically requested)
    if [ -z "$SPECIFIC_ISSUE" ] && grep -q "^$NUM$" "$STATE_FILE"; then
        log "Issue #$NUM already processed, skipping..."
        continue
    fi

    # Get issue details
    ISSUE_DATA=$(gh issue view "$NUM" --repo "$REPO" --json number,title,body,comments)
    TITLE=$(echo "$ISSUE_DATA" | jq -r '.title')
    BODY=$(echo "$ISSUE_DATA" | jq -r '.body')
    COMMENTS=$(echo "$ISSUE_DATA" | jq -r '.comments | map(.body) | join("\n---\n")')

    log ""
    log "========================================="
    log "Processing Issue #$NUM: $TITLE"
    log "========================================="

    if [ "$DRY_RUN" = true ]; then
        log "DRY RUN - Would process this issue"
        echo "Title: $TITLE"
        echo "Body preview: ${BODY:0:200}..."
        continue
    fi

    # Read the guidelines
    GUIDELINES=$(cat "$PROMPT_FILE")

    # Build the prompt for Claude
    PROMPT="A GitHub issue needs your attention for the library-manager project.

**Issue #$NUM: $TITLE**

$BODY

$(if [ -n "$COMMENTS" ] && [ "$COMMENTS" != "null" ] && [ "$COMMENTS" != "" ]; then echo "
## Previous Comments
$COMMENTS
"; fi)

## Your Task

1. First, explore the codebase to understand the project structure
2. Analyze this issue - do you fully understand what they're asking?
3. If YES and you can fix it:
   - Implement the fix
   - Update APP_VERSION in app.py (increment beta number)
   - Update CHANGELOG.md
   - Commit with 'Fixes #$NUM' in the message
   - Push to main
   - Comment on issue #$NUM using: gh issue comment $NUM --body \"your message\"
   - Close the issue using: gh issue close $NUM
4. If NO or you need more info:
   - Comment asking for clarification using: gh issue comment $NUM --body \"your question\"
   - DO NOT attempt a fix
   - DO NOT close the issue

Write responses like a real developer - casual and helpful, not formal AI-speak."

    # Save prompt to temp file
    TEMP_PROMPT="/tmp/claude-issue-$NUM.txt"
    echo "$PROMPT" > "$TEMP_PROMPT"

    log "Launching Claude Code..."

    if [ "$USE_CLI" = true ]; then
        # CLI mode (uses API credits)
        claude -p "$PROMPT" \
            --dangerously-skip-permissions \
            --append-system-prompt "$GUIDELINES"
    else
        # Interactive mode using tmux (uses Max subscription)
        # Check if tmux is available
        if ! command -v tmux &> /dev/null; then
            log "tmux not installed - falling back to CLI mode"
            log "Install tmux for interactive mode: sudo apt install tmux"
            claude -p "$PROMPT" \
                --dangerously-skip-permissions \
                --append-system-prompt "$GUIDELINES"
        else
            # Create a tmux session and run claude interactively
            SESSION_NAME="claude-issue-$NUM"

            # Kill existing session if any
            tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true

            # Create new session and run claude with the prompt
            # The prompt is passed as initial input
            tmux new-session -d -s "$SESSION_NAME" -c "$PROJECT_DIR"

            # Send the claude command with prompt
            tmux send-keys -t "$SESSION_NAME" "claude \"$PROMPT\"" Enter

            log "Claude Code started in tmux session: $SESSION_NAME"
            log "To attach: tmux attach -t $SESSION_NAME"
            log "To check status: tmux ls"

            # Wait a bit for it to start
            sleep 2

            # For fully automated: wait for session to end
            # For semi-automated: just notify and let user attach
            log ""
            log "Claude is working on issue #$NUM in the background."
            log "Attach to watch: tmux attach -t $SESSION_NAME"
        fi
    fi

    # Clean up temp file
    rm -f "$TEMP_PROMPT"

    # Mark as processed
    echo "$NUM" >> "$STATE_FILE"

    log "Finished processing issue #$NUM"

    # Small delay between issues
    sleep 5
done

log ""
log "All issues processed!"
