# Mermaid Validator ループ（CRITICAL）

`generate-state-diagram` SKILL.md Step 6.5 から参照される検証手順。

**背景**: 生成した Mermaid 図が構文エラーで render されない事案が複数発生（`[/text]` のスラッシュ衝突、`<task>` HTML タグ、`-.text.->` のドット衝突、stateDiagram の二重定義 等）。**生成して終わり** ではなく、**MCP server で構文検証してから完了** とする。

## 前提条件

`~/.claude.json` の `mcpServers` に `mermaid-mcp` が登録されていること:

```json
{
  "mcpServers": {
    "mermaid-mcp": {
      "type": "http",
      "url": "https://mcp.mermaid.ai/mcp"
    }
  }
}
```

## 検証ループ手順

```
1. 生成した .md ファイルから ```mermaid ... ``` ブロックを正規表現で全抽出
   (例: Bash で `awk '/^```mermaid$/,/^```$/' file.md`)

2. 各ブロックを連番付きでメモリに保持
   - block_1: flowchart TD ...
   - block_2: stateDiagram-v2 ...
   - block_N: ...

3. 各ブロックを順次 mcp__mermaid-mcp__validate_and_render_mermaid_diagram に投入
   - 入力: { "code": "<mermaid 構文>" }
   - 出力: { "valid": true/false, "errors": [...], "rendered_url": "..." }

4. エラーがあればエラー内容を解析して該当ブロックを修正
   - 典型的な修正パターン:
     a. ノードラベルに /, :, +, (, ), <, > が含まれる → ダブルクォート ["..."] で囲む
     b. 矢印ラベルにドット . が含まれる → -. "text" .-> 形式に変更
     c. stateDiagram で同じ state が二重定義 → 重複削除
     d. <br/> タグが効かない → 改行 \n または引用符化
     e. & 演算子（古い mermaid 非対応）→ 個別矢印に展開

5. 修正後、再度 validator に投入
   - 最大 3 ラウンド試行
   - 全 PASS なら次のステップへ

6. 3 ラウンド経ても失敗するブロックは、当該 mermaid ブロック直前に警告コメントを残す:
   <!-- ⚠️ Mermaid Validator FAILED after 3 rounds. Last error: <内容> -->
   <!-- レンダリングされない可能性があります。手動確認が必要です。 -->
   そして処理を続行（他ブロックは PASS とみなしてユーザーに通知）

7. 検証ログを `<filename>.validation.log` に保存:
   [PASS] block_1 (flowchart TD)
   [PASS] block_2 (stateDiagram-v2)
   [FAIL→PASS] block_3 (sequenceDiagram, 1 round)
   [FAIL] block_4 (classDiagram) — see warning comment in file
```

## 修正対応の優先順位

| エラー種別 | 対応 |
|----------|------|
| Syntax Error (致命的) | 必ず修正、ループ続行 |
| Warning (推奨修正) | 修正試行、PASS なら次へ |
| Render Warning（描画上の問題のみ）| 警告コメント残して続行 |

## スキップ条件

- ファイル中に Mermaid ブロックが 0 個
- ユーザーが明示的に `--skip-validator` を指定（オプション）
- MCP server がオフライン（連続 3 回タイムアウト）→ 警告コメントを残して続行
