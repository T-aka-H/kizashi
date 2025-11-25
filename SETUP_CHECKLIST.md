# ✅ セットアップチェックリスト

## 🎯 現在の状況

### ✅ 既に持っているもの
- [x] **Render** - ホスティングサービス
- [x] **Blueskyアカウント** - 投稿先
- [x] **UptimeRobot** - スリープ対策

---

## 🔴 必須（まだ登録が必要）

### 1. Gemini APIキー（必須）

**理由**: 記事分析に使用します

**取得方法**:
1. https://makersuite.google.com/app/apikey にアクセス
2. Googleアカウントでログイン
3. 「Create API Key」をクリック
4. 生成されたAPIキーをコピー（`AIza...`で始まる）

**無料枠**: 
- 1分あたり15リクエスト
- 1日あたり1,500リクエスト
- 小規模運用には十分

**設定場所**: Render の Environment Variables に追加

---

### 2. GitHubアカウント（必須）

**理由**: コードをプッシュしてRenderにデプロイするため

**取得方法**:
1. https://github.com にアクセス
2. アカウント作成（無料）
3. リポジトリを作成

**必要な作業**:
- コードをGitHubにプッシュ
- RenderでGitHubリポジトリを接続

---

## 🟡 オプション（あった方が良い）

### 3. GitHubリポジトリ（オプション）

**理由**: コード管理と自動デプロイ

**作成方法**:
```bash
# ローカルで実行
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-username/your-repo.git
git push -u origin main
```

**Renderとの連携**:
- Render ダッシュボードで GitHub を接続
- `main`ブランチにプッシュすると自動デプロイ

---

### 4. ドメイン（オプション）

**理由**: カスタムドメインを使用したい場合

**取得先**:
- Namecheap
- Google Domains
- Cloudflare

**設定**: Render の Settings → Custom Domain

---

## 📋 セットアップ手順（優先順位順）

### Step 1: Gemini APIキーを取得（5分）

1. https://makersuite.google.com/app/apikey にアクセス
2. 「Create API Key」をクリック
3. APIキーをコピー
4. **メモ帳に保存**（後でRenderに設定）

---

### Step 2: GitHubアカウントを作成（5分）

1. https://github.com にアクセス
2. アカウント作成
3. リポジトリを作成（例: `wired-bot`）

---

### Step 3: コードをGitHubにプッシュ（10分）

```bash
# プロジェクトディレクトリで実行
cd C:\dev\wired

# Git初期化（まだの場合）
git init

# ファイルを追加
git add .

# コミット
git commit -m "Initial commit"

# GitHubリポジトリを追加
git remote add origin https://github.com/your-username/your-repo.git

# プッシュ
git push -u origin main
```

---

### Step 4: RenderでPostgreSQLを作成（5分）

1. Render ダッシュボード → 「New +」→「PostgreSQL」
2. 設定:
   - **Name**: `wired-db`
   - **Region**: `Singapore`
   - **Plan**: `Free`
3. 「Create Database」をクリック
4. **接続URLをコピー**（後で使用）

---

### Step 5: RenderでWeb Serviceを作成（10分）

1. Render ダッシュボード → 「New +」→「Web Service」
2. GitHubリポジトリを接続
3. 設定:
   - **Name**: `wired-app`
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/healthz`
   - **Health Check Grace Period**: `180`

---

### Step 6: 環境変数を設定（10分）

Render の Web Service → 「Environment」タブで以下を設定：

#### 必須環境変数
```bash
# データベース（PostgreSQLの接続URL）
DATABASE_URL=postgres://user:password@host/database

# Gemini API
GEMINI_API_KEY=AIzaSyC...（取得したAPIキー）

# Bluesky認証
BLUESKY_HANDLE=your_handle.bsky.social
BLUESKY_PASSWORD=xxxx-xxxx-xxxx-xxxx（アプリパスワード）
POST_MODE=bluesky
```

#### オプション環境変数
```bash
# スケジューラー
DISABLE_SCHEDULER=false
SCHEDULER_INTERVAL_MINUTES=15

# Basic認証（フロントエンド用、本番環境では推奨）
AUTH_USERNAME=admin
AUTH_PASSWORD=your_secure_password

# 投稿確認パスワード
POST_PASSWORD=your_post_password
```

---

### Step 7: UptimeRobotの設定（5分）

1. UptimeRobot ダッシュボードにログイン
2. 「Add New Monitor」をクリック
3. 設定:
   - **Monitor Type**: `HTTP(s)`
   - **Friendly Name**: `WIRED Bot`
   - **URL**: `https://your-app.onrender.com/healthz`
   - **Monitoring Interval**: `5 minutes`
4. 「Create Monitor」をクリック

---

## ✅ 完了チェックリスト

デプロイ前の確認：

- [ ] Gemini APIキーを取得
- [ ] GitHubアカウントを作成
- [ ] コードをGitHubにプッシュ
- [ ] RenderでPostgreSQLを作成
- [ ] RenderでWeb Serviceを作成
- [ ] 環境変数をすべて設定
- [ ] UptimeRobotでモニターを作成
- [ ] ヘルスチェックが成功するか確認

---

## 🔍 確認方法

### 1. ヘルスチェック
```bash
curl https://your-app.onrender.com/healthz
```

**期待されるレスポンス**:
```json
{"status": "ok"}
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
    "post_mode": "bluesky"
  }
}
```

### 3. ログ確認

Render ダッシュボード → Web Service → 「Logs」タブで以下を確認：

```
✅ データベース初期化完了
✅ GeminiAnalyzer初期化成功
✅ SocialPoster初期化成功
✅ スケジューラー起動完了
```

---

## 🐛 よくある問題

### 「GeminiAnalyzer初期化エラー」

**原因**: `GEMINI_API_KEY`が設定されていない

**解決**:
1. Render の Environment Variables で`GEMINI_API_KEY`を確認
2. APIキーが正しいか確認
3. デプロイを再実行

### 「データベース接続エラー」

**原因**: `DATABASE_URL`が正しく設定されていない

**解決**:
1. PostgreSQL ダッシュボードで接続URLをコピー
2. Web Service の Environment Variables で`DATABASE_URL`を設定
3. `postgres://`形式でも自動的に`postgresql://`に変換される

### 「Bluesky投稿エラー」

**原因**: Bluesky認証情報が間違っている

**解決**:
1. `BLUESKY_HANDLE`が正しいか確認（`username.bsky.social`形式）
2. `BLUESKY_PASSWORD`がアプリパスワードか確認（通常のパスワードではない）
3. `POST_MODE=bluesky`が設定されているか確認

---

## 📊 必要なものまとめ

### 必須（まだ登録が必要）
1. ✅ **Gemini APIキー** - 記事分析に使用
2. ✅ **GitHubアカウント** - コード管理とデプロイ

### 既に持っているもの
- ✅ Render
- ✅ Blueskyアカウント
- ✅ UptimeRobot

### オプション
- GitHubリポジトリ（コード管理）
- カスタムドメイン（独自ドメイン）

---

## 🎯 次のステップ

1. **Gemini APIキーを取得** ← 最優先
2. **GitHubアカウントを作成**
3. **コードをGitHubにプッシュ**
4. **Renderでデプロイ**
5. **環境変数を設定**
6. **動作確認**

---

**作成日**: 2025年11月09日  
**ステータス**: ✅ セットアップ準備完了

