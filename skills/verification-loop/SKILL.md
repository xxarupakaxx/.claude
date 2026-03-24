---
name: verification-loop
description: "合格基準を定義し、通過するまで検証を自動繰り返しするスキル。/checkpointで状態保存、/verifyで検証実行。Phase 4の品質確認を自動化する。"
---

# Verification Loop — 自動検証ループ

## 概要

合格基準（Pass Criteria）を定義し、全基準を通過するまで検証→修正→再検証を自動で繰り返す。
手動の品質確認を自動化し、見落としを防止する。

## トリガー

- 「検証ループを回して」
- 「合格するまでチェックして」
- `/verify`
- Phase 4の品質確認時

## コンポーネント

### `/checkpoint` — 検証状態の保存

現在の状態をスナップショットとして保存:

```markdown
## Checkpoint: YYYY-MM-DD HH:MM

### Pass Criteria
- [ ] TypeScript: `npx tsc --noEmit` がエラー0
- [ ] Lint: `npm run lint` がエラー0
- [ ] Test: `npm test` が全パス
- [ ] Build: `npm run build` が成功
- [ ] Security: `security-reviewer` が CRITICAL 0件
- [ ] Custom: [ユーザー定義の基準]

### Current Status
- tsc: ❌ 3 errors
- lint: ✅ pass
- test: ❌ 2 failures
- build: ❌ blocked by tsc
```

保存先: `${MEMORY_DIR}/memory/YYMMDD_<task>/checkpoint.md`

### `/verify` — 検証ループ実行

1. checkpoint.mdの合格基準を読み込み
2. 各基準を順次実行
3. 失敗した基準を修正
4. 再検証
5. 全基準通過まで繰り返し

## 検証ループのフロー

```
START
  │
  ▼
[合格基準の定義/読込]
  │
  ▼
[基準1を実行] ──PASS──→ [基準2を実行] ──PASS──→ ... ──→ [全PASS] → END
  │                        │
  FAIL                     FAIL
  │                        │
  ▼                        ▼
[エラー分析]              [エラー分析]
  │                        │
  ▼                        ▼
[最小修正]                [最小修正]
  │                        │
  ▼                        ▼
[基準1を再実行]           [基準2を再実行]
  │                        │
  └── 最大3回失敗 ──→ ユーザーに報告（自動修正限界）
```

## 合格基準テンプレート

### TypeScript プロジェクト
```yaml
criteria:
  - name: typecheck
    command: "npx tsc --noEmit"
    pass: "exit code 0"
  - name: lint
    command: "npm run lint"
    pass: "exit code 0"
  - name: test
    command: "npm test"
    pass: "exit code 0"
  - name: build
    command: "npm run build"
    pass: "exit code 0"
```

### カスタム基準の追加
ユーザーが自由に基準を追加可能:
```yaml
  - name: coverage
    command: "npm test -- --coverage"
    pass: "All files.*[89][0-9]|100"  # 80%以上
  - name: bundle-size
    command: "npm run build && du -sh dist/"
    pass: "size < 5M"
```

## 安全ガード

- **最大ループ回数**: 5回（無限ループ防止）
- **同一エラー3回失敗**: 自動修正を中止し、ユーザーに報告
- **修正の副作用検出**: 修正後に以前PASSだった基準がFAILになったら即報告
- **LLMのみの連続修正は最大3回**: 以降はサブエージェントレビューを挟む（workflow-rules.md準拠）

## `generate-verification-guide`との関係

- `generate-verification-guide`: 手動テスト用のチェックリスト**ドキュメント生成**
- `verification-loop`: 自動テストの**実行と修正ループ**
- 併用推奨: verification-loopで自動チェック → 残りを手動チェックリストで確認
