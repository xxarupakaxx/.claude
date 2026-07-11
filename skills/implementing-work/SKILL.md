---
name: implementing-work
description: spec や ticket に基づいて作業を実装します。
disable-model-invocation: true
---

ユーザーが spec または ticket で示した作業を実装します。

可能なところでは、事前に合意した seam で `/tdd` を使います。

typecheck は定期的に回します。
単体 test file もこまめに回します。
full test suite は最後に一度通します。

終わったら `/reviewing-code` でレビューします。

作業内容は current branch に commit します。
