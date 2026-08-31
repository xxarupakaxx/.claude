# F4 · step sequence

workflowを番号付きの縦列で読む構成。各stageに番号、見出し、入力、変更、出力、合格条件を置く。

~~~html
<ol class="steps">
  <li>
    <span class="stage">01</span>
    <h3>読み取り</h3>
    <dl><dt>入力</dt><dd>現行HTMLとsource</dd>
        <dt>出力</dt><dd>claim ledger</dd></dl>
  </li>
</ol>
~~~

同じ高さのカードを並べず、stage間の余白で順序を示す。失敗時の公開停止をstage内に置く。
