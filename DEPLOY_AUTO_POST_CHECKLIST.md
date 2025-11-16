# ✅ デプロイ後の自動投稿開始チェックリスト

## 🎯 質問: うまくDeployすればもう自動投稿は始まりますか？

**回答**: **はい、デプロイすれば自動投稿が始まります！**

ただし、**必要な環境変数が正しく設定されている必要があります**。

---

## 📋 デプロイ前の確認（必須）

### 1. 必須環境変数の設定

Render ダッシュボード → Web Service → Environment で以下を設定：

```bash
# ✅ 必須: Gemini API
GEMINI_API_KEY=AIzaSyC...

# ✅ 必須: Bluesky認証
BLUESKY_HANDLE=your_handle.bsky.social
BLUESKY_PASSWORD=xxxx-xxxx-xxxx-xxxx
POST_MODE=bluesky

# ✅ 必須: データベース（PostgreSQLから自動設定される）
DATABASE_URL=<Renderが自動設定>
```

### 2. WIRED Botスケジューラーの確認

**デフォルトで有効**になっています。無効化する場合は：

```bash
DISABLE_WIRED_SCHEDULER=false  # デフォルト（有効）
# または
DISABLE_WIRED_SCHEDULER=true  # 無効化する場合
```

**重要**: `DISABLE_WIRED_SCHEDULER`を設定しない場合、**デフォルトで有効**です。

---

## 🚀 デプロイ後の動作

### 自動起動の流れ

1. **RenderがWeb Serviceを起動**
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

2. **FastAPIアプリが起動**
   - `@app.on_event("startup")`で初期化

3. **WIRED Botスケジューラーが自動起動**（30秒後）
   - バックグラウンドスレッドで起動
   - **毎朝8:00（UTC）**にWIRED記事TOP5を自動投稿

4. **常時起動**
   - RenderのWeb Serviceが起動している限り、スケジューラーも動作
   - PCを起動していなくても投稿可能

---

## ✅ デプロイ後の確認方法

### 1. ログで確認（最重要）

Render ダッシュボード → Web Service → 「Logs」タブで以下を確認：

#### ✅ 正常な起動ログ

```
✅ データベース初期化完了
✅ GeminiAnalyzer初期化成功
✅ SocialPoster初期化成功
⏳ WIRED Botスケジューラーを起動します...
🚀 WIRED Botスケジューラー起動を開始...
✅ WIRED Botスケジューラー起動完了（毎朝8:00、改良版）
✅ WIRED Botスケジューラースレッド起動完了
```

#### ⚠️ エラーログがある場合

```
⚠️ GeminiAnalyzer初期化スキップ: GEMINI_API_KEY が設定されていません
⚠️ SocialPoster初期化エラー: BLUESKY_HANDLE が設定されていません
```

**対処**: 環境変数を確認して再デプロイ

### 2. ヘルスチェックで確認

```bash
curl https://kizashi-backend.onrender.com/healthz
```

**期待されるレスポンス**:
```json
{
  "status": "ok",
  "components": {
    "analyzer": "available",
    "poster": "available",
    "scheduler": "stopped"
  }
}
```

**注意**: `scheduler`は標準スケジューラー（無効）なので`stopped`が正常です。WIRED Botスケジューラーは別で動作しています。

### 3. 詳細ヘルスチェック

```bash
curl https://kizashi-backend.onrender.com/health
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
    "scheduler": "stopped"
  }
}
```

---

## 🧪 動作確認方法

### 方法1: テストエンドポイントにアクセス（推奨）

**ブラウザから簡単にアクセス**:

```
https://kizashi-backend.onrender.com/test/wired-bot
```

**または curl で実行**:

```bash
curl https://kizashi-backend.onrender.com/test/wired-bot
```

**動作**:
- WIRED Botが**即座に実行**されます
- WIRED記事TOP5を取得してBlueskyに投稿します
- 実行結果がJSONで返されます

**レスポンス例**:
```json
{
  "status": "success",
  "message": "WIRED Bot (改良版) の実行が完了しました",
  "timestamp": "2025-11-09T10:30:00",
  "note": "Blueskyで投稿を確認してください（POST_MODE=blueskyの場合）"
}
```

**注意**: 
- 実際にBlueskyに投稿されます（`POST_MODE=bluesky`の場合）
- テスト実行後、スケジューラーは通常通り動作します

### 方法2: テストモードで自動実行

環境変数に以下を追加：

```bash
TEST_MODE=true
```

**動作**:
- デプロイ後、30秒後にWIRED Botが**1回だけ即座に実行**されます
- その後、毎朝8:00に通常通り実行されます

**注意**: テストモードを有効にすると、**デプロイ直後に投稿が実行されます**。本番環境では注意してください。

### テストモードを無効化

```bash
TEST_MODE=false  # デフォルト
```

---

## ⏰ 実行時刻の確認

### デフォルト: 毎朝8:00（UTC）

- **UTC 8:00** = **日本時間 17:00（午後5時）**

### 日本時間で8時に投稿したい場合

RenderのタイムゾーンはUTCなので、日本時間の8時はUTCの23時（前日）です。

**コードを修正する必要があります**:

```python
# backend/main.py の _start_wired_scheduler_delayed() 内
# 現在: schedule.every().day.at("08:00").do(wired_job)
# 変更: schedule.every().day.at("23:00").do(wired_job)  # 日本時間8:00 = UTC 23:00
```

---

## 📊 初回投稿の確認

### 1. 毎朝8:00（UTC）に自動投稿

- デプロイ後、**次の8:00（UTC）**に初回投稿が実行されます
- 例: デプロイが10:00（UTC）の場合、次の8:00（UTC）は翌日の8:00

### 2. ログで確認

毎朝8:00（UTC）に以下のログが表示されます：

```
⏰ WIRED Bot実行開始: 2025-11-10 08:00:00
✅ WIRED記事取得完了: 5件
✅ WIRED記事TOP5選定完了
✅ Bluesky投稿完了: 5件
✅ WIRED Bot実行完了
```

### 3. Blueskyで確認

Blueskyアカウントで、毎朝8:00（UTC）に5件の投稿が表示されます。

---

## 🔧 トラブルシューティング

### 問題1: スケジューラーが起動しない

**確認**:
- [ ] ログに「⏳ WIRED Botスケジューラーを起動します...」が表示されているか
- [ ] `DISABLE_WIRED_SCHEDULER=true`になっていないか

**解決**:
```bash
# 環境変数を確認
DISABLE_WIRED_SCHEDULER=false  # または削除（デフォルトで有効）
```

### 問題2: 投稿が実行されない

**確認**:
- [ ] `GEMINI_API_KEY`が設定されているか
- [ ] `BLUESKY_HANDLE`と`BLUESKY_PASSWORD`が正しいか
- [ ] `POST_MODE=bluesky`が設定されているか

**解決**:
- 環境変数を確認して再デプロイ
- ログでエラーを確認

### 問題3: エラーが発生する

**確認**:
- [ ] Render ダッシュボード → Logs でエラーメッセージを確認
- [ ] 環境変数が正しく設定されているか

**解決**:
- エラーメッセージに従って修正
- 環境変数を再設定して再デプロイ

---

## ✅ チェックリスト

### デプロイ前

- [ ] `GEMINI_API_KEY`が設定されている
- [ ] `BLUESKY_HANDLE`が設定されている
- [ ] `BLUESKY_PASSWORD`が設定されている（アプリパスワード）
- [ ] `POST_MODE=bluesky`が設定されている
- [ ] `DISABLE_WIRED_SCHEDULER=false`（または未設定、デフォルトで有効）

### デプロイ後

- [ ] ログで「✅ WIRED Botスケジューラー起動完了」が表示されている
- [ ] `/healthz`エンドポイントが200 OKを返す
- [ ] `/health`エンドポイントで環境変数が正しく設定されていることを確認
- [ ] `/test/wired-bot`エンドポイントで動作確認（推奨）
- [ ] UptimeRobotでバックエンドを監視している（スリープ防止）

### 初回投稿後

- [ ] 毎朝8:00（UTC）にログで実行が確認できる
- [ ] Blueskyで投稿が表示される

---

## 🎯 まとめ

### ✅ 自動投稿が始まる条件

1. **Renderにデプロイ済み**
2. **必須環境変数が設定済み**:
   - `GEMINI_API_KEY`
   - `BLUESKY_HANDLE`
   - `BLUESKY_PASSWORD`
   - `POST_MODE=bluesky`
3. **`DISABLE_WIRED_SCHEDULER=false`**（デフォルト）

### ⏰ 初回投稿のタイミング

- **デプロイ後、次の8:00（UTC）**に初回投稿が実行されます
- 例: デプロイが10:00（UTC）の場合、次の8:00（UTC）は翌日の8:00

### 🧪 即座にテストしたい場合

- `TEST_MODE=true`を設定すると、デプロイ後30秒後に1回だけ実行されます

---

**作成日**: 2025年11月09日

