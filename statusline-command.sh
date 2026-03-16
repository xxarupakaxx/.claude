#!/bin/bash
# Claude Code statusline script
# Format: folder | repo|branch | ctx% model | 5h:X% 7d:X%(~reset)

input=$(cat)

# 1. Current folder name
cwd=$(echo "$input" | jq -r '.workspace.current_dir')
dir=$(basename "$cwd")

# 2. Repo name | branch
branch=$(git -C "$cwd" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')
repo_name=""
if [ -n "$branch" ]; then
  repo_url=$(git -C "$cwd" config --get remote.origin.url 2>/dev/null || echo '')
  if [ -n "$repo_url" ]; then
    repo_name=$(echo "$repo_url" | sed -E 's/.*[:/]([^/]+\/[^/]+)(\.git)?$/\1/' | sed 's/\.git$//')
  fi
fi

# 3. Context usage & model
pct=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
model=$(echo "$input" | jq -r '.model.display_name // .model.id // "?"')

if [ "$pct" -ge 90 ]; then
  pct_color='\033[31m'
elif [ "$pct" -ge 70 ]; then
  pct_color='\033[33m'
else
  pct_color='\033[32m'
fi

# 4. OAuth usage API (cached 60s)
CACHE_FILE="/tmp/.claude-usage-cache.json"
CACHE_TTL=60

usage_color() {
  local val="${1%.*}"
  if [ "$val" -ge 80 ] 2>/dev/null; then
    echo '\033[31m'
  elif [ "$val" -ge 50 ] 2>/dev/null; then
    echo '\033[33m'
  else
    echo '\033[32m'
  fi
}

fetch_usage() {
  local token
  token=$(security find-generic-password -s "Claude Code-credentials" -w 2>/dev/null \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['claudeAiOauth']['accessToken'])" 2>/dev/null)
  if [ -z "$token" ]; then
    return 1
  fi
  curl -s --max-time 3 \
    -H "Authorization: Bearer $token" \
    -H "anthropic-beta: oauth-2025-04-20" \
    "https://api.anthropic.com/api/oauth/usage" 2>/dev/null
}

get_usage() {
  local now
  now=$(date +%s)

  # Check cache
  if [ -f "$CACHE_FILE" ]; then
    local cached_at
    cached_at=$(stat -f %m "$CACHE_FILE" 2>/dev/null || echo 0)
    local age=$(( now - cached_at ))
    if [ "$age" -lt "$CACHE_TTL" ]; then
      cat "$CACHE_FILE"
      return
    fi
  fi

  # Fetch fresh data
  local data
  data=$(fetch_usage)
  if [ -n "$data" ] && echo "$data" | jq -e '.five_hour' >/dev/null 2>&1; then
    echo "$data" > "$CACHE_FILE"
    echo "$data"
  elif [ -f "$CACHE_FILE" ]; then
    # Use stale cache on failure
    cat "$CACHE_FILE"
  fi
}

rate_info=""
usage_data=$(get_usage 2>/dev/null)
if [ -n "$usage_data" ]; then
  five_h=$(echo "$usage_data" | jq -r '.five_hour.utilization // empty')
  five_h_reset=$(echo "$usage_data" | jq -r '.five_hour.resets_at // empty')
  seven_d=$(echo "$usage_data" | jq -r '.seven_day.utilization // empty')
  seven_d_reset=$(echo "$usage_data" | jq -r '.seven_day.resets_at // empty')

  if [ -n "$five_h" ] && [ -n "$seven_d" ]; then
    five_h_int="${five_h%.*}"
    seven_d_int="${seven_d%.*}"
    s_color=$(usage_color "$five_h")
    w_color=$(usage_color "$seven_d")

    # Format reset times
    five_reset_fmt=""
    if [ -n "$five_h_reset" ]; then
      five_reset_fmt=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${five_h_reset%%.*}" "+%H:%M" 2>/dev/null || echo "")
    fi
    seven_reset_fmt=""
    if [ -n "$seven_d_reset" ]; then
      seven_reset_fmt=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${seven_d_reset%%.*}" "+%m/%d %H:%M" 2>/dev/null || echo "")
    fi

    rate_info=$(printf " | ${s_color}5h:%s%%\033[0m" "$five_h_int")
    if [ -n "$five_reset_fmt" ]; then
      rate_info=$(printf "%b\033[90m(~%s)\033[0m" "$rate_info" "$five_reset_fmt")
    fi
    rate_info=$(printf "%b ${w_color}7d:%s%%\033[0m" "$rate_info" "$seven_d_int")
    if [ -n "$seven_reset_fmt" ]; then
      rate_info=$(printf "%b\033[90m(~%s)\033[0m" "$rate_info" "$seven_reset_fmt")
    fi
  fi
fi

# Build output - each printf is a separate line
# Line 1: folder | repo|branch
line1=$(printf "\033[36m%s\033[0m" "$dir")
if [ -n "$repo_name" ] && [ -n "$branch" ]; then
  line1=$(printf "%b | \033[90m%s\033[0m|\033[33m%s\033[0m" "$line1" "$repo_name" "$branch")
elif [ -n "$branch" ]; then
  line1=$(printf "%b | \033[33m%s\033[0m" "$line1" "$branch")
fi
printf "%b\n" "$line1"

# Line 2: ctx% model
printf "${pct_color}%d%%\033[0m \033[35m%s\033[0m\n" "$pct" "$model"

# Line 3: OAuth usage (if available)
if [ -n "$rate_info" ]; then
  # Remove leading " | " from rate_info
  rate_clean=$(printf "%b" "$rate_info" | sed 's/^ | //')
  printf "%b\n" "$rate_clean"
fi
