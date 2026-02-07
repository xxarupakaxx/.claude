# ビデオ録画

ブラウザ自動化セッションをビデオとしてキャプチャする。デバッグ、ドキュメント作成、検証に使用。WebM形式（VP8/VP9コーデック）で出力。

## 基本的な録画

```bash
# 録画を開始
playwright-cli video-start

# アクションを実行
playwright-cli open https://example.com
playwright-cli snapshot
playwright-cli click e1
playwright-cli fill e2 "テスト入力"

# 停止して保存
playwright-cli video-stop demo.webm
```

## ベストプラクティス

### 1. わかりやすいファイル名を使用する

```bash
# ファイル名にコンテキストを含める
playwright-cli video-stop recordings/login-flow-2024-01-15.webm
playwright-cli video-stop recordings/checkout-test-run-42.webm
```

## トレーシング vs ビデオの比較

| 機能 | ビデオ | トレーシング |
|------|--------|------------|
| 出力 | WebMファイル | トレースファイル（Trace Viewerで閲覧） |
| 表示内容 | 視覚的な録画 | DOMスナップショット、ネットワーク、コンソール、アクション |
| 用途 | デモ、ドキュメント | デバッグ、分析 |
| サイズ | 大きい | 小さい |

## 制限事項

- 録画は自動化に若干のオーバーヘッドを追加する
- 大きな録画はディスク容量を大量に消費する可能性がある
