@echo off
chcp 65001 >nul
title Weak Signals App - 起動スクリプト

echo ========================================
echo   Weak Signals App - 全体起動
echo ========================================
echo.
echo バックエンドとフロントエンドを起動します...
echo.

REM プロジェクトルートに移動
cd /d "%~dp0"

REM バックエンドを別ウィンドウで起動
echo バックエンドを起動中...
start "Weak Signals Backend" cmd /k "start_backend.bat"

REM 少し待機
timeout /t 3 /nobreak >nul

REM フロントエンドを別ウィンドウで起動
echo フロントエンドを起動中...
start "Weak Signals Frontend" cmd /k "start_frontend.bat"

echo.
echo ========================================
echo   起動完了
echo ========================================
echo.
echo バックエンド: http://localhost:8000/docs
echo フロントエンド: http://localhost:3000
echo.
echo 各ウィンドウで Ctrl+C を押すと停止します
echo.
echo このウィンドウは閉じても問題ありません
echo.
pause

