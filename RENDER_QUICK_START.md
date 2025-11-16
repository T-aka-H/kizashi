# 🚀 Renderデプロイ - クイックスタート

## ✅ 現在の状況

- ✅ GitHubにプッシュ済み: `https://github.com/T-aka-H/kizashi.git`
- ✅ 次はRenderと同期してデプロイ

---

## 📝 Renderデプロイ手順（5ステップ）

### Step 1: PostgreSQLデータベースを作成（5分）

1. **Render ダッシュボード**にアクセス: https://dashboard.render.com
2. 「**New +**」→「**PostgreSQL**」をクリック
3. 以下を設定：
   - **Name**: `kizashi-db`（任意の名前）
   - **Database**: `weak_signals`（デフォルトでOK）
   - **Region**: `Singapore`（日本に最も近い）
   - **Plan**: `Free`（0.1GB）
4. 「**Create Database**」をクリック
5. **接続URLをコピー**（後で使用）

---

### Step 2: Web Serviceを作成（10分）

1. Render ダッシュボードで「**New +**」→「**Web Service**」をクリック
2. **GitHubリポジトリを接続**
   - 「Connect GitHub」をクリック
   - リポジトリ `T-aka-H/kizashi` を選択
   - 「Connect」をクリック

3. **Basic Settings**を設定：
   ```
   Name: kizashi-app
   Region: Singapore
   Branch: main
   Root Directory: backend
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

4. **Advanced Settings**を開いて設定：
   ```
   Health Check Path: /healthz
   Health Check Grace Period: 180
   Auto-Deploy: Yes
   ```

5. 「**Create Web Service**」をクリック

---

### Step 3: 環境変数を設定（10分）

Web Service の「**Environment**」タブで以下を追加：

#### 必須環境変数

```bash
# データベース（PostgreSQLの接続URLをコピー）
DATABASE_URL=postgres://user:password@host/database

# Gemini API
GEMINI_API_KEY=AIzaSyC...（あなたのAPIキー）

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

# Basic認証（本番環境では推奨）
AUTH_USERNAME=admin
AUTH_PASSWORD=your_secure_password

# 投稿確認パスワード
POST_PASSWORD=your_post_password
```

**設定方法**:
1. 「**Add Environment Variable**」をクリック
2. Key と Value を入力
3. 「**Save Changes**」をクリック

---

### Step 4: データベースを接続（5分）

1. PostgreSQL ダッシュボードを開く
2. 「**Connect**」タブをクリック
3. 「**Internal Database URL**」をコピー
4. Web Service の「**Environment**」タブで：
   - `DATABASE_URL` を追加（または既存のものを更新）
   - コピーしたURLを貼り付け
5. 「**Save Changes**」をクリック

---

### Step 5: デプロイ確認（5分）

1. **ログを確認**
   - Web Service → 「**Logs**」タブ
   - 以下が表示されれば成功：
     ```
     ✅ データベース初期化完了
     ✅ GeminiAnalyzer初期化成功
     ✅ SocialPoster初期化成功
     ✅ スケジューラー起動完了
     ```

2. **ヘルスチェック**
   - ブラウザで開く: `https://your-app.onrender.com/healthz`
   - または:
     ```bash
     curl https://your-app.onrender.com/healthz
     ```
   - **期待されるレスポンス**:
     ```json
     {"status": "ok"}
     ```

3. **詳細ヘルスチェック**
   - `https://your-app.onrender.com/health`
   - すべてのコンポーネントが `available` または `running` になっているか確認

---

## ✅ デプロイ完了チェックリスト

- [ ] PostgreSQLデータベースを作成
- [ ] Web Serviceを作成
- [ ] GitHubリポジトリを接続
- [ ] すべての必須環境変数を設定
- [ ] `DATABASE_URL`をPostgreSQLに接続
- [ ] デプロイが成功（ログで確認）
- [ ] ヘルスチェックが成功（`/healthz`）
- [ ] 詳細ヘルスチェックで全コンポーネントが動作中

---

## 🔄 自動デプロイ

一度設定すれば、`main`ブランチにプッシュするだけで自動的にデプロイされます：

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

## 🐛 よくある問題

### 「デプロイが失敗する」

**確認事項**:
1. `Root Directory`が`backend`になっているか
2. `Build Command`が正しいか: `pip install -r requirements.txt`
3. `Start Command`が正しいか: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. ログでエラーメッセージを確認

### 「GeminiAnalyzer初期化エラー」

**原因**: `GEMINI_API_KEY`が設定されていない

**解決**:
1. Environment Variables で`GEMINI_API_KEY`を確認
2. 正しいAPIキーが設定されているか確認
3. 「Save Changes」をクリック
4. デプロイを再実行

### 「データベース接続エラー」

**原因**: `DATABASE_URL`が正しく設定されていない

**解決**:
1. PostgreSQL ダッシュボードで接続URLをコピー
2. Web Service の Environment Variables で`DATABASE_URL`を設定
3. `postgres://`形式でも自動的に`postgresql://`に変換される

---

## 📊 デプロイ後の確認

### 1. アプリケーションURL

Render ダッシュボード → Web Service → 「**URL**」を確認

例: `https://kizashi-app.onrender.com`

### 2. APIドキュメント

ブラウザで開く: `https://your-app.onrender.com/docs`

### 3. ヘルスチェック

```bash
curl https://your-app.onrender.com/healthz
curl https://your-app.onrender.com/health
```

---

## 🎉 完了！

これでRenderへのデプロイが完了しました！

**次のステップ**:
- UptimeRobotでスリープ対策（既に設定済み）
- フロントエンドからAPIに接続
- WIRED Botの動作確認

---

**作成日**: 2025年11月09日

