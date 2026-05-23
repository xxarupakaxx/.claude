---
description: 強制力ゲート (pre-dangerous-command-block) を一時的にバイパスする
argument-hint: <理由> [--ttl=1h|30m|10m]
---

# /hardgate-disable

危険コマンドブロック hook を TTL 付きで一時バイパスする。
緊急時の escape hatch。バイパス使用は blocked.jsonl に必ず記録される。

## 使い方

```
/hardgate-disable 緊急ロールバック対応
/hardgate-disable 検証用 --ttl=10m
/hardgate-disable リカバリ --ttl=30m
```

引数:
- `$1` (必須): バイパス理由 (人間が読む文字列)
- `--ttl=<duration>` (省略可): TTL。デフォルト 1h。形式: `10m` / `30m` / `1h`

## 動作

1. `~/.claude/.local/hooks/state/hardgate_bypass.json` に以下を書き込む:
   ```json
   {
     "reason": "<理由>",
     "expires_at": <unix_timestamp>,
     "issued_at": <unix_timestamp>
   }
   ```
2. TTL 経過後、`pre-dangerous-command-block.sh` が次の起動時に自動削除
3. バイパス有効期間中、危険コマンドはブロックされず **ただし blocked.jsonl に bypass_used:true で記録**
4. 早期解除: `/hardgate-enable` (もしくは `rm ~/.claude/.local/hooks/state/hardgate_bypass.json`)

## CRITICAL

- 緊急時以外は使わない (常用は禁止)
- バイパス使用は監査ログに永続記録される
- TTL は最小限に (10m-30m 推奨)

## 実装

ユーザーが `/hardgate-disable <reason> [--ttl=...]` を打ったら、以下を実行:

```bash
REASON="$1"  # 引数の最初の単語以降全て
TTL_SEC=3600  # default 1h
# --ttl=10m / --ttl=30m / --ttl=1h パース
# 残り引数を REASON に集約

NOW=$(date +%s)
EXPIRES=$((NOW + TTL_SEC))

mkdir -p ~/.claude/.local/hooks/state
jq -n \
  --arg r "$REASON" \
  --argjson e "$EXPIRES" \
  --argjson i "$NOW" \
  '{reason: $r, expires_at: $e, issued_at: $i}' \
  > ~/.claude/.local/hooks/state/hardgate_bypass.json

echo "HARDGATE バイパス有効化: reason='$REASON' / 有効期限: $(date -r $EXPIRES '+%Y-%m-%d %H:%M:%S')"
```
