# ADR の形式

ADR は `docs/adr/` に置き、`0001-slug.md`、`0002-slug.md` のように連番で命名します。

`docs/adr/` directory は lazy に作ります。
最初の ADR が必要になるまでは作りません。

## テンプレート

```md
# {判断の短いタイトル}

{1〜3 文で、文脈、何を決めたか、なぜそう決めたかを書く。}
```

これだけで十分です。
ADR は一段落だけでも構いません。
価値があるのは、判断があったことと、その理由が記録されることです。
section を埋めること自体には価値がありません。

## 任意セクション

本当に価値があるときだけ追加します。
多くの ADR では不要です。

- **Status** frontmatter（`proposed | accepted | deprecated | superseded by ADR-NNNN`）。
  判断を見直す可能性があるときに役立ちます。
- **Considered Options**。
  却下した代替案も覚えておく価値があるときだけ書きます。
- **Consequences**。
  downstream effect のうち、見落とされやすいものを明示したいときだけ書きます。

## 番号の振り方

`docs/adr/` を scan して、最大番号を見つけて 1 を足します。

## ADR を提案してよいとき

次の三つがすべて真のときだけです。

1. **Hard to reverse**。
2. **Surprising without context**。
3. **The result of a real trade-off**。

判断が簡単に覆せるなら記録しません。
どうせひっくり返すからです。
驚きがないなら、誰も理由を不思議がりません。
本当の代替案がなかったなら、「当然のことをやった」以上の記録価値はありません。

### 何が該当するか

- **Architectural shape**。
  たとえば monorepo を採る判断や、write model を event-sourced にし read model を Postgres へ projection する判断です。
- **context 間の integration pattern**。
  たとえば Ordering と Billing が synchronous HTTP ではなく domain event で通信する判断です。
- **lock-in を伴う technology choice**。
  database、message bus、auth provider、deployment target などです。
  library 全般ではなく、入れ替えに四半期単位のコストがかかるものだけです。
- **boundary と scope の判断**。
  たとえば Customer data は Customer context が所有し、他 context は ID 参照だけにする、といったものです。
  「やらない」と決めたことも、「やる」と同じくらい価値があります。
- **明白な道からの意図的な逸脱**。
  たとえば ORM ではなく manual SQL を選ぶ判断です。
  理由がなければ次の engineer が「直したつもり」で壊します。
- **code から見えない constraint**。
  たとえば compliance requirement のため AWS を使えない、partner API contract のため response time を 200ms 未満にする必要がある、といったものです。
- **却下理由が非自明な代替案**。
  たとえば GraphQL を検討したうえで subtle な理由により REST を選んだなら記録します。
  そうしないと、半年後にまた GraphQL を提案されます。
