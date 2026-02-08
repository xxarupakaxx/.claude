---
name: confluence-export
description: kiro design.mdをConfluence用Markdown（PlantUMLダイアグラム）に変換し、mcp-atlassianでConfluenceページを作成・更新。/kiro:spec-design完了後または手動で実行。使用タイミング: (1) design完了後のConfluence出力依頼、(2) /confluence-export {feature}実行時。
model: opus
---

# Confluence Export Skill

design.md をConfluence用に整形し、mcp-atlassianを使ってConfluenceページを直接作成・更新するスキル。
ConfluenceはMarkdownをサポートしているため、基本的にはMarkdown形式を維持し、ダイアグラムのみPlantUML形式に変換する。

## 既存設定との関係

- **kiro:spec-design**: design.md生成後に本スキルを実行
- **mcp-atlassian**: Confluence API連携に使用
- **出力先**: Confluenceページ（YDBSOL空間、「内部仕様」配下）

## トリガー条件

1. `/confluence-export {feature}` を実行した場合
2. design完了後に「Confluenceに出力」「Confluence形式で」「wikiに更新」等のリクエストがあった場合

## ワークフロー

### Step 1: 引数確認

- Feature name: 第1引数または直前のdesign対象feature
- 引数なしの場合: 直前に作業したfeatureを使用

### Step 2: バリデーション

以下を確認:

- `.kiro/specs/{feature}/` が存在すること
- `.kiro/specs/{feature}/design.md` が存在すること

存在しない場合はエラーメッセージを表示して終了。

### Step 3: design.md読み込み

`.kiro/specs/{feature}/design.md` を読み込む。

### Step 4: Confluence用に変換・整形

以下のルールを適用:

1. **出力フォーマット**: @references/output-format.md
2. **ダイアグラム変換**: @references/confluence-conversion-rules.md

変換結果を `.kiro/specs/{feature}/confluence.md` にも保存する（ローカルバックアップ用）。

### Step 5: 更新内容のプレビュー表示（IMPORTANT）

**CRITICAL: Confluenceに書き込む前に、必ず以下を表示してユーザーに確認を取ること。**

1. **ページタイトル**: `内部仕様 - {機能名（日本語）}` 形式
2. **変換後のコンテンツ全文**: confluence.mdの内容を表示
3. **操作種別**: 新規作成 or 既存ページ更新
   - 既存ページの場合はページIDとURLも表示
4. **親ページ**: 「内部仕様」（ID: 900613032）

AskUserQuestionツールで以下を確認:
- 「この内容でConfluenceに{作成/更新}してよろしいですか？」
- 選択肢: 「はい、実行してください」/「タイトルを変更したい」/「内容を修正したい」

**ユーザーの承認なしにConfluenceへの書き込みを実行してはならない。**

### Step 6: Confluenceページの作成 or 更新

#### 6.1 既存ページの検索

親ページ（ID: 900613032）の子ページから、同名タイトルのページを検索:

```
mcp-atlassian confluence_get_page_children(parent_id="900613032")
```

#### 6.2 ページが存在しない場合: 新規作成

```
mcp-atlassian confluence_create_page(
  space_key="YDBSOL",
  title="内部仕様 - {機能名}",
  content=<変換後のMarkdown>,
  parent_id="900613032",
  content_format="markdown"
)
```

#### 6.3 ページが存在する場合: 更新

```
mcp-atlassian confluence_update_page(
  page_id=<既存ページID>,
  title="内部仕様 - {機能名}",
  content=<変換後のMarkdown>,
  content_format="markdown",
  version_comment="design.mdから自動更新"
)
```

### Step 7: 完了報告

以下を報告:

- ローカル保存先: `.kiro/specs/{feature}/confluence.md`
- Confluenceページ: URL（作成 or 更新結果から取得）
- 操作種別: 新規作成 / 更新
- PlantUMLダイアグラムがある場合は「PlantUMLマクロが必要です」と注記

## 設定

| 項目 | 値 |
|------|-----|
| Confluence空間 | YDBSOL |
| 親ページID | 900613032 |
| 親ページタイトル | 内部仕様 |
| ページタイトル形式 | `内部仕様 - {機能名}` |
| コンテンツ形式 | markdown |

## 使用例

```bash
# design完了後
/confluence-export gate-opening-delay-display

# 直前のfeature対象
/confluence-export
```

## 注意事項

- **書き込み前に必ずユーザー確認を取ること**
- Markdown形式はそのまま維持（Confluenceがサポート）
- Mermaid/アスキーアート → PlantUML形式に変換
- PlantUMLマクロがConfluenceにインストールされている前提
- 見出しにアイコンを付けて視認性を向上
- 図を積極的に使用（システム構成、データフロー、処理フロー）
- 長い箇条書きはテーブルで整理
- 既存ページタイトルの命名規則「内部仕様 - {機能名}」に従うこと
