# UI Copy Rules

UIの新規画面・コンポーネント追加、または既存UIの文言を変更する作業に適用されるルール。

## 基本原則

> Avoid unnecessary secondary labels and descriptions. Let the layout do the explaining.

スローガン、全カード・ページ・ダイアログへ一律に付ける説明サブタイトル、ユーザーがエージェントに与えた指示文をそのままUIへ書き写すことは避ける。配置・見出し・階層などlayout自体に説明させ、不要なsupporting text・descriptive copy・冗長なUI microcopyを加えない。

- UI文言の区切りに中黒「·」を使わない。既存のものも見つけたら除く。
- 画面の対象ユーザーに合わせて文言を見直す。分かりやすく、ただし砕けすぎない言葉を選び、長さは機能に見合ったものにして、冗長さと造語を避ける。

## 境界

- 必要なフォームラベル、操作の名前、アクセシブルネーム（`aria-label`等）は残す。
- 視覚的な冗長さを削っても、スクリーンリーダー等のアクセシビリティは壊さない。

## 出典

- https://x.com/luinlee/status/2113085361836744764 （スレッド内の返信含む）
- https://x.com/ZaynHao/status/2113456751915982917
