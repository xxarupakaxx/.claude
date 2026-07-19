# 作業ログ

## 2026-07-19 11:33 JST

- Phase 0：user-scope project を `.codex/projects/matt-skill-harness/` に作成した。
- 過去知見：Matt Skill は薄い routing、Goal Quality Gate、Sprint Contract、Outcome Trace を中心に統合済みだった。
- 現状差分：実装は存在しても、`wayfinder` など upstream の正式名が discovery surface に出ていなかった。
- ユーザー所感：計画を重視する一方、実行後の観察と後からの修正を正規の流れにしたい。

## 2026-07-19 11:34 JST

- Phase 1：upstream `main` と監査済み revision が `9603c1cc8118d08bc1b3bf34cf714f62178dea3b` で一致することを確認した。
- GitHub の現行 README で `wayfinder`、`to-spec`、`to-tickets`、`implement`、`teach` が user-invoked surface であることを確認した。
- `batch-grill-me` と `to-questionnaire` は `in-progress` の user-invoked Skill である。
- governance source live check は成功した。
- governance catalog の人間向け出力は `observed_revision` 欠落で例外になった。基盤修正対象へ追加した。
- GO/NO-GO：CONDITIONAL GO。
  - in-progress 2件は明示起動専用、状態表示、外部投稿なしを条件に導入できる。
  - deprecated は置換先と参照更新を確認してから削除できる。
  - discovery 名は既存実装の重複起動を避ける薄い入口として追加できる。

## Phase 2: 計画完了

- `30_plan.md`、`checkpoint.md`、`team-journal.md` に計画、合格基準、Outcome Trace を固定した。
- 実行後に得た観察は Revision Log に記録し、関連する acceptance と evidence を再検証する。

## 2026-07-19 11:48 JST

- Phase 3A：`wayfinder`、`to-spec`、`to-tickets`、`implement`、`teach` のuser-invoked entryを追加した。
- Phase 3A：`batch-grill-me` と `to-questionnaire` をin-progress表示と安全境界付きで導入した。
- Phase 3A：`conducting-quality-assurance`、`planning-refactors`、`ubiquitous-language` の参照を置換し、Skill本体を削除した。
- Phase 3A：41件のinventoryと12件のrouting evalを作成した。
- Phase 3A：governance catalogの人間向け表示が欠損fieldで落ちる不具合を修正し、unit testを追加した。

## 2026-07-19 11:55 JST

- Phase 3B：first screenをNow、Next human decision、Coverage、Outcome Trace、Observation / Revisionへ絞った。
- Phase 3B：Outcome TraceへHuman ReviewとObjectionを追加した。
- Phase 3B：Implementation Stripとevidence shortcutを折りたたみへ移した。
- Phase 3B：teach lesson、reference、図、二問の小テストをuser-scope projectへ追加した。
- 直接検証：roadmap Python 10件、Node 27件、governance 98件、Matt harness validatorがPASSした。

## 2026-07-19 12:08 JST

- Phase 4：desktop、mobile、teach lessonを実ブラウザで確認した。
- 観察：mobileではorder未指定のRevision panelがNow / Nextより先に表示された。
- 修正：mobileの表示順をNow / Next、Outcome Trace、Revision、詳細へ固定し、静的回帰テストを追加した。
- Playwrightの`iPhone 13`指定は未導入WebKitを要求して失敗したため、Chromiumの390×844 viewportへ切り替えて同じresponsive layoutを確認した。
- accessibility直接検証でhidden file inputのname欠落を検出し、`aria-label`と回帰テストを追加した。
- 全41件の再照合で、deprecated名`design-an-interface`の旧local Skillが残る矛盾を検出した。旧sub-agent API前提でもあるため削除し、`brainstorming`と`designing-codebases`へ参照を分離した。

## 2026-07-19 12:24 JST

- Phase 4：独立reviewでstaleな`roadmap-snapshot.json`、retired routingの1件不足、空directoryを検出した。
- 修正：roadmapを`--json`付きで再生成し、retired 4件のroutingとdirectory absenceを揃えた。
- 修正：synthetic estate生成時にCodex selector 8件を落としていたため、live `estate-plan`の493件を正本として再生成した。
- fresh検証：governance audit、parity、catalog、deliveryはすべてPASSした。
- fresh検証：source、live、origin/mainのHEAD一致とruntime-only file、設定checksumの不変を確認した。
- Phase 5：security、UI、accessibilityの独立reviewはCRITICAL 0、IMPORTANT 0、MINOR 0でAPPROVEした。
