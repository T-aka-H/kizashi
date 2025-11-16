# 🔄 改良版WIRED Botの動作フロー

## ❓ 質問: 今は改良版で本文にアクセスして生成AIがそれを呼んで要約してくれているということですか？

**回答**: **はい、その通りです！**

---

## 📋 改良版の動作フロー

### 1. WIRED RSSから記事を取得

```python
articles = self.fetch_wired_articles(max_items=20)
```

- WIREDのRSSフィードから記事を取得
- 取得される情報: **タイトル、URL、要約（RSSの抜粋）**

---

### 2. GeminiでTOP5を選定

```python
top5_articles = self.select_top5_with_gemini(articles)
```

- Geminiに記事リストを送信
- 技術トレンド・イノベーション・未来への影響度を基準にTOP5を選定

---

### 3. TOP5の記事本文を取得 ⭐

```python
for article in top5_articles:
    self.fetch_article_content(article)
```

**ここで記事のURLにアクセスして本文を取得します！**

```python
def fetch_article_content(self, article: Dict) -> Dict:
    url = article.get('url')
    full_article = self.fetcher.fetch_from_url(url)  # ← 記事のURLにアクセス
    if full_article and full_article.get('content'):
        article['full_content'] = full_article['content']  # ← 本文を保存
```

- 記事のURLにHTTPリクエストを送信
- Webスクレイピングで記事の**本文を取得**
- `article['full_content']`に保存

---

### 4. Geminiで詳細な要約を生成 ⭐⭐

```python
for article in top5_articles:
    summary_data = self.create_detailed_summary(article)
    article.update(summary_data)
```

**ここで取得した本文をGemini（生成AI）に送って要約を生成します！**

```python
def create_detailed_summary(self, article: Dict) -> Dict:
    title = article.get('title', '')
    content = article.get('full_content') or article.get('content', '')  # ← 本文を使用
    
    prompt = f"""以下のWIRED記事を日本語で要約してください。
    
タイトル: {title}
本文: {content[:2000]}  # ← 本文の最初の2000文字をGeminiに送信
    
以下のJSON形式で回答してください:
{{
    "summary": "記事の要旨（100文字以内）",
    "key_point": "最も重要なポイント（100文字以内）"
}}
"""
    
    response = self.analyzer.model.generate_content(prompt)  # ← Gemini APIを呼び出し
    # JSONを解析して要約を取得
```

- 取得した本文（`full_content`）をGeminiに送信
- Geminiが要約（`summary`）とポイント（`key_point`）を生成
- 生成された要約を記事データに追加

---

### 5. TOP5を個別にBlueskyに投稿

```python
result = self.post_articles_to_bluesky(top5_articles)
```

- 要約とポイントを含む投稿テキストを作成
- 各記事を個別にBlueskyに投稿

---

## 🎯 まとめ

### 改良版の処理フロー

```
1. RSSから記事を取得（タイトル、URL、要約）
   ↓
2. GeminiでTOP5を選定
   ↓
3. TOP5の記事URLにアクセスして本文を取得 ⭐
   ↓
4. 取得した本文をGeminiに送って要約を生成 ⭐⭐
   ↓
5. 要約とポイントを使って投稿テキストを作成
   ↓
6. Blueskyに投稿
```

### 重要なポイント

- ✅ **記事のURLにアクセス**: `fetch_article_content`メソッドで本文を取得
- ✅ **生成AI（Gemini）で要約**: `create_detailed_summary`メソッドで本文をGeminiに送信
- ✅ **詳細な要約**: RSSの抜粋ではなく、記事の本文から要約を生成

---

## 📊 基本版との違い

| 項目 | 基本版 | 改良版 |
|------|--------|--------|
| **使用する情報** | RSSの要約のみ | RSSの要約 + 記事の本文 |
| **本文取得** | ❌ なし | ✅ あり（URLにアクセス） |
| **要約生成** | RSSの要約をそのまま使用 | ✅ Geminiで本文から要約を生成 |
| **処理時間** | 速い | やや遅い（HTTPリクエスト + AI処理） |
| **要約の精度** | 低い（RSSの抜粋のみ） | 高い（本文から生成） |

---

**作成日**: 2025年11月16日

