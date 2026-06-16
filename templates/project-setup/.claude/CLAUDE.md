# Project Settings

## 基本設定

BASE_BRANCH=main
MEMORY_DIR=.local

## PJ固有の品質チェック

```bash
# typecheck
npm run typecheck

# lint
npm run lint

# test
npm run test
```

## PJ固有のレビュー観点

- このPJでは特に[ドメイン固有の観点]を重視する
- [フレームワーク名]の公式パターンに従うこと

## Bullpen 設定（自動開発ループ用）

### レビュー観点

PJ固有のドメインレビュアーを `.claude/agents/` に配置:
- `domain-reviewer.md` — ビジネスロジック/ドメイン整合性

### デプロイ

- デプロイ先: [Cloud Run / Vercel / etc.]
- デプロイコマンド: `npm run deploy`
- ステージング確認URL: [URL]
