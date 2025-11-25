# 📰 RSSフィードの構造

## ❓ 質問: RSSは内容は書いて無く、題名だけですか？

**回答**: **いいえ、RSSフィードには要約や説明も含まれています。**

ただし、**記事の全文は含まれていません**。

---

## 📋 RSSフィードに含まれる情報

### 一般的なRSSフィードの構造

RSSフィードには以下の情報が含まれます：

1. **タイトル** (`title`) - ✅ 必須
2. **URL** (`link`) - ✅ 必須
3. **要約/説明** (`summary` / `description`) - ⚠️ オプション（通常は含まれる）
4. **全文** (`content`) - ❌ 通常は含まれない（一部のRSSフィードのみ）

---

## 🔍 現在のコードでの処理

### `article_fetcher.py`の`fetch_from_rss`メソッド

```python
# コンテンツの取得
content = ""
if hasattr(entry, 'content'):
    content = entry.content[0].value if entry.content else ""
elif hasattr(entry, 'summary'):
    content = entry.summary
elif hasattr(entry, 'description'):
    content = entry.description
```

**取得順序**:
1. `entry.content` - 全文（通常は含まれない）
2. `entry.summary` - 要約（通常は含まれる）
3. `entry.description` - 説明（通常は含まれる）

---

## 📊 WIRED Botの基本版と改良版の違い

### 基本版 (`wired_bluesky_bot.py`)

- **使用する情報**: RSSフィードの要約のみ
- **取得方法**: `article.get('content')` - RSSから取得した要約
- **特徴**: 
  - 高速（追加のHTTPリクエスト不要）
  - 要約のみなので情報量が限られる

### 改良版 (`wired_bluesky_bot_advanced.py`)

- **使用する情報**: RSSフィードの要約 + 記事の本文
- **取得方法**: 
  1. RSSから要約を取得
  2. 記事のURLにアクセスして本文を取得（`fetch_article_content`メソッド）
- **特徴**: 
  - より詳細な要約が可能
  - 追加のHTTPリクエストが必要（時間がかかる）

---

## 📝 実際のRSSフィードの例

### WIRED RSSフィードの構造（一般的な例）

```xml
<item>
  <title>記事のタイトル</title>
  <link>https://www.wired.com/story/...</link>
  <description>
    <!-- 記事の要約や抜粋（通常100-300文字程度） -->
    記事の要約がここに含まれます...
  </description>
  <pubDate>Mon, 16 Nov 2025 10:00:00 +0000</pubDate>
</item>
```

**注意**: 
- `<description>`には記事の全文ではなく、**要約や抜粋**が含まれます
- 記事の全文を取得するには、`<link>`のURLにアクセスする必要があります

---

## 🎯 まとめ

### RSSフィードに含まれる情報

| 情報 | 含まれるか | 説明 |
|------|-----------|------|
| **タイトル** | ✅ 必須 | 記事のタイトル |
| **URL** | ✅ 必須 | 記事のURL |
| **要約/説明** | ⚠️ 通常含まれる | 記事の要約や抜粋（100-300文字程度） |
| **全文** | ❌ 通常含まれない | 記事の全文（URLにアクセスする必要がある） |

### WIRED Botでの使用

- **基本版**: RSSの要約のみを使用（高速）
- **改良版**: RSSの要約 + 記事の本文を取得（詳細）

---

**作成日**: 2025年11月16日

