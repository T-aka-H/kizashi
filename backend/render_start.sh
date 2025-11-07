#!/bin/bash
# Render用の起動スクリプト

# データベースの初期化（初回のみ）
python -c "from database import init_db; init_db()"

# FastAPIサーバーを起動
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

