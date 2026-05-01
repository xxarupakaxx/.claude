# Feedback Loop Recipes

バグ診断用の観測ループ10種類。**1サイクル30秒以内**を目標に設計する。

## 1. Failing Test Loop

**適用**: 単体ロジック異常、ライブラリのAPI挙動確認

```sh
# watch mode で常時実行
npm test -- --watch path/to/foo.test.ts
# or
pytest -x -k "test_foo" --looponfail
```

**設計**: 失敗を再現するテストをまず書く。修正中はwatchが回り続ける。

## 2. curl / HTTP Probe Loop

**適用**: HTTP API、Webhook受信、外部サービス連携

```sh
# テンプレ
while true; do
  curl -sS -w '\n[%{http_code} %{time_total}s]\n' \
    -X POST http://localhost:3000/api/foo \
    -H 'Content-Type: application/json' \
    -d '{"input":"bug-trigger"}' | tee /tmp/last-response.json
  read -p "Press enter to retry..."
done
```

**ポイント**: `-w` でステータス・時間も記録。`tee` で過去レスポンスを保持。

## 3. CLI Fixture Loop

**適用**: コマンドラインツール、変換スクリプト、CLIエントリポイント

```sh
# fixture を固定し、コマンドを1行で
echo '{"trigger": "bug"}' > /tmp/fixture.json
./your-cli --input /tmp/fixture.json --debug 2>&1 | tee /tmp/last-output.txt
```

**ポイント**: fixtureを固定化することで「再現性」が消えるリスクを排除。

## 4. Headless Browser Loop

**適用**: フロントエンド、SPA、E2E異常、レイアウト崩れ

`playwright-skill` を使用:

```sh
playwright-cli goto http://localhost:3000/buggy-page
playwright-cli click 'button[data-test="trigger"]'
playwright-cli screenshot /tmp/state.png
```

**ポイント**: スクショを比較することで「失敗」を機械判定可能にする。

## 5. Replay Trace Loop

**適用**: 本番でしか出ない、ログから後追いで再現したい

```sh
# 本番ログから入力を抽出
grep "request_id=abc123" /var/log/app.log | jq -r '.payload' > /tmp/replay-input.json

# 入力をローカルにリプレイ
node scripts/replay.js /tmp/replay-input.json
```

**ポイント**: ログ→fixture→ローカル実行 のパイプライン。tracing IDを軸にする。

## 6. Throwaway Harness Loop

**適用**: 既存コードに組み込めない、ライブラリ単独の挙動確認

```sh
# 最小再現スクリプトを作成
cat > /tmp/repro.ts <<'EOF'
import { suspectFunction } from '../src/foo';
console.log(suspectFunction({ input: 'bug-trigger' }));
EOF
npx tsx /tmp/repro.ts
```

**ポイント**: 修正後は `/tmp/repro.ts` を捨てる（コードベースに混入させない）。

## 7. Property / Fuzz Loop

**適用**: 入力依存性が高い、エッジケース全般

```sh
# fast-check (TypeScript) の例
npx jest property-test.ts --testTimeout=60000
```

```ts
import fc from 'fast-check';
test('foo never throws', () => {
  fc.assert(fc.property(fc.anything(), (input) => {
    expect(() => foo(input)).not.toThrow();
  }));
});
```

**ポイント**: fast-check / hypothesis / proptestなどの property-based testing。`shrink` で最小反例を得る。

## 8. Bisection Loop

**適用**: いつから壊れたか不明、回帰原因の追跡

```sh
git bisect start
git bisect bad HEAD
git bisect good v1.2.0

# 自動化版
git bisect run npm test -- --testPathPattern=regression
```

**ポイント**: `git bisect run` で完全自動化。テストが10秒以下なら数十コミットでも数分で終わる。

## 9. Differential Loop

**適用**: 既存の正解と比較したい、リファクタの等価性確認

```sh
# 同じ入力を2実装に流して差分を見る
for input in fixtures/*.json; do
  out_old=$(node old-impl.js < "$input")
  out_new=$(node new-impl.js < "$input")
  if [ "$out_old" != "$out_new" ]; then
    echo "DIFF: $input"
    diff <(echo "$out_old") <(echo "$out_new")
  fi
done
```

**ポイント**: ゴールデンファイル比較とも相性が良い。

## 10. HITL Bash Loop

**適用**: 環境依存性が強い、自動化が難しい、本番アクセスが必要

ユーザーが手で叩くテンプレを作り、AIは観測のみ:

```sh
# template
cat <<'EOF'
[ユーザーへ] 以下を実行し、出力を貼り付けてください:

  ssh prod-host 'tail -n 50 /var/log/app.log | grep ERROR'

EOF
```

詳細: `references/hitl-loop.template.sh`

---

## 選択ガイド

| 状況 | レシピ |
|------|--------|
| まずローカルで再現したい | 1, 3, 6 |
| 本番障害の調査 | 5, 10 |
| フレーキー / たまに再現 | 7, 8 |
| 性能劣化 | 2 (with `time_total`), 9 |
| UI崩れ | 4 |
| いつから壊れた | 8 |

複数組み合わせ可（例: 8+1 で git bisect run + failing test）。
