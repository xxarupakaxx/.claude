---
name: create-skill
description: 新しいSkillの作成や、既存Skillの説明・構成・起動条件の整理を依頼されたときに使う。
allowed-tools: Read, Write, Glob, Grep
---

# Skillを作成・整理する

`/create-skill [--user|--project] <内容>`で使う。既定はuser scope。既存Skillの改訂では、そのSkillの配置と名前を維持する。

## 必要性と範囲を決める

現在の依頼と近いCLAUDE.mdを確認し、必要な正本だけを読む。関連する既存Skillのname・descriptionを検索して重複を確かめる。`context/*.md`、`rules/*.md`、全Skill本文の一括読込は行わない。

繰り返し使う固有の知識・手順・scriptがあればSkillにする。一回限りならtask promptで足りる。CLAUDE.mdには毎回必要な不変条件と条件付き参照だけを置く。Skillを追加すること自体を目的にしない。

第三者Skillの導入・更新・廃止は`skill-governance`へ戻る。未使用の証拠なしに削除せず、既存の依頼範囲を超えて有効・無効設定を変えない。

## 起動条件を短く書く

descriptionは「何をするか」と「いつ使うか」が分かる短い文にする。同義語、利用場面の長い列挙、性能の宣伝、広すぎる必須トリガーを入れない。

例: `データベースのschema移行を作成・検証する。migration変更時に使う。`

データベース全般への言及だけでmigration Skillを起動するような説明は避ける。関連するが対象外の依頼でも選ばれないか確認する。

## 本文は必要な分岐への入口にする

SKILL.mdには目的、選択条件、固有の判断、重要な制約、参照先を残す。複数workflowがあれば「この場合はこの参照を読む」と分け、例・テンプレート・長い手順を`references/`へ置く。単純なSkillは一つの短い本文でよい。

共通のPhase・承認・test手順を複製せず、正本へ参照を置く。モデル名だけを理由に固定の読込順、全test、全員reviewを要求しない。完了条件と必要な証拠を示し、実装方法は現行projectに合わせる。

新規作成時のfrontmatterと配置例は[Skillテンプレート](references/skill-template.md)を読む。既存Skillの局所修正では必要な項目だけ参照する。

## 完了を確認する

frontmatter、参照先、起動すべき依頼と起動すべきでない依頼を確認する。scriptを変更した場合は、その変更に対応する検証を行う。変更したSkillを全文で読み、本文と参照先の矛盾、共通指示の重複を解消する。

変更したファイル、使い方、実施した確認を報告する。短さだけで必要な制約や例外を落とさない。
