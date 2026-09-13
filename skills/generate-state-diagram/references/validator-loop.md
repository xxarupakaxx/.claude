# SVG検証ループ

生成したSVGは、保存して終わりにしない。

1. XML parserでparseする。
2. rootの `xmlns`、`viewBox`、`role="img"` を確認する。
3. `title` と `desc` が空でないことを確認する。
4. 外部resource、script、`foreignObject`、event handler属性がないことを確認する。
5. evidence inventory、SVG、Markdownの遷移ledger、source anchorを照合する。
6. 各遷移のtrigger、guard、effect、failure、recoveryに欠落があれば、根拠不足として明示されていることを確認する。
7. HTMLを作った場合だけ、inline SVGと参照を確認する。
8. HTMLを作った場合だけ、1440x900でlabelの欠落、重なり、overflowを確認する。
9. mobile、print、PDFは明示依頼がある場合だけ検証する。

失敗した場合は原因を分類して修正し、同じ検証を最初から実行する。
3回修正しても成立しない場合は、壊れた図を成果物として残さず、詳細ledgerと根拠不足を保持して失敗を報告する。
