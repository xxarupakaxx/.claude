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
context_file="$state_dir/claude_context.json"
mkdir -p "$state_dir"
temp_file="$(mktemp "$state_dir/claude_status.XXXXXX")"
jq -n \
  --arg state "$state" \
  --argjson updated "$(date +%s)" \
  '{state:$state, updated:$updated}' > "$temp_file"
mv "$temp_file" "$state_file"

# Headless/background Claude sessions do not render the status line, so refresh
# the shared context metric from the transcript carried by hook events.
transcript_path="$(printf '%s' "$input" | jq -r '.transcript_path // empty')"
context=""
if [[ -f "$transcript_path" ]]; then
  usage_json="$(
    tail -r "$transcript_path" 2>/dev/null \
      | jq -c 'select(.type == "assistant" and (.message.usage | type == "object"))
          | {
              model: (.message.model // ""),
              tokens: ((.message.usage.input_tokens // 0)
                + (.message.usage.cache_creation_input_tokens // 0)
                + (.message.usage.cache_read_input_tokens // 0))
            }' 2>/dev/null \
      | head -n 1
  )"
  model="$(printf '%s' "$usage_json" | jq -r '.model // empty' 2>/dev/null)"
  tokens="$(printf '%s' "$usage_json" | jq -r '.tokens // empty | floor' 2>/dev/null)"
  if [[ "$tokens" =~ ^[0-9]+$ ]]; then
    context_size=200000
    [[ "$model" == claude-*-5* || "$tokens" -gt 200000 ]] \
      && context_size=1000000
    context=$(( (tokens * 100 + context_size / 2) / context_size ))
    (( context > 100 )) && context=100
  fi
fi
context_temp="$(mktemp "$state_dir/claude_context.XXXXXX")"
if [[ "$context" =~ ^[0-9]+$ ]]; then
  jq -n --argjson context "$context" --argjson updated "$(date +%s)" \
    '{context:$context, updated:$updated}' > "$context_temp"
else
  jq -n --argjson updated "$(date +%s)" \
    '{context:null, updated:$updated}' > "$context_temp"
fi
mv "$context_temp" "$context_file"

/opt/homebrew/bin/sketchybar --trigger claude_status_changed >/dev/null 2>&1 || true
