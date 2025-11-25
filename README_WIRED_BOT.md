# 📰 WIRED記事TOP5 Bluesky投稿Bot

WIREDの人気記事TOP5を毎朝8時にBlueskyに自動投稿するシステムです。

## ✨ 特徴

1. **自動記事取得**: WIREDのRSSフィードから最新記事を取得
2. **AI選定**: Gemini APIが技術トレンド・イノベーション基準でTOP5を判定
3. **日本語要約**: 各記事を日本語で要約（改良版）
4. **自動投稿**: Blueskyに整形して投稿
5. **スケジュール実行**: 毎朝8時に自動実行

## 📦 作成したファイル

| ファイル | 説明 |
|---------|------|
| `wired_bluesky_bot.py` | 基本版（RSSのsummaryを使用） |
| `wired_bluesky_bot_advanced.py` | 改良版（記事本文を取得して詳細な要約）|
| `wired_scheduler.py` | 毎朝8時に自動実行するスケジューラー |
| `.env.template` | 環境変数テンプレート |

## 🚀 セットアップ手順

### 1. 必要なパッケージのインストール

すでに `requirements.txt` があるので、インストール済みです。
もし追加で必要な場合：

```bash
cd C:\dev\wired
.\activate_venv.bat
pip install -r backend\requirements.txt
```

### 2. APIキーの取得

#### **Gemini API**
1. https://makersuite.google.com/app/apikey にアクセス
2. 「Create API Key」でキーを取得
3. 無料枠あり（1分あたり15リクエスト）

#### **Bluesky**
1. Blueskyアカウントを作成: https://bsky.app
2. 設定 → アプリパスワード → 新しいアプリパスワードを作成
3. パスワードを保存（後で使用）

### 3. 環境変数の設定

`.env` ファイルを作成します（まだない場合）：

```bash
# .env.templateをコピー
copy .env.template .env

# .envファイルを編集
notepad .env
```

以下の内容を設定：

```env
# Gemini API設定
GEMINI_API_KEY=あなたのGemini APIキー

# Bluesky設定
BLUESKY_HANDLE=あなたのハンドル.bsky.social
BLUESKY_PASSWORD=アプリパスワード

# 投稿モード (bluesky または demo)
POST_MODE=bluesky

# ボット設定
USE_ADVANCED_BOT=true  # true: 改良版、false: 基本版

# テストモード (true: 起動時に1回だけ実行、false: スケジュール実行)
TEST_MODE=false
```

### 4. テスト実行

#### デモモード（実際には投稿しない）

```bash
cd C:\dev\wired\backend
python wired_bluesky_bot.py
```

または改良版：

```bash
python wired_bluesky_bot_advanced.py
```

#### 本番モード（実際に投稿）

`.env` ファイルで `POST_MODE=bluesky` に変更してから：

```bash
python wired_bluesky_bot_advanced.py
```

### 5. 自動実行（毎朝8時）

#### スケジューラーを起動

```bash
cd C:\dev\wired\backend
python wired_scheduler.py
```

これで毎朝8時に自動的にWIRED記事TOP5がBlueskyに投稿されます。

#### バックグラウンドで実行（Windows）

タスクスケジューラーを使用：

1. 「タスクスケジューラー」を開く
2. 「タスクの作成」
3. トリガー: 毎日8:00
4. 操作: プログラムの開始
   - プログラム: `C:\dev\wired\venv\Scripts\python.exe`
   - 引数: `C:\dev\wired\backend\wired_scheduler.py`
   - 開始: `C:\dev\wired\backend`

## 🔧 設定オプション

### 環境変数

| 変数 | 説明 | デフォルト |
|------|------|-----------|
| `GEMINI_API_KEY` | Gemini APIキー | 必須 |
| `BLUESKY_HANDLE` | Blueskyハンドル | 必須 |
| `BLUESKY_PASSWORD` | Blueskyアプリパスワード | 必須 |
| `POST_MODE` | 投稿モード（bluesky/demo） | demo |
| `USE_ADVANCED_BOT` | 改良版を使用 | true |
| `TEST_MODE` | テストモード | false |

### ボットの違い

| 機能 | 基本版 | 改良版 |
|------|--------|--------|
| 記事取得 | RSSのみ | RSS + 本文取得 |
| 要約精度 | 普通 | 高い |
| 実行時間 | 速い | やや遅い |
| おすすめ | テスト用 | 本番用 |

## 📝 投稿例

**TOP5を個別に投稿します**（合計5つの投稿）

### 投稿1（1位の記事）
```
📰 WIRED TOP1 (11/09)

【AIが生成する新しいアート形式が美術界に革命】

📝 AI技術の進化により、従来のアート制作手法が根本的に変化。
アーティストとAIの協働が新しい創造性を生み出している。

💡 デジタルアートの民主化が進み、誰でもクリエイターになれる時代へ。

🔗 https://www.wired.com/story/ai-art-...
```

### 投稿2（2位の記事）
```
📰 WIRED TOP2 (11/09)

【量子コンピューターの最新ブレイクスルー】

📝 Googleが開発した新型量子プロセッサが従来比1000倍の性能を実現。
暗号技術や創薬分野への応用が期待される。

💡 10年以内に実用レベルの量子コンピューターが登場する可能性。

🔗 https://www.wired.com/story/quantum-...
```

（3位、4位、5位も同様に個別投稿）

**特徴:**
- ✅ 各記事を個別投稿（詳細な情報を掲載可能）
- ✅ 要旨とポイントで理解しやすい
- ✅ URLで詳細へアクセス可能
- ✅ 5秒間隔で投稿（スパム判定回避）

## 🐛 トラブルシューティング

### 「記事の取得に失敗しました」

- インターネット接続を確認
- WIREDのRSSフィード（https://www.wired.com/feed/rss）が利用可能か確認

### 「Gemini API エラー」

- `GEMINI_API_KEY` が正しく設定されているか確認
- APIキーが有効か確認
- レート制限に達していないか確認

### 「Bluesky投稿エラー」

- `BLUESKY_HANDLE` と `BLUESKY_PASSWORD` が正しく設定されているか確認
- アプリパスワードを使用しているか確認（通常のパスワードではない）
- `POST_MODE=bluesky` に設定されているか確認

### 「投稿が280文字を超える」

- ボットは自動的に280文字以内に収めます
- それでも問題がある場合は、タイトルの短縮処理を確認

## 📚 参考リンク

- [Gemini API ドキュメント](https://ai.google.dev/docs)
- [Bluesky API ドキュメント](https://docs.bsky.app/)
- [WIRED RSS フィード](https://www.wired.com/feed/rss)

## 🎯 次のステップ

- [ ] 投稿時刻をカスタマイズ
- [ ] 複数回投稿（朝・昼・夜）
- [ ] 画像付き投稿
- [ ] 他のメディア（TechCrunch等）にも対応
- [ ] Webダッシュボードで管理

## 💡 ヒント

1. **テストは必ずデモモードで**: `POST_MODE=demo` でテストしてから本番投稿
2. **APIレート制限に注意**: Gemini APIは無料枠で1分15リクエストまで
3. **記事が重複しないよう**: 毎日異なる時刻に実行すると新しい記事が投稿される
4. **ログを確認**: 実行ログを確認して問題がないか定期的にチェック

## ❓ FAQ

**Q: 投稿時刻を変更したい**
A: `wired_scheduler.py` の `schedule.every().day.at("08:00")` を変更

**Q: TOP5じゃなくてTOP3にしたい**
A: `wired_bluesky_bot.py` の `create_post_text` メソッドで `[:5]` を `[:3]` に変更

**Q: 他のニュースサイトにも対応したい**
A: `WIRED_RSS_URL` を変更するか、新しいBotクラスを作成

**Q: 要約をもっと短く/長くしたい**
A: プロンプトの「100文字以内」を調整

## 📄 ライセンス

このプロジェクトは既存のWIREDプロジェクトの一部として作成されています。

---

**作成日**: 2025年11月09日
**最終更新**: 2025年11月09日

