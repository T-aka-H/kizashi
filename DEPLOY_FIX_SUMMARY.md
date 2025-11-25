# 🔧 デプロイ修正サマリー

## ❌ 問題点

ログから以下の問題が確認されました：

1. **`/healthz`が401 Unauthorizedを返している**
   - Basic認証が有効になっているため、UptimeRobotがアクセスできない

2. **標準スケジューラー（未来の兆し生成）が起動している**
   - ログに「🚀 スケジューラー起動を開始...」と「🚀 初回実行を開始...」が表示されている
   - これは無効化すべき（RSS機能のみに絞ったため）

3. **WIRED Botスケジューラーが起動していない**
   - ログに「⏳ WIRED Botスケジューラーを起動します...」が表示されていない

---

## ✅ 修正内容

### 1. `/healthz`を認証不要にする

**ファイル**: `backend/auth.py`

```python
# 修正前
if request.url.path == "/" or request.url.path == "/docs" or request.url.path == "/openapi.json":

# 修正後
if request.url.path in ["/", "/docs", "/openapi.json", "/healthz", "/health"]:
```

**効果**: UptimeRobotが`/healthz`にアクセスできるようになります

---

### 2. 標準スケジューラーの完全無効化

**確認**: `backend/main.py`では既に標準スケジューラーは無効化されています

```python
# 標準スケジューラーは無効化
scheduler = None
```

**問題**: デプロイされたコードが古い可能性があります

**解決策**: 最新のコードを再デプロイしてください

---

### 3. WIRED Botスケジューラーの起動確認

**確認**: `backend/main.py`ではWIRED Botスケジューラーは起動するようになっています

```python
if disable_wired_scheduler:
    logger.info("📝 WIRED Botスケジューラーは無効化されています（DISABLE_WIRED_SCHEDULER=true）")
else:
    # WIRED Botスケジューラーをバックグラウンドで起動
    logger.info("⏳ WIRED Botスケジューラーを起動します...")
    threading.Thread(target=_start_wired_scheduler_delayed, daemon=True, name="WiredSchedulerStarter").start()
```

**問題**: ログに「⏳ WIRED Botスケジューラーを起動します...」が表示されていない

**解決策**: 最新のコードを再デプロイしてください

---

## 🚀 再デプロイ手順

### 1. 変更をコミット

```bash
git add backend/auth.py
git commit -m "Fix: /healthzを認証不要にする"
git push origin main
```

### 2. Renderで再デプロイ

- Render ダッシュボードで自動的に再デプロイが開始されます
- または、手動で「Manual Deploy」をクリック

### 3. ログで確認

再デプロイ後、以下のログが表示されることを確認：

```
✅ データベース初期化完了
✅ GeminiAnalyzer初期化成功
✅ SocialPoster初期化成功
⏳ WIRED Botスケジューラーを起動します...
✅ アプリケーション初期化完了
🚀 WIRED Botスケジューラー起動を開始...
✅ WIRED Botスケジューラー起動完了（毎朝8:00、改良版）
✅ WIRED Botスケジューラースレッド起動完了
```

**注意**: 標準スケジューラーのログ（「🚀 スケジューラー起動を開始...」など）は表示されないはずです

---

## ✅ 確認項目

### デプロイ後の確認

1. **`/healthz`が200 OKを返す**
   ```bash
   curl https://kizashi-backend.onrender.com/healthz
   ```

2. **ログにWIRED Botスケジューラーの起動メッセージが表示される**
   - 「⏳ WIRED Botスケジューラーを起動します...」
   - 「✅ WIRED Botスケジューラー起動完了」

3. **標準スケジューラーのログが表示されない**
   - 「🚀 スケジューラー起動を開始...」は表示されないはず

---

## 📝 環境変数の確認

### 必須環境変数

```bash
GEMINI_API_KEY=AIzaSyC...
BLUESKY_HANDLE=your_handle.bsky.social
BLUESKY_PASSWORD=xxxx-xxxx-xxxx-xxxx
POST_MODE=bluesky
```

### WIRED Botスケジューラー

```bash
# デフォルトで有効（設定不要）
DISABLE_WIRED_SCHEDULER=false  # または未設定

# 無効化する場合
DISABLE_WIRED_SCHEDULER=true
```

---

**作成日**: 2025年11月16日

