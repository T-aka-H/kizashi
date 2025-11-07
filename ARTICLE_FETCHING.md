# 記事の取得方法について

## 現在の実装状況

### 記事の取得元

記事は以下のソースから取得できます：

1. **RSSフィード**（`article_fetcher.py`）
   - TechCrunch
   - The Verge
   - Zenn
   - Qiita
   - その他のRSSフィード

2. **Webスクレイピング**（`article_fetcher.py`）
   - 指定したURLから記事を取得

3. **手動作成**（API）
   - `POST /articles` エンドポイントで手動作成

### デフォルトのRSSフィード

`article_fetcher.py`に以下のデフォルトフィードが設定されています：

```python
DEFAULT_FEEDS = [
    {'url': 'https://techcrunch.com/feed/', 'max_items': 5},
    {'url': 'https://www.theverge.com/rss/index.xml', 'max_items': 5},
    {'url': 'https://zenn.dev/feed', 'max_items': 5},
    {'url': 'https://qiita.com/feed', 'max_items': 5},
]
```

## 記事を取得する方法

### 方法1: APIエンドポイントから取得・分析

```bash
# デフォルトのRSSフィードから取得して分析
curl -X POST http://localhost:8000/fetch/analyze

# 特定のRSSフィードから取得
curl -X POST "http://localhost:8000/fetch/analyze?rss_url=https://example.com/feed"
```

### 方法2: スケジューラーを実行

```bash
cd backend
python scheduler.py
```

### 方法3: 手動で記事を作成

```bash
curl -X POST http://localhost:8000/articles \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "title": "記事タイトル",
    "content": "記事本文"
  }'
```

## 重要なポイント

### ⚠️ 現在は自動取得されていません

- 記事は**手動で取得する必要があります**
- フロントエンドからは記事を**表示するだけ**です
- データベースに記事がない場合、何も表示されません

### 記事を表示するには

1. **まず記事を取得する**
   - APIエンドポイント `/fetch/analyze` を呼び出す
   - または `scheduler.py` を実行

2. **その後、フロントエンドで表示**
   - 記事一覧ページで自動的に表示されます

## 改善案

### オプション1: フロントエンドに「記事取得」ボタンを追加

ダッシュボードや記事一覧ページにボタンを追加して、ワンクリックで記事を取得・分析できるようにする。

### オプション2: Renderで定期実行を設定

RenderのCronジョブやバックグラウンドジョブで定期実行する。

### オプション3: バックエンド起動時に自動実行

`main.py`の起動時に1回だけ実行する。

どの方法がお好みですか？

