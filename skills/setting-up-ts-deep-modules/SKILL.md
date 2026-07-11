---
name: setting-up-ts-deep-modules
description: TypeScript リポジトリへ dependency-cruiser を組み込み、各 package を deep module にする。実装をサブフォルダへ隠し、entry-point ファイルからだけ到達できるようにする。ユーザー起動。
disable-model-invocation: true
---

# TypeScript の deep module を設定する

このリポジトリのすべての package を、狭い interface の背後に多くの振る舞いを持つ **deep module** にする。
package の公開面は package ルートのファイルである **entry point** とし、サブフォルダ内のすべてを隠す。
このスキルは [dependency-cruiser](https://github.com/sverweij/dependency-cruiser) と、entry point だけを入口にするルールをインストールし、ルールが実際に機能することを証明する。

deep module、interface、seam、depth の語彙については `/designing-codebases` スキルを実行し、その言葉を全体で使う。

## 強制する構造

```
src/packages/
  <name>/
    index.ts        ← an entry point (public). Import this from outside.
    client.ts       ← another entry point. Packages may expose SEVERAL.
    lib/            ← implementation: hidden from outside, free to import each other.
    tests/          ← co-located tests + fixtures (a subfolder, so private).
```

公開面は指定された一つの `index.ts` ではなく、package の**ルートファイル**である。
慣例として、実装を `lib/`、テストを `tests/` に置き、すべての package を同じ二フォルダ構造にする。
ただし、ルール自体は一般的である。
あらゆるサブフォルダ内の**すべて**を private にするため、新しいフォルダを設定へ追加する必要はない。

次の四つのルールをすべて `error` にする。

1. **Entry-point boundary**：package 外部のコード（application code または別の package）は、その package の entry point（ルートファイル）だけを import できる。
   サブフォルダ内は import できない。
2. **Intra-package freedom**：package 内のファイルは、互いを自由に import できる。
3. **Tests through the entry points**：`<pkg>/tests/` 配下のファイルは、あらゆる package の entry point と、自分の `tests/` fixture を import できる。
   ただし、自分の package を含め、package のサブフォルダ内の実装は import できない。
   package をまたぐ integration test は許可するが、deep import は許可しない。
4. **No cycles**：依存関係の循環を許可しない。

**Entry point であり、barrel ではない。**
公開面は**すべて**のルートファイルであるため、一つの巨大な `index.ts` にすべてを通さず、`index.ts`、`client.ts`、`server.ts` のように複数の小さな entry point を公開できる。
サブツリー全体を再 export する barrel file は避ける。
entry point を小さく保ち、実装をサブフォルダへ隠す。

どの package がどの package に依存できるかという layering は**別の**問題である。
リポジトリ側で埋めるコメント済みのスタブとして設定に残す。

## 手順

### 1. 環境を判定する

- **Package manager**：`pnpm-lock.yaml` があれば pnpm、`yarn.lock` なら yarn、`bun.lockb` なら bun、それ以外は npm を使う。
  以下のすべてのコマンドで、検出したもの（`pnpm` / `yarn` / `npm run` / `bunx`）を使う。
- **Packages root**：`src/` があれば `src/packages`、なければ `packages` を使う。
  リポジトリに別の明確な慣例がすでにある場合は、ユーザーへ確認する。
- **既存の設定**：`.dependency-cruiser.*` ファイルを探す。
  存在する場合は上書きせず、四つのルールと options をマージし、追加内容をユーザーへ伝える。

**完了条件：**package manager、packages root、既存設定の有無がすべて判明している。

### 2. dependency-cruiser をインストールする

検出した package manager を使い、`dependency-cruiser` を devDependency としてインストールする。

**完了条件：**`dependency-cruiser` が `devDependencies` にある。

### 3. 設定を書く

[`dependency-cruiser.config.cjs`](./dependency-cruiser.config.cjs) をリポジトリのルートへ `.dependency-cruiser.cjs` としてコピーする。
`PACKAGES_ROOT` を手順1で検出したルートへ設定する。
ルールはパスの深さに基づき、拡張子に依存しないため、ほかに調整するものはない。

**完了条件：**正しい `PACKAGES_ROOT` と四つの禁止ルールを含む `.dependency-cruiser.cjs` が存在する。

### 4. 検査へ組み込む

- `lint:boundaries` スクリプトを追加する：`depcruise <packages-root>`（または `depcruise src`）。
- typecheck をすでに実行するリポジトリの包括的な検査コマンド（`check`、`ci`、`validate` など）へ組み込む。
  `tsconfig` へ触れず、path alias も追加しない。
- 包括的なスクリプトがない場合は `lint:boundaries` を追加し、CI に含める必要があることをユーザーへ伝える。

**完了条件：**`lint:boundaries` が存在し、typecheck と同じコマンドの一部として実行される。

### 5. example package のひな形を作る

コピー用テンプレートとして、コミット対象の `<packages-root>/example/` を作る。

- `index.ts`：entry point。
  internal file へ処理を委譲する関数を一つ export し、単なる pass-through ではなく package が目に見えて **deep** になるようにする。
- `lib/impl.ts`：**サブフォルダ**内の internal file。
  `index.ts` から import するが、外部から到達できないようにする。
- `tests/example.test.ts`：entry point である `../index` **だけ**を import し、公開関数を検証する。

コピーまたは削除できる starter template であることをユーザーへ伝える。

**完了条件：**example package が存在し、ルートの entry point を通じて振る舞いを公開し、`impl` をサブフォルダへ隠している。

### 6. ルールが機能することを証明する

これはスキル全体の完了基準である。
違反時に失敗しない設定には価値がない。

1. `lint:boundaries` を実行する。
   正常な example で**成功**する必要がある。
2. `tests/example.test.ts` へ deep import を一時的に追加する（例：`import { thing } from "../lib/impl"`）。
   `lint:boundaries` を再実行する。
   `tests-through-entrypoints` によって**失敗**する必要がある。
3. deep import を元に戻す。
   もう一度実行し、**成功**する必要がある。

**完了条件：**成功、deep import による失敗、再び成功という順序を観測している。
手順2が失敗しない場合、ルールが正しく組み込まれていないため、完了前に修正する。

### 7. 慣例を文書化する

対象 package の隣にある packages フォルダ内（`<packages-root>/README.md`）へ `README.md` を書く。
`src/packages/<name>/` の構造（ルートの entry point、実装用の `lib/`、テスト用の `tests/`）、「package の entry point（ルートファイル）からだけ import する」というルール、`lint:boundaries` の実行方法を含める。
**barrel file を明示的に避ける**よう伝える。
一つの index でサブツリー全体を再 export せず、複数の小さな entry point を公開する。
コピー用の snippet と、四つのルールをそれぞれ一段落にまとめた長さにする。

次に、リポジトリのエージェント指示ファイルから、この文書への**コンテキストポインター**を追加する。
`CLAUDE.md` があれば使い、なければ `AGENTS.md` を使う。
どちらもなければ `AGENTS.md` を作る。
一行でよい。
例：`Packages are deep modules — see [src/packages/README.md](./src/packages/README.md) before adding or importing one.`
これにより、エージェントは境界ルールへ違反して初めて気付くのではなく、事前に発見できる。

**完了条件：**`<packages-root>/README.md` が存在して barrel を避けるよう明記し、リポジトリの `CLAUDE.md` または `AGENTS.md` からリンクされている。

## 注記

- 設定の `$1` back-reference（dependency-cruiser の group matching）によって、package 自身は内部へ到達でき、外部からは到達できない。
  package ごとの個別ルールへ平坦化しない。
- public と private は**深さ**で決まる。
  package のルートファイルが entry point で、サブフォルダ内はすべて private である。
  慣例的なサブフォルダは実装用の `lib/` と `tests/` だが、ルールには hardcode しない。
  どのサブフォルダも private なので、新しいフォルダを追加しても設定変更は不要である。
  entry point の追加はルートファイルを追加するだけで、barrel は不要になる。
- Package は**平坦**にする。
  ルート直下の一階層だけを package とする。
  package の内部は任意の深さまで入れ子にできるが、package の中に別の package を置かない。
- `"type": "module"` のリポジトリでも設定の `module.exports` が動作するように、`.js` ではなく `.cjs` を使う。
