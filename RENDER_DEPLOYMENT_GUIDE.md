# 🚀 Render デプロイガイド

このガイドでは、WIRED記事TOP5投稿Botを含む「Weak Signals App」をRenderにデプロイする手順を説明します。

---

## 📋 前提条件

- [ ] Renderアカウント（無料プランでOK）
- [ ] GitHubリポジトリにコードをプッシュ済み
- [ ] Gemini APIキー取得済み
- [ ] Blueskyアカウント作成済み（アプリパスワード取得済み）

---

## 🎯 デプロイ構成

### Web Service（FastAPI）
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path**: `/healthz`
- **Auto-Deploy**: `main`ブランチにプッシュで自動デプロイ

### PostgreSQL Database
- Renderが自動的に`DATABASE_URL`環境変数を設定
- バックアップ機能あり

### スケジューラー
- バックグラウンドスレッドで実行
- 環境変数で有効/無効を切り替え可能

---

## 📝 デプロイ手順

### 1. PostgreSQLデータベースを作成

1. Render ダッシュボードで「New +」→「PostgreSQL」
2. 以下を設定：
   - **Name**: `wired-db`（任意の名前）
   - **Database**: `weak_signals`（デフォルトでOK）
   - **User**: 自動生成
   - **Region**: `Singapore`（日本に最も近い）
   - **Plan**: `Free`（0.1GB）
3. 「Create Database」をクリック

### 2. Web Serviceを作成

1. Render ダッシュボードで「New +」→「Web Service」
2. GitHubリポジトリを接続
3. 以下を設定：

#### Basic Settings
- **Name**: `wired-app`（任意の名前）
- **Region**: `Singapore`
- **Branch**: `main`
- **Root Directory**: `backend`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

#### Advanced Settings
- **Health Check Path**: `/healthz`
- **Auto-Deploy**: `Yes`

4. 「Create Web Service」をクリック

### 3. 環境変数を設定

Web Service の「Environment」タブで以下を設定：

#### 必須
```bash
# データベース（RenderのPostgreSQLから自動設定）
DATABASE_URL=<Renderが自動設定>

# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Bluesky認証
BLUESKY_HANDLE=your_handle.bsky.social
BLUESKY_PASSWORD=your_app_password_here
POST_MODE=bluesky
```

#### オプション
```bash
# スケジューラー設定
DISABLE_SCHEDULER=false
SCHEDULER_INTERVAL_MINUTES=15

# Basic認証（フロントエンド用）
AUTH_USERNAME=admin
AUTH_PASSWORD=your_secure_password

# 投稿確認パスワード
POST_PASSWORD=your_post_password
```

### 4. データベースを接続

1. Web Service の「Environment」タブで「Add Environment Variable」
2. `DATABASE_URL`を追加（PostgreSQLの接続URLをコピー）
   - PostgreSQL ダッシュボード → 「Connect」→ 「External Connection String」をコピー
   - **形式**: `postgres://user:password@host/database`
   - Renderが自動的に`postgresql://`に変換します

---

## ✅ デプロイ確認

### 1. ヘルスチェック
```bash
curl https://your-app.onrender.com/healthz
```

**期待されるレスポンス**:
```json
{
  "status": "ok",
  "components": {
    "analyzer": "available",
    "poster": "available",
    "scheduler": "running"
  }
}
```

### 2. 詳細ヘルスチェック
```bash
curl https://your-app.onrender.com/health
```

**期待されるレスポンス**:
```json
{
  "status": "ok",
  "database": "connected",
  "environment": {
    "gemini_api_key_set": true,
    "bluesky_handle_set": true,
    "post_mode": "bluesky",
    "scheduler_enabled": true
  },
  "components": {
    "analyzer": "available",
    "poster": "available",
    "scheduler": "running"
  }
}
```

### 3. ログを確認

Render ダッシュボード → Web Service → 「Logs」タブで以下を確認：

```
✅ .envファイルが見つかりません（環境変数から直接取得します）
✅ データベース初期化完了
📊 データベースタイプ: PostgreSQL
🚀 アプリケーション初期化を開始...
✅ GeminiAnalyzer初期化成功
✅ SocialPoster初期化成功
✅ スケジューラーをバックグラウンドで起動（15分間隔）
✅ アプリケーション初期化完了
```

---

## 🔧 環境変数リファレンス

### 必須環境変数

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `DATABASE_URL` | PostgreSQL接続URL | `postgres://user:pass@host/db` |
| `GEMINI_API_KEY` | Gemini APIキー | `AIza...` |
| `BLUESKY_HANDLE` | Blueskyハンドル | `username.bsky.social` |
| `BLUESKY_PASSWORD` | Blueskyアプリパスワード | `xxxx-xxxx-xxxx-xxxx` |

### オプション環境変数

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `POST_MODE` | `demo` | `bluesky`: 実際に投稿, `demo`: テストモード |
| `DISABLE_SCHEDULER` | `false` | `true`: スケジューラー無効化 |
| `SCHEDULER_INTERVAL_MINUTES` | `15` | スケジューラー実行間隔（分） |
| `AUTH_USERNAME` | - | Basic認証ユーザー名（フロントエンド用） |
| `AUTH_PASSWORD` | - | Basic認証パスワード（フロントエンド用） |
| `POST_PASSWORD` | - | 投稿確認パスワード |

---

## 📊 スケジューラーの動作

### デフォルト動作
- **実行間隔**: 15分ごとに記事取得・分析
- **投稿間隔**: 5分ごとに承認済み記事を投稿
- **バックグラウンド実行**: デーモンスレッドで実行

### 無効化する場合
```bash
DISABLE_SCHEDULER=true
```

### 実行間隔を変更
```bash
SCHEDULER_INTERVAL_MINUTES=30  # 30分間隔
```

---

## 🐛 トラブルシューティング

### 「GeminiAnalyzer初期化エラー」

**原因**: `GEMINI_API_KEY`が設定されていない

**解決**:
1. Render の Environment タブで`GEMINI_API_KEY`を設定
2. デプロイを再実行

### 「データベース接続エラー」

**原因**: `DATABASE_URL`が正しく設定されていない

**解決**:
1. PostgreSQL ダッシュボードで接続URLをコピー
2. Web Service の Environment タブで`DATABASE_URL`を設定
3. `postgres://`形式でも自動的に`postgresql://`に変換される

### 「SocialPoster初期化エラー」

**原因**: Bluesky認証情報が設定されていない

**解決**:
1. `BLUESKY_HANDLE`と`BLUESKY_PASSWORD`を設定
2. アプリパスワードを使用（通常のパスワードではない）
3. `POST_MODE=bluesky`を設定

### 「スケジューラーが起動しない」

**確認**:
```bash
curl https://your-app.onrender.com/health
```

`"scheduler": "stopped"`の場合：

**原因1**: `DISABLE_SCHEDULER=true`が設定されている
**原因2**: 初期化エラーが発生している

**解決**:
1. ログを確認してエラーメッセージを確認
2. `DISABLE_SCHEDULER`を`false`に設定

### 「Health Check Failed」

**原因**: `/healthz`エンドポイントが応答していない

**解決**:
1. Start Commandが正しいか確認: `uvicorn main:app --host 0.0.0.0 --port $PORT`
2. ログでエラーを確認
3. `requirements.txt`がすべてインストールされているか確認

---

## 📈 モニタリング

### ヘルスチェック
```bash
# 基本ヘルスチェック
curl https://your-app.onrender.com/healthz

# 詳細ヘルスチェック
curl https://your-app.onrender.com/health

# 統計情報
curl https://your-app.onrender.com/stats
```

### ログ監視
- Render ダッシュボード → Logs
- リアルタイムでログを確認可能

---

## 🔄 自動デプロイ

`main`ブランチにプッシュすると自動的にデプロイされます：

```bash
git add .
git commit -m "Update"
git push origin main
```

Renderが自動的に：
1. 変更を検知
2. ビルドを実行
3. デプロイ
4. ヘルスチェックを実行

---

## 💰 コスト

### 無料プラン
- **Web Service**: 750時間/月（1つのサービスで使い切る）
- **PostgreSQL**: 0.1GB（小規模プロジェクトには十分）
- **制限**: 
  - 15分間アクセスがないとスリープ
  - 次回アクセス時に起動（30秒程度）

### スリープ対策
外部サービス（UptimeRobot等）で定期的に`/healthz`にアクセス

---

## 📚 参考リンク

- [Render公式ドキュメント](https://render.com/docs)
- [FastAPIデプロイガイド](https://render.com/docs/deploy-fastapi)
- [PostgreSQLセットアップ](https://render.com/docs/databases)

---

## ✅ チェックリスト

デプロイ前の確認：

- [ ] PostgreSQLデータベースを作成
- [ ] Web Serviceを作成
- [ ] すべての必須環境変数を設定
- [ ] `DATABASE_URL`をPostgreSQLに接続
- [ ] Start Commandが正しい
- [ ] Health Check Pathが`/healthz`
- [ ] デプロイ完了後、`/healthz`にアクセスして確認
- [ ] ログでエラーがないか確認
- [ ] フロントエンドからAPIに接続できるか確認

---

**作成日**: 2025年11月09日  
**最終更新**: 2025年11月09日

