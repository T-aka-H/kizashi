# Weak Signals Frontend

Next.js 14を使用したフロントエンドアプリケーション

## セットアップ

### 1. 依存パッケージのインストール

```bash
cd frontend
npm install
# または
yarn install
```

### 2. 環境変数の設定

`.env.local`ファイルを作成（オプション）:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. 開発サーバー起動

```bash
npm run dev
# または
yarn dev
```

ブラウザで http://localhost:3000 を開きます。

## 機能

### ダッシュボード (`/`)
- 統計情報の表示
- 総記事数、投稿済み数、承認待ち数、テーマ数

### 記事一覧 (`/articles`)
- 記事の一覧表示
- テーマでフィルター
- 記事の分析実行
- 記事詳細表示

### 投稿キュー (`/queue`)
- 承認待ちの投稿一覧
- 投稿の承認・却下
- 直接投稿機能

### テーマ分析 (`/themes`)
- テーマ別の統計表示
- テーマごとの記事一覧
- 平均感情スコア・関連性スコア

## 技術スタック

- **Next.js 14** - Reactフレームワーク（App Router）
- **TypeScript** - 型安全性
- **Tailwind CSS** - スタイリング
- **Lucide React** - アイコン
- **Axios** - HTTPクライアント
- **date-fns** - 日付フォーマット

## プロジェクト構造

```
frontend/
├── app/                    # Next.js App Router
│   ├── page.tsx           # ダッシュボード
│   ├── articles/          # 記事一覧ページ
│   ├── queue/             # 投稿キューページ
│   ├── themes/            # テーマ分析ページ
│   ├── layout.tsx         # ルートレイアウト
│   └── globals.css        # グローバルスタイル
├── components/            # Reactコンポーネント
│   ├── Navigation.tsx     # ナビゲーション
│   ├── Dashboard.tsx      # ダッシュボード
│   ├── ArticleList.tsx    # 記事一覧
│   ├── PostApproval.tsx   # 投稿承認
│   └── ThemeSelector.tsx  # テーマ選択
└── lib/                   # ユーティリティ
    └── api.ts             # APIクライアント
```

## ビルド

```bash
npm run build
npm start
```

## デプロイ

Vercelへのデプロイが推奨されます：

```bash
npm install -g vercel
vercel
```

