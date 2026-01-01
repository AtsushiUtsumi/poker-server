# Poker Game - マルチクライアント対応オンラインポーカー

WebブラウザとAPIクライアント（CLI/ボット）が混在してプレイできるTexas Hold'em Pokerゲーム

## 概要

このプロジェクトは、以下のコンポーネントで構成されています:

- **サーバー**: FastAPI製のポーカーゲームサーバー
- **Webクライアント**: ブラウザで遊べるHTML/JavaScript UI
- **Go CLIクライアント**: ターミナルで遊べるカラフルなCLI
- **Pythonボット**: 自動プレイするAIボット

## クイックスタート

### 起動スクリプトを使う（推奨）

```bash
./start_game.sh
```

起動後、メニューから以下を選択できます:
1. Webブラウザでプレイ
2. Go CLIクライアントで起動
3. Pythonボットを起動
4. デモモード（Web + 2ボット）
5. サーバーのみ起動
6. 停止して終了

### 手動起動

#### サーバー起動
```bash
cd server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python poker_server_full.py
```

サーバーは http://localhost:8000 で起動します

#### Webクライアント
ブラウザで http://localhost:8000 にアクセス

#### Go CLIクライアント
```bash
cd clients/go
go mod download
go build -o poker-cli .
./poker-cli -server http://localhost:8000 -name "YourName"
```

#### Pythonボット
```bash
cd clients/python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python poker_bot.py --server http://localhost:8000 --name "BotName"
```

## プロジェクト構成

```
poker-server/
├── server/                  # サーバー
│   ├── poker_server_full.py # FastAPIサーバー
│   ├── static/              # Webクライアント
│   │   └── index.html
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
├── clients/                 # クライアント
│   ├── go/                  # Go CLI
│   │   ├── main.go
│   │   ├── client/
│   │   └── ui/
│   └── python/              # Pythonボット
│       └── poker_bot.py
├── SPECIFICATION.md         # 詳細仕様書
└── start_game.sh           # 起動スクリプト
```

## 機能

### 実装済み
- REST API (テーブル管理、アクション実行)
- WebSocketリアルタイム通信
- カード配布とデッキ管理
- 基本的なゲームフロー（プリフロップ〜リバー）
- ブラインド自動徴収
- 複数クライアント対応
- マルチテーブル対応

### 今後の実装
- ハンド判定（役の強さ）
- 正確なショーダウン処理
- ユーザー認証
- チャット機能
- ゲーム統計

## Docker での起動

```bash
cd server
docker-compose up -d
```

## API仕様

詳細は [SPECIFICATION.md](SPECIFICATION.md) を参照してください。

主なエンドポイント:
- `GET /api/tables` - テーブル一覧
- `POST /api/tables` - テーブル作成
- `POST /api/tables/{id}/join` - テーブル参加
- `POST /api/tables/{id}/action` - アクション実行
- `WS /ws/{table_id}/{player_id}` - WebSocket接続

## テスト実行結果

すべてのクライアントが正常に動作することを確認済み:
- サーバーが正常に起動
- 2つのPythonボットが自動プレイ
- Go CLIクライアントがテーブルに参加
- ボット同士でゲームが進行（フロップ、ターン、リバー、ショーダウン）
- Webクライアントが正しく配信

## ライセンス

MIT License
