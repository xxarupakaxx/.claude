---
name: prototyping-solutions
description: 設計上の問いに答えるための捨て prototype を作ります。 state model や logic がしっくり来るか確かめたいとき、あるいは UI をどう見せるか探りたいときに使います。
---

# プロトタイプ

prototype とは、**一つの問いに答えるための捨てコード** です。
形を決めるのは問いのほうです。

## 分岐を選ぶ

何の問いに答えるのかを見極めます。
判断材料はユーザーの prompt、周辺 code、あるいはユーザーへ聞けるかどうかです。

- **「この logic / state model はしっくり来るか」** → [LOGIC.md](LOGIC.md) を使います。
  紙の上では判断しづらい case に state machine を通してみる、小さな interactive terminal app を作ります。
- **「見た目はどうあるべきか」** → [UI.md](UI.md) を使います。
  一つの route 上で切り替えられる radically different な UI variation を複数作り、floating bottom bar で比較できるようにします。

この二つの branch は、できる artifact がまったく違います。
ここを取り違えると prototype 全体が無駄になります。
問いが本当に曖昧で、しかもユーザーに聞けないなら、周辺 code により合うほうを既定にします。
backend module なら logic、page や component なら UI を選びます。
そして、その前提を prototype の冒頭に明記します。

## 両分岐に共通するルール

1. **最初から throwaway と決め、そう見えるようにします。**
   prototype code は、実際に使われる場所の近くへ置きます。
   module や page のそばに置き、文脈が明確になるようにします。
   ただし casual reader でも production code と見間違えない名前にします。
   throwaway な UI route でも、project の既存 routing convention に従います。
2. **実行 command は一つにします。**
   `pnpm <name>`、`python <path>`、`bun <path>` など、project がすでに使っている task runner や runtime に乗せます。
   ユーザーが迷わず起動できることが条件です。
3. **既定では persistence を持ちません。**
   state は memory 上に置きます。
   persistence は prototype が *確かめる対象* であって、prototype 自体が依存する前提ではありません。
   問いが database を明示的に含むときだけ、scratch DB や local file を使います。
   その場合も、`PROTOTYPE — wipe me` のように明確な名前を付けます。
4. **磨き込みはしません。**
   test は書きません。
   prototype を *動かすために必要な範囲* を超える error handling もしません。
   abstraction も追加しません。
   目的は、早く何かを学ぶことです。
5. **state を見える場所に出します。**
   logic なら各 action のあと、UI なら variant 切り替えのたびに、関係する state 全体を print または render します。
   何が変わったかをユーザーがすぐ見えることが重要です。
6. **終わったら decision と prototype を捕捉します。**
   妥当だと分かった decision は real code に fold します。
   prototype 自体は **primary source** として保持します。
   main とは別の throwaway branch に commit し、その branch への context pointer を implementation issue に残します。
   どの問いを、どういう verdict で片付けたかも、issue か commit に書いて残します。
   main branch には validated decision だけを残します。
