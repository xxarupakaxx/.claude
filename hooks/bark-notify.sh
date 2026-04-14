#!/bin/bash
BARK_KEY="${BARK_DEVICE_KEY:?Set BARK_DEVICE_KEY in settings.json env}"
ENCRYPT_KEY="${BARK_ENCRYPT_KEY:?Set BARK_ENCRYPT_KEY in settings.json env}"
ENCRYPT_IV="${BARK_ENCRYPT_IV:?Set BARK_ENCRYPT_IV in settings.json env}"

INPUT=$(cat)

{
  read -r TITLE
  read -r MESSAGE
  read -r CWD
  read -r TRANSCRIPT
} < <(jq -r '(.title // "Claude Code"), (.message // "Waiting for input"), (.cwd // ""), (.transcript_path // "")' <<< "$INPUT")

PROJECT=$(basename "$CWD")

BARK_URL=""
if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
  BARK_URL=$(jq -r 'select(.url) | .url | select(test("claude\\.ai/code/session_"))' "$TRANSCRIPT" 2>/dev/null | tail -1)
fi
[ -z "$BARK_URL" ] && exit 0

PAYLOAD=$(jq -n \
  --arg title "${TITLE} [${PROJECT}]" \
  --arg body "$MESSAGE" \
  --arg url "$BARK_URL" \
  --arg group "$PROJECT" \
  --arg level "timeSensitive" \
  '{title: $title, body: $body, url: $url, group: $group, level: $level}')

KEY_HEX=$(printf '%s' "$ENCRYPT_KEY" | xxd -ps -c 200)
IV_HEX=$(printf '%s' "$ENCRYPT_IV" | xxd -ps -c 200)

CIPHERTEXT=$(printf '%s' "$PAYLOAD" | openssl enc -aes-256-cbc -K "$KEY_HEX" -iv "$IV_HEX" -base64 -A)

curl -s \
  --data-urlencode "ciphertext=${CIPHERTEXT}" \
  --data-urlencode "iv=${ENCRYPT_IV}" \
  "https://api.day.app/${BARK_KEY}" &
