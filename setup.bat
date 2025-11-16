@echo off
chcp 65001 >nul
title Weak Signals App - セットアップ

echo ========================================
echo   Weak Signals App - 初期セットアップ
echo ========================================
echo.

REM プロジェクトルートに移動
cd /d "%~dp0"

echo このスクリプトは、Weak Signals Appの初期セットアップを行います。
echo.

REM Pythonの確認
echo [1/5] Pythonの確認中...
python --version >nul 2>&1
if errorlevel 1 (
    echo [エラー] Pythonがインストールされていません。
    echo Python 3.11または3.12をインストールしてください: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Pythonバージョンを取得してチェック
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo 検出されたPythonバージョン: %PYTHON_VER%

REM Python 3.13の場合は警告
echo %PYTHON_VER% | findstr /R "^3\.13" >nul
if not errorlevel 1 (
    echo.
    echo [警告] Python 3.13が検出されました。
    echo atprotoライブラリがPython 3.13に対応していない可能性があります。
    echo.
    echo 推奨される対応:
    echo 1. Python 3.11または3.12を使用する（推奨）
    echo 2. または、Python 3.13で続行する（エラーが発生する可能性があります）
    echo.
    set /p CONTINUE="Python 3.13で続行しますか？ (y/n): "
    if /i not "%CONTINUE%"=="y" (
        echo.
        echo Python 3.11または3.12をインストールしてから、再度実行してください。
        echo Python 3.11: https://www.python.org/downloads/release/python-3119/
        echo Python 3.12: https://www.python.org/downloads/release/python-3120/
        pause
        exit /b 1
    )
    echo.
)

REM Python 3.11または3.12の推奨メッセージ
echo %PYTHON_VER% | findstr /R "^3\.1[12]" >nul
if not errorlevel 1 (
    echo OK - 推奨バージョンです
) else (
    echo %PYTHON_VER% | findstr /R "^3\." >nul
    if not errorlevel 1 (
        echo [注意] Python 3.11または3.12の使用を推奨します
    )
)
echo.

REM Node.jsの確認
echo [2/5] Node.jsの確認中...
node --version >nul 2>&1
if errorlevel 1 (
    echo [エラー] Node.jsがインストールされていません。
    echo Node.js 20.x以上をインストールしてください: https://nodejs.org/
    pause
    exit /b 1
)
node --version
echo OK
echo.

REM .envファイルの確認
echo [3/5] 環境変数ファイルの確認中...
if not exist ".env" (
    echo .envファイルが見つかりません。
    if exist ".env.example" (
        echo .env.exampleをコピーして.envファイルを作成します...
        copy .env.example .env >nul
        echo .envファイルを作成しました。
        echo.
        echo [重要] .envファイルを編集して、GEMINI_API_KEYを設定してください。
        echo.
        notepad .env
    ) else (
        echo [警告] .env.exampleファイルが見つかりません。
        echo 手動で.envファイルを作成してください。
    )
) else (
    echo .envファイルが見つかりました。
)
echo.

REM バックエンドの依存パッケージインストール
echo [4/5] バックエンドの依存パッケージをインストール中...
cd backend
echo.
echo [注意] psycopg2-binaryはスキップされます（ローカル開発ではSQLiteを使用）
echo 本番環境でPostgreSQLを使用する場合は、requirements-prod.txtを使用してください
echo.
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
echo [5/5] フロントエンドの依存パッケージをインストール中...
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
echo 1. .envファイルにGEMINI_API_KEYを設定してください
echo 2. start_all.batをダブルクリックしてアプリを起動してください
echo.
pause

