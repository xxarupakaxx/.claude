# Library Research Rules

ライブラリ/フレームワーク使用時に適用されるルール。

## Context7を使う場面

- 新しいライブラリの導入検討時
- APIの使い方を確認する時
- バージョンアップ時の変更点確認
- エラー解決時の公式ドキュメント参照
- 非推奨（deprecated）警告への対応時

## Context7の使用手順

1. `resolve-library-id`でライブラリIDを取得
   - 入力: ライブラリ名（例: `react`, `prisma`）
   - 出力: Context7互換ID（例: `/facebook/react`, `/prisma/docs`）

2. `query-docs`でドキュメントを取得
   - 入力: ライブラリID + 質問/タスク
   - 出力: 関連ドキュメント（コード例、API説明等）

## よく使うライブラリID一覧

### フロントエンド
| ライブラリ | ID |
|-----------|-----|
| React | `/facebook/react` |
| Next.js | `/vercel/next.js` |
| Vue | `/vuejs/core` |
| Svelte | `/sveltejs/svelte` |

### スタイリング
| ライブラリ | ID |
|-----------|-----|
| Tailwind CSS | `/tailwindlabs/tailwindcss` |
| shadcn/ui | `/shadcn-ui/ui` |
| Radix UI | `/radix-ui/primitives` |

### バックエンド
| ライブラリ | ID |
|-----------|-----|
| Express | `/expressjs/express` |
| Hono | `/honojs/hono` |
| NestJS | `/nestjs/nest` |
| Fastify | `/fastify/fastify` |

### ORM/Database
| ライブラリ | ID |
|-----------|-----|
| Prisma | `/prisma/docs` |
| Drizzle | `/drizzle-team/drizzle-orm` |
| TypeORM | `/typeorm/typeorm` |

### ユーティリティ
| ライブラリ | ID |
|-----------|-----|
| Zod | `/colinhacks/zod` |
| date-fns | `/date-fns/date-fns` |
| Lodash | `/lodash/lodash` |

## ツールの使い分け

| 目的 | ツール | 理由 |
|------|--------|------|
| ライブラリの最新API確認 | **Context7** | バージョン固有の正確な情報 |
| OSSリポジトリの設計理解 | deepwiki | 実装詳細、アーキテクチャ |
| 一般的な技術情報 | WebSearch | ブログ、比較記事、チュートリアル |

## 注意事項

- Context7が対応していないライブラリもある（その場合はdeepwikiまたはWebSearch使用）
- ライブラリIDが不明な場合は`resolve-library-id`で検索
- 複数バージョンがある場合、最新の安定版ドキュメントが返される
