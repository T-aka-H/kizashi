# Renderサービス名の命名規則

## サービス名について

Renderのサービス名は自由に設定できますが、以下の点に注意してください。

## 名前の影響

### 1. URLに影響する

サービス名がそのままURLになります：

- `kizashi-backend` → `https://kizashi-backend.onrender.com`
- `kizashi-frontend` → `https://kizashi-frontend.onrender.com`

### 2. 環境変数の設定に影響する

フロントエンドの`NEXT_PUBLIC_API_URL`は、バックエンドのURLを指定する必要があります：

```
NEXT_PUBLIC_API_URL=https://kizashi-backend.onrender.com
```

## 推奨される命名規則

### ✅ 良い例

- `kizashi-backend` / `kizashi-frontend`
- `myapp-api` / `myapp-web`
- `project-backend` / `project-frontend`

**特徴:**
- 小文字とハイフンのみ
- 意味が明確
- 一貫性がある

### ❌ 避けるべき例

- `Kizashi-Backend`（大文字は使えない）
- `kizashi_backend`（アンダースコアは使えるが、ハイフンの方が一般的）
- `kizashi-backend-123`（数字は使えるが、意味がない）

## 現在の設定

`render.yaml`では以下のように設定されています：

- **バックエンド**: `kizashi-backend`
- **フロントエンド**: `kizashi-frontend`
- **データベース**: `kizashi-db`

## デプロイ後のURL

- バックエンド: `https://kizashi-backend.onrender.com`
- フロントエンド: `https://kizashi-frontend.onrender.com`
- APIドキュメント: `https://kizashi-backend.onrender.com/docs`

## 環境変数の設定

フロントエンドサービスで以下を設定：

```
NEXT_PUBLIC_API_URL=https://kizashi-backend.onrender.com
```

## 注意事項

1. **名前の変更**: デプロイ後に名前を変更すると、URLも変わります
2. **一意性**: Renderアカウント内で一意である必要があります
3. **長さ**: 長すぎるとURLが長くなります（推奨: 20文字以内）

## 結論

`kizashi-frontend`と`kizashi-backend`は**問題ありません**。むしろ良い命名です！

- ✅ 短くて覚えやすい
- ✅ 一貫性がある
- ✅ 意味が明確
- ✅ URLも分かりやすい

