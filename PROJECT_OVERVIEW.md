# 📰 Weak Signals App - プロジェクト概要

## 🎯 このプログラムについて

**Weak Signals App**は、**AIを活用した記事分析・自動投稿システム**です。

技術トレンドやイノベーションに関する記事を自動で収集し、AI（Gemini API）で分析して、Blueskyに自動投稿するWebアプリケーションです。

---

## ✨ 主な機能

### 1. 📰 記事の自動取得
- **RSSフィード**から記事を自動取得
- **Webスクレイピング**で記事本文を取得
- 複数のニュースサイトに対応

### 2. 🤖 AIによる記事分析
- **Gemini API**を使用して記事を分析
- テーマ分類、要約、主要ポイントを抽出
- 技術トレンドやイノベーションの重要度を判定

### 3. 📤 ソーシャルメディア自動投稿
- **Bluesky**に自動投稿
- 投稿キュー管理（承認フロー）
- デモモード（テスト用）

### 4. 🔄 定期実行スケジューラー
- 15分間隔で記事を自動取得・分析
- 承認済み記事を自動投稿
- バックグラウンドで実行

### 5. 🌐 Webダッシュボード（フロントエンド）
- Next.jsで構築された管理画面
- 記事一覧、投稿キュー管理
- 統計情報の表示

### 6. 📰 WIRED記事TOP5自動投稿ボット（追加機能）
- WIREDの人気記事TOP5を毎朝8時に自動投稿
- Gemini APIが重要度を判定
- 各記事を個別に投稿（5つの投稿）

---

## 🏗️ システム構成

### バックエンド（FastAPI）
```
backend/
├── main.py                    # FastAPIメインアプリ
├── gemini_analyzer.py         # Gemini API連携（記事分析）
├── twitter_poster.py          # Bluesky投稿機能
├── article_fetcher.py          # 記事取得（RSS/スクレイピング）
├── database.py                # データベース操作
├── scheduler.py               # 定期実行スケジューラー
├── wired_bluesky_bot.py       # WIRED Bot（基本版）
├── wired_bluesky_bot_advanced.py  # WIRED Bot（改良版）
└── wired_scheduler.py         # WIRED Botスケジューラー
```

### フロントエンド（Next.js）
```
frontend/
├── app/                       # Next.js App Router
│   ├── articles/              # 記事一覧ページ
│   ├── queue/                 # 投稿キュー管理
│   └── themes/                # テーマ別表示
└── components/                # Reactコンポーネント
```

### データベース
- **開発環境**: SQLite
- **本番環境**: PostgreSQL（Render）

---

## 🚀 主な使用シーン

### 1. 技術トレンドの自動収集・分析
- 複数の技術系ニュースサイトから記事を自動取得
- AIが重要度を判定して、注目すべき記事を選定

### 2. ソーシャルメディア自動投稿
- 分析結果をBlueskyに自動投稿
- 承認フローで品質管理

### 3. WIRED記事の定期投稿
- 毎朝8時にWIREDの人気記事TOP5を自動投稿
- 技術トレンドをフォロワーに共有

### 4. 未来の兆し（Weak Signals）の発見
- AIが記事から「未来の兆し」を抽出
- テーマに基づいて未来洞察を生成

---

## 🛠️ 技術スタック

### バックエンド
- **FastAPI**: Webフレームワーク
- **SQLAlchemy**: ORM
- **Google Gemini API**: AI分析
- **atproto**: Bluesky API
- **BeautifulSoup**: Webスクレイピング
- **feedparser**: RSS解析

### フロントエンド
- **Next.js**: Reactフレームワーク
- **TypeScript**: 型安全性
- **Tailwind CSS**: スタイリング

### インフラ
- **Render**: ホスティング（Web Service + PostgreSQL）
- **GitHub**: ソースコード管理

---

## 📊 データフロー

```
1. RSSフィード/Webスクレイピング
   ↓
2. 記事取得・保存（データベース）
   ↓
3. Gemini APIで分析
   - テーマ分類
   - 要約生成
   - 重要度判定
   ↓
4. 投稿キューに追加（承認待ち）
   ↓
5. 承認後、Blueskyに投稿
```

---

## 🎯 このプログラムの特徴

### ✅ 自動化
- 記事取得から投稿まで完全自動化
- スケジューラーで定期実行

### ✅ AI活用
- Gemini APIで高精度な分析
- 重要度の自動判定

### ✅ 柔軟性
- デモモードで安全にテスト
- 承認フローで品質管理
- 環境変数で設定変更

### ✅ スケーラブル
- Renderで簡単にデプロイ
- PostgreSQLで大量データに対応
- 複数のニュースサイトに対応

---

## 📝 使用例

### 1. WIRED記事TOP5を自動投稿
```bash
cd backend
python wired_bluesky_bot_advanced.py
```

毎朝8時に自動実行：
```bash
python wired_scheduler.py
```

### 2. 記事を取得して分析
```bash
curl -X POST http://localhost:8000/fetch/analyze
```

### 3. 投稿キューを確認
```bash
curl http://localhost:8000/post-queue
```

### 4. 記事を承認して投稿
```bash
curl -X POST http://localhost:8000/post-queue/1/approve
curl -X POST http://localhost:8000/post-queue/1/post \
  -H "Content-Type: application/json" \
  -d '{"confirm_password": "your_password"}'
```

---

## 🔐 セキュリティ機能

- **Basic認証**: フロントエンドへのアクセス制限
- **投稿確認パスワード**: 投稿時の二重確認
- **環境変数**: 機密情報の安全な管理

---

## 📚 ドキュメント

### セットアップ
- `LOCAL_SETUP.md` - ローカル開発環境のセットアップ
- `ENVIRONMENT_VARIABLES.md` - 環境変数の詳細

### デプロイ
- `RENDER_DEPLOYMENT_GUIDE.md` - Renderへのデプロイ手順
- `RENDER_STARTUP_FIX.md` - 起動時間の最適化

### WIRED Bot
- `README_WIRED_BOT.md` - WIRED Botの詳細ガイド
- `WIRED_BOT_QUICKSTART.md` - クイックスタート

---

## 🎓 このプログラムで学べること

1. **FastAPI**: モダンなPython Webフレームワーク
2. **AI API連携**: Gemini APIの活用方法
3. **ソーシャルメディアAPI**: Bluesky APIの使い方
4. **Webスクレイピング**: BeautifulSoupでのデータ取得
5. **スケジューラー**: 定期実行の実装
6. **クラウドデプロイ**: Renderでのデプロイ
7. **Next.js**: Reactフレームワーク
8. **データベース設計**: SQLAlchemyでのORM

---

## 💡 応用例

このプログラムをベースに、以下のような拡張が可能です：

- **他のニュースサイト対応**: TechCrunch, The Verge等
- **他のSNS対応**: Twitter/X, Mastodon等
- **画像生成**: DALL-E等で画像を生成して投稿
- **多言語対応**: 英語記事を日本語に翻訳
- **通知機能**: Slack, Discord等に通知
- **分析ダッシュボード**: より詳細な統計情報

---

## 📊 プロジェクト規模

- **バックエンド**: Python（FastAPI）
- **フロントエンド**: TypeScript（Next.js）
- **データベース**: SQLite（開発）/ PostgreSQL（本番）
- **総ファイル数**: 50+ファイル
- **コード行数**: 約5,000行

---

## 🎯 まとめ

**Weak Signals App**は、**AIを活用した記事分析・自動投稿システム**です。

- 📰 記事を自動取得
- 🤖 AIで分析
- 📤 Blueskyに自動投稿
- 🔄 定期実行で完全自動化

技術トレンドを追いかける人、ソーシャルメディア運用を自動化したい人、AI活用を学びたい人におすすめのプロジェクトです。

---

**作成日**: 2025年11月09日  
**バージョン**: 1.0.0  
**ライセンス**: MIT

