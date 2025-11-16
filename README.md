# Weak Signals App

Gemini APIを使用した記事分析とBluesky自動投稿アプリケーション

## 機能

- 📰 記事の自動取得と分析（Gemini API + WIRED RSS）
- 🔍 テーマ分類、要約、主要ポイント抽出
- 📤 ソーシャルメディア投稿キュー管理（Bluesky）
- ✅ 投稿承認フロー
- 📊 統計ダッシュボード
- 🌐 RSSフィード・Webスクレイピング対応
- 🦋 Bluesky対応（無料・投稿制限なし）

## クイックスタート

### ローカル開発

詳細な手順は [LOCAL_SETUP.md](./LOCAL_SETUP.md) を参照してください。

#### バックエンド

```bash
cd backend
pip install -r requirements.txt

# 環境変数を設定（プロジェクトルートで実行）
cd ..
copy .env.example .env  # Windows
# または
cp .env.example .env   # macOS/Linux

# .envファイルを編集してGemini APIキーを設定

# サーバー起動
cd backend
python main.py
# または（開発モード）
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

#### フロントエンド

```bash
cd frontend
npm install

# 開発サーバー起動
npm run dev
```

**アクセスURL**:
- フロントエンド: http://localhost:3000
- APIドキュメント: http://localhost:8000/docs

### Renderへのデプロイ

詳細は [DEPLOY.md](./DEPLOY.md) を参照してください。

```bash
# 1. GitHubにプッシュ
git push origin main

# 2. Render DashboardでBlueprintを作成
# render.yamlを使用して自動デプロイ
```

## セットアップ

### 1. 依存パッケージのインストール

**バックエンド:**
```bash
cd backend
pip install -r requirements.txt
```

**フロントエンド:**
```bash
cd frontend
npm install
```

### 2. 環境変数の設定

`.env.example`をコピーして`.env`を作成し、APIキーを設定してください：

```bash
cp .env.example .env
```

`.env`ファイルを編集：

```env
GEMINI_API_KEY=AIzaSyC...

# 投稿モード設定（bluesky, demo）
POST_MODE=demo

# Bluesky設定（POST_MODE=blueskyの場合に必要）
BLUESKY_HANDLE=yourname.bsky.social
BLUESKY_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

### 3. APIキーの取得

#### Gemini API
1. [Google AI Studio](https://makersuite.google.com/app/apikey)にアクセス
2. Googleアカウントでログイン
3. 「Create API Key」をクリック
4. 生成されたAPIキーをコピー（`AIza...`で始まる文字列）
5. `.env`に設定

#### Bluesky
詳細は [BLUESKY_SETUP.md](./BLUESKY_SETUP.md) を参照してください。

1. [Bluesky](https://bsky.app)でアカウント作成
2. 設定 → App passwords → 新規作成
3. 生成されたパスワードをコピー
4. `.env`に設定

### 4. テスト実行

```bash
cd backend
python test_backend.py
```

### 5. サーバー起動

**バックエンド:**
```bash
cd backend
python main.py
```

**フロントエンド:**
```bash
cd frontend
npm run dev
```

APIドキュメント: http://localhost:8000/docs

フロントエンド: http://localhost:3000

## プロジェクト構造

```
weak-signals-app/
├── backend/
│   ├── main.py                  # FastAPI メインアプリ
│   ├── gemini_analyzer.py       # Gemini API連携（記事分析）
│   ├── twitter_poster.py        # Bluesky API連携
│   ├── article_fetcher.py      # 記事取得（RSS/スクレイピング）
│   ├── database.py              # DB操作
│   ├── models.py                # データモデル
│   ├── scheduler.py             # 定期実行
│   ├── test_backend.py          # テストスクリプト
│   ├── test_article_fetcher.py  # 記事取得テスト
│   └── requirements.txt         # 依存パッケージ
├── frontend/
│   ├── app/                     # Next.js App Router
│   ├── components/              # Reactコンポーネント
│   ├── lib/                     # ユーティリティ
│   └── package.json
├── render.yaml                  # Renderデプロイ設定
├── DEPLOY.md                    # デプロイガイド
├── .env.example                 # 環境変数テンプレート
└── README.md                    # このファイル
```

## APIエンドポイント

### 記事関連

- `POST /articles` - 記事を作成
- `GET /articles` - 記事一覧を取得
- `GET /articles/{id}` - 記事を取得
- `POST /articles/{id}/analyze` - 記事を分析

### 投稿キュー関連

- `GET /post-queue` - 投稿キューを取得
- `POST /post-queue/{id}/approve` - 投稿を承認
- `POST /post-queue/{id}/post` - ツイートを投稿

### 統計

- `GET /stats` - 統計情報を取得

### 記事取得

- `POST /fetch/rss` - RSSフィードから記事を取得
- `POST /fetch/url` - URLから記事を取得（Webスクレイピング）
- `POST /fetch/analyze` - 記事を取得して自動分析

## 使用例

### Pythonから記事を分析

```python
from database import SessionLocal, create_article, update_article_analysis
from gemini_analyzer import GeminiAnalyzer

db = SessionLocal()
analyzer = GeminiAnalyzer()

# 記事作成
article = create_article(
    db,
    url="https://example.com/article",
    title="記事タイトル",
    content="記事本文..."
)

# 分析
analysis = analyzer.analyze_article(article.title, article.content, article.url)
update_article_analysis(db, article.id, analysis)
```

### ツイートを投稿

```python
from twitter_poster import SocialPoster

poster = SocialPoster()
result = poster.post("投稿テキスト")
```

### 投稿モードの切り替え

環境変数`POST_MODE`で切り替え可能：

- `bluesky` - Blueskyに投稿
- `demo` - デモモード（実際には投稿しない）

### 記事取得機能

RSSフィードやWebスクレイピングで記事を自動取得できます。

```python
from article_fetcher import ArticleFetcher, RSSFeedManager

# RSSフィードから取得
fetcher = ArticleFetcher()
articles = fetcher.fetch_from_rss("https://example.com/feed", max_items=10)

# URLから直接取得
article = fetcher.fetch_from_url("https://example.com/article")

# 複数フィードを管理
manager = RSSFeedManager()
manager.add_feed("https://example.com/feed1", max_items=5)
manager.add_feed("https://example.com/feed2", max_items=5)
articles = manager.fetch_all_feeds()
```

## 開発

### データベース

- **開発環境**: SQLite（デフォルト）
- **本番環境**: PostgreSQL（Renderで自動設定）

### 定期実行

`scheduler.py`を使用して記事の定期取得・分析を実行できます。

```bash
# スケジューラーを実行（60分間隔）
cd backend
python scheduler.py
```

または、APIから直接実行：

```bash
# 記事を取得して自動分析
curl -X POST http://localhost:8000/fetch/analyze
```

## デプロイ

Renderへのデプロイ手順は [DEPLOY.md](./DEPLOY.md) を参照してください。

## ライセンス

MIT
