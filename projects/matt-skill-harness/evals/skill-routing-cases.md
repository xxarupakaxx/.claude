# Skill routing cases

| # | Prompt | Expected | Reason |
| ---: | --- | --- | --- |
| 1 | `/wayfinder 新規事業の全体を整理して` | `wayfinder` | 明示起動で、複数sessionのfog-of-warを扱う |
| 2 | `明日の買い物を三つに分けて` | direct | 小さくrouteが明確なのでwayfinderは使わない |
| 3 | `/to-spec 今まで話した内容を仕様にして` | `to-spec` | 合意済み会話の明示的なspec化 |
| 4 | `まだ何を作るか決まっていないけど仕様を書いて` | clarification | 未決事項をspecで埋めない |
| 5 | `/to-tickets このspecを実装単位にして` | `to-tickets` | 明示起動でblocking edgeを作る |
| 6 | `/implement 承認済みticket 01を実装して` | `implement` | acceptanceがある実装入口 |
| 7 | `/teach Outcome Traceの読み方を教えて` | `teach` | stateful教材の明示依頼 |
| 8 | `Outcome Traceって何？一文で` | direct | 単発説明に教育workspaceは不要 |
| 9 | `/batch-grill-me 質問をまとめて出して` | `batch-grill-me` | 利用者がround形式を明示した |
| 10 | `一問ずつ確認して` | `grill-me` | 安定版の逐次interviewを使う |
| 11 | `/to-questionnaire 顧客担当者への質問票を作って` | `to-questionnaire` | local questionnaireの明示起動 |
| 12 | `この質問票をSlackへ送って` | external-write-gate | questionnaire作成と送信承認を分離する |
