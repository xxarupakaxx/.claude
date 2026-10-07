# yomiyasu の出典

- 配布元: https://github.com/nanaism/yomiyasu
- 固定コミット: `8f77b7aa8f19c3f718b511e71a3eee5d06eb3013`（root tree `894790bb068a446eb8f0232e14e9655ed896aea3`、`.claude-plugin/plugin.json` の version は 1.0.8）
- 元ファイル: リポジトリのルートにある `SKILL.md`、`references/` の5ファイル、`scripts/` の3ファイル（`yomiyasu_lint.py`、`yomiyasu_diff.py`、`markdown_visibility.py`）、`LICENSE`、`UNICODE-LICENSE.txt`。上流の登録用ZIPと同じ11ファイル
- 原文: https://github.com/nanaism/yomiyasu/tree/8f77b7aa8f19c3f718b511e71a3eee5d06eb3013
- ライセンス: MIT（同梱の `LICENSE`）。`UNICODE-LICENSE.txt` も上流のまま同梱
- 確認日: 2026-10-07

## SHA-256

```text
15defbbff83deaa7eb946d993230c0230e576d32ed0b715b0bb9c3bce5b7e4a5  SKILL.md
ff114713715aa9d5290549f3bd441808f4691ee6b9b97600255e3992b216a5b7  references/slop-catalog.md
be520d5b673058874928f1ad736f335c60b75945d265d9754531979153151dba  references/gemini-syntax.md
b0b48c4ef83b76e1bdb13c233a1bcac69675a99e9026b5c36b87023d10708bc4  references/domains/business.md
aaec0eae3da65e7f12e529d96a1e172fa727614cd8abe240140a480e028be50c  references/domains/essay.md
bfad82a08de02325b1e7339f23aef4ac29892b39babdb74a7ad7c3f1c6a36131  references/domains/tech.md
4d5ba2b3384a95ea2638ed460e212c202ed75993df3aeedb138e6684523a9ec6  scripts/yomiyasu_lint.py
de917e91eeb5464228bd0a3ad2a941ef0f333e82be93ab968b42040ddaf1ecc6  scripts/yomiyasu_diff.py
e0cc01d3263d65f4c1ccddb939972b4098fdd1453fc0de8fc7e8e25522ec5c8d  scripts/markdown_visibility.py
79d802f15bc8caf67f1a83c1bdbe214ccb41a0a0275f9046b329b89c65ee1fca  LICENSE
e7a93b009565cfce55919a381437ac4db883e9da2126fa28b91d12732bc53d96  UNICODE-LICENSE.txt
```

## 取り込んだ範囲

11ファイルは上記コミットと同一。次のものは含まない。

- `assets/`（画像）、`tests/`、`evals/`、`articles/`、`README.md`
- `.claude-plugin/`（plugin manifest）、`skills/yomiyasu/`（ルートと同じ内容の重複）
- `scripts/` のコーパス用3本（`build_corpus.py`、`benchmark_corpus.py`、`setup_corpus_static.py`）。未審査

hook と plugin manifest は追加していない。

## 審査

2026-10-07 に固定コミットを runtime の外へ取得し、`skill-governance` の `inspect` と、独立レビュー2本（スクリプト3本の全行、規範本文と参照資料の全行）を行った。CRITICAL の指摘はない。

スクリプトは標準ライブラリだけを使い、引数で渡したファイルを読んで結果を標準出力へ出す。ネットワーク、外部コマンド、ファイル書き込みの呼び出しはない。処理時間の上限は持たないので、長い入力では呼び出し側で時間を区切る。実行は `python3 -I -B` で行い、点検用の一時ファイルはVaultやリポジトリの外に置く。

## 台帳

`skill-governance` の registry には未登録。導入した端末では `audit` が DEGRADED（台帳が別端末のパスを前提にしている）で、ユーザーが 2026-10-07 に直接の導入を承認した。台帳への登録と receipt の作成は、台帳が前提にしている端末で行う。

適用範囲と指示の優先順位は、ユーザー全体の `AGENTS.md` / `CLAUDE.md` で定める。
