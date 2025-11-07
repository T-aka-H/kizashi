# Bluesky セットアップガイド

Blueskyは無料で利用できる分散型ソーシャルネットワークです。このガイドでは、Weak Signals AppでBlueskyを使用するためのセットアップ手順を説明します。

## 🦋 Blueskyの特徴

- ✅ **無料**: 完全無料で利用可能
- ✅ **投稿制限なし**: 月間投稿数の制限なし
- ✅ **300文字**: 長文投稿が可能
- ✅ **セットアップ簡単**: 5分でセットアップ完了
- ✅ **API制限緩い**: レート制限が緩い

## 📋 セットアップ手順

### ステップ1: Blueskyアカウントを作成

1. [https://bsky.app](https://bsky.app) にアクセス
2. 「Sign up」をクリック
3. メールアドレスまたは電話番号でアカウント作成
4. ユーザー名を設定（例: `yourname.bsky.social`）

### ステップ2: アプリパスワードを作成

1. Blueskyにログイン
2. 設定（Settings）→「App passwords」を開く
3. 「Add App Password」をクリック
4. 名前を入力（例: "Weak Signals App"）
5. 生成されたパスワードをコピー（`xxxx-xxxx-xxxx-xxxx`形式）

**重要**: このパスワードは一度しか表示されません。必ず保存してください。

### ステップ3: 環境変数を設定

`.env`ファイルに以下を追加：

```env
# 投稿モード設定
POST_MODE=bluesky

# Bluesky認証情報
BLUESKY_HANDLE=yourname.bsky.social
BLUESKY_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

### ステップ4: 依存パッケージをインストール

```bash
cd backend
pip install -r requirements.txt
```

`atproto`パッケージがインストールされます。

### ステップ5: テスト実行

```bash
python test_backend.py
```

成功すると：

```
✅ Bluesky接続成功: @yourname.bsky.social
📱 投稿モード: BLUESKY
✅ BLUESKY認証成功: @yourname.bsky.social
```

## 🧪 テスト投稿

### Pythonシェルから

```python
from twitter_poster import SocialPoster

poster = SocialPoster()
result = poster.post("テスト投稿 🔮 #未来の兆し")
print(result)
```

### デモモードでテスト

環境変数を設定せずに実行すると、デモモードで動作します：

```env
POST_MODE=demo
```

デモモードでは実際には投稿せず、プレビューを表示します：

```
【デモモード: BLUESKY 投稿プレビュー】
==================================================
テスト投稿 🔮 #未来の兆し
==================================================
文字数: 15 / 300
```

## 🔄 投稿モードの切り替え

環境変数`POST_MODE`で切り替え可能：

- `bluesky` - Blueskyに投稿
- `twitter` - X (Twitter)に投稿
- `demo` - デモモード（実際には投稿しない）

## 📝 文字数制限

- **Bluesky**: 300文字
- **X (Twitter)**: 280文字

自動的に文字数制限に合わせて調整されます。

## 🚨 トラブルシューティング

### 認証エラー

```
⚠️ Bluesky初期化エラー: ...
```

**解決方法:**
1. `BLUESKY_HANDLE`が正しいか確認（`@`は不要）
2. `BLUESKY_PASSWORD`が正しいか確認（アプリパスワードを使用）
3. アプリパスワードが有効か確認

### パッケージエラー

```
ImportError: atprotoパッケージがインストールされていません
```

**解決方法:**
```bash
pip install atproto
```

### 投稿エラー

```
⚠️ Bluesky投稿エラー: ...
```

**解決方法:**
1. インターネット接続を確認
2. Blueskyのサービス状態を確認
3. 文字数制限（300文字）を確認

## 📚 参考リンク

- [Bluesky公式サイト](https://bsky.app)
- [atproto SDK (Python)](https://github.com/MarshalX/atproto)
- [Bluesky API Documentation](https://docs.bsky.app)

## 💡 ヒント

1. **デモモードでテスト**: まずデモモードで動作確認してから、実際の投稿を試す
2. **アプリパスワード**: 通常のパスワードではなく、必ずアプリパスワードを使用
3. **文字数**: Blueskyは300文字まで投稿可能なので、より詳細な投稿が可能
4. **レート制限**: Blueskyのレート制限は緩いため、頻繁な投稿も可能

## 🎉 次のステップ

セットアップが完了したら：

1. 記事を取得して分析
2. 投稿キューに追加
3. 承認して投稿

自動化の設定は`scheduler.py`を参照してください。

