# 📦 CursorからGitリポジトリを新規作成する方法

## ✅ 現在の状況

あなたのプロジェクトは**既にGitリポジトリとして初期化されています**。

```bash
git status
# → On branch main
# → Your branch is up to date with 'origin/main'
```

つまり、**新規作成する必要はありません**。既存のリポジトリにプッシュするだけでOKです。

---

## 🆕 もし新規プロジェクトでリポジトリを作成する場合

### 方法1: Cursorの統合ターミナルから（推奨）

1. **Cursorでターミナルを開く**
   - `Ctrl + `` （バッククォート）
   - または `View → Terminal`

2. **プロジェクトディレクトリに移動**
   ```bash
   cd C:\dev\your-project
   ```

3. **Gitリポジトリを初期化**
   ```bash
   git init
   ```

4. **ファイルを追加**
   ```bash
   git add .
   ```

5. **初回コミット**
   ```bash
   git commit -m "Initial commit"
   ```

6. **ブランチ名をmainに設定**
   ```bash
   git branch -M main
   ```

---

### 方法2: CursorのGitパネルから

1. **ソースコントロールパネルを開く**
   - 左サイドバーのGitアイコン（📁）をクリック
   - または `Ctrl + Shift + G`

2. **「Initialize Repository」をクリック**
   - パネル上部に「Initialize Repository」ボタンが表示される
   - クリックすると自動的に`git init`が実行される

3. **ファイルをステージング**
   - 変更されたファイルの横にある「+」をクリック
   - または「Stage All Changes」をクリック

4. **コミット**
   - コミットメッセージを入力
   - 「✓ Commit」ボタンをクリック

---

### 方法3: コマンドパレットから

1. **コマンドパレットを開く**
   - `Ctrl + Shift + P`（Windows）
   - `Cmd + Shift + P`（Mac）

2. **「Git: Initialize Repository」を検索**
   - 入力して選択

3. **プロジェクトフォルダを選択**
   - 現在のフォルダが自動的に選択される

---

## 🔗 GitHubリポジトリと接続する方法

### Step 1: GitHubでリポジトリを作成

1. **GitHubにアクセス**
   - https://github.com/new

2. **リポジトリを作成**
   - Repository name: `wired-bot`（任意の名前）
   - Description: 任意
   - Public / Private: 選択
   - **「Initialize this repository with a README」はチェックしない**（既にローカルにコードがあるため）

3. **「Create repository」をクリック**

---

### Step 2: ローカルリポジトリと接続

#### 方法A: GitHubが表示するコマンドを使用（推奨）

GitHubでリポジトリを作成すると、以下のようなコマンドが表示されます：

```bash
git remote add origin https://github.com/your-username/wired-bot.git
git branch -M main
git push -u origin main
```

**Cursorのターミナルで実行**：

```bash
# 1. リモートを追加
git remote add origin https://github.com/your-username/wired-bot.git

# 2. ブランチ名を確認（既にmainなら不要）
git branch -M main

# 3. プッシュ
git push -u origin main
```

#### 方法B: CursorのGitパネルから

1. **ソースコントロールパネルを開く**（`Ctrl + Shift + G`）

2. **「...」メニューをクリック**
   - パネル上部の「...」をクリック

3. **「Remote」→「Add Remote」を選択**
   - Remote name: `origin`
   - Remote URL: `https://github.com/your-username/wired-bot.git`

4. **「OK」をクリック**

5. **プッシュ**
   - 「...」メニュー → 「Push」→ 「origin」→ 「main」

---

## 🔍 現在のリポジトリの状態確認

### リモート設定を確認

```bash
git remote -v
```

**出力例**:
```
origin  https://github.com/your-username/wired-bot.git (fetch)
origin  https://github.com/your-username/wired-bot.git (push)
```

### ブランチを確認

```bash
git branch -a
```

**出力例**:
```
* main
  remotes/origin/main
```

---

## 📝 あなたの場合（既存リポジトリ）

現在のプロジェクトは既にGitリポジトリとして初期化されているので：

### 1. 変更をコミット

```bash
git add .
git commit -m "Add WIRED Bot and Render deployment support"
```

### 2. プッシュ

```bash
git push origin main
```

**これで完了です！**

---

## ⚠️ よくある問題

### Q: 「remote origin already exists」エラー

**A:** 既存のリモートを変更：

```bash
git remote set-url origin https://github.com/your-username/new-repo.git
```

### Q: 認証エラー

**A:** GitHubの認証方法を確認：

- **HTTPS**: Personal Access Tokenが必要
  - Settings → Developer settings → Personal access tokens → Generate new token
- **SSH**: SSH鍵を設定
  - Settings → SSH and GPG keys → New SSH key

### Q: プッシュできない

**A:** 確認事項：

1. GitHubにリポジトリが存在するか
2. 認証情報が正しいか
3. ブランチ名が正しいか（`main` または `master`）

---

## 🎯 まとめ

### 新規プロジェクトの場合

1. **Cursorのターミナルで `git init`**
2. **GitHubでリポジトリを作成**
3. **`git remote add origin` で接続**
4. **`git push -u origin main` でプッシュ**

### あなたの場合（既存リポジトリ）

1. **`git add .` で変更を追加**
2. **`git commit -m "..."` でコミット**
3. **`git push origin main` でプッシュ**

**✅ これで完了です！**

---

**作成日**: 2025年11月09日

