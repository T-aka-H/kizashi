@echo off
chcp 65001 >nul
title Weak Signals App - Backend Server

echo ========================================
echo   Weak Signals App - バックエンド起動
echo ========================================
echo.

REM プロジェクトルートに移動
cd /d "%~dp0"

REM バックエンドディレクトリに移動
cd backend

REM Pythonがインストールされているか確認
python --version >nul 2>&1
if errorlevel 1 (
    echo [エラー] Pythonがインストールされていません。
    echo Python 3.11以上をインストールしてください。
    pause
    exit /b 1
)

REM .envファイルの存在確認
if not exist "..\.env" (
    echo [警告] .envファイルが見つかりません。
    echo .env.exampleをコピーして.envファイルを作成し、GEMINI_API_KEYを設定してください。
    echo.
    pause
)

REM 仮想環境が存在する場合は有効化
if exist "..\venv\Scripts\activate.bat" (
    echo 仮想環境を有効化中...
    call ..\venv\Scripts\activate.bat
    echo 仮想環境のPythonバージョン:
    python --version
    echo.
)

REM 依存パッケージの確認（必要に応じてインストール）
echo 依存パッケージを確認中...
pip show google-generativeai >nul 2>&1
if errorlevel 1 (
    echo 依存パッケージをインストール中...
    echo [注意] psycopg2-binaryはスキップされます（ローカル開発ではSQLiteを使用）
    echo ホイール優先でインストールします...
    python -m pip install --only-binary=:all: -r requirements.txt
    if errorlevel 1 (
        echo [警告] --only-binaryで失敗しました。通常のインストールを試行します...
        pip install -r requirements.txt
        if errorlevel 1 (
            echo [エラー] 依存パッケージのインストールに失敗しました。
            pause
            exit /b 1
        )
    )
)

echo.
echo ========================================
echo   バックエンドサーバーを起動します
echo ========================================
echo.
echo APIドキュメント: http://localhost:8000/docs
echo ヘルスチェック: http://localhost:8000/
echo.
echo 停止するには Ctrl+C を押してください
echo.

REM サーバー起動
python main.py

pause

