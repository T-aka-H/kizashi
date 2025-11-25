# 📊 WIRED記事TOP5投稿Bot - システム概要

## ✅ 完成しました！

WIRED の人気記事TOP5を毎朝8時にBlueskyに投稿するシステムを作成しました。

---

## 📦 作成したファイル

### メインファイル
| ファイル | 場所 | 説明 |
|---------|------|------|
| `wired_bluesky_bot.py` | `backend/` | 基本版（RSSのsummaryを使用） |
| `wired_bluesky_bot_advanced.py` | `backend/` | **改良版**（記事本文を取得して詳細な要約）⭐ |
| `wired_scheduler.py` | `backend/` | 毎朝8時に自動実行するスケジューラー |

### ドキュメント
| ファイル | 場所 | 説明 |
|---------|------|------|
| `README_WIRED_BOT.md` | ルート | 詳細なセットアップガイド |
| `WIRED_BOT_QUICKSTART.md` | ルート | クイックスタートガイド（5分） |
| `WIRED_BOT_ENV_EXAMPLE.txt` | ルート | 環境変数のサンプル |
| `WIRED_BOT_SUMMARY.md` | ルート | このファイル |

### ツール
| ファイル | 場所 | 説明 |
|---------|------|------|
| `test_wired_bot.bat` | ルート | テスト実行用バッチファイル |

---

## 🔧 既存ファイルの活用

以下の既存ファイルを活用しています：

| ファイル | 用途 |
|---------|------|
| `article_fetcher.py` | WIRED RSSフィードから記事を取得 |
| `gemini_analyzer.py` | Gemini APIで記事を分析・要約 |
| `twitter_poster.py` | Blueskyに投稿 |
| `requirements.txt` | 必要なパッケージ（既にインストール済み） |

**不要なファイルの削除は行っていません**。既存のシステムに影響を与えず、新しいボットを追加する形にしています。

---

## 🚀 使い方

### 1. 環境変数を設定

`C:\dev\wired\.env` に以下を追加：

```env
GEMINI_API_KEY=あなたのAPIキー
BLUESKY_HANDLE=あなたのハンドル.bsky.social
BLUESKY_PASSWORD=アプリパスワード
POST_MODE=demo
USE_ADVANCED_BOT=true
```

詳細は `WIRED_BOT_ENV_EXAMPLE.txt` を参照。

### 2. テスト実行

```bash
# 方法1: バッチファイルで実行（推奨）
test_wired_bot.bat

# 方法2: 直接実行
cd backend
python wired_bluesky_bot_advanced.py
```

### 3. 本番投稿

`.env` で `POST_MODE=bluesky` に変更してから：

```bash
python wired_bluesky_bot_advanced.py
```

### 4. 自動実行（毎朝8時）

```bash
cd backend
python wired_scheduler.py
```

---

## ✨ 主な機能

1. ✅ **WIRED RSS取得**: 最新20記事を取得
2. ✅ **AI選定**: Gemini APIが重要度TOP5を判定
3. ✅ **日本語要約**: 記事を日本語で要約
4. ✅ **個別投稿**: TOP5を5つの投稿として個別に投稿
5. ✅ **詳細情報**: 各投稿に要旨・ポイント・URLを含む
6. ✅ **スケジュール実行**: 毎朝8時に自動実行
7. ✅ **デモモード**: テスト用（実際には投稿しない）
8. ✅ **スパム対策**: 投稿間隔5秒で安全に投稿

---

## 📝 投稿例

**TOP5を個別に投稿**（合計5つの投稿）

### 投稿1（1位）
```
📰 WIRED TOP1 (11/09)

【AIが生成する新しいアート形式が美術界に革命】

📝 AI技術の進化により、従来のアート制作手法が根本的に変化。
アーティストとAIの協働が新しい創造性を生み出している。

💡 デジタルアートの民主化が進み、誰でもクリエイターになれる時代へ。

🔗 https://www.wired.com/story/ai-art-...
```

### 投稿2〜5
同様に、2位〜5位の記事も個別投稿されます。

**特徴:**
- ✅ 各記事を個別投稿（5つの投稿）
- ✅ 要旨とポイントで分かりやすく
- ✅ URLで詳細へアクセス可能
- ✅ 5秒間隔で投稿（スパム判定回避）

---

## 🔄 2つのバージョン

| 機能 | 基本版 | 改良版 ⭐ |
|------|--------|---------|
| ファイル | `wired_bluesky_bot.py` | `wired_bluesky_bot_advanced.py` |
| 記事取得 | RSSのみ | RSS + 本文取得 |
| 要約精度 | 普通 | 高い（本文を読んで要約） |
| 実行時間 | 速い（約10秒） | やや遅い（約30-60秒） |
| おすすめ | テスト用 | **本番用**（推奨） |

**推奨**: `wired_bluesky_bot_advanced.py` を使用してください。

---

## 🎯 次のステップ

### すぐできること
- [ ] `.env` に環境変数を設定
- [ ] `test_wired_bot.bat` でテスト実行
- [ ] デモモードで動作確認
- [ ] 本番投稿（POST_MODE=bluesky）
- [ ] スケジューラー起動（毎朝8時）

### カスタマイズ（オプション）
- [ ] 投稿時刻を変更（8時 → 好きな時刻）
- [ ] TOP5 → TOP3に変更
- [ ] 他のニュースサイトに対応
- [ ] 画像付き投稿

---

## 📚 詳細ドキュメント

- **セットアップ**: `README_WIRED_BOT.md`
- **クイックスタート**: `WIRED_BOT_QUICKSTART.md`
- **環境変数**: `WIRED_BOT_ENV_EXAMPLE.txt`

---

## ✅ 動作確認済み

- ✅ Python構文チェック: OK
- ✅ 既存システムとの互換性: OK
- ✅ 必要なパッケージ: すべてインストール済み
- ✅ コード品質: リンターエラーなし

---

## 💡 ヒント

1. **必ずデモモードでテスト**: `POST_MODE=demo` でテストしてから本番投稿
2. **APIキーの取得**: Gemini APIキーは https://makersuite.google.com/app/apikey で取得
3. **Blueskyアプリパスワード**: 通常のパスワードではなく、設定で作成したアプリパスワードを使用
4. **レート制限**: Gemini API無料枠は1分15リクエストまで

---

## ❓ 困ったら

1. `README_WIRED_BOT.md` のトラブルシューティングを確認
2. `test_wired_bot.bat` で環境をチェック
3. デモモードで動作確認

---

**作成日**: 2025年11月09日  
**バージョン**: 1.0.0  
**ステータス**: ✅ 完成

