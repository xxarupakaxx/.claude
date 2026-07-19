# Matt Skill harness の user-scope 統合

## 問題

現在の harness には Matt Skill の規律が複数入っているが、利用者が知っている名前と discovery surface の名前が一致しない。

ロードマップは情報を保持しているものの、計画、実装、合格基準、証拠、人間の確認箇所を一続きに読みにくい。

計画を先に固める運用は維持したいが、実行して初めて得られる観察によって計画を修正する経路も必要である。

## Outcomes

- O-1：Matt upstream 41 Skill の採用判断を user-scope の証拠として残す。
- O-2：`batch-grill-me` と `to-questionnaire` を明示起動専用として導入する。
- O-3：`wayfinder`、`to-spec`、`to-tickets`、`implement`、`teach` をその名前で発見できるようにする。
- O-4：置換済み deprecated Skill を runtime から削除する。
- O-5：計画から証拠までの対応と漏れを、最初の画面で人間が判断できるロードマップにする。
- O-6：観察、計画変更、再検証を正規の履歴として扱う。
- O-7：ロードマップの読み方と想定される反論を、teach 用の図解で確認できるようにする。
- O-8：Codex と Claude の user-scope parity を保ち、live home を安全に更新する。

## Scope

正本は `.codex`、追従側は `.claude-global` とする。

Vault にはこの project の成果物を作らず、最終的な submodule pointer だけを更新する。

## Out of scope

- Matt upstream の全 Skill を自動起動対象にすること。
- in-progress Skill を安定版と表現すること。
- tracker への issue 作成や外部投稿を無承認で行うこと。
- 計画変更を無条件に許し、合格基準を弱めること。
