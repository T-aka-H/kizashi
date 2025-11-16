# 🔐 環境変数リファレンス

このファイルでは、アプリケーションで使用するすべての環境変数を説明します。

---

## 📋 環境変数一覧

### データベース

| 変数名 | 必須 | デフォルト | 説明 |
|--------|------|-----------|------|
| `DATABASE_URL` | ローカル:No<br>Render:Yes | `sqlite:///./weak_signals.db` | データベース接続URL<br>- ローカル: SQLite<br>- Render: PostgreSQL（自動設定） |

**例**:
```bash
# ローカル開発（デフォルト）
DATABASE_URL=sqlite:///./weak_signals.db

# Render（PostgreSQL、自動設定される）
DATABASE_URL=postgres://user:password@host:5432/database
# または
DATABASE_URL=postgresql://user:password@host:5432/database
```

---

### Gemini API

| 変数名 | 必須 | デフォルト | 説明 |
|--------|------|-----------|------|
| `GEMINI_API_KEY` | Yes | - | Google Gemini APIキー<br>取得先: https://makersuite.google.com/app/apikey |

**例**:
```bash
GEMINI_API_KEY=AIzaSyC...
```

---

### Bluesky認証

| 変数名 | 必須 | デフォルト | 説明 |
|--------|------|-----------|------|
| `BLUESKY_HANDLE` | POST_MODE=bluesky時 | - | Blueskyハンドル |
| `BLUESKY_PASSWORD` | POST_MODE=bluesky時 | - | Blueskyアプリパスワード<br>（通常のパスワードではない）|
| `POST_MODE` | No | `demo` | 投稿モード<br>- `demo`: テスト（投稿しない）<br>- `bluesky`: 実際に投稿 |

**例**:
```bash
BLUESKY_HANDLE=username.bsky.social
BLUESKY_PASSWORD=xxxx-xxxx-xxxx-xxxx
POST_MODE=bluesky
```

**アプリパスワードの取得方法**:
1. Blueskyアプリにログイン
2. 設定 → アプリパスワード
3. 「新しいアプリパスワードを作成」
4. 生成されたパスワードをコピー

---

### スケジューラー

| 変数名 | 必須 | デフォルト | 説明 |
|--------|------|-----------|------|
| `DISABLE_SCHEDULER` | No | `false` | スケジューラーを無効化<br>- `false`: 有効（自動実行）<br>- `true`: 無効 |
| `SCHEDULER_INTERVAL_MINUTES` | No | `15` | スケジューラー実行間隔（分） |

**例**:
```bash
# スケジューラーを有効化（15分間隔）
DISABLE_SCHEDULER=false
SCHEDULER_INTERVAL_MINUTES=15

# スケジューラーを無効化
DISABLE_SCHEDULER=true

# スケジューラーを30分間隔に変更
SCHEDULER_INTERVAL_MINUTES=30
```

---

### Basic認証（フロントエンド用）

| 変数名 | 必須 | デフォルト | 説明 |
|--------|------|-----------|------|
| `AUTH_USERNAME` | No | - | Basic認証ユーザー名<br>設定しない場合は認証無効 |
| `AUTH_PASSWORD` | No | - | Basic認証パスワード<br>設定しない場合は認証無効 |
| `POST_PASSWORD` | No | - | 投稿確認パスワード<br>設定しない場合は確認なし |

**例**:
```bash
AUTH_USERNAME=admin
AUTH_PASSWORD=your_secure_password
POST_PASSWORD=your_post_password
```

---

### WIRED Bot（追加機能）

| 変数名 | 必須 | デフォルト | 説明 |
|--------|------|-----------|------|
| `DISABLE_WIRED_SCHEDULER` | No | `false` | WIRED Botスケジューラーを無効化<br>- `false`: 有効（毎朝8:00に自動投稿）<br>- `true`: 無効 |
| `USE_ADVANCED_BOT` | No | `true` | WIRED Botで改良版を使用<br>- `true`: 改良版（記事本文取得）<br>- `false`: 基本版 |
| `TEST_MODE` | No | `false` | WIRED Botのテストモード<br>- `true`: デプロイ後30秒後に1回だけ実行<br>- `false`: スケジュール実行（毎朝8:00） |

**例**:
```bash
USE_ADVANCED_BOT=true
TEST_MODE=false
```

---

## 📝 環境別設定例

### ローカル開発（.env）

```bash
# データベース（SQLite）
DATABASE_URL=sqlite:///./weak_signals.db

# Gemini API
GEMINI_API_KEY=AIzaSyC...

# Bluesky（デモモード）
BLUESKY_HANDLE=your_handle.bsky.social
BLUESKY_PASSWORD=xxxx-xxxx-xxxx-xxxx
POST_MODE=demo

# スケジューラー
DISABLE_SCHEDULER=false
SCHEDULER_INTERVAL_MINUTES=15

# Basic認証（開発環境では無効化）
# AUTH_USERNAME=
# AUTH_PASSWORD=

# 投稿確認パスワード（開発環境では無効化）
# POST_PASSWORD=

# WIRED Bot
DISABLE_WIRED_SCHEDULER=false  # デフォルト（有効）
USE_ADVANCED_BOT=true
TEST_MODE=false
```

### Render本番環境

```bash
# データベース（Renderが自動設定）
DATABASE_URL=postgres://user:pass@host/db

# Gemini API
GEMINI_API_KEY=AIzaSyC...

# Bluesky（本番モード）
BLUESKY_HANDLE=your_handle.bsky.social
BLUESKY_PASSWORD=xxxx-xxxx-xxxx-xxxx
POST_MODE=bluesky

# スケジューラー
DISABLE_SCHEDULER=false
SCHEDULER_INTERVAL_MINUTES=15

# Basic認証（本番環境では有効化推奨）
AUTH_USERNAME=admin
AUTH_PASSWORD=strong_password_here

# 投稿確認パスワード（本番環境では有効化推奨）
POST_PASSWORD=secure_post_password

# WIRED Bot
DISABLE_WIRED_SCHEDULER=false  # デフォルト（有効）
USE_ADVANCED_BOT=true
TEST_MODE=false
```

### テスト環境

```bash
# データベース（SQLite）
DATABASE_URL=sqlite:///./test.db

# Gemini API
GEMINI_API_KEY=AIzaSyC...

# Bluesky（デモモード）
BLUESKY_HANDLE=test_handle.bsky.social
BLUESKY_PASSWORD=test-password
POST_MODE=demo

# スケジューラー（無効化）
DISABLE_SCHEDULER=true

# Basic認証（無効化）
# AUTH_USERNAME=
# AUTH_PASSWORD=

# WIRED Bot（テストモード）
USE_ADVANCED_BOT=false
TEST_MODE=true
```

---

## 🔒 セキュリティのベストプラクティス

### ✅ DO
- 本番環境では必ずBasic認証を有効化
- パスワードは強力なものを使用（20文字以上推奨）
- Blueskyアプリパスワードを使用（通常のパスワードは使わない）
- `.env`ファイルをGitにコミットしない（`.gitignore`に追加）
- Renderの環境変数機能を使用（コードに埋め込まない）

### ❌ DON'T
- パスワードをコードに直接書かない
- `.env`ファイルを公開リポジトリにプッシュしない
- 開発環境と本番環境で同じパスワードを使わない
- APIキーを共有しない

---

## 🛠️ 環境変数の設定方法

### ローカル開発

`.env`ファイルを作成：

```bash
# .envファイルを作成
cp WIRED_BOT_ENV_EXAMPLE.txt .env

# .envファイルを編集
notepad .env
```

### Render

1. Render ダッシュボード → Web Service を選択
2. 「Environment」タブをクリック
3. 「Add Environment Variable」で追加
4. 「Save Changes」でデプロイ

---

## 📊 環境変数の確認

### アプリケーションログ

アプリ起動時にログで確認：

```
✅ .envファイルを読み込みました: /path/to/.env
🚀 アプリケーション初期化を開始...
✅ GeminiAnalyzer初期化成功
✅ SocialPoster初期化成功
✅ スケジューラーをバックグラウンドで起動（15分間隔）
```

### ヘルスチェックAPI

```bash
curl https://your-app.onrender.com/health
```

**レスポンス**:
```json
{
  "environment": {
    "gemini_api_key_set": true,
    "bluesky_handle_set": true,
    "post_mode": "bluesky",
    "scheduler_enabled": true
  }
}
```

---

## 🐛 トラブルシューティング

### 「GEMINI_API_KEY環境変数が設定されていません」

**原因**: `GEMINI_API_KEY`が設定されていない

**解決**:
- ローカル: `.env`ファイルに追加
- Render: Environment Variables に追加

### 「Bluesky接続失敗」

**原因**: Bluesky認証情報が間違っている

**チェック**:
- [ ] `BLUESKY_HANDLE`が正しいか（`username.bsky.social`形式）
- [ ] `BLUESKY_PASSWORD`がアプリパスワードか（通常のパスワードではない）
- [ ] `POST_MODE=bluesky`が設定されているか

### 「データベース接続エラー」

**原因**: `DATABASE_URL`が間違っている

**チェック**:
- [ ] ローカル: SQLiteファイルへのパスが正しいか
- [ ] Render: PostgreSQL URLが正しく設定されているか
- [ ] `postgres://`または`postgresql://`形式か

---

**作成日**: 2025年11月09日  
**最終更新**: 2025年11月09日

