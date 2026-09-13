# Archify計画図

Roadmapのarchitecture figureは、計画本文に明示した実装構成をArchifyでSVGにする。Taskの並び、進捗、時刻、旧Codemapからdependency graphを自動生成しない。`30_plan.html`が人とagentの正本で、SVGはその本文に置く図の検証済み出力である。

## Claude Codeでの実行

Archify adapter、固定container設定、cacheは `~/.codex` に一本化されている。`.claude` 側へ複製せず、`commands/lfg.md` の `sync-roadmap.py` と同じく共有CLIを `~/.codex/scripts/` から呼ぶ。CLIが見つからない場合は停止し、別の描画方式へ切り替えない。

## 入力とauthoring

計画のTask内に、実際のcomponentとdata flowを記述した`data-plan-fragment="diagram"`のJSONを置く。共通parserはこのJSONをTaskの`diagramData`へ格納する。fragmentの正確なschemaは`plan_architecture.py`を正本とし、Task順やpath列挙から補作しない。図へ投影するcomponent、入口、変換、保存先、外部境界、data flowはsourceと計画本文で明示する。

同じTask内に置く最小例（nodeとedgeは実装に合わせて記述する）:

```html
<figure id="implementation-architecture"><figcaption>実装構成</figcaption></figure>
<script type="application/json" data-plan-fragment="diagram">
{"version":1,"kind":"architecture","id":"implementation-architecture","title":"実装構成",
 "nodes":[{"id":"view","label":"画面","col":0},{"id":"api","label":"API","col":1}],
 "edges":[{"from":"view","to":"api","label":"リクエスト"}]}
</script>
```

authoringでは次の順に行う。

1. 対象component、直接import、data flow、関連testをsourceから確認する。
2. 共有CLI `python3 ~/.codex/scripts/plan_architecture.py <task-dir>` を実行する。helperが明示fragmentを読み、同じTaskのmatching figureへ検証済みSVGを書き込む。
3. `python3 ~/.codex/scripts/plan_architecture.py --check <task-dir>` で、現在のfragment、独立したarchitecture input hash、matching SVG、receiptをread-only検証する。
4. checkが通った完成済みの`30_plan.html`を共有CLI `~/.codex/scripts/sync-roadmap.py`（`commands/lfg.md` の呼び出し形）へ渡す。syncは再生成せず、図を検証してからHTMLをDOM/CSSごとコピーする。

ブラウザはsourceを読んだりArchifyを実行したりしない。Roadmapの`embedded-snapshot`はTask索引のための不活性JSONであり、図のsourceやDOMを置き換えない。

## Hashと表示

architecture inputは`30_plan.html`全体のraw hashとは別にhashする。SVGやreceiptを計画本文へ埋めて自分自身をhash入力に戻さない。checkではfragmentのcanonical bytes、SVG bytes、Archify revision、実行環境、geometry、安全なSVG構造を照合する。

`verified`のときだけmatching figureのSVGを表示する。SVGは白基調、日本語のtitle/descとlang、`role="img"`を持つ。SVGをinnerHTMLへ渡さず、検証済みbytesをimgまたは安全な表示要素として使う。

`empty`、`invalid`、`blocked`、`error`では理由を日本語で示し、古い図や操作リンクを成功扱いで残さない。別の描画方式へ黙って切り替えない。本文と既存の安全な操作は保持する。

## 固定生成エンジン

- Archify revisionは`5de7275fe87a66a19d52a4d9b0b3a4f2a5a90115`。`~/.codex/config/archify-container.json`に固定したimage・Node・Chrome・entrypointとsource manifestだけを使う。
- hostは第一者の`archify_plan.py`または`plan_architecture.py`から既存Docker/Colimaへ接続する。第三者sourceはcontainer内だけで実行し、workflow生成に必要な固定argv以外を呼ばない。
- network none、個人host mountなし、非root、read-only root、cap-drop ALL、no-new-privileges、Chrome内蔵sandboxを維持する。子へ個人の環境変数やcredentialを継承しない。
- CPU 1、memory 1 GiB、PID 128、FSIZE 32 MiB、全処理60秒。private tmpfsは生成物32 MiB、browser64 MiB。成功・失敗・timeoutの全経路でcontainerを回収する。
- 入力は上限付きstdin、返却は検証済みSVGのbase64とreceiptだけ。private中間HTMLは開いたり配布したりしない。
- 通常生成中にimageの取得、install、daemon起動や設定変更を行わない。固定image・境界が利用できなければblockedを示す。

architecture bundleとSVGはCodex home配下の既存`~/.codex/.local/archify-plan-assets/`へ原子的に保存し、directory 0700、file 0600を守る。共通Archify adapterのcache pathと固定契約は変更しない。cache再利用時も原本、実行環境、raw/final SVG、geometry、fragment hashを再検査し、cacheを外部同期しない。

## 採用と境界

Archifyは実装構成を説明する図のproducerであり、plan本文・UI mock・source evidenceの代替ではない。元packageの監査、固定source/image、wrapper、実行制限、license、安全性・価値の検証、ユーザーの導入依頼は既存の採用記録へ結ぶ。source、image、実行境界、依存を変える場合は同じ範囲で再審査する。

個人ファイルのmount、通信、任意コマンド、権限追加、別Skillへの適用へ承認を流用しない。通常の計画作成・更新では追加入力や都度の導入承認を求めない。
