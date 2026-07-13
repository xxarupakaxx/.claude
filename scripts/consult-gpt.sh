#!/usr/bin/env bash
# consult-gpt.sh — Claude Code から GPT(Codex) への単発セカンドオピニオン相談ブリッジ。
# 呼び出し規律は skills/consult-gpt/SKILL.md を参照。実装を渡すのは codex:codex-rescue、こちらは「意見だけ聞く」。
#
# 使い方:
#   consult-gpt.sh "相談内容"                        # 新規相談（Board Advisor 役割を先頭に注入）
#   consult-gpt.sh --resume <session_id> "追い質問"   # 追い質問（1回まで）
#   echo "相談内容" | consult-gpt.sh -                # stdin から
#
# 出力: codex exec のイベントログに続けて、最終応答を === ADVISOR RESPONSE === ブロックで表示。
#       session id はイベントログ冒頭に表示される。
# モデル: 既定 gpt-5.5（CONSULT_GPT_MODEL で上書き可）。config.toml の既定モデルが
#         CLI 未対応のことがある（例: gpt-5.6-sol）ため、CLI で確実に使えるモデルを明示する。
set -euo pipefail

MAX_CALLS_PER_DAY="${CONSULT_GPT_MAX_PER_DAY:-8}"
TIMEOUT_SECS="${CONSULT_GPT_TIMEOUT:-300}"
MODEL="${CONSULT_GPT_MODEL:-gpt-5.5}"
COUNT_DIR="${TMPDIR:-/tmp}/consult-gpt"
COUNT_FILE="${COUNT_DIR}/count-$(date +%Y%m%d)"

RESUME_ID=""
if [[ "${1:-}" == "--resume" ]]; then
  RESUME_ID="${2:?--resume には session_id が必要}"
  shift 2
fi

PROMPT="${1:-}"
if [[ -z "$PROMPT" || "$PROMPT" == "-" ]]; then
  PROMPT="$(cat)"
fi
if [[ -z "$PROMPT" ]]; then
  echo "usage: consult-gpt.sh [--resume <session_id>] \"相談内容\"" >&2
  exit 2
fi

# 乱用ガード: 1往復原則の機械的な裏付け（日次上限）
mkdir -p "$COUNT_DIR"
COUNT=$(( $(cat "$COUNT_FILE" 2>/dev/null || echo 0) + 1 ))
if (( COUNT > MAX_CALLS_PER_DAY )); then
  echo "consult-gpt: 日次上限 ${MAX_CALLS_PER_DAY} 回を超過したため停止する（hot path 化防止ガード）。" >&2
  echo "本当に必要ならユーザー承認を得て ${COUNT_FILE} を削除するか、CONSULT_GPT_MAX_PER_DAY を上げる。" >&2
  exit 1
fi
printf '%s' "$COUNT" > "$COUNT_FILE"

ADVISOR_ROLE='あなたは Board Advisor（セカンドオピニオン担当）として、Claude オーケストレーターから単発の相談を受けている。
役割: 戦略・設計・計画への独立した批評、リスク指摘、taste判断。実装・修正・ファイル変更は行わない。
必要なら読み取り専用でコードや設定を確認してから判断する。
出力: 結論を最初の1文で述べ、根拠は3点以内、代替案は最大1つ。相談は原則1往復なので、質問を返さずその場で判断を下す。'

OUT_FILE="$(mktemp "${COUNT_DIR}/last-message.XXXXXX")"
trap 'rm -f "$OUT_FILE"' EXIT

run_codex() {
  if command -v timeout >/dev/null 2>&1; then
    timeout "$TIMEOUT_SECS" codex "$@"
  elif command -v gtimeout >/dev/null 2>&1; then
    gtimeout "$TIMEOUT_SECS" codex "$@"
  else
    codex "$@"
  fi
}

if [[ -n "$RESUME_ID" ]]; then
  # resume ではモデル・サンドボックスを再指定できない（セッション既定で動く）
  run_codex exec resume "$RESUME_ID" --skip-git-repo-check -o "$OUT_FILE" "$PROMPT"
else
  run_codex exec -m "$MODEL" --sandbox read-only --skip-git-repo-check -o "$OUT_FILE" "${ADVISOR_ROLE}

---

${PROMPT}"
fi

echo
echo "=== ADVISOR RESPONSE ==="
cat "$OUT_FILE"
