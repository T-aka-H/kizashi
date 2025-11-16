# 🚀 Renderデプロイ - 最終版（Render前提）

## ✅ Render前提の実装

このアプリケーションは**Render前提**で実装されています。

**PCを起動していないときでも投稿できます！**

---

## 🎯 実装されている機能

### 1. WIRED RSSからの記事取得
- **エンドポイント**: `POST /fetch/wired-rss`
- WIREDのRSSフィードから記事を取得

### 2. 未来の兆し生成 + Bluesky自動投稿
- **エンドポイント**: `POST /fetch/research`
- テーマに基づいて「未来の兆し」を生成
- **生成された未来の兆しをBlueskyに自動投稿**

### 3. WIRED Bot自動投稿（Render内で実行）
- **毎朝8時に自動実行**（RenderのWeb Service内でバックグラウンド実行）
- WIRED記事TOP5を選定してBlueskyに投稿
- PCを起動していなくても動作

---

## 🔄 Renderでの動作

### 起動時の動作

1. **RenderがWeb Serviceを起動**
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

2. **FastAPIアプリが起動**
   - `@app.on_event("startup")`で初期化

3. **WIRED Botスケジューラーが自動起動**
   - 30秒後にバックグラウンドスレッドで起動
   - 毎朝8時にWIRED記事TOP5を自動投稿

4. **常時起動**
   - RenderのWeb Serviceが起動している限り、スケジューラーも動作
   - PCを起動していなくても投稿可能

---

## ⚙️ 環境変数設定（Render）

### 必須環境変数

```bash
# データベース（PostgreSQLから自動設定）
DATABASE_URL=<Renderが自動設定>

# Gemini API
GEMINI_API_KEY=AIzaSyC...

# Bluesky認証
BLUESKY_HANDLE=your_handle.bsky.social
BLUESKY_PASSWORD=xxxx-xxxx-xxxx-xxxx
POST_MODE=bluesky
```

### オプション環境変数

```bash
# WIRED Botスケジューラー
DISABLE_WIRED_SCHEDULER=false  # true: 無効化
USE_ADVANCED_BOT=true          # true: 改良版、false: 基本版
TEST_MODE=false                # true: 起動時に1回実行

# その他
AUTH_USERNAME=admin            # Basic認証（オプション）
AUTH_PASSWORD=your_password    # Basic認証（オプション）
```

---

## 📋 スケジューラーの動作

### WIRED Botスケジューラー

- **実行時刻**: 毎朝8:00（UTC）
- **実行内容**: WIRED記事TOP5を選定してBlueskyに投稿
- **実行場所**: RenderのWeb Service内（バックグラウンドスレッド）
- **PC不要**: Renderが起動していれば動作

### 無効化する場合

```bash
DISABLE_WIRED_SCHEDULER=true
```

---

## 🔍 動作確認

### 1. ログで確認

Render ダッシュボード → Web Service → 「Logs」タブで以下を確認：

```
✅ データベース初期化完了
✅ GeminiAnalyzer初期化成功
✅ SocialPoster初期化成功
⏳ WIRED Botスケジューラーを起動します...
🚀 WIRED Botスケジューラー起動を開始...
✅ WIRED Botスケジューラー起動完了（毎朝8:00、改良版）
✅ WIRED Botスケジューラースレッド起動完了
```

### 2. ヘルスチェック

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
    "scheduler": "stopped"  // 標準スケジューラーは無効
  }
}
```

### 3. 動作確認: テストエンドポイントにアクセス（推奨）

**ブラウザから簡単にアクセス**:

```
https://kizashi-backend.onrender.com/test/wired-bot
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

**注意**: 実際にBlueskyに投稿されます（`POST_MODE=bluesky`の場合）

### 4. 毎朝8時の投稿確認

毎朝8時（UTC）に自動的にWIRED記事TOP5がBlueskyに投稿されます。

**注意**: RenderのタイムゾーンはUTCです。日本時間の8時はUTCの23時（前日）です。

---

## 🕐 タイムゾーンの設定

### 日本時間で8時に投稿したい場合

RenderのタイムゾーンはUTCなので、日本時間の8時はUTCの23時（前日）です。

**環境変数で調整**:

```bash
# 日本時間8:00 = UTC 23:00（前日）
# schedule.every().day.at("23:00") に変更する必要がある
```

または、コードを修正：

```python
# 日本時間8:00に実行（UTC 23:00）
schedule.every().day.at("23:00").do(wired_job)
```

---

## ✅ Render前提の確認

### 実装済み

- ✅ 環境変数から設定を取得（.envファイル不要）
- ✅ PostgreSQL対応（DATABASE_URL自動設定）
- ✅ ヘルスチェックエンドポイント（/healthz）
- ✅ エラーハンドリング（一部失敗してもアプリは起動）
- ✅ WIRED Botスケジューラーが自動起動
- ✅ バックグラウンドスレッドで実行

### PC不要

- ✅ RenderのWeb Serviceが起動していれば動作
- ✅ PCを起動していなくても投稿可能
- ✅ 24時間365日動作可能（無料プランは15分でスリープするが、UptimeRobotで対策済み）

---

## 🔄 UptimeRobot設定（スリープ防止）

### 問題
Renderの無料プランは、**15分間リクエストがないと自動的にスリープ**します。

### 解決策
**UptimeRobot**を設定して、定期的にヘルスチェックエンドポイントにリクエストを送信します。

### 設定手順

1. **UptimeRobotにログイン**
   - https://uptimerobot.com/

2. **新しいモニターを作成**
   - Monitor Type: **HTTP(s)**
   - URL: `https://your-app-name.onrender.com/healthz`
   - Monitoring Interval: **5 minutes**
   - Friendly Name: `WIRED Bot API`

3. **完了**
   - これで、5分間隔で `/healthz` にリクエストが送信され、スリープを防げます

### 詳細
詳細な設定方法は **`UPTIMEROBOT_SETUP.md`** を参照してください。

---

## 🎯 まとめ

**✅ Render前提で実装されています！**

- PCを起動していないときでも投稿できます
- RenderのWeb Serviceが起動していれば、毎朝8時に自動投稿
- WIRED Botスケジューラーは自動的に起動

**設定**: 環境変数 `DISABLE_WIRED_SCHEDULER=false` で有効化（デフォルト）

---

**作成日**: 2025年11月09日

