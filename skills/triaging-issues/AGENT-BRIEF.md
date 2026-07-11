# Agent brief の書き方

agent brief は、GitHub issue または PR が `ready-for-agent` に移るときに投稿する構造化された comment である。
AFK agent は、この正式な仕様をもとに作業する。
元の body と議論は context であり、agent brief が contract になる。

brief には **agent が行うべきこと**を書く。
issue では変更を一から構築する作業を、PR では*既存の diff*に残っている作業（完成させる、不足を埋める、review point に対応する）を示す。
どちらにも同じ原則を使う。
違いは後述の PR 例で示す。

## 原則

### 精密さより長く使えることを優先する

issue は数日または数週間、`ready-for-agent` のままになることがある。
その間にも codebase は変わる。
ファイルが rename、移動、refactor されても役立つ brief を書く。

- interface、type、behavioral contract を説明する。
- agent が探す、または変更する具体的な type、function signature、config shape を挙げる。
- すぐに古くなるため、file path を参照しない。
- line number を参照しない。
- 現在の実装構造が維持されると仮定しない。

### 手順ではなく挙動を書く

実装の**方法**ではなく、system が行うべき**挙動**を説明する。
agent は codebase を改めて調査し、自分で実装上の判断を下す。

- **良い例：**「`SkillConfig` type は、`CronExpression` type の任意の `schedule` field を受け付ける。」
- **悪い例：**「src/types/skill.ts を開き、42 行目に schedule field を追加する。」
- **良い例：**「ユーザーが引数なしで `/triaging-issues` を実行すると、確認が必要な issue の要約が表示される。」
- **悪い例：**「main handler function に switch statement を追加する。」

### 完全な acceptance criteria

agent は完了条件を把握する必要がある。
すべての agent brief に、具体的でテスト可能な acceptance criteria を設ける。
各 criterion は独立して検証できるようにする。

- **良い例：**「`gh issue list --label needs-triage` を実行すると、初期分類を終えた issue が返る。」
- **悪い例：**「Triage が正しく動く。」

### scope の境界を明示する

対象外の事項を明記する。
これにより、agent が過剰に作り込んだり、隣接する機能を推測したりすることを防ぐ。

## Template

```markdown
## Agent Brief

**Category:** bug / enhancement
**Summary:** 必要な作業を一行で説明する

**Current behavior:**
現在の挙動を説明する。
bug では、壊れている挙動を書く。
enhancement では、feature を追加する前の現状を書く。

**Desired behavior:**
agent の作業完了後に実現する挙動を説明する。
edge case と error condition を具体的に書く。

**Key interfaces:**
- `TypeName`：変更する内容と理由
- `functionName()` の return type：現在の返り値と、変更後に返すべき値
- Config shape：必要な新しい設定 option

**Acceptance criteria:**
- [ ] 具体的でテスト可能な criterion 1
- [ ] 具体的でテスト可能な criterion 2
- [ ] 具体的でテスト可能な criterion 3

**Out of scope:**
- この issue で変更または対応してはならない事項
- 関係があるように見えるが、別に扱う隣接 feature
```

## 例

### 良い agent brief（bug）

```markdown
## Agent Brief

**Category:** bug
**Summary:** skill description が単語の途中で切り捨てられ、壊れた出力になる

**Current behavior:**
skill description が 1024 文字を超えると、単語の境界に関係なく 1024 文字で切り捨てられる。
そのため、description が単語の途中で終わる（例：「Use when the user wants to confi」）。

**Desired behavior:**
1024 文字より前にある最後の単語境界で切り捨て、切り捨てたことを示す「...」を追加する。

**Key interfaces:**
- `SkillMetadata` type の `description` field：type の変更は不要だが、値を設定する validation / processing logic は単語境界を考慮する。
- SKILL.md の frontmatter を読み、description を抽出するすべての function

**Acceptance criteria:**
- [ ] 1024 文字未満の description は変更されない。
- [ ] 1024 文字を超える description は、1024 文字より前の最後の単語境界で切り捨てられる。
- [ ] 切り捨てた description は「...」で終わる。
- [ ] 「...」を含む全体の長さが 1024 文字を超えない。

**Out of scope:**
- 1024 文字という上限自体の変更
- 複数行の description への対応
```

### 良い agent brief（enhancement）

```markdown
## Agent Brief

**Category:** enhancement
**Summary:** 却下した feature request を追跡する `.out-of-scope/` directory への対応を追加する

**Current behavior:**
feature request を却下すると、issue は `wontfix` label と comment を付けて close される。
decision や理由の永続的な記録はない。
あとから似た request が来ると、maintainer は以前の議論を思い出すか検索する必要がある。

**Desired behavior:**
却下した feature request は `.out-of-scope/<concept>.md` file に記録する。
file には decision、reason、feature を要求したすべての issue への link を含める。
新しい issue を triage するときは、これらの file と一致するか確認する。

**Key interfaces:**
- `.out-of-scope/` の Markdown file format：各 file に `# Concept Name` heading、`**Decision:**` 行、`**Reason:**` 行、issue link を持つ `**Prior requests:**` list を設ける。
- triage workflow は早い段階ですべての `.out-of-scope/*.md` file を読み、受け取った issue を concept の類似性で照合する。

**Acceptance criteria:**
- [ ] feature を wontfix として close すると、`.out-of-scope/` の file が作成または更新される。
- [ ] file に decision、reason、close した issue への link が含まれる。
- [ ] 一致する `.out-of-scope/` file がすでにある場合、重複 file を作らず、新しい issue を「Prior requests」list に追記する。
- [ ] triage 中に既存の `.out-of-scope/` file を確認し、新しい issue が以前の却下内容と一致した場合に提示する。

**Out of scope:**
- 自動照合（人間が一致を確認する）
- 以前に却下した feature の reopen
- bug report（`.out-of-scope/` へ記録するのは enhancement の却下だけ）
```

### 良い agent brief（PR）

PR の「Current behavior」には diff の状態を書く。
brief では agent に、一から構築するのではなく、既存の変更を完成または修正するよう求める。

```markdown
## Agent Brief

**Category:** enhancement
**Summary:** contributor が追加した `triage list` の `--json` 出力 flag を完成させる

**Current behavior:**
PR は issue list を JSON に serialize する `--json` flag を追加している。
happy path は動作し、diff は project の command structure に合っている。
ただし、error が JSON ではなく人間向けの text で出力されることと、新しい flag の test coverage がないことの二点が残っている。

**Desired behavior:**
`--json` を指定した場合は error を含むすべての出力を整形式の JSON として stdout へ出し、command の exit code は変更しない。
flag がない場合の既存の人間向け出力は変更しない。

**Key interfaces:**
- `--json` では command の error path が plain-text error の代わりに `{ "error": string }` を出力する。
- PR が追加済みの serializer を再利用し、二つ目を導入しない。

**Acceptance criteria:**
- [ ] `triage list --json` が成功時と error 時の両方で有効な JSON を出力する。
- [ ] exit code が JSON を使わない command と一致する。
- [ ] `--json` の成功時出力と一つの error case を test する。
- [ ] 既定の JSON を使わない出力が byte 単位で変更されていない。

**Out of scope:**
- 他の command への `--json` 追加
- PR が定義済みの成功 payload の JSON shape 変更
```

### 悪い agent brief

```markdown
## Agent Brief

**Summary:** triage の bug を修正する

**What to do:**
triage が壊れている。
main file を見て修正する。
150 行目付近の function に問題がある。

**Files to change:**
- src/triage/handler.ts（150 行目）
- src/types.ts（42 行目）
```

この brief には次の問題がある。

- category がない。
- 説明が曖昧である（「triage が壊れている」）。
- すぐに古くなる file path と line number を参照している。
- acceptance criteria がない。
- scope の境界がない。
- 現在の挙動と望ましい挙動の説明がない。
