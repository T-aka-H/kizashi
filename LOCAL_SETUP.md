# ローカル実行ガイド

このガイドでは、Weak Signals Appをローカル環境で実行する手順を説明します。

## 📋 前提条件

- **Python 3.11以上**がインストールされていること
- **Node.js 20.x以上**がインストールされていること
- **OpenAI APIキー**を取得済みであること

## 🚀 クイックスタート

### 方法1: バッチファイルを使用（Windows推奨）

1. **初回セットアップ**: `setup.bat`をダブルクリック
   - 依存パッケージのインストールと環境設定を行います
   - `.env`ファイルが自動的に作成されます

2. **アプリ起動**: `start_all.bat`をダブルクリック
   - バックエンドとフロントエンドが自動的に起動します
   - 2つのウィンドウが開きます

3. **個別起動**:
   - `start_backend.bat` - バックエンドのみ起動
   - `start_frontend.bat` - フロントエンドのみ起動

### 方法2: コマンドラインを使用

### ステップ1: リポジトリのクローン（既にクローン済みの場合はスキップ）

```bash
git clone <repository-url>
cd kizashi_local
```

### ステップ2: バックエンドのセットアップ

#### 2-1. Python仮想環境の作成（推奨）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 2-2. 依存パッケージのインストール

```bash
cd backend
pip install -r requirements.txt
```

#### 2-3. 環境変数の設定

プロジェクトルートに`.env`ファイルを作成：

```bash
# プロジェクトルートに戻る
cd ..

# .env.exampleをコピー
copy .env.example .env  # Windows
# または
cp .env.example .env   # macOS/Linux
```

`.env`ファイルを編集して、OpenAI APIキーを設定：

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
POST_MODE=demo
```

**重要**: `.env`ファイルは`.gitignore`に含まれているため、Gitにコミットされません。

### ステップ3: フロントエンドのセットアップ

```bash
cd frontend
npm install

# 環境変数ファイルの作成（オプション）
# バックエンドのURLを変更する場合のみ必要
copy .env.local.example .env.local  # Windows
# または
cp .env.local.example .env.local   # macOS/Linux
```

**注意**: `.env.local`は作成しなくても動作します。`next.config.js`でデフォルト値（`http://localhost:8000`）が設定されているためです。バックエンドのURLを変更する場合のみ`.env.local`を作成してください。

### ステップ4: サーバーの起動

#### バックエンドの起動

**ターミナル1**で：

```bash
cd backend
python main.py
```

または、開発モード（ホットリロード有効）：

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

バックエンドが起動すると、以下のメッセージが表示されます：

```
INFO:     Started server process
INFO:     Waiting for application startup.
✅ データベース初期化完了
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

#### フロントエンドの起動

**ターミナル2**で：

```bash
cd frontend
npm run dev
```

フロントエンドが起動すると、以下のメッセージが表示されます：

```
  ▲ Next.js 14.0.4
  - Local:        http://localhost:3000
```

### ステップ5: ブラウザでアクセス

- **フロントエンド**: http://localhost:3000
- **APIドキュメント**: http://localhost:8000/docs
- **ヘルスチェック**: http://localhost:8000/

## 🔑 APIキーの取得方法

### OpenAI APIキー

1. [OpenAI Platform](https://platform.openai.com/)にアクセス
2. アカウントを作成（またはログイン）
3. 「API keys」→「Create new secret key」をクリック
4. 生成されたAPIキーをコピー（`sk-`で始まる文字列）
5. `.env`ファイルの`OPENAI_API_KEY`に設定

**注意**: APIキーは一度しか表示されません。必ず保存してください。

## 🧪 動作確認

### バックエンドのテスト

```bash
cd backend
python test_backend.py
```

### APIのテスト

ブラウザで http://localhost:8000/docs にアクセスして、Swagger UIでAPIをテストできます。

または、curlコマンドで：

```bash
# ヘルスチェック
curl http://localhost:8000/

# 統計情報取得（認証が必要な場合）
curl http://localhost:8000/stats
```

## 📝 環境変数の詳細

### 必須設定

- `OPENAI_API_KEY`: OpenAI APIキー（必須）

### オプション設定

- `OPENAI_MODEL`: OpenAIモデル名（デフォルト: `gpt-4o-mini-search-preview`）
  - Web検索対応モデルを使用（Responses API + Web searchツール）
  - 使用できない場合は自動的に`OPENAI_MODEL_FALLBACK`にフォールバック
- `OPENAI_MODEL_FALLBACK`: フォールバック用モデル名（デフォルト: `gpt-4o-search-preview`）
- `POST_MODE`: 投稿モード（`demo` または `bluesky`、デフォルト: `demo`）
- `BLUESKY_HANDLE`: Blueskyハンドル（`POST_MODE=bluesky`の場合に必要）
- `BLUESKY_PASSWORD`: Blueskyアプリパスワード（`POST_MODE=bluesky`の場合に必要）
- `AUTH_USERNAME`: Basic認証のユーザー名（オプション）
- `AUTH_PASSWORD`: Basic認証のパスワード（オプション）
- `POST_PASSWORD`: 投稿確認パスワード（オプション）
- `DATABASE_URL`: PostgreSQL接続URL（オプション、未設定の場合はSQLiteを使用）
- `DISABLE_SCHEDULER`: スケジューラー無効化フラグ（`true`/`false`、デフォルト: `false`）

### フロントエンド環境変数（`frontend/.env.local`）

- `NEXT_PUBLIC_API_URL`: バックエンドAPIのURL（デフォルト: `http://localhost:8000`）
  - バックエンドのURLを変更する場合のみ設定が必要
  - `next.config.js`でデフォルト値が設定されているため、通常は作成不要

## 🐛 トラブルシューティング

### lxmlのビルドエラー（Python 3.13）

**エラー**: `lxml`のビルドエラーや`Microsoft Visual C++ 14.0 or greater is required`

**原因**: `lxml`の古いバージョン（4.9.3など）はPython 3.13用のホイールがなく、ソースからビルドしようとして失敗します。

**解決策**:
1. **`install_deps.bat`を実行**（推奨）
   - 仮想環境を有効化した状態で`install_deps.bat`をダブルクリック
   - `lxml>=6.0.2`がホイール優先でインストールされます

2. **手動でインストール**
   ```bash
   # 仮想環境を有効化後
   python -m pip install --upgrade pip
   python -m pip install --only-binary=:all: -r backend/requirements.txt -c backend/constraints.txt
   ```

3. **Python 3.11または3.12を使用する（最も確実）**
   - `setup_python311.bat`をダブルクリックして、Python 3.11用のセットアップを実行

### Python 3.13の互換性問題

**エラー**: `atproto`ライブラリのビルドエラーやその他のパッケージのインストールエラー

**原因**: `atproto`ライブラリがPython 3.13に対応していない可能性があります。

**解決策**:
1. **Python 3.11または3.12を使用する（推奨）**
   - `setup_python311.bat`をダブルクリックして、Python 3.11用のセットアップを実行
   - または、手動でPython 3.11/3.12をインストールして仮想環境を作成

2. **Python 3.13で続行する場合**
   - `setup.bat`で警告が表示されますが、続行を選択できます
   - エラーが発生する場合は、Python 3.11または3.12にダウングレードしてください

### psycopg2-binaryのインストールエラー

**エラー**: `pg_config executable not found` または `Error: pg_config executable not found`

**原因**: `psycopg2-binary`はPostgreSQL用のライブラリですが、ローカル開発ではSQLiteを使用するため不要です。

**解決策**:
- `requirements.txt`から`psycopg2-binary`は既にコメントアウトされています
- エラーが発生する場合は、`requirements.txt`を確認してください
- 本番環境でPostgreSQLを使用する場合は、`requirements-prod.txt`を使用してください

### バックエンドが起動しない

**エラー**: `OPENAI_API_KEY環境変数が設定されていません`

**解決策**:
1. `.env`ファイルがプロジェクトルートに存在するか確認
2. `.env`ファイルに`OPENAI_API_KEY`が設定されているか確認
3. Pythonの`python-dotenv`がインストールされているか確認（`pip install python-dotenv`）

### フロントエンドがバックエンドに接続できない

**エラー**: `Network Error` または `Connection refused`

**解決策**:
1. バックエンドが起動しているか確認（http://localhost:8000/ にアクセス）
2. `frontend/lib/api.ts`の`API_URL`が`http://localhost:8000`になっているか確認
3. CORS設定を確認（`backend/main.py`の`allow_origins`）

### データベースエラー

**エラー**: `sqlite3.OperationalError`

**解決策**:
1. `backend`ディレクトリに書き込み権限があるか確認
2. SQLiteファイル（`weak_signals.db`）がロックされていないか確認
3. 必要に応じて`weak_signals.db`を削除して再作成

### ポートが既に使用されている

**エラー**: `Address already in use`

**解決策**:
1. 既に起動しているプロセスを終了
2. 別のポートを使用（例: `uvicorn main:app --port 8001`）
3. フロントエンドの`NEXT_PUBLIC_API_URL`も変更

## 📚 次のステップ

- [Blueskyセットアップガイド](./BLUESKY_SETUP.md) - Bluesky投稿機能の設定
- [デプロイガイド](./DEPLOY.md) - Renderへのデプロイ手順
- [APIドキュメント](http://localhost:8000/docs) - APIの詳細な使用方法

## 💡 開発のヒント

### 仮想環境の有効化

**Windowsでの正しいコマンド**:

```bash
# プロジェクトルートで実行
venv\Scripts\activate

# または、activate_venv.batをダブルクリック
```

**注意**: `venv activate` は正しくありません。正しくは `venv\Scripts\activate` です。

仮想環境が有効化されると、プロンプトの前に `(venv)` が表示されます。

```bash
(venv) C:\dev\kizashi_local>
```

仮想環境を無効化するには:
```bash
deactivate
```

### 開発モードでの実行

バックエンドを開発モードで実行すると、コード変更が自動的に反映されます：

```bash
cd backend
uvicorn main:app --reload
```

### データベースのリセット

SQLiteデータベースをリセットする場合：

```bash
cd backend
rm weak_signals.db  # macOS/Linux
# または
del weak_signals.db  # Windows
```

次回起動時に自動的に再作成されます。

### ログの確認

バックエンドのログはターミナルに出力されます。エラーが発生した場合は、ターミナルの出力を確認してください。

