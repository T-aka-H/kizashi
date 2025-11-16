# ✅ GitHubプッシュ前チェックリスト

## 🔒 セキュリティ確認

### ✅ .envファイルの除外確認

`.gitignore`ファイルを確認しました：

```gitignore
# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
```

**✅ 確認結果**: `.env`ファイルは正しく除外されています

---

## 📋 プッシュ前の最終確認

### 1. 機密情報の確認

以下のファイルが**含まれていない**ことを確認：

- [ ] `.env` - 環境変数（APIキー等）
- [ ] `.env.local`
- [ ] `*.db` - データベースファイル
- [ ] `*.sqlite` - SQLiteファイル
- [ ] `venv/` - 仮想環境
- [ ] `__pycache__/` - Pythonキャッシュ
- [ ] `node_modules/` - Node.js依存パッケージ

### 2. 含めるべきファイル

以下のファイルは**含める**必要があります：

- [x] `.gitignore` - Git除外設定
- [x] `README.md` - プロジェクト説明
- [x] `backend/` - バックエンドコード
- [x] `frontend/` - フロントエンドコード
- [x] `requirements.txt` - Python依存パッケージ
- [x] `package.json` - Node.js依存パッケージ
- [x] `render.yaml` - Renderデプロイ設定
- [x] ドキュメントファイル（`.md`）

---

## 🚀 プッシュ手順

### Step 1: 変更を確認

```bash
git status
```

**確認ポイント**:
- `.env`ファイルが表示されていないか
- 機密情報を含むファイルが含まれていないか

### Step 2: 変更をステージング

```bash
# すべての変更を追加（.gitignoreで除外されたファイルは自動的に除外される）
git add .

# または、個別に追加
git add backend/
git add frontend/
git add *.md
git add .gitignore
```

### Step 3: コミット

```bash
git commit -m "Add WIRED Bot and Render deployment support"
```

### Step 4: プッシュ

```bash
git push origin main
```

---

## ⚠️ 注意事項

### もし.envファイルが誤って追加されていた場合

**即座に対処**:

```bash
# .envファイルをGitから削除（ファイル自体は残る）
git rm --cached .env

# .gitignoreを確認して.envが含まれているか確認
# 含まれていなければ追加

# コミット
git commit -m "Remove .env from Git tracking"

# プッシュ
git push origin main
```

### 既に.envファイルがプッシュされてしまった場合

**重要**: APIキーを**すぐに無効化**して新しいキーを生成してください。

1. **Gemini APIキーを無効化**
   - https://makersuite.google.com/app/apikey
   - 該当キーを削除

2. **Blueskyアプリパスワードを削除**
   - Bluesky設定 → アプリパスワード
   - 該当パスワードを削除

3. **新しいキーを生成**
   - 新しいAPIキーを取得
   - 新しいアプリパスワードを作成

4. **Git履歴から削除**（上級者向け）
   ```bash
   # Git履歴から.envファイルを完全に削除
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   
   # 強制プッシュ（注意：他の人と共有しているリポジトリでは危険）
   git push origin --force --all
   ```

---

## ✅ 現在の状態確認

### Git Statusの結果

```
✅ .envファイルは表示されていません
✅ 機密情報を含むファイルは含まれていません
✅ .gitignoreが正しく設定されています
```

### 含まれるファイル（安全）

- ✅ ソースコード（`.py`, `.tsx`, `.ts`）
- ✅ 設定ファイル（`requirements.txt`, `package.json`）
- ✅ ドキュメント（`.md`）
- ✅ デプロイ設定（`render.yaml`）

### 除外されるファイル（安全）

- ✅ `.env` - 環境変数
- ✅ `*.db` - データベースファイル
- ✅ `venv/` - 仮想環境
- ✅ `__pycache__/` - Pythonキャッシュ
- ✅ `node_modules/` - Node.js依存パッケージ

---

## 🎯 結論

**✅ 安全にプッシュできます！**

`.env`ファイルは`.gitignore`で正しく除外されており、Git statusにも表示されていません。

---

## 📝 プッシュ後の確認

プッシュ後、GitHubで以下を確認：

1. **リポジトリのファイル一覧**
   - `.env`ファイルが表示されていないか確認

2. **コミット履歴**
   - `.env`ファイルが含まれていないか確認

3. **セキュリティ警告**
   - GitHubが機密情報を検出していないか確認

---

## 🔐 追加のセキュリティ対策

### GitHub Secrets（推奨）

GitHub Actionsを使用する場合、機密情報は「Secrets」に保存：

1. リポジトリ → Settings → Secrets and variables → Actions
2. 「New repository secret」をクリック
3. 機密情報を追加

### Render Environment Variables

Renderでは、環境変数を直接設定：

1. Render ダッシュボード → Web Service
2. 「Environment」タブ
3. 「Add Environment Variable」で追加

**✅ これが最も安全な方法です**

---

**作成日**: 2025年11月09日  
**ステータス**: ✅ プッシュ準備完了

