# 🔄 UptimeRobot セットアップガイド

## ✅ UptimeRobotは使えます！

UptimeRobotを設定すると、Renderの無料プランで**15分間リクエストがないとスリープしてしまう問題**を解決できます。

---

## 🎯 UptimeRobotの役割

### 問題
- Renderの無料プランは、15分間リクエストがないと自動的にスリープします
- スリープ中は、APIリクエストやスケジューラーが動作しません

### 解決策
- UptimeRobotが**定期的にヘルスチェックエンドポイントにリクエストを送信**
- これにより、Renderのサービスがスリープしなくなります
- **5分間隔**でリクエストを送信するのが推奨です

---

## 📋 セットアップ手順

### プロジェクト構成

このプロジェクトは**2つのWeb Service**で構成されています：

1. **バックエンド（FastAPI）** - `kizashi-backend`
   - URL例: `https://kizashi-backend.onrender.com`
   - **重要**: WIRED Botスケジューラーが動作しているため、**必ず監視が必要**

2. **フロントエンド（Next.js）** - `kizashi-frontend`
   - URL例: `https://kizashi-frontend.onrender.com`
   - **オプション**: UIなので、スリープしても問題ないが、監視するのが安全

---

### 1. UptimeRobotにログイン

https://uptimerobot.com/ にアクセスしてログイン

### 2. バックエンドのモニターを作成（必須）

1. **「+ Add New Monitor」** をクリック

2. **Monitor Type** を選択
   - **HTTP(s)** を選択

3. **設定を入力**

   ```
   Friendly Name: WIRED Bot Backend
   
   URL (or IP): https://kizashi-backend.onrender.com/healthz
   
   Monitoring Interval: 5 minutes
   
   Alert Contacts: （通知先を選択、オプション）
   ```

4. **「Create Monitor」** をクリック

### 3. フロントエンドのモニターを作成（オプション）

1. **「+ Add New Monitor」** をクリック

2. **Monitor Type** を選択
   - **HTTP(s)** を選択

3. **設定を入力**

   ```
   Friendly Name: WIRED Bot Frontend
   
   URL (or IP): https://kizashi-frontend.onrender.com
   
   Monitoring Interval: 5 minutes
   
   Alert Contacts: （通知先を選択、オプション）
   ```

4. **「Create Monitor」** をクリック

**注意**: フロントエンドには `/healthz` エンドポイントがないため、ルートURL（`/`）を監視します。

---

## ⚙️ 設定の詳細

### バックエンドのURL（重要）

**推奨**: `/healthz` エンドポイントを使用

```
https://kizashi-backend.onrender.com/healthz
```

**理由**:
- 軽量で高速（データベース接続テストなし）
- アプリの起動状態を確認するのに最適
- RenderのHealth Check Pathにも使用可能
- **WIRED Botスケジューラーが動作しているか確認可能**

### フロントエンドのURL

フロントエンドには `/healthz` エンドポイントがないため、ルートURLを使用：

```
https://kizashi-frontend.onrender.com
```

**注意**: フロントエンドはNext.jsなので、ルートURL（`/`）にアクセスして200 OKが返れば正常です。

### 代替エンドポイント（バックエンド）

詳細な情報が必要な場合は `/health` も使用可能：

```
https://kizashi-backend.onrender.com/health
```

**注意**: `/health` はデータベース接続テストも行うため、少し重いです。

---

## 🔍 ヘルスチェックエンドポイントの仕様

### `/healthz` エンドポイント

**用途**: 軽量なヘルスチェック（UptimeRobot推奨）

**レスポンス例**:
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

**特徴**:
- ✅ 高速（データベース接続テストなし）
- ✅ 常に200 OKを返す（アプリが起動していれば）
- ✅ コンポーネントの状態も確認可能

### `/health` エンドポイント

**用途**: 詳細なヘルスチェック（監視用）

**レスポンス例**:
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

**特徴**:
- ✅ データベース接続状態も確認
- ✅ 環境変数の設定状態も確認
- ⚠️ 少し重い（データベース接続テストあり）

---

## ⏰ モニタリング間隔の推奨設定

### 推奨: 5分間隔

- **理由**: Renderの無料プランは15分でスリープするため、5分間隔なら確実にスリープを防げます
- **無料プラン**: 50モニターまで無料、5分間隔まで可能

### その他の間隔

- **1分間隔**: より確実だが、無料プランでは制限がある可能性
- **10分間隔**: ギリギリ（15分でスリープするため、リスクあり）

---

## ✅ 動作確認

### 1. UptimeRobotで確認

1. UptimeRobotダッシュボードにアクセス
2. 作成したモニターのステータスを確認
3. **「UP」** と表示されていれば成功

### 2. ログで確認

Render ダッシュボード → Logs で以下を確認：

```
INFO:     127.0.0.1:xxxxx - "GET /healthz HTTP/1.1" 200 OK
```

定期的に（5分間隔で）リクエストが来ていれば成功です。

### 3. 手動テスト

#### バックエンド

ブラウザで以下にアクセス：

```
https://kizashi-backend.onrender.com/healthz
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

#### フロントエンド

ブラウザで以下にアクセス：

```
https://kizashi-frontend.onrender.com
```

**期待される動作**: ページが正常に表示されればOK（200 OK）

---

## 🎯 まとめ

### ✅ 設定完了後の動作

1. **UptimeRobotが5分間隔でバックエンドの `/healthz` にリクエスト**
2. **Renderのバックエンドサービスがスリープしない**
3. **WIRED Botスケジューラーが正常に動作**
4. **毎朝8時に自動投稿が実行される**

### 📊 監視の優先順位

1. **バックエンド（必須）** ⭐⭐⭐
   - WIRED Botスケジューラーが動作しているため、**必ず監視が必要**
   - URL: `https://kizashi-backend.onrender.com/healthz`

2. **フロントエンド（オプション）** ⭐
   - UIなので、スリープしても問題ないが、監視するのが安全
   - URL: `https://kizashi-frontend.onrender.com`

### 📝 チェックリスト

#### バックエンド（必須）
- [ ] UptimeRobotにログイン
- [ ] バックエンドのモニターを作成
- [ ] URL: `https://kizashi-backend.onrender.com/healthz`
- [ ] モニタリング間隔: 5分
- [ ] モニターのステータスが「UP」になっている
- [ ] Renderのログで定期的なリクエストを確認

#### フロントエンド（オプション）
- [ ] フロントエンドのモニターを作成
- [ ] URL: `https://kizashi-frontend.onrender.com`
- [ ] モニタリング間隔: 5分
- [ ] モニターのステータスが「UP」になっている

---

## 🔧 トラブルシューティング

### モニターが「DOWN」と表示される

**原因**:
- Renderのサービスがスリープしている
- URLが間違っている
- アプリが起動していない

**解決策**:
1. Renderダッシュボードでサービスを確認
2. URLが正しいか確認（`/healthz` が正しい）
3. 手動で `/healthz` にアクセスして確認

### リクエストが来ない

**原因**:
- UptimeRobotの設定が間違っている
- モニターが無効になっている

**解決策**:
1. UptimeRobotのモニター設定を確認
2. モニターが「Active」になっているか確認

---

**作成日**: 2025年11月09日

