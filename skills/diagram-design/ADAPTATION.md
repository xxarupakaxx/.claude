# 適合差分

この review-stage target は、`diagram-design` の固定原典をそのまま runtime へ複製するものではない。計画書の実装説明に必要な静的図の判断規則、依存関係・処理・構造・比較の構図、source traceability だけを日本語入口と JIT reference に再構成する。

## 採用した要素

- semantic pattern を先に選び、次に図種を選ぶ流れ。
- 「図より表が短いなら表」を優先する削除規則。
- dependency の rank、fan-in、cycle、node / edge 上限。
- process / data flow の lane・step・payload と決定的な入力契約。
- architecture の zone、trust boundary、直交 connector、線を node より先に描く順序。
- comparison の同一 id、first divergence、同単位の2状態、fidelity ledger。
- 4px rhythm、1–2 focal accent、SVG の title / desc / aria、system font、静的 HTML。

## この target で変更した要素

| upstream | local adaptation | 理由 |
|---|---|---|
| 39 visual types の大きな選択表 | dependency / process / data flow / architecture / comparison の4入口 | 計画書の実装理解に必要な範囲へ context を限定するため |
| Instrument Serif / Geist / Geist Mono と live font link | system font stack と local mono stack | 外部 load 0、オフライン閲覧、CJK 読みやすさ |
| URL onboarding と profile resolution | 固定された local tokens と明示した source | URL取得、永続書込み、global state を持ち込まないため |
| 多数の example HTML | 5つの小さなデモ（dependency Before / candidate、process、architecture、comparison） | 構図を実際に検証し、gallery を常時読む必要をなくすため |
| official export / import / gallery scripts | 参照だけに留め、実行経路から除外 | 未審査 code、browser automation、network を実行しないため |

## 明示的に非採用

公式の 155 example HTML、gallery の iframe、animation controller、`drawio_extract.py`、`mermaid_extract.py`、`self_check.py`、Playwright export、URL onboarding、profiles の保存・削除、remote fonts、external assets、`foreignObject`、上流の global style-guide mutation はこの target に含めない。

Roadmap の progress、task order、session / Hub、canonical state diagram もこの target の責務ではない。本文内の dependency / processing / structure / comparison 説明図だけを、plan renderer が選択した場合に生成する。
