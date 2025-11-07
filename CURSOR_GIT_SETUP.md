# CursorでGitリポジトリを設定する方法

## 方法1: コマンドパレットから設定

1. **コマンドパレットを開く**
   - Windows: `Ctrl + Shift + P`
   - Mac: `Cmd + Shift + P`

2. **Gitコマンドを検索**
   - `Git: Clone` と入力して選択
   - または `Git: Add Remote` と入力

3. **リポジトリURLを入力**
   - `https://github.com/yourusername/weak-signals-app.git`
   - または `git@github.com:yourusername/weak-signals-app.git`

## 方法2: ターミナルから設定

Cursorの統合ターミナル（`Ctrl + `` または `View → Terminal`）で実行：

### 既存のリポジトリにリモートを追加

```bash
# リモートを確認
git remote -v

# リモートを追加（まだない場合）
git remote add origin https://github.com/yourusername/weak-signals-app.git

# リモートを変更（既にある場合）
git remote set-url origin https://github.com/yourusername/weak-signals-app.git

# 確認
git remote -v
```

### 新規リポジトリを作成してプッシュ

```bash
# リポジトリを初期化
git init

# ファイルを追加
git add .

# 初回コミット
git commit -m "Initial commit"

# ブランチ名をmainに設定
git branch -M main

# リモートを追加
git remote add origin https://github.com/yourusername/weak-signals-app.git

# プッシュ
git push -u origin main
```

## 方法3: CursorのGitパネルから

1. **ソースコントロールパネルを開く**
   - 左サイドバーのGitアイコンをクリック
   - または `Ctrl + Shift + G`

2. **「...」メニューをクリック**
   - パネル上部の「...」をクリック

3. **「Remote」→「Add Remote」を選択**
   - リモート名: `origin`
   - URL: `https://github.com/yourusername/weak-signals-app.git`

## 方法4: GitHubでリポジトリを作成してから

1. **GitHubでリポジトリを作成**
   - [GitHub](https://github.com/new)で新しいリポジトリを作成
   - リポジトリ名: `weak-signals-app`（任意）

2. **GitHubが表示するコマンドを実行**
   - GitHubが表示する「…or push an existing repository from the command line」のコマンドをコピー
   - Cursorのターミナルで実行

```bash
git remote add origin https://github.com/yourusername/weak-signals-app.git
git branch -M main
git push -u origin main
```

## 現在のリモート設定を確認

```bash
# リモート一覧を表示
git remote -v

# 詳細情報を表示
git remote show origin
```

## よくある問題

### Q: 「remote origin already exists」エラー

**A:** 既存のリモートを変更：
```bash
git remote set-url origin https://github.com/yourusername/weak-signals-app.git
```

### Q: 認証エラーが出る

**A:** GitHubの認証方法を確認：
- HTTPS: Personal Access Tokenが必要
- SSH: SSH鍵を設定する必要がある

### Q: プッシュできない

**A:** 確認事項：
1. GitHubにリポジトリが存在するか
2. 認証情報が正しいか
3. ブランチ名が正しいか（`main` または `master`）

## 推奨設定

### .gitignoreの確認

プロジェクトルートに`.gitignore`があることを確認：

```bash
# .gitignoreが存在するか確認
ls -la .gitignore

# 内容を確認
cat .gitignore
```

### 初回プッシュ前の確認

```bash
# ステータス確認
git status

# コミット履歴確認
git log --oneline

# リモート確認
git remote -v
```

## 次のステップ

リポジトリを設定したら：

1. **変更をコミット**
   ```bash
   git add .
   git commit -m "Initial commit"
   ```

2. **プッシュ**
   ```bash
   git push -u origin main
   ```

3. **Renderでデプロイ**
   - Render Dashboardでリポジトリを接続
   - `render.yaml`が自動検出される

