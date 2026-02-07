# Confluence用変換ルール

ConfluenceはMarkdownをサポートしているため、基本的にはMarkdown形式を維持。
ダイアグラムのみMermaid → PlantUML形式に変換する。

## 基本方針

| 要素           | 変換               |
| -------------- | ------------------ |
| 見出し         | そのまま維持       |
| テーブル       | そのまま維持       |
| コードブロック | そのまま維持       |
| リスト         | そのまま維持       |
| リンク         | そのまま維持       |
| **Mermaid**    | **PlantUMLに変換** |

## Mermaid → PlantUML 変換

### フローチャート

**Mermaid:**

````markdown
```mermaid
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
    C --> E[End]
    D --> E
```
````

**PlantUML:**

````markdown
```plantuml
@startuml
start
if (Decision?) then (Yes)
  :Action 1;
else (No)
  :Action 2;
endif
stop
@enduml
```
````

### シーケンス図

**Mermaid:**

````markdown
```mermaid
sequenceDiagram
    participant Client
    participant Server
    participant DB
    Client->>Server: Request
    Server->>DB: Query
    DB-->>Server: Result
    Server-->>Client: Response
```
````

**PlantUML:**

````markdown
```plantuml
@startuml
participant Client
participant Server
participant DB

Client -> Server: Request
Server -> DB: Query
DB --> Server: Result
Server --> Client: Response
@enduml
```
````

### クラス図

**Mermaid:**

````markdown
```mermaid
classDiagram
    class User {
        +String name
        +String email
        +login()
    }
    class Order {
        +int id
        +Date date
    }
    User "1" --> "*" Order
```
````

**PlantUML:**

````markdown
```plantuml
@startuml
class User {
  +name: String
  +email: String
  +login()
}

class Order {
  +id: int
  +date: Date
}

User "1" --> "*" Order
@enduml
```
````

### ER図

**Mermaid:**

````markdown
```mermaid
erDiagram
    USER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_ITEM : contains
    USER {
        int id PK
        string name
    }
```
````

**PlantUML:**

````markdown
```plantuml
@startuml
entity User {
  * id : int <<PK>>
  --
  name : string
}

entity Order {
  * id : int <<PK>>
  --
  user_id : int <<FK>>
}

entity OrderItem {
  * id : int <<PK>>
  --
  order_id : int <<FK>>
}

User ||--o{ Order : places
Order ||--|{ OrderItem : contains
@enduml
```
````

### コンポーネント図

**Mermaid:**

````markdown
```mermaid
graph LR
    subgraph Frontend
        A[React App]
    end
    subgraph Backend
        B[API Server]
        C[Worker]
    end
    subgraph Database
        D[(PostgreSQL)]
    end
    A --> B
    B --> D
    C --> D
```
````

**PlantUML:**

````markdown
```plantuml
@startuml
package "Frontend" {
  [React App] as A
}

package "Backend" {
  [API Server] as B
  [Worker] as C
}

database "PostgreSQL" as D

A --> B
B --> D
C --> D
@enduml
```
````

## アスキーアート図の扱い

design.mdにアスキーアートで書かれた図がある場合:

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│   Server    │
└─────────────┘
```

→ PlantUMLに変換:

````markdown
```plantuml
@startuml
node "Client"
node "Server"

Client --> Server
@enduml
```
````

## 変換しない要素

以下はMarkdownのまま維持:

- `# 見出し`
- `**太字**`, `*斜体*`
- `- リスト`, `1. 番号リスト`
- `| テーブル |`
- `` `インラインコード` ``
- ` ```コードブロック``` `
- `[リンク](url)`
- `> 引用`
- `---` 水平線

## 注意事項

1. **PlantUMLマクロ必須**: ConfluenceにPlantUMLマクロがインストールされている必要がある
2. **複雑な図**: 自動変換が難しい場合は手動調整が必要
3. **プレビュー確認**: 変換後はConfluenceでプレビュー確認を推奨
