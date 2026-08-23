# SVG検証ループ

生成したSVGは、保存して終わりにしない。

1. XML parserでparseする。
2. rootの `xmlns`、`viewBox`、`role="img"` を確認する。
3. `title` と `desc` が空でないことを確認する。
4. 外部resource、script、`foreignObject`、event handler属性がないことを確認する。
5. MarkdownとHTMLの参照先を確認する。
6. browserでdesktop幅とmobile幅を開き、labelの欠落、重なり、overflowを確認する。
7. 図のnodeとedgeを、同値なtext関係一覧と照合する。

失敗した場合は原因を分類して修正し、同じ検証を最初から実行する。
3回修正しても成立しない場合は、壊れた図を成果物として残さず、text関係一覧を保持して失敗を報告する。
