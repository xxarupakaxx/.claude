# Sprint Contract

| ID | 合格基準 | 検証 |
| --- | --- | --- |
| AC-01 | upstream 41 Skill の各行に採用状態と理由がある | inventory validator |
| AC-02 | `batch-grill-me` と `to-questionnaire` は user-invoked、in-progress 表示、外部送信なし | static test、prompt eval |
| AC-03 | `wayfinder`、`to-spec`、`to-tickets`、`implement`、`teach` を名前で発見できる | discovery test |
| AC-04 | 削除対象4 Skillのdirectory、active route、registry entryが0件 | `rg`、governance audit |
| AC-05 | first screen に Now、Next human decision、Coverage、Outcome Trace だけが主要情報として出る | browser test、visual review |
| AC-06 | 各 outcome が requirement、implementation、acceptance、evidence、human review、objectionへ接続される | trace parser test |
| AC-07 | 観察後の変更が Revision Log に残り、再検証対象が示される | revision parser test |
| AC-08 | lesson と reference が単独で利用でき、図、小テスト、想定反論を含む | browser test、content test |
| AC-09 | governance unit test、audit、parity、delivery が両repoでPASSする | fresh commands |
| AC-10 | live user-scope のruntime-only fileを保持し、tracked HEADがorigin/mainと一致する | before/after manifest、exact SHA |

## 変更の再承認条件

- in-progress Skill を model-invoked に変える。
- local-only output を外部送信へ変える。
- acceptance を削除または弱める。
- Vault を成果物の正本へ変える。
- deprecated 以外の Skill を追加削除する。
