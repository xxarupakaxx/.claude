# トレーシング

デバッグと分析のための詳細な実行トレースをキャプチャする。トレースにはDOMスナップショット、スクリーンショット、ネットワークアクティビティ、コンソールログが含まれる。

## 基本的な使い方

```bash
# トレース記録を開始
playwright-cli tracing-start

# アクションを実行
playwright-cli open https://example.com
playwright-cli click e1
playwright-cli fill e2 "test"

# トレース記録を停止
playwright-cli tracing-stop
```

## トレース出力ファイル

トレーシングを開始すると、Playwrightは `traces/` ディレクトリに以下のファイルを作成する:

### `trace-{timestamp}.trace`

**アクションログ** - 以下を含むメインのトレースファイル:
- 実行されたすべてのアクション（クリック、入力、ナビゲーション）
- 各アクションの前後のDOMスナップショット
- 各ステップのスクリーンショット
- タイミング情報
- コンソールメッセージ
- ソースの場所

### `trace-{timestamp}.network`

**ネットワークログ** - 完全なネットワークアクティビティ:
- すべてのHTTPリクエストとレスポンス
- リクエストヘッダーとボディ
- レスポンスヘッダーとボディ
- タイミング（DNS、接続、TLS、TTFB、ダウンロード）
- リソースサイズ
- 失敗したリクエストとエラー

### `resources/`

**リソースディレクトリ** - キャッシュされたリソース:
- 画像、フォント、スタイルシート、スクリプト
- リプレイ用のレスポンスボディ
- ページ状態の再構築に必要なアセット

## トレースがキャプチャするもの

| カテゴリ | 詳細 |
|---------|------|
| **アクション** | クリック、入力、ホバー、キーボード入力、ナビゲーション |
| **DOM** | 各アクションの前後の完全なDOMスナップショット |
| **スクリーンショット** | 各ステップの視覚的状態 |
| **ネットワーク** | 全リクエスト、レスポンス、ヘッダー、ボディ、タイミング |
| **コンソール** | console.log、warn、errorの全メッセージ |
| **タイミング** | 各操作の精密なタイミング |

## ユースケース

### 失敗したアクションのデバッグ

```bash
playwright-cli tracing-start
playwright-cli open https://app.example.com

# このクリックが失敗する - 原因は？
playwright-cli click e5

playwright-cli tracing-stop
# トレースを開いてクリック試行時のDOM状態を確認
```

### パフォーマンス分析

```bash
playwright-cli tracing-start
playwright-cli open https://slow-site.com
playwright-cli tracing-stop

# ネットワークウォーターフォールで遅いリソースを特定
```

### エビデンスの取得

```bash
# ドキュメント用にユーザーフロー全体を記録
playwright-cli tracing-start

playwright-cli open https://app.example.com/checkout
playwright-cli fill e1 "4111111111111111"
playwright-cli fill e2 "12/25"
playwright-cli fill e3 "123"
playwright-cli click e4

playwright-cli tracing-stop
# トレースにイベントの正確な順序が記録される
```

## トレース vs ビデオ vs スクリーンショットの比較

| 機能 | トレース | ビデオ | スクリーンショット |
|------|---------|--------|------------------|
| **形式** | .traceファイル | .webm動画 | .png/.jpeg画像 |
| **DOM検査** | 可能 | 不可 | 不可 |
| **ネットワーク詳細** | 可能 | 不可 | 不可 |
| **ステップ別リプレイ** | 可能 | 連続再生 | 単一フレーム |
| **ファイルサイズ** | 中 | 大 | 小 |
| **最適な用途** | デバッグ | デモ | クイックキャプチャ |

## ベストプラクティス

### 1. 問題が発生する前にトレーシングを開始する

```bash
# 失敗するステップだけでなく、フロー全体をトレース
playwright-cli tracing-start
playwright-cli open https://example.com
# ... 問題に至るすべてのステップ ...
playwright-cli tracing-stop
```

### 2. 古いトレースをクリーンアップする

トレースはディスク容量を大量に消費する可能性がある:

```bash
# 7日以上前のトレースを削除
find .playwright-cli/traces -mtime +7 -delete
```

## 制限事項

- トレースは自動化にオーバーヘッドを追加する
- 大きなトレースはディスク容量を大量に消費する可能性がある
- 一部の動的コンテンツは完全にリプレイできない場合がある
