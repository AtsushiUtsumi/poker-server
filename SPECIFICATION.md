# ポーカーゲーム - プロジェクト仕様書

**バージョン:** 1.0.0  
**最終更新:** 2026-01-01  
**ステータス:** 開発中（MVP実装完了）

---

## 📋 目次

1. [プロジェクト概要](#プロジェクト概要)
2. [アーキテクチャ](#アーキテクチャ)
3. [技術スタック](#技術スタック)
4. [ディレクトリ構成](#ディレクトリ構成)
5. [サーバー仕様](#サーバー仕様)
6. [API仕様](#api仕様)
7. [クライアント仕様](#クライアント仕様)
8. [データモデル](#データモデル)
9. [デプロイ仕様](#デプロイ仕様)
10. [実装状況](#実装状況)
11. [今後の開発計画](#今後の開発計画)

---

## プロジェクト概要

### プロジェクト名
**Poker Game** - マルチクライアント対応オンラインポーカー

### 目的
- WebブラウザとAPIクライアント（CLI/ボット）が混在してプレイできるポーカーゲーム
- 個人開発者が低コスト（月額$5〜）で運用できるサーバー
- 複数のプログラミング言語でクライアントを実装できる拡張性

### ターゲットユーザー
1. **エンドユーザー** - Webブラウザでカジュアルにプレイ
2. **開発者** - 自作ボット/CLIでプレイ
3. **学習者** - API実装の学習教材として

### ゲームルール
- **Texas Hold'em Poker**
- 最大6人プレイ
- ブラインド方式（スモールブラインド、ビッグブラインド）

---

## アーキテクチャ

### システム構成図

```
┌─────────────────────────────────────────────────┐
│              Users / Developers                 │
└───────┬─────────────┬───────────────┬───────────┘
        │             │               │
   ┌────▼────┐   ┌────▼────┐   ┌─────▼──────┐
   │ Web UI  │   │ Go CLI  │   │ Python Bot │
   │(Browser)│   │         │   │            │
   └────┬────┘   └────┬────┘   └─────┬──────┘
        │             │               │
        │    HTTP/WS  │  HTTP/WS      │  HTTP
        └─────────────┴───────────────┘
                      │
            ┌─────────▼──────────┐
            │  FastAPI Server    │
            │  ┌──────────────┐  │
            │  │ REST API     │  │
            │  │ WebSocket    │  │
            │  │ Static Files │  │
            │  └──────────────┘  │
            └────────────────────┘
```

### 通信プロトコル

| プロトコル | 用途 | クライアント |
|-----------|------|-------------|
| HTTP REST | アクション実行、テーブル管理 | 全クライアント |
| WebSocket | リアルタイム状態更新 | Web、Go CLI |
| HTTP Static | Webクライアント配信 | Web |

### データフロー

```
1. プレイヤー参加
   Client → POST /api/tables/{id}/join → Server
   Server → WebSocket broadcast → All Clients

2. アクション実行
   Client → POST /api/tables/{id}/action → Server
   Server → ゲームロジック処理
   Server → WebSocket broadcast → All Clients

3. 状態確認
   Client → GET /api/tables/{id} → Server
   Server → 現在の状態を返す
```

---

## 技術スタック

### サーバー

| 技術 | バージョン | 用途 |
|------|-----------|------|
| Python | 3.11+ | プログラミング言語 |
| FastAPI | 0.109.0+ | Webフレームワーク |
| Uvicorn | 0.27.0+ | ASGIサーバー |
| WebSockets | 12.0+ | リアルタイム通信 |
| Pydantic | 2.5.3+ | データバリデーション |

### クライアント

#### Webクライアント
| 技術 | 用途 |
|------|------|
| HTML5 | マークアップ |
| CSS3 | スタイリング |
| Vanilla JavaScript | 動的処理 |
| WebSocket API | リアルタイム通信 |

#### Go CLI
| 技術 | バージョン | 用途 |
|------|-----------|------|
| Go | 1.21+ | プログラミング言語 |
| gorilla/websocket | 1.5.1 | WebSocket |
| fatih/color | 1.16.0 | カラー表示 |

#### Python Bot
| 技術 | バージョン | 用途 |
|------|-----------|------|
| Python | 3.11+ | プログラミング言語 |
| requests | 最新 | HTTP通信 |

### インフラ

| 技術 | 用途 |
|------|------|
| Docker | コンテナ化 |
| Docker Compose | 開発環境 |
| Nginx | リバースプロキシ（本番） |
| AWS Lightsail | ホスティング（推奨） |

---

## ディレクトリ構成

```
poker-game/
│
├── server/                          # サーバー + Webクライアント（デプロイ単位）
│   ├── poker_server_full.py        # FastAPI サーバー本体
│   ├── static/                      # Webクライアント
│   │   └── index.html               # ゲームUI
│   ├── requirements.txt             # Python依存関係
│   ├── Dockerfile                   # Dockerイメージ定義
│   ├── docker-compose.yml           # Docker Compose設定
│   ├── nginx-lightsail.conf         # Nginx設定（本番用）
│   └── README.md                    # サーバードキュメント
│
├── clients/                         # 外部クライアント（独立パッケージ）
│   │
│   ├── python/                      # Pythonボット
│   │   ├── poker_bot.py             # ボット本体
│   │   ├── requirements.txt         # 依存関係
│   │   └── README.md
│   │
│   ├── go/                          # Go CLI
│   │   ├── main.go                  # エントリーポイント
│   │   ├── client/
│   │   │   └── client.go            # API/WebSocketクライアント
│   │   ├── ui/
│   │   │   └── ui.go                # CLI表示ロジック
│   │   ├── go.mod                   # Go モジュール定義
│   │   ├── go.sum                   # 依存関係ロック
│   │   ├── Makefile                 # ビルドスクリプト
│   │   └── README.md
│   │
│   └── README.md                    # クライアント全般の説明
│
├── docs/                            # プロジェクト全体のドキュメント
│   ├── SPECIFICATION.md             # このファイル
│   ├── API.md                       # API仕様書
│   ├── DEPLOYMENT.md                # デプロイ手順
│   ├── STRUCTURE_COMPARISON.md      # 構成の設計判断
│   └── CONTRIBUTING.md              # コントリビュートガイド
│
├── scripts/                         # 便利スクリプト
│   ├── start-all.sh                 # 全コンポーネント起動
│   ├── setup-dev.sh                 # 開発環境セットアップ
│   └── test-all.sh                  # 全テスト実行
│
├── .github/
│   └── workflows/                   # CI/CD
│       ├── server-ci.yml
│       ├── python-client-ci.yml
│       └── go-client-ci.yml
│
├── .gitignore
├── LICENSE
└── README.md                        # プロジェクト概要
```

### ディレクトリ設計の原則

1. **サーバー + Web = 一体型**
   - Webクライアントは `server/static/` に配置
   - デプロイ時に一緒にパッケージング
   - 理由: Webクライアントは単独では動作しない

2. **外部クライアント = 独立型**
   - `clients/` 配下に言語別に配置
   - 各クライアントは独立して動作可能
   - 理由: 他のサーバーにも接続できる汎用性

---

## サーバー仕様

### 動作環境

| 項目 | 要件 |
|------|------|
| OS | Linux / macOS / Windows |
| Python | 3.11以上 |
| メモリ | 最小512MB、推奨1GB |
| CPU | 1 vCPU以上 |
| ディスク | 1GB以上 |

### 起動方法

#### 開発環境
```bash
cd server
pip install -r requirements.txt
python poker_server_full.py
```

#### 本番環境（Docker）
```bash
cd server
docker-compose up -d
```

### ポート

| ポート | プロトコル | 用途 |
|-------|-----------|------|
| 8000 | HTTP/WS | API & WebSocket |
| 80 | HTTP | Nginx（本番） |
| 443 | HTTPS | Nginx（本番、SSL） |

### 環境変数

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| ENVIRONMENT | development | 環境（development/production） |
| LOG_LEVEL | info | ログレベル |
| HOST | 0.0.0.0 | バインドホスト |
| PORT | 8000 | ポート番号 |

### ログ

- **フォーマット:** JSON形式
- **出力先:** 標準出力
- **ログレベル:** DEBUG, INFO, WARNING, ERROR, CRITICAL

---

## API仕様

### ベースURL

```
http://localhost:8000
```

### 認証

現バージョンでは認証なし（今後実装予定）

### エンドポイント一覧

#### テーブル管理

##### 1. テーブル一覧取得

```http
GET /api/tables
```

**レスポンス:**
```json
{
  "tables": [
    {
      "table_id": "a1b2c3d4-...",
      "players": 3,
      "max_players": 6,
      "phase": "pre_flop",
      "small_blind": 5
    }
  ]
}
```

##### 2. テーブル作成

```http
POST /api/tables?max_players=6&small_blind=5
```

**パラメータ:**
- `max_players` (int): 最大プレイヤー数（デフォルト: 6）
- `small_blind` (int): スモールブラインド（デフォルト: 5）

**レスポンス:**
```json
{
  "table_id": "a1b2c3d4-...",
  "max_players": 6,
  "small_blind": 5,
  "big_blind": 10
}
```

##### 3. テーブル状態取得

```http
GET /api/tables/{table_id}?player_id={player_id}
```

**パラメータ:**
- `player_id` (string, optional): 指定すると自分のカードが見える

**レスポンス:**
```json
{
  "table_id": "a1b2c3d4-...",
  "pot": 150,
  "current_bet": 20,
  "community_cards": ["A♠", "K♦", "Q♥"],
  "phase": "flop",
  "small_blind": 5,
  "big_blind": 10,
  "players": [
    {
      "id": "player-1",
      "name": "Alice",
      "chips": 980,
      "current_bet": 20,
      "folded": false,
      "is_bot": false,
      "cards": ["A♥", "K♠"]  // 自分のカードのみ表示
    },
    {
      "id": "player-2",
      "name": "Bot",
      "chips": 950,
      "current_bet": 20,
      "folded": false,
      "is_bot": true,
      "cards": ["hidden", "hidden"]
    }
  ]
}
```

##### 4. テーブル参加

```http
POST /api/tables/{table_id}/join?player_name={name}&is_bot={bool}
```

**パラメータ:**
- `player_name` (string): プレイヤー名
- `is_bot` (boolean): ボットかどうか（デフォルト: false）

**レスポンス:**
```json
{
  "player_id": "e5f6g7h8-...",
  "table_state": { /* テーブル状態 */ },
  "api_token": "token..."  // is_bot=true の場合のみ
}
```

#### ゲームプレイ

##### 5. アクション実行

```http
POST /api/tables/{table_id}/action
Content-Type: application/json

{
  "player_id": "e5f6g7h8-...",
  "action": "bet",
  "amount": 50
}
```

**アクション種別:**

| アクション | amount必須 | 説明 |
|-----------|-----------|------|
| fold | ❌ | フォールド |
| check | ❌ | チェック |
| call | ❌ | コール |
| bet | ✅ | ベット |
| raise | ✅ | レイズ |
| all_in | ❌ | オールイン |

**レスポンス:**
```json
{
  "success": true,
  "table_state": { /* 更新後のテーブル状態 */ }
}
```

**エラーレスポンス:**
```json
{
  "detail": "Not your turn. Current player: Bob"
}
```

#### その他

##### 6. ヘルスチェック

```http
GET /health
```

**レスポンス:**
```json
{
  "status": "healthy",
  "tables": 3,
  "active_connections": 5
}
```

### WebSocket

#### 接続

```
WS /ws/{table_id}/{player_id}
```

#### 受信メッセージ形式

```json
{
  "type": "action_performed",
  "player_id": "player-1",
  "player_name": "Alice",
  "action": "bet",
  "amount": 50,
  "table_state": { /* テーブル状態 */ }
}
```

#### メッセージタイプ

| type | 説明 |
|------|------|
| connected | 接続確立 |
| player_joined | プレイヤー参加 |
| action_performed | アクション実行 |
| player_disconnected | プレイヤー退出 |
| table_state | 状態更新 |

#### ハートビート

クライアントは30秒ごとに `"ping"` を送信

---

## クライアント仕様

### Webクライアント

#### 技術仕様
- **ファイル:** `server/static/index.html`
- **フレームワーク:** なし（Vanilla JS）
- **対応ブラウザ:** Chrome, Firefox, Safari, Edge（モダンブラウザ）

#### 機能
- [x] テーブル一覧表示
- [x] テーブル作成
- [x] テーブル参加
- [x] リアルタイムゲーム表示（WebSocket）
- [x] アクション実行（Fold, Check, Call, Bet, Raise, All-in）
- [x] プレイヤー情報表示
- [x] コミュニティカード表示
- [x] ゲームログ表示

#### UI構成
```
┌─────────────────────────────────────┐
│  🎲 TABLE STATE                     │
│  💰 POT: ¥150  Current Bet: ¥20     │
│  🃏 Community: [A♠] [K♦] [Q♥]       │
├─────────────────────────────────────┤
│  👥 Players:                        │
│  → Alice  💵 ¥980  [A♥] [K♠]       │
│     Bob    💵 ¥950  [🂠] [🂠]        │
├─────────────────────────────────────┤
│  [Fold] [Check] [Call] [Bet] [...]│
└─────────────────────────────────────┘
```

### Go CLI

#### 技術仕様
- **言語:** Go 1.21+
- **依存パッケージ:**
  - gorilla/websocket
  - fatih/color

#### 機能
- [x] テーブル一覧表示
- [x] テーブル作成・参加
- [x] インタラクティブコマンド入力
- [x] カラフルなCLI表示
- [x] WebSocketリアルタイム更新
- [x] 全アクション対応

#### コマンド

| コマンド | エイリアス | 説明 |
|---------|-----------|------|
| fold | f | フォールド |
| check | k | チェック |
| call | c | コール |
| bet \<amount\> | b | ベット |
| raise \<amount\> | r | レイズ |
| allin | a | オールイン |
| state | s | テーブル状態表示 |
| help | h, ? | ヘルプ表示 |
| quit | exit, q | 終了 |

#### 起動オプション

```bash
./poker-cli [options]

Options:
  -server string
        Poker server URL (default "http://localhost:8000")
  -name string
        Your player name (default "GoPlayer")
  -table string
        Table ID to join (empty to create new)
```

### Python Bot

#### 技術仕様
- **言語:** Python 3.11+
- **依存パッケージ:** requests

#### 機能
- [x] REST APIで接続
- [x] 自動アクション実行
- [x] 簡易AI戦略
- [x] テーブル参加

#### AI戦略

**現在の実装:**
- ベットなし: 20%の確率でベット、80%でチェック
- コール必要: 金額に応じてフォールド/コール判断
- ランダム性あり

**拡張可能:**
- ハンド強度の評価
- ポット オッズ計算
- 相手のプレイスタイル学習

---

## データモデル

### Player（プレイヤー）

```python
class Player:
    id: str              # UUID
    name: str            # プレイヤー名
    chips: int           # 所持チップ
    current_bet: int     # 現在のベット額
    cards: List[str]     # 手札（2枚）
    folded: bool         # フォールドしたか
    is_bot: bool         # ボットかどうか
    last_action_time: datetime
```

### PokerTable（テーブル）

```python
class PokerTable:
    id: str                      # UUID
    players: Dict[str, Player]   # プレイヤー一覧
    max_players: int             # 最大プレイヤー数
    small_blind: int             # スモールブラインド
    big_blind: int               # ビッグブラインド
    pot: int                     # ポット
    current_bet: int             # 現在のベット額
    community_cards: List[str]   # コミュニティカード（最大5枚）
    phase: GamePhase             # ゲームフェーズ
    dealer_position: int         # ディーラー位置
    current_player_index: int    # 現在のプレイヤー
    created_at: datetime
```

### GamePhase（ゲームフェーズ）

```python
class GamePhase(Enum):
    WAITING = "waiting"        # 待機中
    PRE_FLOP = "pre_flop"      # プリフロップ
    FLOP = "flop"              # フロップ
    TURN = "turn"              # ターン
    RIVER = "river"            # リバー
    SHOWDOWN = "showdown"      # ショーダウン
```

### Action（アクション）

```python
class Action(Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"
```

---

## デプロイ仕様

### 推奨環境

#### AWS Lightsail（推奨）

| プラン | 月額 | メモリ | vCPU | 推奨用途 |
|--------|------|--------|------|----------|
| $3.50 | $3.50 | 512MB | 1 | テスト |
| **$5** | **$5** | **1GB** | **1** | **個人開発（推奨）** |
| $10 | $10 | 2GB | 1 | 本格運用 |

**特徴:**
- 静的IP無料
- 簡単セットアップ
- 予測可能な料金

#### その他のオプション

| 環境 | 月額コスト | 推奨度 |
|------|-----------|--------|
| AWS EC2 t3.small | $15〜 | ⭐⭐⭐ |
| Heroku | $7〜 | ⭐⭐ |
| DigitalOcean | $6〜 | ⭐⭐⭐⭐ |
| ローカル開発 | $0 | ⭐⭐⭐⭐⭐ |

### デプロイ手順（Lightsail）

```bash
# 1. Lightsailインスタンス作成（Web GUI）
#    - リージョン: Tokyo
#    - OS: Amazon Linux 2023
#    - プラン: $5

# 2. SSH接続
ssh -i key.pem ec2-user@YOUR_IP

# 3. Dockerインストール（起動スクリプトで自動化可能）
sudo yum update -y
sudo yum install -y docker git
sudo service docker start
sudo usermod -a -G docker ec2-user

# 4. リポジトリクローン
git clone https://github.com/your-repo/poker-game.git
cd poker-game/server

# 5. 起動
docker-compose up -d

# 6. アクセス
# http://YOUR_IP:8000
```

### HTTPS対応（Let's Encrypt）

```bash
# 1. ドメイン取得・設定
# 2. Certbot実行
sudo certbot certonly --standalone -d poker.yourdomain.com

# 3. 証明書配置
sudo cp /etc/letsencrypt/live/poker.yourdomain.com/fullchain.pem server/ssl/cert.pem
sudo cp /etc/letsencrypt/live/poker.yourdomain.com/privkey.pem server/ssl/key.pem

# 4. Nginx設定（nginx-lightsail.conf）のHTTPS部分を有効化
# 5. 再起動
docker-compose restart
```

### モニタリング

#### ヘルスチェック
```bash
curl http://localhost:8000/health
```

#### ログ確認
```bash
docker-compose logs -f poker-server
```

#### リソース監視
- Lightsailメトリクス（CPU, メモリ, ネットワーク）
- Dockerログ

---

## 実装状況

### ✅ 実装済み機能

#### サーバー
- [x] FastAPI サーバー
- [x] REST API（全エンドポイント）
- [x] WebSocket リアルタイム通信
- [x] テーブル管理
- [x] プレイヤー管理
- [x] アクション処理（基本ロジック）
- [x] Webクライアント配信
- [x] Docker対応
- [x] ヘルスチェック

#### Webクライアント
- [x] UI実装
- [x] テーブル参加
- [x] WebSocket接続
- [x] アクション実行
- [x] リアルタイム表示

#### Go CLI
- [x] REST APIクライアント
- [x] WebSocketクライアント
- [x] インタラクティブCLI
- [x] カラー表示
- [x] 全アクション対応

#### Python Bot
- [x] REST APIクライアント
- [x] 自動プレイ
- [x] 簡易AI戦略

### 🚧 未実装機能（今後の開発）

#### ゲームロジック
- [ ] カード配布機能
- [ ] デッキ管理
- [ ] ハンド判定（役の強さ）
- [ ] ターン管理（順番制御）
- [ ] ブラインド自動徴収
- [ ] ポット計算（サイドポット対応）
- [ ] ショーダウン処理
- [ ] 勝者判定
- [ ] チップ配分

#### 機能拡張
- [ ] ユーザー認証
- [ ] テーブルのパスワード保護
- [ ] プライベートテーブル
- [ ] チャット機能
- [ ] ゲーム履歴・リプレイ
- [ ] プレイヤー統計（勝率、収支）
- [ ] ランキング
- [ ] トーナメントモード
- [ ] 観戦モード

#### インフラ
- [ ] データベース（PostgreSQL/Redis）
- [ ] セッション管理
- [ ] スケーリング対応
- [ ] ロードバランサー
- [ ] CI/CD パイプライン
- [ ] 自動テスト

---

## 今後の開発計画

### Phase 1: ゲームロジック完成（優先度: 高）

**目標:** 完全に動作するポーカーゲーム

- [ ] カード配布・デッキ管理
- [ ] ハンド判定ロジック
- [ ] ターン管理
- [ ] ブラインド処理
- [ ] ショーダウン・勝者判定

**期間:** 2-3週間

### Phase 2: ユーザー体験向上（優先度: 中）

**目標:** 使いやすく楽しいゲーム

- [ ] ユーザー認証
- [ ] チャット機能
- [ ] ゲーム統計
- [ ] UI/UX改善
- [ ] モバイル対応

**期間:** 2-4週間

### Phase 3: スケーラビリティ（優先度: 低）

**目標:** 多人数対応

- [ ] データベース導入
- [ ] 負荷分散
- [ ] パフォーマンス最適化
- [ ] 監視・ログ集約

**期間:** 3-4週間

### Phase 4: 高度な機能（優先度: 低）

**目標:** エンターテイメント性向上

- [ ] トーナメント
- [ ] リプレイ機能
- [ ] AI強化
- [ ] マルチテーブル

**期間:** 継続的

---

## 技術的制約・前提

### 現在の制約

1. **メモリストレージ**
   - テーブル情報はメモリに保存
   - サーバー再起動で消失
   - スケールアウト不可

2. **シングルサーバー**
   - 1インスタンスのみ
   - 負荷分散なし

3. **認証なし**
   - 誰でもアクセス可能
   - プライバシー保護なし

4. **ゲームロジック簡易版**
   - カード配布なし
   - ハンド判定なし
   - 手動でアクション実行のみ

### 技術的負債

- テストコードの不足
- エラーハンドリングの不完全性
- ドキュメントの一部未整備
- セキュリティ対策の不足

---

## パフォーマンス要件

### 目標値

| 項目 | 目標 |
|------|------|
| 同時接続数 | 30人（$5プラン） |
| API レスポンス | < 100ms |
| WebSocket遅延 | < 50ms |
| サーバー起動時間 | < 5秒 |
| メモリ使用量 | < 500MB |

### 負荷試験

未実施（今後必要）

---

## セキュリティ

### 現在の対策

- [x] CORS設定
- [x] 入力バリデーション（Pydantic）
- [x] HTTPS対応可能（Nginx）

### 今後必要な対策

- [ ] 認証・認可
- [ ] レート制限
- [ ] SQLインジェクション対策（DB導入時）
- [ ] XSS対策
- [ ] CSRF対策
- [ ] セッション管理

---

## ライセンス

MIT License

---

## 変更履歴

| バージョン | 日付 | 変更内容 |
|-----------|------|---------|
| 1.0.0 | 2026-01-01 | 初版作成 |

---

## 補足資料

- [API詳細仕様](API.md)
- [デプロイガイド](DEPLOYMENT.md)
- [構成設計の判断](STRUCTURE_COMPARISON.md)
- [コントリビュートガイド](CONTRIBUTING.md)

---

**作成者:** 内海淳司  
**プロジェクトURL:** https://github.com/your-repo/poker-game  
**お問い合わせ:** [GitHub Issues](https://github.com/your-repo/poker-game/issues)
