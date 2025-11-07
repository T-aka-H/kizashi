# Python バージョン指定

## 問題

atprotoライブラリ（0.0.45）はPython 3.13に対応していません。
Python 3.13を使用すると、ビルドエラーが発生します。

## 解決策

Python 3.11を使用するように設定します。

## 設定ファイル

### 1. render.yaml

`render.yaml`で既に設定済み：

```yaml
envVars:
  - key: PYTHON_VERSION
    value: 3.11.0
```

### 2. runtime.txt（追加）

プロジェクトルートに`runtime.txt`を作成：

```
python-3.11.0
```

### 3. backend/.python-version（追加）

バックエンドディレクトリに`.python-version`を作成：

```
3.11.0
```

## Renderでの確認

デプロイ後、Render Dashboardで確認：

1. `kizashi-backend` → Settings → Environment
2. `PYTHON_VERSION`が`3.11.0`に設定されているか確認

## ローカル開発環境

ローカルでもPython 3.11を使用することを推奨：

```bash
# pyenvを使用している場合
pyenv install 3.11.0
pyenv local 3.11.0

# 仮想環境を作成
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

## 確認方法

```bash
# Pythonバージョンを確認
python --version

# 3.11.xが表示されればOK
```

