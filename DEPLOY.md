# Render デプロイガイド

## 前提条件

- GitHubアカウント
- Renderアカウント（[https://render.com](https://render.com)）
- Gemini APIキー
- Blueskyアカウント（アプリパスワード）

## デプロイ手順

### ステップ1: リポジトリの準備

```bash
# リポジトリを初期化（まだの場合）
git init
git add .
git commit -m "Initial commit"

# GitHubにプッシュ
git remote add origin https://github.com/yourusername/weak-signals-app.git
git push -u origin main
```

### ステップ2: RenderでBlueprintを作成

1. [Render Dashboard](https://dashboard.render.com/)にログイン
2. "New +" → "Blueprint" を選択
3. GitHubリポジトリを接続・選択
4. Renderが自動的に`render.yaml`を検出
5. "Apply" をクリック

### ステップ3: 環境変数の設定

Blueprint作成後、各サービスで環境変数を設定：

#### バックエンドサービス

Render Dashboard → `kizashi-backend` → Environment

以下の環境変数を追加：

```
GEMINI_API_KEY=your_gemini_api_key
POST_MODE=bluesky
BLUESKY_HANDLE=yourname.bsky.social
BLUESKY_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

**注意**: `DATABASE_URL`は自動的に設定されます（データベースサービスから）

#### フロントエンドサービス

`NEXT_PUBLIC_API_URL`は自動的に設定されますが、手動で設定する場合：

```
NEXT_PUBLIC_API_URL=https://kizashi-backend.onrender.com
```

### ステップ4: デプロイの確認

1. 各サービスのログを確認
2. バックエンド: `https://kizashi-backend.onrender.com/docs`
3. フロントエンド: `https://kizashi-frontend.onrender.com`

### ステップ5: データベースの初期化

初回デプロイ後、データベーステーブルを作成：

**方法1: Render Shellを使用**

1. Render Dashboard → `kizashi-backend` → Shell
2. 以下を実行：

```bash
cd backend
python -c "from database import init_db; init_db()"
```

**方法2: APIから実行**

バックエンドが起動すると、`init_db()`が自動実行されます（`main.py`で呼び出されています）

## 手動デプロイ（Blueprintを使わない場合）

### バックエンドのデプロイ

1. "New +" → "Web Service"
2. GitHubリポジトリを接続
3. 設定：
   - **Name**: `kizashi-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Starter（無料プラン）

### フロントエンドのデプロイ

1. "New +" → "Web Service"
2. GitHubリポジトリを接続
3. 設定：
   - **Name**: `kizashi-frontend`
   - **Environment**: `Node`
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Start Command**: `cd frontend && npm start`
   - **Plan**: Starter

### データベースの作成

1. "New +" → "PostgreSQL"
2. 設定：
   - **Name**: `kizashi-db`
   - **Database**: `kizashi`
   - **User**: `kizashi_user`
   - **Plan**: Starter（無料プラン）

3. バックエンドサービスに`DATABASE_URL`環境変数を追加（自動的に提供されます）

## 環境変数の取得方法

### Gemini APIキー

1. [Google AI Studio](https://makersuite.google.com/app/apikey)にアクセス
2. "Create API Key" をクリック
3. キーをコピー

### Bluesky認証情報

1. [Bluesky](https://bsky.app)にログイン
2. 設定 → App passwords → 新規作成
3. 生成されたパスワードをコピー
4. `BLUESKY_HANDLE` と `BLUESKY_PASSWORD` を設定

## トラブルシューティング

### ビルドが失敗する

- ログを確認: Render Dashboard → Service → Logs
- 依存パッケージのバージョンを確認
- `requirements.txt`と`package.json`が正しいか確認

### データベース接続エラー

- `DATABASE_URL`が正しく設定されているか確認
- データベースサービスが起動しているか確認
- 接続文字列の形式を確認（`postgresql://`で始まる必要があります）

### CORSエラー

- `main.py`のCORS設定を確認
- フロントエンドのURLを`allow_origins`に追加

### 環境変数が反映されない

- 環境変数を設定後、サービスを再デプロイ
- 環境変数の名前が正しいか確認（大文字小文字を区別）

## カスタムドメインの設定

1. Render Dashboard → Service → Settings
2. "Custom Domains" セクション
3. ドメインを追加
4. DNS設定を更新

## 無料プランの制限

- **スピンアップ時間**: 15分間の非アクティブ後にスリープ
- **月間実行時間**: 750時間
- **データベース**: 90日間の非アクティブ後に削除される可能性

本番環境では有料プランの使用を推奨します。

## 継続的デプロイ

GitHubにプッシュすると自動的にデプロイされます。

無効化する場合：
- Render Dashboard → Service → Settings → "Auto-Deploy" をオフ

## ログの確認

- Render Dashboard → Service → Logs
- リアルタイムログを確認可能
- エラーの詳細を確認

## サポート

問題が解決しない場合：
- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com/)

