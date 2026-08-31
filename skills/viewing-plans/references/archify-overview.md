# Archify計画図

Roadmapと計画書の通常ブラウザ表示では、共通generatorが計画全体の依存関係をArchifyで描く。正本HTMLへ生成SVGやreceiptを埋めず、派生表示とprivate cacheへ保存する。Code Map、本文、実装根拠は別の役割として維持する。

## 入力と更新

- `resolve_plan_source(task_dir)`で正本を選び、`planSourceRawSha256`と再読したUTF-8 bytesを照合する。HTMLがある場合は唯一の入力とし、不正HTMLをMDで隠さない。
- `archify_for_plan(raw_text, plan_model=model)`へ型付きPlanを渡す。Task番号・題名・明示依存だけを図へ投影し、進捗や時刻から依存を補わない。
- raw plan 1 MiB、Task 128、edge 256、title 512 code pointsを上限とする。重複Task、不明な依存先、自己依存、cycleを拒否する。
- 本文の変更時に同じ生成経路で更新する。図の構造が変わらない説明・進捗の変更でも、原本とのhash対応は取り直す。

## 表示と保存

- snapshotの`archify`を使い、`verified`のときだけ`overview.svg`を表示する。provider、固定revision、原本・SVGのhash、安全なSVG構造を照合する。
- SVGは白基調、日本語のtitle/descとlang、role=imgを持つ。図を開く・保存する操作には表示と同じ検証済みbytesを使う。
- `empty / invalid / blocked / error`では理由を日本語で示し、旧図と操作リンクを消す。別の描画方式へ黙って切り替えない。本文と既存操作は保持する。
- SVGをinnerHTMLへ渡さずimgとして表示する。script、event、foreignObject、外部参照、危険なCSSを拒否する。
- bundleとSVGはCodex home配下の`.local/archify-plan-assets/`へ原子的に保存する。directory 0700、file 0600。cache再利用時も原本、実行環境、raw/final SVG、geometryとhashを再検査する。cacheを外部同期しない。

## 固定生成エンジン

- Archify revisionは`5de7275fe87a66a19d52a4d9b0b3a4f2a5a90115`。`config/archify-container.json`に固定したimage・Node・Chrome・entrypointと、source manifestだけを使う。第三者のSKILL.mdをhostのSkill検索面へ追加しない。
- hostは第一者の`archify_plan.py`から既存Docker/Colimaへ接続する。第三者sourceの実行はcontainer内だけ。固定argvのworkflow生成に限定し、update、capture、preview、npm install、upstream test、任意optionは呼ばない。
- network none、個人host mountなし、非root、read-only root、cap-drop ALL、no-new-privileges、Chrome内蔵sandboxを維持する。子へ個人の環境変数やcredentialを継承しない。
- CPU 1、memory 1 GiB、PID 128、FSIZE 32 MiB、全処理60秒。private tmpfsは生成物32 MiB、browser64 MiB。成功・失敗・timeoutの全経路で当該containerを回収する。
- 入力は上限付きstdin、返却はSVGのbase64とreceiptだけ。private中間HTMLは開いたり配布したりしない。公開する成果物は検査済みSVGと自己完結した計画表示だけ。
- 通常生成中にimageの取得、install、daemon起動や設定変更を行わない。固定image・境界が利用できなければblockedを示す。

## 採用と変更

元packageの全件監査と静的指摘は隔離証跡として保持する。engine依存のsource/image、wrapper、実行制限、license、安全性・価値の検証、ユーザーの導入依頼、反映対象を同じ採用記録へ結ぶ。元packageをactive/legacy-activeなSkillとして登録したとは扱わない。

source、image、実行境界、依存を変える場合は同じ範囲で再審査する。個人ファイルのmount、通信、任意コマンド、権限追加、別のSkillへの適用へ承認を流用しない。通常の計画作成・更新では追加入力や都度の導入承認を求めない。
