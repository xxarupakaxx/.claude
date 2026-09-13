---
name: hardgate-disable
description: 明示された緊急対応で pre-dangerous-command-block の bypass を最小 TTL で有効化するときに使う。通常の作業、テスト、承認の代替には使わない。
argument-hint: <理由> [--ttl=1h|30m|10m]
---

# `/hardgate-disable`

危険コマンドをブロックする hook を一時的にバイパスする escape hatch。実行すると `~/.claude/.local/hooks/state/hardgate_bypass.json` に理由と発行・期限時刻を書き、hook は危険コマンドを `blocked.jsonl` へ `bypass_used:true` 付きで監査する。自動実行や暗黙の提案では起動しない。

## 引数と境界

```text
/hardgate-disable 緊急ロールバック対応
/hardgate-disable 検証用 --ttl=10m
```

- 理由は必須で、人間が読める目的をすべて渡す。
- `--ttl=10m`、`--ttl=30m`、`--ttl=1h` のみ受け付ける。省略時は `1h`、緊急時も `10m` または `30m` を優先する。
- 使う前に対象コマンドと、通常の承認・安全確認を省略する必要がある理由を確認する。TTLを短くしても危険性は下がるだけで、承認そのものにはならない。
- 早期解除は `rm -f -- ~/.claude/.local/hooks/state/hardgate_bypass.json`。監査記録は削除しない。

## 実行

ユーザーが明示的に `/hardgate-disable <理由> [--ttl=...]` を入力した場合だけ、次のように引数を検証して実行する。

```bash
set -eu
REASON=""
TTL_SEC=3600
for ARG in "$@"; do
  case "$ARG" in
    --ttl=10m) TTL_SEC=600 ;;
    --ttl=30m) TTL_SEC=1800 ;;
    --ttl=1h)  TTL_SEC=3600 ;;
    --ttl=*) echo "unsupported TTL: $ARG" >&2; exit 2 ;;
    *)
      if [ -n "$REASON" ]; then REASON="$REASON "; fi
      REASON="$REASON$ARG"
      ;;
  esac
done
[ -n "$REASON" ] || { echo "reason is required" >&2; exit 2; }

NOW=$(date +%s)
EXPIRES=$((NOW + TTL_SEC))
STATE_DIR=~/.claude/.local/hooks/state
mkdir -p "$STATE_DIR"
jq -n \
  --arg r "$REASON" \
  --argjson e "$EXPIRES" \
  --argjson i "$NOW" \
  '{reason: $r, expires_at: $e, issued_at: $i}' \
  > "$STATE_DIR/hardgate_bypass.json"

echo "HARDGATE バイパス有効化: reason='$REASON' / 有効期限: $(date -r "$EXPIRES" '+%Y-%m-%d %H:%M:%S')"
```

TTLが切れた後は `pre-dangerous-command-block.sh` の次回起動時削除に任せ、ファイルの期限を延長して常用しない。`jq`、hook、監査ログの状態を確認できない場合は有効化せず、ブロックとして報告する。
