# Render デプロイ設定ガイド

## Render設定の詳細

### バックエンド（FastAPI）

#### Language / Environment
- **Language**: `Python 3`
- **Environment**: `python` (render.yamlでは `env: python`)

#### Build Command
```bash
pip install -r backend/requirements.txt
```

#### Start Command
```bash
cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

**説明:**
- `$PORT` はRenderが自動的に設定する環境変数です
- `0.0.0.0` で全インターフェースからアクセス可能にします
- `cd backend` でbackendディレクトリに移動してから実行

#### Root Directory（オプション）
設定しない場合、プロジェクトルートが使用されます。

#### 環境変数
- `PYTHON_VERSION`: `3.11.0`（自動設定）
- `DATABASE_URL`: データベースから自動設定
- `GEMINI_API_KEY`: 手動設定が必要
- `POST_MODE`: `bluesky` または `demo`
- `BLUESKY_HANDLE`: Blueskyのハンドル（例: `yourname.bsky.social`）
- `BLUESKY_PASSWORD`: Blueskyのアプリパスワード

---

### フロントエンド（Next.js）

#### Language / Environment
- **Language**: `Node`
- **Environment**: `node` (render.yamlでは `env: node`)

#### Build Command
```bash
cd frontend && npm install && npm run build
```

**説明:**
- `cd frontend` でfrontendディレクトリに移動
- `npm install` で依存パッケージをインストール
- `npm run build` でNext.jsアプリをビルド

#### Start Command
```bash
cd frontend && npm start
```

**説明:**
- `npm start` でビルド済みのNext.jsアプリを起動
- 本番環境用のコマンドです（`npm run dev`ではない）

#### Root Directory（オプション）
設定しない場合、プロジェクトルートが使用されます。

#### 環境変数
- `NODE_VERSION`: `20.x`（自動設定）
- `NEXT_PUBLIC_API_URL`: バックエンドのURL（例: `https://weak-signals-backend.onrender.com`）

---

## 手動設定手順（Blueprintを使わない場合）

### バックエンドの設定

1. Render Dashboard → "New +" → "Web Service"
2. GitHubリポジトリを接続
3. 以下の設定を入力：

| 項目 | 値 |
|------|-----|
| **Name** | `weak-signals-backend` |
| **Region** | `Oregon (US West)` |
| **Branch** | `main`（または使用するブランチ） |
| **Root Directory** | （空白のまま） |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r backend/requirements.txt` |
| **Start Command** | `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Plan** | `Starter`（無料プラン） |

### フロントエンドの設定

1. Render Dashboard → "New +" → "Web Service"
2. GitHubリポジトリを接続
3. 以下の設定を入力：

| 項目 | 値 |
|------|-----|
| **Name** | `weak-signals-frontend` |
| **Region** | `Oregon (US West)` |
| **Branch** | `main`（または使用するブランチ） |
| **Root Directory** | （空白のまま） |
| **Environment** | `Node` |
| **Build Command** | `cd frontend && npm install && npm run build` |
| **Start Command** | `cd frontend && npm start` |
| **Plan** | `Starter`（無料プラン） |

### データベースの設定

1. Render Dashboard → "New +" → "PostgreSQL"
2. 以下の設定を入力：

| 項目 | 値 |
|------|-----|
| **Name** | `weak-signals-db` |
| **Database** | `weak_signals` |
| **User** | `weak_signals_user` |
| **Region** | `Oregon (US West)` |
| **Plan** | `Starter`（無料プラン） |

3. バックエンドサービスに`DATABASE_URL`環境変数を追加：
   - データベースの「Connections」タブから「Internal Database URL」をコピー
   - バックエンドサービスの環境変数に`DATABASE_URL`として追加

---

## 環境変数の設定

### バックエンドサービス

Render Dashboard → `weak-signals-backend` → Environment → Add Environment Variable

| キー | 値 | 説明 |
|------|-----|------|
| `GEMINI_API_KEY` | `your_gemini_api_key` | Gemini APIキー |
| `POST_MODE` | `bluesky` | 投稿モード（`bluesky` または `demo`） |
| `BLUESKY_HANDLE` | `yourname.bsky.social` | Blueskyハンドル |
| `BLUESKY_PASSWORD` | `xxxx-xxxx-xxxx-xxxx` | Blueskyアプリパスワード |
| `DATABASE_URL` | （自動設定） | データベース接続URL |

### フロントエンドサービス

Render Dashboard → `weak-signals-frontend` → Environment → Add Environment Variable

| キー | 値 | 説明 |
|------|-----|------|
| `NEXT_PUBLIC_API_URL` | `https://weak-signals-backend.onrender.com` | バックエンドのURL |

**重要**: `NEXT_PUBLIC_` プレフィックスが必要です（Next.jsの仕様）

---

## よくある質問

### Q: Build Commandでエラーが出る

**A:** パスの確認：
- `backend/requirements.txt` が存在するか確認
- プロジェクトルートから見た相対パスが正しいか確認

### Q: Start Commandでエラーが出る

**A:** 確認事項：
- `$PORT` 環境変数が設定されているか（Renderが自動設定）
- `cd backend` で正しいディレクトリに移動しているか
- `uvicorn` がインストールされているか（requirements.txtに含まれているか）

### Q: フロントエンドがバックエンドに接続できない

**A:** 確認事項：
- `NEXT_PUBLIC_API_URL` が正しく設定されているか
- バックエンドのURLが正しいか（`.onrender.com` で終わる）
- CORS設定が正しいか（`main.py`で確認）

### Q: データベース接続エラー

**A:** 確認事項：
- `DATABASE_URL` が設定されているか
- データベースサービスが起動しているか
- 接続文字列の形式が正しいか（`postgresql://` で始まる）

---

## デプロイ後の確認

1. **バックエンド**: `https://weak-signals-backend.onrender.com/docs`
   - FastAPIの自動生成ドキュメントが表示されれば成功

2. **フロントエンド**: `https://weak-signals-frontend.onrender.com`
   - ダッシュボードが表示されれば成功

3. **ログ確認**: Render Dashboard → Service → Logs
   - エラーがないか確認

---

## トラブルシューティング

### ビルドが失敗する場合

1. ログを確認: Render Dashboard → Service → Logs
2. 依存パッケージのバージョンを確認
3. `requirements.txt` と `package.json` が正しいか確認

### サービスが起動しない場合

1. Start Commandが正しいか確認
2. 環境変数が正しく設定されているか確認
3. ポート番号が`$PORT`を使用しているか確認

### データベース接続エラー

1. `DATABASE_URL` が正しく設定されているか確認
2. データベースサービスが起動しているか確認
3. 接続文字列の形式を確認

