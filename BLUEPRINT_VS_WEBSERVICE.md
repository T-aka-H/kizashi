# Renderデプロイ方法：Blueprint vs Web Service

## 2つの方法の比較

### 方法1: Blueprint（推奨・簡単）

**メリット:**
- ✅ `render.yaml`の設定を自動適用
- ✅ バックエンド、フロントエンド、データベースを一度に作成
- ✅ 環境変数の連携が自動
- ✅ 設定ミスが少ない

**デメリット:**
- ⚠️ `render.yaml`ファイルが必要

### 方法2: Web Service（手動設定）

**メリット:**
- ✅ 各サービスを個別に設定できる
- ✅ `render.yaml`がなくても動作
- ✅ より細かい制御が可能

**デメリット:**
- ⚠️ 手動で設定する必要がある
- ⚠️ 設定ミスの可能性がある
- ⚠️ 時間がかかる

## 推奨：Blueprintを使う

`render.yaml`ファイルがあるので、**Blueprintを使うことを強く推奨**します。

## Blueprintを使う場合の手順

1. Render Dashboard → "New +" → **"Blueprint"**
2. GitHubリポジトリを接続
3. `T-aka-H/kizashi` を選択
4. Renderが自動的に`render.yaml`を検出
5. "Apply" をクリック
6. 環境変数を設定（後で）

**これだけで完了！** バックエンド、フロントエンド、データベースが自動的に作成されます。

## Web Serviceを個別に作成する場合

もしBlueprintを使わずに、Web Serviceを個別に作成する場合は：

### 1. データベースを先に作成

1. "New +" → "PostgreSQL"
2. 設定：
   - Name: `weak-signals-db`
   - Database: `weak_signals`
   - User: `weak_signals_user`
   - Plan: Starter

### 2. バックエンドを作成

1. "New +" → **"Web Service"**（Blueprintではない）
2. GitHubリポジトリを接続
3. 設定：
   - Name: `weak-signals-backend`
   - Environment: `Python 3`
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Plan: Starter
4. 環境変数を設定：
   - `DATABASE_URL`（データベースのConnectionsタブからコピー）
   - `GEMINI_API_KEY`
   - `POST_MODE` = `bluesky`
   - `BLUESKY_HANDLE`
   - `BLUESKY_PASSWORD`

### 3. フロントエンドを作成

1. "New +" → **"Web Service"**（Blueprintではない）
2. GitHubリポジトリを接続
3. 設定：
   - Name: `weak-signals-frontend`
   - Environment: `Node`
   - Build Command: `cd frontend && npm install && npm run build`
   - Start Command: `cd frontend && npm start`
   - Plan: Starter
4. 環境変数を設定：
   - `NEXT_PUBLIC_API_URL` = `https://weak-signals-backend.onrender.com`

## 結論

**Blueprintを使うことを強く推奨します。**

理由：
- ✅ 設定が簡単
- ✅ ミスが少ない
- ✅ 時間がかからない
- ✅ `render.yaml`が既にある

Web Serviceを個別に作成する必要があるのは：
- `render.yaml`を使いたくない場合
- より細かい制御が必要な場合
- 既存のサービスに追加する場合

あなたの場合は`render.yaml`があるので、**Blueprintを使うのが最適**です。

