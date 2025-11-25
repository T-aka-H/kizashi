@echo off
chcp 65001 >nul
title Weak Signals App - Python 3.11用セットアップ

echo ========================================
echo   Weak Signals App - Python 3.11用セットアップ
echo ========================================
echo.

REM プロジェクトルートに移動
cd /d "%~dp0"

echo このスクリプトは、Python 3.11を使用してセットアップを行います。
echo.

REM Python 3.11の確認
echo Python 3.11の確認中...
python3.11 --version >nul 2>&1
if errorlevel 1 (
    python --version | findstr /R "^Python 3\.11" >nul
    if errorlevel 1 (
        echo [エラー] Python 3.11が見つかりません。
        echo.
        echo Python 3.11をインストールしてください:
        echo https://www.python.org/downloads/release/python-3119/
        echo.
        echo インストール後、python3.11コマンドが使用できることを確認してください。
        pause
        exit /b 1
    )
    set PYTHON_CMD=python
) else (
    set PYTHON_CMD=python3.11
    %PYTHON_CMD% --version
    echo OK
)

echo.
echo ========================================
echo   仮想環境の作成
echo ========================================
echo.

REM 既存の仮想環境を削除（オプション）
if exist "venv" (
    echo 既存の仮想環境が見つかりました。
    set /p REMOVE_VENV="削除して再作成しますか？ (y/n): "
    if /i "%REMOVE_VENV%"=="y" (
        echo 仮想環境を削除中...
        rmdir /s /q venv
        echo 削除完了
    )
)

REM 仮想環境を作成
if not exist "venv" (
    echo 仮想環境を作成中...
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo [エラー] 仮想環境の作成に失敗しました。
        pause
        exit /b 1
    )
    echo 仮想環境を作成しました
) else (
    echo 仮想環境は既に存在します
)

echo.
echo ========================================
echo   仮想環境の有効化とパッケージインストール
echo ========================================
echo.

REM 仮想環境を有効化
echo 仮想環境を有効化中...
call venv\Scripts\activate.bat

REM Pythonバージョンの確認
python --version
echo.

REM 依存パッケージのインストール
echo 依存パッケージをインストール中...
cd backend
echo pipをアップグレード中...
python -m pip install --upgrade pip
echo.
echo 依存パッケージをインストール中（ホイール優先）...
python -m pip install --only-binary=:all: -r requirements.txt
if errorlevel 1 (
    echo.
    echo [警告] --only-binaryで失敗しました。通常のインストールを試行します...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [エラー] 依存パッケージのインストールに失敗しました。
        cd ..
        pause
        exit /b 1
    )
)
cd ..
echo OK
echo.

REM フロントエンドの依存パッケージインストール
echo フロントエンドの依存パッケージをインストール中...
cd frontend
call npm install
if errorlevel 1 (
    echo [エラー] 依存パッケージのインストールに失敗しました。
    cd ..
    pause
    exit /b 1
)
cd ..
echo OK
echo.

echo ========================================
echo   セットアップ完了
echo ========================================
echo.
echo 次のステップ:
echo 1. .envファイルにOPENAI_API_KEYを設定してください
echo 2. start_all.batをダブルクリックしてアプリを起動してください
echo.
echo [注意] 仮想環境を使用する場合:
echo   - start_backend.batとstart_frontend.batは自動的に仮想環境を有効化します
echo   - 手動で有効化する場合: venv\Scripts\activate
echo.
pause

