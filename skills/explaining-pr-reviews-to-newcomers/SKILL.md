---
name: explaining-pr-reviews-to-newcomers
description: 初めて触る領域の PR をレビューし、指摘ごとに根拠コードの抜き書き・初学者向けの解説・自分で確かめる手順・推奨を並べた解説 HTML を作る。引き継いだ PR や不慣れなドメインの PR を、読み手が自分で採否を判断できる形でレビューしてほしいときに使う。レビュー結果だけが要るとき（pr-review）、レビューを伴わない差分の解説、PR の無い branch、PR 以外の HTML（creating-html-documents）には使わない。
---

# 初めての人向けに PR レビューを解説する

読み手は、その PR の領域を初めて触る人（PR を引き継いだ人など）です。成果は指摘の数ではありません。読み手が抜き書きのコードを自分で読み、各指摘の採否を決められることです。

## ほかの Skill との関係

- `pr-review` で findings を作り、このSkillで検証し直して解説にする。
- HTML の作法（一列のレイアウト、左上の折りたたみ目次、用語集の条件、全体像の図の形と凡例、検査）は `creating-html-documents` を正本とし、このSkillは複製しない。このSkillが足すのは、レビュー固有の章、指摘カード、git から切り出す抜き書き、検証の落とし穴だけ。
- 読み手自身の理解と採否の判断の両方が目的なので、`creating-html-documents` の初学者向けの既定と理解の確認の既定を重ねる。「チームが差分を確かめて判断するためのレビュー記録」には当たらない。

## 境界

- read-only で行う。コードの修正、commit、push、PR へのコメントは、読み手が採否を決めた後に別の依頼として行う。
- PR の背景（なぜ今この処理が要るか）は、依頼者の説明と PR 本文から書き、出典ラベルを付ける。推測で補わない。
- 依頼者が個別の問い（状態の定義、migration の妥当性、代替案など）を出したら、それぞれを独立した節で答える。

## 手順

1. **レビューする。** `pr-review` を実行し、固定した snapshot（base、head、merge-base の40桁の SHA）と findings を受け取る。
2. **検証し直す。** [検証の落とし穴](references/verification-pitfalls.md) を読み、依頼者の問いと findings をコードで確かめ直す。PR 前の挙動は merge-base の版で、PR 後の挙動は head の版で確かめる。merge-base の後に base branch で対象ファイルが変わっていれば、指摘が崩れないかも確かめる。
3. **作業フォルダを決める。** 対象に近い CLAUDE.md の `MEMORY_DIR`（無ければ `.local`）を、その CLAUDE.md のあるディレクトリ基準で使い、`<そこ>/memory/pr-review-<PR番号>/` とする。`git check-ignore` で無視されないと分かったら、`~/.claude/.local/pr-review-guides/<owner>-<repo>-<PR番号>/` を使う。`$TMPDIR` は再起動で消えるので使わない。
4. **本文を書く。** `creating-html-documents` の SKILL.md を全文読む。続けて [解説 HTML の構成](references/document-structure.md) を読み、作業フォルダに `spec.json`（抜き書きの定義）と `body.html`（本文）を書く。
5. **生成して照合する。** パスはすべて絶対パスで渡す。`<skill>` はこの SKILL.md のあるディレクトリ。
   ```bash
   python3 -I <skill>/scripts/render_review_guide.py render --spec <作業フォルダ>/spec.json --body <作業フォルダ>/body.html --out <作業フォルダ>/review-guide.html
   python3 -I <skill>/scripts/render_review_guide.py verify --repo <リポジトリのルート> <作業フォルダ>/review-guide.html
   ```
6. **検査する。** `python3 ~/.claude/scripts/lint-html-document.py <HTML>` の誤りを0にする。日本語は、`render_review_guide.py text <HTML> --out "$TMPDIR/review-guide.md"` で本文の文章を書き出してから `yomiyasu_lint.py` にかけ、終わったら消す（HTML のままでは文章が検査されない）。ブラウザでの検査は `creating-html-documents` の `references/validation.md` に従い、1440x900 で横のはみ出しが無いこと、図の文字の重なりとはみ出しが0件であることを確かめる。
7. **独立レビューを受ける。** まっさらな文脈の `general-purpose`（opus）に、HTML のパス、目的、一次情報（リポジトリのルートと commit、PR 番号）を渡す。観点は、`creating-html-documents` の `references/mastery-explainer.md` の独立レビューの確認観点と、[検証の落とし穴](references/verification-pitfalls.md)。指摘はコードで確かめてから `body.html` と `spec.json` に反映し、手順 5〜6 をやり直す。
8. **開いて報告する。** 既定のブラウザで開く。報告の順は、マージまでにやること → 依頼者の問いへの答え → 指摘の要約 → 検証した範囲 → まだしていないこと（修正・push）。検証した範囲には、`creating-html-documents` の `references/validation.md` の「Evidence report」の項目を含める。採否は「F1 採用」のように番号で返せばよいと伝える。

## 更新するとき

指摘の反映や採否の記録は、`body.html` と `spec.json` を直して手順 5 から再生成する。出力の HTML は直接編集しない。直接編集した場合は、`verify` で抜き書きが git と一致することを確かめる。

## 完了条件

- 各指摘に、重要度、一言の要約、抜き書き、初学者向けの解説、自分で確かめる手順、推奨（選択肢）、根拠ラベル、判断欄がある。
- 依頼者の個別の問いに、根拠付きの答えがある。PR 作者が本文で判断を求めた点にも見解がある。
- `verify` の不一致が0件、lint の誤りが0件（要確認は理由を判断済み）、本文の日本語の検査を済ませた。
- 1440x900 で横のはみ出しが無く、図の文字の重なりとはみ出しが0件。
- 独立レビューの指摘を確かめて反映し（反証した指摘は理由を残す）、既定のブラウザで開いた。
