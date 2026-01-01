# Poker Game Server - API Documentation

**Version:** 1.0.0
**Base URL:** `http://localhost:8000`
**Protocol:** HTTP/1.1, WebSocket

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Data Models](#data-models)
4. [REST API Endpoints](#rest-api-endpoints)
5. [WebSocket API](#websocket-api)
6. [Error Responses](#error-responses)
7. [Examples](#examples)

---

## Overview

このAPIは、Texas Hold'em Pokerゲームを提供するRESTful APIです。リアルタイム通信にはWebSocketを使用します。

### Features

- マルチテーブル対応
- リアルタイムゲーム状態更新（WebSocket）
- REST APIによるゲームアクション
- 自動ブラインド徴収
- カード配布とデッキ管理

---

## Authentication

現バージョンでは認証機能は実装されていません。すべてのエンドポイントは公開されています。

---

## Data Models

### GamePhase

ゲームの進行フェーズを表す列挙型

| Value | Description |
|-------|-------------|
| `waiting` | 待機中（プレイヤー募集中） |
| `pre_flop` | プリフロップ（コミュニティカード配布前） |
| `flop` | フロップ（コミュニティカード3枚配布後） |
| `turn` | ターン（コミュニティカード4枚目配布後） |
| `river` | リバー（コミュニティカード5枚目配布後） |
| `showdown` | ショーダウン（勝者決定中） |

### ActionType

プレイヤーが実行できるアクション

| Value | Description | Amount Required |
|-------|-------------|----------------|
| `fold` | フォールド（降りる） | No |
| `check` | チェック（ベットなしでパス） | No |
| `call` | コール（現在のベットに合わせる） | No |
| `bet` | ベット（最初のベット） | Yes |
| `raise` | レイズ（ベットを上げる） | Yes |
| `all_in` | オールイン（全チップを賭ける） | No |

### Player

プレイヤー情報

```json
{
  "id": "string (UUID)",
  "name": "string",
  "chips": "integer",
  "current_bet": "integer",
  "cards": ["string", "string"],  // 自分のカードは見える、他人は["hidden", "hidden"]
  "folded": "boolean",
  "is_bot": "boolean",
  "all_in": "boolean"
}
```

### TableState

テーブルの状態

```json
{
  "table_id": "string (UUID)",
  "pot": "integer",
  "current_bet": "integer",
  "community_cards": ["string"],  // 最大5枚
  "phase": "GamePhase",
  "small_blind": "integer",
  "big_blind": "integer",
  "current_player_id": "string (UUID) | null",
  "players": ["Player"],
  "last_action": {
    "player_id": "string",
    "player_name": "string",
    "action": "ActionType",
    "amount": "integer"
  } | null
}
```

### Card Format

カードは文字列で表現されます: `"<Rank><Suit>"`

**Ranks:** `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`, `J`, `Q`, `K`, `A`
**Suits:** `♠` (スペード), `♥` (ハート), `♦` (ダイヤ), `♣` (クラブ)

**Examples:** `"A♠"`, `"K♥"`, `"10♦"`, `"2♣"`

---

## REST API Endpoints

### 1. Health Check

サーバーの稼働状況を確認

**Endpoint:** `GET /health`

**Parameters:** None

**Response:**

```json
{
  "status": "healthy",
  "tables": 3,
  "active_connections": 5
}
```

**Status Codes:**
- `200 OK` - サーバーが正常に稼働中

---

### 2. List Tables

すべてのテーブル一覧を取得

**Endpoint:** `GET /api/tables`

**Parameters:** None

**Response:**

```json
{
  "tables": [
    {
      "table_id": "e7142dcc-5972-4c8b-b30a-02b8f63a6620",
      "players": 3,
      "max_players": 6,
      "phase": "flop",
      "small_blind": 5
    }
  ]
}
```

**Status Codes:**
- `200 OK` - 成功

---

### 3. Create Table

新しいテーブルを作成

**Endpoint:** `POST /api/tables`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `max_players` | integer | No | 6 | 最大プレイヤー数（2-10） |
| `small_blind` | integer | No | 5 | スモールブラインド額 |

**Request Example:**

```
POST /api/tables?max_players=6&small_blind=5
```

**Response:**

```json
{
  "table_id": "e7142dcc-5972-4c8b-b30a-02b8f63a6620",
  "max_players": 6,
  "small_blind": 5,
  "big_blind": 10
}
```

**Status Codes:**
- `200 OK` - テーブル作成成功

---

### 4. Get Table State

テーブルの現在の状態を取得

**Endpoint:** `GET /api/tables/{table_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `table_id` | string (UUID) | テーブルID |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `player_id` | string (UUID) | No | 指定すると自分のカードが見える |

**Request Example:**

```
GET /api/tables/e7142dcc-5972-4c8b-b30a-02b8f63a6620?player_id=c2e676da-7ca4-460e-a01b-f37d4d2c57ae
```

**Response:**

```json
{
  "table_id": "e7142dcc-5972-4c8b-b30a-02b8f63a6620",
  "pot": 150,
  "current_bet": 20,
  "community_cards": ["A♠", "K♦", "Q♥"],
  "phase": "flop",
  "small_blind": 5,
  "big_blind": 10,
  "current_player_id": "c2e676da-7ca4-460e-a01b-f37d4d2c57ae",
  "players": [
    {
      "id": "c2e676da-7ca4-460e-a01b-f37d4d2c57ae",
      "name": "Player1",
      "chips": 980,
      "current_bet": 20,
      "cards": ["A♥", "K♠"],
      "folded": false,
      "is_bot": false,
      "all_in": false
    },
    {
      "id": "f2c466ad-1128-4bc6-a479-51fb42099f34",
      "name": "Bot1",
      "chips": 950,
      "current_bet": 20,
      "cards": ["hidden", "hidden"],
      "folded": false,
      "is_bot": true,
      "all_in": false
    }
  ],
  "last_action": {
    "player_id": "c2e676da-7ca4-460e-a01b-f37d4d2c57ae",
    "player_name": "Player1",
    "action": "bet",
    "amount": 20
  }
}
```

**Status Codes:**
- `200 OK` - 成功
- `404 Not Found` - テーブルが見つからない

---

### 5. Join Table

テーブルに参加

**Endpoint:** `POST /api/tables/{table_id}/join`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `table_id` | string (UUID) | テーブルID |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `player_name` | string | Yes | - | プレイヤー名 |
| `is_bot` | boolean | No | false | ボットかどうか |

**Request Example:**

```
POST /api/tables/e7142dcc-5972-4c8b-b30a-02b8f63a6620/join?player_name=Alice&is_bot=false
```

**Response:**

```json
{
  "player_id": "c2e676da-7ca4-460e-a01b-f37d4d2c57ae",
  "table_state": {
    "table_id": "e7142dcc-5972-4c8b-b30a-02b8f63a6620",
    "pot": 0,
    "current_bet": 0,
    "community_cards": [],
    "phase": "waiting",
    "small_blind": 5,
    "big_blind": 10,
    "current_player_id": null,
    "players": [
      {
        "id": "c2e676da-7ca4-460e-a01b-f37d4d2c57ae",
        "name": "Alice",
        "chips": 1000,
        "current_bet": 0,
        "cards": [],
        "folded": false,
        "is_bot": false,
        "all_in": false
      }
    ],
    "last_action": null
  },
  "api_token": "token_c2e676da-7ca4-460e-a01b-f37d4d2c57ae"  // is_bot=true の場合のみ
}
```

**Status Codes:**
- `200 OK` - 参加成功
- `400 Bad Request` - テーブルが満員、または参加失敗
- `404 Not Found` - テーブルが見つからない

**Notes:**
- 2人目のプレイヤーが参加すると、自動的にゲームが開始されます
- 開始時のチップ数は1000です
- `is_bot=true`の場合、`api_token`が返されます（現在は使用されていません）

---

### 6. Perform Action

ゲームアクションを実行

**Endpoint:** `POST /api/tables/{table_id}/action`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `table_id` | string (UUID) | テーブルID |

**Request Body:**

```json
{
  "player_id": "string (UUID)",
  "action": "ActionType",
  "amount": "integer (optional)"
}
```

**Request Examples:**

```json
// Fold
{
  "player_id": "c2e676da-7ca4-460e-a01b-f37d4d2c57ae",
  "action": "fold"
}

// Check
{
  "player_id": "c2e676da-7ca4-460e-a01b-f37d4d2c57ae",
  "action": "check"
}

// Call
{
  "player_id": "c2e676da-7ca4-460e-a01b-f37d4d2c57ae",
  "action": "call"
}

// Bet
{
  "player_id": "c2e676da-7ca4-460e-a01b-f37d4d2c57ae",
  "action": "bet",
  "amount": 50
}

// Raise
{
  "player_id": "c2e676da-7ca4-460e-a01b-f37d4d2c57ae",
  "action": "raise",
  "amount": 100
}

// All-in
{
  "player_id": "c2e676da-7ca4-460e-a01b-f37d4d2c57ae",
  "action": "all_in"
}
```

**Response:**

```json
{
  "success": true,
  "table_state": {
    // TableState object
  }
}
```

**Status Codes:**
- `200 OK` - アクション成功
- `400 Bad Request` - 自分のターンではない、または無効なアクション
- `404 Not Found` - テーブルが見つからない

**Error Response Example:**

```json
{
  "detail": "Not your turn. Current player: Bob"
}
```

**Action Rules:**

| Action | Conditions | Notes |
|--------|-----------|-------|
| `fold` | Always available | ゲームから降りる |
| `check` | `current_bet == player.current_bet` | ベット額が同じ場合のみ |
| `call` | `current_bet > player.current_bet` | 現在のベットに合わせる |
| `bet` | `current_bet == 0` | 最初のベット |
| `raise` | `current_bet > 0` | 既存のベットを上げる |
| `all_in` | `player.chips > 0` | 全チップを賭ける |

---

## WebSocket API

### Connection

リアルタイム更新を受信するために、WebSocket接続を確立します。

**Endpoint:** `WS /ws/{table_id}/{player_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `table_id` | string (UUID) | テーブルID |
| `player_id` | string (UUID) | プレイヤーID |

**Connection Example:**

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/e7142dcc-5972-4c8b-b30a-02b8f63a6620/c2e676da-7ca4-460e-a01b-f37d4d2c57ae');
```

---

### Outgoing Messages (Client → Server)

#### Heartbeat (Ping)

接続を維持するために定期的に送信

**Message:**

```
"ping"
```

**Response:**

```
"pong"
```

**Recommended Interval:** 30秒

---

### Incoming Messages (Server → Client)

すべてのメッセージはJSON形式です。

#### 1. Connected

接続が確立されたときに送信されます

**Message:**

```json
{
  "type": "connected",
  "player_id": "c2e676da-7ca4-460e-a01b-f37d4d2c57ae",
  "table_id": "e7142dcc-5972-4c8b-b30a-02b8f63a6620"
}
```

---

#### 2. Player Joined

新しいプレイヤーがテーブルに参加したとき

**Message:**

```json
{
  "type": "player_joined",
  "player_id": "f2c466ad-1128-4bc6-a479-51fb42099f34",
  "player_name": "Bob",
  "table_state": {
    // TableState object
  }
}
```

---

#### 3. Action Performed

プレイヤーがアクションを実行したとき

**Message:**

```json
{
  "type": "action_performed",
  "player_id": "c2e676da-7ca4-460e-a01b-f37d4d2c57ae",
  "player_name": "Alice",
  "action": "bet",
  "amount": 50,
  "table_state": {
    // TableState object
  }
}
```

---

#### 4. Player Disconnected

プレイヤーが切断したとき

**Message:**

```json
{
  "type": "player_disconnected",
  "player_id": "f2c466ad-1128-4bc6-a479-51fb42099f34"
}
```

---

## Error Responses

すべてのエラーレスポンスは以下の形式です：

```json
{
  "detail": "Error message"
}
```

### Common Error Codes

| Status Code | Description | Example |
|-------------|-------------|---------|
| `400 Bad Request` | 無効なリクエスト | テーブルが満員、自分のターンではない |
| `404 Not Found` | リソースが見つからない | テーブルが存在しない |
| `422 Unprocessable Entity` | バリデーションエラー | 無効なパラメータ |
| `500 Internal Server Error` | サーバーエラー | 予期しないエラー |

---

## Examples

### Example 1: Create and Join a Game

```bash
# 1. Create a table
curl -X POST "http://localhost:8000/api/tables?max_players=6&small_blind=5"

# Response:
# {
#   "table_id": "e7142dcc-5972-4c8b-b30a-02b8f63a6620",
#   "max_players": 6,
#   "small_blind": 5,
#   "big_blind": 10
# }

# 2. Join the table
curl -X POST "http://localhost:8000/api/tables/e7142dcc-5972-4c8b-b30a-02b8f63a6620/join?player_name=Alice"

# Response:
# {
#   "player_id": "c2e676da-7ca4-460e-a01b-f37d4d2c57ae",
#   "table_state": {...}
# }
```

---

### Example 2: Play a Hand

```bash
# 1. Get current table state
curl "http://localhost:8000/api/tables/e7142dcc-5972-4c8b-b30a-02b8f63a6620?player_id=c2e676da-7ca4-460e-a01b-f37d4d2c57ae"

# 2. Perform an action (if it's your turn)
curl -X POST "http://localhost:8000/api/tables/e7142dcc-5972-4c8b-b30a-02b8f63a6620/action" \
  -H "Content-Type: application/json" \
  -d '{
    "player_id": "c2e676da-7ca4-460e-a01b-f37d4d2c57ae",
    "action": "bet",
    "amount": 50
  }'
```

---

### Example 3: WebSocket Connection (JavaScript)

```javascript
// Connect to WebSocket
const tableId = 'e7142dcc-5972-4c8b-b30a-02b8f63a6620';
const playerId = 'c2e676da-7ca4-460e-a01b-f37d4d2c57ae';
const ws = new WebSocket(`ws://localhost:8000/ws/${tableId}/${playerId}`);

// Handle messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'connected':
      console.log('Connected to table');
      break;
    case 'player_joined':
      console.log(`${data.player_name} joined`);
      updateGameState(data.table_state);
      break;
    case 'action_performed':
      console.log(`${data.player_name} ${data.action} ${data.amount || ''}`);
      updateGameState(data.table_state);
      break;
    case 'player_disconnected':
      console.log(`Player ${data.player_id} disconnected`);
      break;
  }
};

// Send heartbeat every 30 seconds
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send('ping');
  }
}, 30000);

// Handle errors
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

// Handle disconnection
ws.onclose = () => {
  console.log('WebSocket disconnected');
};
```

---

### Example 4: Python Bot

```python
import requests
import time

SERVER_URL = "http://localhost:8000"

# Create table
response = requests.post(f"{SERVER_URL}/api/tables?max_players=6&small_blind=5")
table_id = response.json()["table_id"]

# Join table
response = requests.post(
    f"{SERVER_URL}/api/tables/{table_id}/join",
    params={"player_name": "PythonBot", "is_bot": True}
)
player_id = response.json()["player_id"]

# Game loop
while True:
    # Get table state
    response = requests.get(
        f"{SERVER_URL}/api/tables/{table_id}",
        params={"player_id": player_id}
    )
    state = response.json()

    # Check if it's our turn
    if state["current_player_id"] == player_id:
        # Perform action (simple strategy: always call or check)
        action = "call" if state["current_bet"] > 0 else "check"

        response = requests.post(
            f"{SERVER_URL}/api/tables/{table_id}/action",
            json={
                "player_id": player_id,
                "action": action,
                "amount": 0
            }
        )
        print(f"Performed action: {action}")

    time.sleep(1)
```

---

## Game Flow

1. **Waiting Phase**
   - テーブル作成後、プレイヤーが参加を待つ
   - 2人以上集まると自動的にゲーム開始

2. **Pre-Flop**
   - 各プレイヤーに2枚のカードが配られる
   - スモールブラインド、ビッグブラインドが自動徴収される
   - ビッグブラインドの次のプレイヤーからアクション開始

3. **Flop**
   - コミュニティカード3枚が配られる
   - ディーラーの次のプレイヤーからアクション開始

4. **Turn**
   - コミュニティカード4枚目が配られる
   - ベッティングラウンド

5. **River**
   - コミュニティカード5枚目が配られる
   - 最終ベッティングラウンド

6. **Showdown**
   - 勝者決定（現在は簡易実装: ランダムまたは最後まで残ったプレイヤー）
   - チップ配分
   - 新しいハンドが自動的に開始

---

## Rate Limiting

現在、レート制限は実装されていません。

---

## Changelog

### Version 1.0.0 (2026-01-01)
- Initial release
- REST API endpoints
- WebSocket real-time updates
- Basic game logic
- Card dealing and deck management
- Automatic blind collection

---

## Support

問題が発生した場合は、GitHubのIssuesで報告してください。

**Project URL:** https://github.com/your-repo/poker-game

---

## License

MIT License
