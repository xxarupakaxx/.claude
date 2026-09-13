---
name: setting-up-pre-commit-hooks
description: 現在のrepoへHusky pre-commit、lint-staged/Prettier、既存scriptのtypecheck/testを組み込む。pre-commit、Husky、lint-stagedの設定依頼で使い、既存の設定と未コミット変更を保つ。
---

# Pre-commit hook

ユーザーが依頼したrepoだけを対象に、staged変更を整形し、既存の型検査・テストをcommit前に実行する。作業開始時にrepo、package manager、既存の `.husky` / lint-staged / Prettier設定、dirty stateを確認し、ユーザーの未コミット変更をstage・上書きしない。

## 手順

### 1. package managerと既存設定

lockfileを確認する。

| lockfile | manager |
| --- | --- |
| `package-lock.json` | npm |
| `pnpm-lock.yaml` | pnpm |
| `yarn.lock` | yarn |
| `bun.lockb` | bun |

複数ある場合はrepoの既存scriptと実行方針に合わせ、判別不能ならnpmを候補として報告する。既存設定があれば統合し、無断で置換しない。

### 2. 依存とHusky

選んだmanagerで `husky`、`lint-staged`、`prettier` をdevDependenciesへ追加する。installによるlockfile変更を行う前にdirty stateを分離し、必要な外部通信・承認境界に従う。

```bash
# npmの例。pnpm/yarn/bunでは同等のmanagerコマンドへ置き換える
npm install --save-dev husky lint-staged prettier
npx husky init
```

`npx husky init` が作る `.husky/` と package.json の `prepare: "husky"` を確認する。Husky v9以降のhookにshebangは不要。

### 3. hookと設定

`.husky/pre-commit` は既存scriptの名前を確認してから、必要な行だけを置く。

```text
npx lint-staged
npm run typecheck
npm run test
```

検出したmanagerの実行形式へ変換する。package.jsonに `typecheck` または `test` がない場合はその行を省き、欠落を報告する。既存hookの処理、環境変数、順序を壊さない。

`.lintstagedrc` がなければ次を作る。既存設定は内容を確認し、必要なpatternだけを追加する。

```json
{
  "*": "prettier --ignore-unknown --write"
}
```

`.prettierrc` がない場合だけ既定値を作る。

```json
{
  "useTabs": false,
  "tabWidth": 2,
  "printWidth": 80,
  "singleQuote": false,
  "trailingComma": "es5",
  "semi": true,
  "arrowParens": "always"
}
```

既存のformatter方針と競合する場合は新しい既定値で上書きせず、差分と選択肢を返す。

## 検証

- `.husky/pre-commit` が存在し実行可能である。
- package.jsonのprepare、lint-staged設定、Prettier設定が意図どおりである。
- `lint-staged` を安全なstaged fixtureまたは実際のstaged変更で一度実行する。
- 既存のtypecheck/testをrepoのscriptで実行し、結果を分けて記録する。
- `git diff --check` と `git status --short` で意図しないpath、削除、ユーザー変更の混入がないことを確認する。

検証に失敗したら原因を直して該当検証を再実行する。依頼外の整形、依存更新、設定変更を追加しない。

## commit

commitはユーザーが明示した場合、または現在のproject policyがこの依頼に含めている場合だけ行う。stageするのはこの作業で変更したファイルだけとし、指定されたmessageがなければ日本語の簡潔なmessage案を返す。commit前後のdirty stateと検証結果を報告する。
