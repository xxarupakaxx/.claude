# 対象外の knowledge base

repo の `.out-of-scope/` directory には、却下した feature request の永続的な記録を保存する。
目的は二つある。

1. **組織の記憶**：feature を却下した理由を残し、issue の close 後も判断の根拠を失わない。
2. **重複の排除**：以前に却下したものと一致する新しい issue が来たとき、同じ議論を繰り返さず、以前の決定を提示する。

## Directory 構成

```
.out-of-scope/
├── dark-mode.md
├── plugin-system.md
└── graphql-api.md
```

issue ごとではなく、**concept** ごとに一つのファイルを使う。
同じものを要求する複数の issue は、一つのファイルにまとめる。

## ファイル形式

database entry よりも短い design document に近い、堅すぎず読みやすい文体で書く。
初めて読む人にも判断の根拠が明確で役立つように、段落、code sample、例を使う。

```markdown
# ダークモード

この project は dark mode とユーザー向けの theming に対応しない。

## 対象外にする理由

rendering pipeline は、`ThemeConfig` で定義した単一の color palette を前提とする。
複数の theme へ対応するには、次の変更が必要になる。

- component tree 全体を囲む theme context provider
- component ごとの theme-aware な style 解決
- ユーザーの theme 設定を保存する persistence layer

これは大規模な architecture 変更であり、content authoring に集中する project の方針と合わない。
theming は、出力を埋め込む、または再配布する downstream consumer が扱う。

```ts
// The current ThemeConfig interface is not designed for runtime switching:
interface ThemeConfig {
  colors: ColorPalette; // single palette, resolved at build time
  fonts: FontStack;
}
```

## 以前の request

- #42：「dark mode への対応を追加してほしい」
- #87：「accessibility のための night theme」
- #134：「dark theme option」
```

### ファイル名

concept を表す短く説明的な kebab-case の名前を使う。
例は `dark-mode.md`、`plugin-system.md`、`graphql-api.md` である。
directory を見るだけで、ファイルを開かずに却下したものを理解できる名前にする。

### 理由を書く

「望まない」だけでなく、その理由を具体的に書く。
良い理由は次の事項を参照する。

- project の scope または方針（「この project は X に集中しており、theming は downstream consumer の責務である」）
- 技術的な制約（「対応には Y が必要だが、Z architecture と競合する」）
- 戦略上の決定（「次の理由から B ではなく A を選んだ……」）

理由は長く通用するものにする。
「今は忙しすぎる」のような一時的な事情は避ける。
それは却下ではなく延期である。

## `.out-of-scope/` を確認する時期

triage の step 1「コンテキストを集める」で、`.out-of-scope/` のすべてのファイルを読む。
新しい issue を評価するときは、次を行う。

- request が既存の対象外 concept と一致するか確認する。
- keyword ではなく concept の類似性で照合する。
「night theme」は `dark-mode.md` と一致する。
- 一致した場合は maintainer に伝える。
「これは `.out-of-scope/dark-mode.md` と似ています。
以前は [reason] のため却下しました。
今も同じ判断ですか。」

maintainer は次のいずれかを選べる。

- **確認する**：新しい issue を既存ファイルの「Prior requests」list に追加して close する。
- **再検討する**：対象外ファイルを削除または更新し、issue を通常どおり triage する。
- **一致しないと判断する**：issue 同士には関係があるが別物として、通常どおり triage する。

## `.out-of-scope/` へ書く時期

**enhancement**（bug ではない）を `wontfix` として*却下した*場合だけ書く。
enhancement PR にも issue と同じ規則を適用する。
却下した PR をここに記録し、同じ request が新しい code として再び持ち込まれることを防ぐ。

**実装済み**という理由で `wontfix` として close する場合は、ここに書かない。
それは構築済みの feature であり、却下したものではない。
記録すると、誤った却下情報で重複 check を汚染する。
代わりに、close comment から既存 feature の場所を示す。

手順：

1. maintainer が feature request を対象外と判断する。
2. 一致する `.out-of-scope/` file がすでにあるか確認する。
3. ある場合は、新しい issue を「Prior requests」list に追記する。
4. ない場合は、concept 名、decision、reason、最初の prior request を記した新しいファイルを作る。
5. issue に、決定を説明して `.out-of-scope/` file に言及する comment を投稿する。
6. `wontfix` label を付けて issue を close する。

## 対象外ファイルを更新または削除する

maintainer が以前に却下した concept について判断を変えた場合：

- `.out-of-scope/` file を削除する。
- 過去の issue は履歴であるため、skill が reopen する必要はない。
- 再検討のきっかけになった新しい issue は、通常どおり triage する。
