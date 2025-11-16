"""
FastAPI メインアプリケーション（最小構成版）

【機能】
- WIRED RSSからの記事取得
- 未来の兆し生成
- WIRED Bot機能
"""
import os
import sys
import logging
import time
import threading
from pathlib import Path
from dotenv import load_dotenv

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# .envファイルを読み込む（ローカル開発用、ファイルが存在する場合のみ）
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.info(f"✅ .envファイルを読み込みました: {env_path}")
else:
    logger.info("📝 .envファイルが見つかりません（環境変数から直接取得します）")

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db, init_db
from gemini_analyzer import GeminiAnalyzer
from twitter_poster import SocialPoster
from article_fetcher import ArticleFetcher

# FastAPIアプリ初期化
app = FastAPI(title="WIRED Bot API", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 必要に応じて制限
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# グローバル変数
analyzer = None
poster = None
article_fetcher = ArticleFetcher()

# WIREDのRSS URL
WIRED_RSS_URL = "https://www.wired.com/feed/rss"


def initialize_app():
    """アプリケーションの初期化"""
    global analyzer, poster
    
    logger.info("🚀 アプリケーション初期化を開始...")
    
    # GeminiAnalyzer の初期化
    try:
        analyzer = GeminiAnalyzer()
        logger.info("✅ GeminiAnalyzer初期化成功")
    except Exception as e:
        logger.warning(f"⚠️ GeminiAnalyzer初期化エラー: {e}")
        analyzer = None

    # SocialPoster の初期化
    try:
        poster = SocialPoster()
        logger.info("✅ SocialPoster初期化成功")
    except Exception as e:
        logger.warning(f"⚠️ SocialPoster初期化エラー: {e}")
        poster = None
    
    logger.info("✅ アプリケーション初期化完了")


@app.on_event("startup")
async def startup_event():
    """FastAPIアプリ起動時の処理"""
    logger.info("🚀 FastAPI起動イベント開始...")
    
    # データベース初期化
    try:
        init_db()
        logger.info("✅ データベース初期化完了")
    except Exception as e:
        logger.error(f"⚠️ データベース初期化エラー: {e}", exc_info=True)
    
    # その他のコンポーネントを初期化
    initialize_app()
    
    logger.info("✅ FastAPI起動イベント完了")


# Pydanticモデル
class RSSFeedRequest(BaseModel):
    rss_url: str = WIRED_RSS_URL
    max_items: int = 20


class ThemeResearchRequest(BaseModel):
    themes: str  # カンマ区切りのテーマリスト


# APIエンドポイント
@app.get("/")
async def root():
    """ヘルスチェック"""
    return {
        "message": "WIRED Bot API",
        "status": "running",
        "features": ["WIRED RSS取得", "未来の兆し生成"]
    }


@app.get("/healthz")
async def health_check():
    """ヘルスチェックエンドポイント（Render用）"""
    return {
        "status": "ok",
        "components": {
            "analyzer": "available" if analyzer else "unavailable",
            "poster": "available" if poster else "unavailable"
        }
    }


@app.get("/health")
async def health_check_detailed(db: Session = Depends(get_db)):
    """詳細ヘルスチェックエンドポイント"""
    try:
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        logger.error(f"データベース接続エラー: {e}")
        db_status = "error"
    
    return {
        "status": "ok",
        "database": db_status,
        "environment": {
            "gemini_api_key_set": bool(os.getenv("GEMINI_API_KEY")),
            "bluesky_handle_set": bool(os.getenv("BLUESKY_HANDLE")),
            "post_mode": os.getenv("POST_MODE", "demo")
        },
        "components": {
            "analyzer": "available" if analyzer else "unavailable",
            "poster": "available" if poster else "unavailable"
        }
    }


@app.post("/fetch/wired-rss")
async def fetch_wired_rss(
    request: RSSFeedRequest,
    db: Session = Depends(get_db)
):
    """
    WIRED RSSから記事を取得
    
    【機能】
    - WIREDのRSSフィードから記事を取得
    - デフォルトでWIRED RSSを使用
    """
    if not analyzer:
        raise HTTPException(status_code=503, detail="GeminiAnalyzerが初期化されていません")
    
    try:
        # WIRED RSSから記事を取得
        rss_url = request.rss_url or WIRED_RSS_URL
        articles = article_fetcher.fetch_from_rss(rss_url, request.max_items)
        
        logger.info(f"✅ {len(articles)}件の記事を取得しました")
        
        return {
            "message": "WIRED記事取得完了",
            "fetched": len(articles),
            "articles": [
                {
                    "title": a.get("title"),
                    "url": a.get("url"),
                    "published_at": a.get("published_at").isoformat() if a.get("published_at") else None
                }
                for a in articles[:10]  # 最初の10件のみ返す
            ]
        }
    except Exception as e:
        logger.error(f"⚠️ WIRED RSS取得エラー: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"取得エラー: {str(e)}")


@app.post("/fetch/research")
async def fetch_by_research(
    request: ThemeResearchRequest,
    db: Session = Depends(get_db)
):
    """
    テーマに基づく「未来の兆し」を生成
    
    【機能】
    - Gemini APIを使用してテーマに基づく「未来の兆し」を生成
    - 生成された内容をBlueskyに自動投稿
    """
    if not analyzer:
        raise HTTPException(status_code=503, detail="GeminiAnalyzerが初期化されていません")
    
    try:
        # テーマに基づいて「未来の兆し」を生成
        themes_list = [t.strip() for t in request.themes.split(',') if t.strip()]
        generated_items = []
        
        for theme in themes_list:
            try:
                result = analyzer.generate_future_signal(theme)
                generated_items.append(result)
                logger.info(f"✅ テーマ '{theme}' の未来の兆しを生成")
            except Exception as e:
                logger.warning(f"⚠️ テーマ '{theme}' の未来の兆し生成エラー: {e}")
                continue
        
        if not generated_items:
            raise HTTPException(status_code=500, detail="未来の兆しの生成に失敗しました")
        
        # 生成された「未来の兆し」を処理
        processed_count = 0
        posted_count = 0
        
        for item in generated_items:
            title = item.get('title', '')
            summary = item.get('summary', '')
            future_signal = item.get('future_signal', '')
            
            if not title or not summary or not future_signal:
                logger.warning(f"⚠️ 不完全なデータをスキップ: {title}")
                continue
            
            # 投稿テキストを生成（未来の兆しを含める、URLなし）
            future_label = "🔮 未来の兆し: "
            
            # 280文字以内に収める
            post_text = f"{title}\n\n{summary}\n\n{future_label}{future_signal}"
            
            if len(post_text) > 280:
                # 未来の兆しを短縮
                base_length = len(f"{title}\n\n{summary}\n\n{future_label}")
                remaining_length = 280 - base_length
                if remaining_length > 0:
                    future_signal = future_signal[:remaining_length - 3] + "..."
                    post_text = f"{title}\n\n{summary}\n\n{future_label}{future_signal}"
                else:
                    # 要約を短縮
                    max_summary_length = 280 - len(title) - len(future_label) - 20
                    summary = summary[:max_summary_length - 3] + "..."
                    post_text = f"{title}\n\n{summary}\n\n{future_label}{future_signal[:50]}"
            
            # Blueskyに自動投稿
            if poster:
                try:
                    result = poster.post(post_text)
                    if result:
                        logger.info(f"✅ 自動投稿完了: {title[:50]}...")
                        posted_count += 1
                    else:
                        logger.warning(f"⚠️ 投稿失敗: {title[:50]}...")
                except Exception as e:
                    logger.error(f"⚠️ 自動投稿エラー ({title[:50]}...): {e}")
            else:
                logger.warning("⚠️ ソーシャルポスターが利用できません")
            
            processed_count += 1
        
        return {
            "message": "未来の兆し生成・投稿完了",
            "processed": processed_count,
            "posted": posted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"⚠️ エラー: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"エラー: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

