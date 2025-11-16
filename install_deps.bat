@echo off
chcp 65001 >nul
title Weak Signals App - 依存パッケージ再インストール

echo ========================================
echo   依存パッケージの再インストール
echo ========================================
echo.

REM プロジェクトルートに移動
cd /d "%~dp0"

REM 仮想環境が存在する場合は有効化
if exist "venv\Scripts\activate.bat" (
    echo 仮想環境を有効化中...
    call venv\Scripts\activate.bat
    python --version
    echo.
) else (
    echo [警告] 仮想環境が見つかりません。
    echo setup.batまたはsetup_python311.batを先に実行してください。
    pause
    exit /b 1
)

cd backend

echo pipをアップグレード中...
python -m pip install --upgrade pip
echo.

echo 依存パッケージをインストール中（ホイール優先）...
echo [注意] lxml 6.0.2以上を使用します（Python 3.13対応）
echo.

REM constraints.txtを使用してlxmlを固定
if exist "constraints.txt" (
    echo constraints.txtを使用してインストール...
    python -m pip install --only-binary=:all: -r requirements.txt -c constraints.txt
) else (
    python -m pip install --only-binary=:all: -r requirements.txt
)

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

echo.
echo ========================================
echo   インストール完了
echo ========================================
echo.
echo インストールされたパッケージを確認:
pip list | findstr "lxml"
echo.
pause

