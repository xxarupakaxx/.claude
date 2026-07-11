---
name: setting-up-pre-commit-hooks
description: 現在のリポジトリに、lint-staged（Prettier）、型検査、テストを実行する Husky pre-commit hook を設定する。ユーザーが pre-commit hook の追加、Husky の設定、lint-staged の構成、コミット時の整形、型検査、テストを望む場合に使用する。
---

# Pre-commit hook を設定する

## 設定するもの

- **Husky** の pre-commit hook
- staged ファイルすべてに Prettier を実行する **lint-staged**
- **Prettier** の設定（存在しない場合）
- pre-commit hook 内の **typecheck** と **test** スクリプト

## 手順

### 1. パッケージマネージャーを判定する

`package-lock.json`（npm）、`pnpm-lock.yaml`（pnpm）、`yarn.lock`（yarn）、`bun.lockb`（bun）を確認する。
存在するものを使う。
判別できない場合は npm を既定とする。

### 2. 依存パッケージをインストールする

次を devDependencies としてインストールする。

```
husky lint-staged prettier
```

### 3. Husky を初期化する

```bash
npx husky init
```

このコマンドは `.husky/` ディレクトリを作成し、package.json に `prepare: "husky"` を追加する。

### 4. `.husky/pre-commit` を作成する

次の内容を書く（Husky v9 以降では shebang は不要）。

```
npx lint-staged
npm run typecheck
npm run test
```

**調整**：`npm` を検出したパッケージマネージャーへ置き換える。
package.json に `typecheck` または `test` スクリプトがない場合は該当行を省き、そのことをユーザーへ伝える。

### 5. `.lintstagedrc` を作成する

```json
{
  "*": "prettier --ignore-unknown --write"
}
```

### 6. `.prettierrc` を作成する（存在しない場合）

Prettier の設定が存在しない場合だけ作成する。
次の既定値を使う。

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

### 7. 検証する

- [ ] `.husky/pre-commit` が存在し、実行可能である。
- [ ] `.lintstagedrc` が存在する。
- [ ] package.json の `prepare` スクリプトが `"husky"` である。
- [ ] `prettier` の設定が存在する。
- [ ] `npx lint-staged` を実行し、動作を確認する。

### 8. コミットする

変更および作成したファイルをすべて stage し、`Add pre-commit hooks (husky + lint-staged + prettier)` というメッセージでコミットする。

新しい pre-commit hook が実行されるため、このコミットは適切なスモークテストにもなる。

## 注記

- Husky v9 以降の hook ファイルに shebang は不要である。
- `prettier --ignore-unknown` は、Prettier が解析できないファイル（画像など）をスキップする。
- pre-commit は、最初に高速で staged ファイルだけを対象にする lint-staged を実行し、その後に完全な型検査とテストを実行する。
