@echo off
echo ====================================
echo WIRED記事TOP5投稿Bot - テスト実行
echo ====================================
echo.

cd /d "%~dp0backend"

echo [1/3] 環境変数をチェック中...
python -c "import os; from dotenv import load_dotenv; load_dotenv('../.env'); print('GEMINI_API_KEY:', 'OK' if os.getenv('GEMINI_API_KEY') else 'NOT SET'); print('BLUESKY_HANDLE:', os.getenv('BLUESKY_HANDLE', 'NOT SET')); print('POST_MODE:', os.getenv('POST_MODE', 'NOT SET'))"
echo.

echo [2/3] パッケージをチェック中...
python -c "import feedparser, google.generativeai, atproto, schedule; print('必要なパッケージがインストールされています')"
if errorlevel 1 (
    echo エラー: 必要なパッケージがインストールされていません
    echo pip install -r requirements.txt を実行してください
    pause
    exit /b 1
)
echo.

echo [3/3] ボットを実行中...
echo.
python wired_bluesky_bot_advanced.py

echo.
echo ====================================
echo テスト完了
echo ====================================
pause

