# 🚀 WIRED記事TOP5投稿Bot - クイックスタート

## 最速セットアップ（5分）

### 1. 環境変数を設定

```bash
# .envファイルを編集
notepad C:\dev\wired\.env
```

以下を追加（`WIRED_BOT_ENV_EXAMPLE.txt`の内容を参考に）：

```env
GEMINI_API_KEY=あなたのAPIキー
BLUESKY_HANDLE=あなたのハンドル.bsky.social
BLUESKY_PASSWORD=アプリパスワード
POST_MODE=demo
USE_ADVANCED_BOT=true
TEST_MODE=false
```

### 2. テスト実行（デモモード）

```bash
cd C:\dev\wired\backend
python wired_bluesky_bot_advanced.py
```

コンソールに投稿プレビューが表示されます。

### 3. 本番投稿

`.env`を編集して `POST_MODE=bluesky` に変更：

```bash
python wired_bluesky_bot_advanced.py
```

実際にBlueskyに投稿されます！

### 4. 毎朝8時に自動実行

```bash
python wired_scheduler.py
```

Ctrl+Cで停止するまで、毎朝8時に自動実行されます。

---

## 詳細は README_WIRED_BOT.md をご覧ください

