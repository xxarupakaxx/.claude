# Mocking: 境界と使いどころ

## 原則: System Boundary だけ Mock する

> "Mock at the edges, not at the middle."

Mock するのは**システム境界**だけ。内部モジュール間の協調はモックしない。

### Mock すべきもの（System Boundary）

| 種類 | 例 | 理由 |
|------|----|------|
| 外部API | HTTP, gRPC, GraphQL先 | 不安定・有料・遅い |
| データベース | RDB, Redis, S3 | 状態管理が複雑、並列で壊れる |
| 時刻 | `Date.now()`, `time.Now()` | フレーキーの主因 |
| 乱数 | `Math.random()`, `crypto.randomUUID()` | 再現性なし |
| ファイルシステム | `fs.readFile` | 環境依存 |
| プロセス境界 | 子プロセス、メッセージキュー | I/O待ち |

### Mock してはいけないもの

- 同じレイヤーの内部クラス（テストが実装詳細に依存する）
- 純粋関数（モックする意味がない）
- DTOやValue Object（普通にインスタンス化する）

## Mock の手段

### 1. Fake（推奨）

実装の代替を提供:

```ts
class FakeMailer implements Mailer {
  sent: Email[] = [];
  send(email: Email) { this.sent.push(email); }
}

// テスト
const mailer = new FakeMailer();
service.notify(...);
expect(mailer.sent).toHaveLength(1);
```

**メリット**:
- 状態を持てる（連続呼び出しのテストが容易）
- 振る舞いベース（実装詳細に依存しない）

### 2. Stub

固定の戻り値を返す:

```ts
const repo = { findById: () => Promise.resolve(fixtureUser) };
```

簡単な依存に有効。

### 3. Spy / Mock（最終手段）

呼び出し履歴を検証:

```ts
const spy = jest.spyOn(logger, "error");
// ...
expect(spy).toHaveBeenCalledWith(expect.stringContaining("..."));
```

**注意**: 呼び出し回数や引数を厳密にチェックすると壊れやすい。

## Seam の作り方

System Boundary を Mock 可能にするには **Seam（縫い目）** が必要。

### Constructor Injection（推奨）

```ts
class UserService {
  constructor(
    private repo: UserRepo,
    private mailer: Mailer,
    private clock: Clock,  // Date.now() の代わり
  ) {}
}
```

### Function Parameter Injection

```ts
export const calculateExpiry = (
  base: Date,
  now: () => Date = () => new Date(),
) => { ... };
```

簡易版。クラスを使わない言語/コードベース向け。

## アンチパターン

### 1. 内部実装をMock

```ts
// Bad: UserService 内部の private メソッドをstub
jest.spyOn(service as any, "_normalizeEmail").mockReturnValue(...)
```

→ private実装変更で全テスト破綻。

### 2. 全部Mock（Mockist Extreme）

```ts
// Bad: 何もMockせずに済むはずの関数までMock
const calculator = { add: jest.fn().mockReturnValue(3) };
```

→ テストが「実装をなぞるだけ」になり、価値がなくなる。

### 3. 時刻をハードコードしない

```ts
// Bad
expect(result.expiresAt).toBe("2026-12-31T00:00:00Z");

// Good (clock 注入)
const clock = { now: () => new Date("2026-01-01T00:00:00Z") };
const service = new TokenService(clock);
expect(result.expiresAt).toEqual(new Date("2026-12-31T00:00:00Z"));
```

### 4. 環境変数や global state を読む実装

→ Seam を作って引数で受け取る。`process.env.X` を直接参照しない。

## 判断フロー

```
依存はSystem Boundaryか？
  YES → Fake or Stub を作る
  NO  → そのまま使う（モックしない）

Fake と Stub どちらか？
  状態を持つ必要あり/連続呼び出しがある → Fake
  単純な値を返すだけ → Stub
```
