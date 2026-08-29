#!/usr/bin/env bash

input="$(cat)"
event="$(printf '%s' "$input" | jq -r '.hook_event_name // empty')"
notification="$(printf '%s' "$input" | jq -r '.notification_type // empty')"

case "$event:$notification" in
  UserPromptSubmit:*) state="working" ;;
  Notification:permission_prompt|Notification:elicitation_dialog) state="blocked" ;;
  Notification:idle_prompt|Stop:*) state="complete" ;;
  StopFailure:*) state="error" ;;
  *) exit 0 ;;
esac

state_dir="${XDG_CACHE_HOME:-$HOME/.cache}/sketchybar"
state_file="$state_dir/claude_status.json"
mkdir -p "$state_dir"
temp_file="$(mktemp "$state_dir/claude_status.XXXXXX")"
jq -n \
  --arg state "$state" \
  --argjson updated "$(date +%s)" \
  '{state:$state, updated:$updated}' > "$temp_file"
mv "$temp_file" "$state_file"

/opt/homebrew/bin/sketchybar --trigger claude_status_changed >/dev/null 2>&1 || true
