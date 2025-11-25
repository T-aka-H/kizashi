# 🏗️ Renderデプロイ構成

## ✅ デプロイ構成

**2つのWeb Service + 1つのPostgreSQL**で構成します：

1. **Backend (FastAPI)** - `kizashi-backend`
2. **Frontend (Next.js)** - `kizashi-frontend`
3. **PostgreSQL Database** - `kizashi-db`

---

## 📋 各サービスの設定

### 1. Backend (FastAPI)

**サービス名**: `kizashi-backend`

**設定**:
- **Type**: Web Service
- **Runtime**: Python 3
- **Root Directory**: `backend`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path**: `/healthz`
- **Health Check Grace Period**: `180`

**環境変数**:
```bash
DATABASE_URL=<PostgreSQL接続URL>
GEMINI_API_KEY=AIzaSyC...
BLUESKY_HANDLE=your_handle.bsky.social
BLUESKY_PASSWORD=xxxx-xxxx-xxxx-xxxx
POST_MODE=bluesky
DISABLE_SCHEDULER=false
SCHEDULER_INTERVAL_MINUTES=15
```

**URL例**: `https://kizashi-backend.onrender.com`

---

### 2. Frontend (Next.js)

**サービス名**: `kizashi-frontend`

**設定**:
- **Type**: Web Service
- **Runtime**: Node.js
- **Root Directory**: `frontend`
- **Build Command**: `npm install && npm run build`
- **Start Command**: `npm start`
- **Node Version**: `20.x`

**環境変数**:
```bash
NEXT_PUBLIC_API_URL=https://kizashi-backend.onrender.com
NEXT_PUBLIC_API_BASE_URL=https://kizashi-backend.onrender.com
```

**重要**: `NEXT_PUBLIC_API_URL`は**BackendのURL**を設定してください。

**URL例**: `https://kizashi-frontend.onrender.com`

---

### 3. PostgreSQL Database

**データベース名**: `kizashi-db`

**設定**:
- **Type**: PostgreSQL
- **Plan**: Free (0.1GB)
- **Region**: Singapore（またはOregon）

**自動設定**:
- `DATABASE_URL`がBackendに自動的に設定される

---

## 🚀 デプロイ方法

### 方法1: render.yamlを使用（推奨）

`render.yaml`が既に設定されているので、Render Dashboardで：

1. 「**New +**」→「**Blueprint**」をクリック
2. GitHubリポジトリ `T-aka-H/kizashi` を選択
3. 「**Apply**」をクリック

**自動的に以下が作成されます**:
- ✅ Backend Web Service
- ✅ Frontend Web Service
- ✅ PostgreSQL Database

### 方法2: 手動で作成

#### Step 1: PostgreSQLを作成
1. 「New +」→「PostgreSQL」
2. Name: `kizashi-db`
3. 「Create Database」

#### Step 2: Backendを作成
1. 「New +」→「Web Service」
2. GitHubリポジトリを接続
3. 設定:
   - Name: `kizashi-backend`
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Health Check Path: `/healthz`
4. 環境変数を設定
5. 「Create Web Service」

#### Step 3: Frontendを作成
1. 「New +」→「Web Service」
2. 同じGitHubリポジトリを選択
3. 設定:
   - Name: `kizashi-frontend`
   - Root Directory: `frontend`
   - Build Command: `npm install && npm run build`
   - Start Command: `npm start`
   - Node Version: `20.x`
4. 環境変数を設定:
   - `NEXT_PUBLIC_API_URL=https://kizashi-backend.onrender.com`
5. 「Create Web Service」

---

## 🔗 サービス間の接続

### Frontend → Backend

Frontendの環境変数でBackendのURLを設定：

```bash
NEXT_PUBLIC_API_URL=https://kizashi-backend.onrender.com
```

**重要**: BackendのURLは**デプロイ後に確定**するので、デプロイ後に環境変数を更新してください。

---

## 💰 コスト（無料プラン）

### 制限
- **Web Service**: 750時間/月（**2つのサービスで共有**）
- **PostgreSQL**: 0.1GB（無料）

### 注意
2つのWeb Serviceを作成すると、**1つのサービスあたり約375時間/月**になります。

**対策**:
- FrontendをVercelやNetlifyにデプロイ（無料、制限なし）
- または、BackendのみをRenderにデプロイ

---

## 🎯 推奨構成

### オプション1: Renderに2つ（現在の構成）

**メリット**:
- ✅ すべてがRenderで管理される
- ✅ 簡単にデプロイできる

**デメリット**:
- ⚠️ 無料プランの時間制限（750時間/月を2つで共有）

### オプション2: BackendのみRender、FrontendはVercel

**メリット**:
- ✅ Frontendは無制限（Vercel無料プラン）
- ✅ BackendはRenderで十分な時間が使える

**デメリット**:
- ⚠️ 2つのプラットフォームで管理が必要

---

## 📝 デプロイ後の確認

### Backend
```bash
curl https://kizashi-backend.onrender.com/healthz
curl https://kizashi-backend.onrender.com/health
```

### Frontend
```bash
# ブラウザで開く
https://kizashi-frontend.onrender.com
```

### 接続確認
1. Frontendにアクセス
2. ブラウザの開発者ツール（F12）→ Networkタブ
3. APIリクエストがBackendに送信されているか確認

---

## 🔄 自動デプロイ

`main`ブランチにプッシュすると、**両方のサービスが自動的にデプロイ**されます：

```bash
git push origin main
```

---

## ✅ まとめ

**質問**: Renderにはbackendとfrontendの2つでいいですか？

**回答**: **はい、2つのWeb Serviceで正しいです！**

- ✅ Backend: FastAPI（`backend/`）
- ✅ Frontend: Next.js（`frontend/`）
- ✅ Database: PostgreSQL（1つ）

`render.yaml`も既にこの構成になっているので、Blueprintで一括デプロイできます。

---

**作成日**: 2025年11月09日

