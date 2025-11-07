# セキュリティ設定ガイド

## 🔐 認証機能の実装

### 実装した機能

1. **Basic認証**: 全てのAPI操作に認証が必要
2. **投稿確認パスワード**: 投稿時に追加のパスワード確認
3. **環境変数による管理**: パスワードを安全に保管
4. **スケジューラー無効化**: 自動投稿を停止可能

---

## 🚀 設定方法

### ステップ1: Render環境変数を設定

Render Dashboard → kizashi-backend → Environment

以下の環境変数を追加:

```
# Basic認証（サイト全体のアクセス制限）
AUTH_USERNAME=your_username
AUTH_PASSWORD=your_strong_password_123

# 投稿確認パスワード（投稿時の追加確認）
POST_PASSWORD=post_confirm_456

# スケジューラー無効化（自動投稿を停止）
DISABLE_SCHEDULER=true
```

**推奨パスワード強度**:
- 12文字以上
- 大文字・小文字・数字・記号を含む
- 例: `MyStr0ng!Pass2024`

---

## 🔑 パスワードの使い分け

### AUTH_USERNAME / AUTH_PASSWORD

```
用途: サイト全体へのアクセス制限
誰が使う: あなた（管理者）のみ
いつ使う: 最初にサイトにアクセスする時
```

### POST_PASSWORD

```
用途: 投稿実行時の追加確認
誰が使う: あなた（管理者）のみ
いつ使う: Blueskyに投稿する直前
```

---

## 📱 実際の使い方

### 1. サイトにアクセス

```
https://your-frontend.onrender.com にアクセス
↓
認証が必要な場合、ブラウザに認証ダイアログが表示される
または、ログインページにリダイレクトされる
↓
Username: your_username
Password: your_strong_password_123
↓
ログイン成功 → ダッシュボード表示
```

### 2. 記事を分析

```
テーマ分析 → テーマ選択 → 分析開始
↓
（自動的に認証済みセッションを使用）
```

### 3. 投稿実行

```
投稿キュー → 記事を選択 → [投稿]ボタン
↓
投稿確認パスワード入力画面が表示
↓
パスワード: post_confirm_456
↓
投稿実行 → Blueskyに投稿
```

---

## 🛡️ セキュリティレベル

### レベル1: Basic認証のみ（現在の実装）

```
✅ サイトへのアクセス制限
✅ API操作の認証
✅ 投稿時の追加確認
⚠️ パスワードは暗号化されずに送信（HTTPSで保護）
```

**適している用途**:
- 個人利用
- 小規模チーム（3人以下）
- プライベートプロジェクト

### レベル2: JWT認証（将来実装）

```
✅ トークンベース認証
✅ セッション管理
✅ ユーザーごとの権限管理
✅ より高度なセキュリティ
```

**適している用途**:
- チーム利用（4人以上）
- 複数ユーザー管理が必要
- 監査ログが必要

---

## 🚨 緊急：自動投稿を停止

### スケジューラーを無効化

Renderで環境変数を追加:

```
DISABLE_SCHEDULER=true
```

これで自動投稿が停止されます。

---

## 📋 セキュリティチェックリスト

### 設定確認

- [ ] `AUTH_USERNAME` を設定
- [ ] `AUTH_PASSWORD` を強力なパスワードに設定
- [ ] `POST_PASSWORD` を設定
- [ ] `DISABLE_SCHEDULER=true` を設定（自動投稿停止）
- [ ] GitHubに`.env`をプッシュしていないか確認

### アクセステスト

- [ ] サイトにアクセス → 認証ダイアログが表示
- [ ] 間違ったパスワード → アクセス拒否
- [ ] 正しいパスワード → アクセス成功
- [ ] 投稿時 → 投稿パスワード要求

---

## 💡 追加のセキュリティ対策（オプション）

### IP制限

特定のIPアドレスからのみアクセス許可:

```python
# main.py

ALLOWED_IPS = os.getenv("ALLOWED_IPS", "").split(",")

@app.middleware("http")
async def check_ip(request: Request, call_next):
    client_ip = request.client.host
    if ALLOWED_IPS and client_ip not in ALLOWED_IPS:
        raise HTTPException(status_code=403, detail="IP not allowed")
    return await call_next(request)
```

### レート制限

API呼び出しの頻度制限:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/post")
@limiter.limit("5/hour")  # 1時間に5回まで
async def post_to_social(...):
    ...
```

---

## 🎉 完了

この設定で:

- ✅ サイトへのアクセスが制限される
- ✅ 投稿時に追加確認が入る
- ✅ 勝手に投稿されることがなくなる

**パスワードは絶対に誰にも教えないでください！**

