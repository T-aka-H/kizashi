"""
FastAPI メインアプリケーション

【Render デプロイ対応】
- 環境変数は Render の Environment Variables から取得
- .env ファイルが存在しない場合でもエラーにならない
- Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
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
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# .envファイルを読み込む（ローカル開発用、ファイルが存在する場合のみ）
# Render では環境変数が直接設定されるため、.env ファイルは不要
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.info(f"✅ .envファイルを読み込みました: {env_path}")
else:
    logger.info("📝 .envファイルが見つかりません（環境変数から直接取得します）")

# ↓ ここから既存のimport
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from database import get_db, init_db, create_article, get_article_by_url, update_article_analysis
from database import add_to_post_queue, get_pending_posts
from gemini_analyzer import GeminiAnalyzer
from twitter_poster import SocialPoster
from article_fetcher import ArticleFetcher, RSSFeedManager, get_default_feed_manager
from url_shortener import URLShortener
from auth import BasicAuthMiddleware, AUTH_ENABLED, verify_post_password
from models import Article, PostQueue
from scheduler import ArticleScheduler

# FastAPIアプリ初期化
app = FastAPI(title="WIRED Bot API", version="1.0.0")

# CORS設定（必ず最初に追加、順序重要）
# 401/403エラーでもCORSヘッダが付くように、Basic認証より前に配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://kizashi-frontend.onrender.com",  # 本番環境のフロントエンド
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic認証ミドルウェア（CORSより後に追加、OPTIONSはスキップ）
if AUTH_ENABLED:
    app.add_middleware(BasicAuthMiddleware)
    print("🔐 Basic認証が有効です")

# データベース初期化は startup イベントで実行
# init_db()  # ← コメントアウト（後で startup イベントで実行）

# アナライザーとポスターのインスタンス（グローバル変数として初期化）
analyzer = None
poster = None
scheduler = None
_scheduler_thread = None

# 初期化フラグ（二重実行防止）
_initialized = False
_startup_complete = False

def initialize_app():
    """
    アプリケーションの初期化（一度だけ実行）
    
    【エラーハンドリング】
    - 各コンポーネントの初期化に失敗してもアプリは起動し続ける
    - エラーはログに記録され、該当機能のみが無効化される
    - Render では環境変数が正しく設定されていることが前提
    """
    global analyzer, poster, scheduler, _scheduler_thread, _initialized
    
    if _initialized:
        logger.info("既に初期化済みです")
        return  # 既に初期化済み
    
    logger.info("🚀 アプリケーション初期化を開始...")
    
    # 1. GeminiAnalyzer の初期化
    try:
        analyzer = GeminiAnalyzer()
        logger.info("✅ GeminiAnalyzer初期化成功")
    except ValueError as e:
        # 環境変数が設定されていない場合
        logger.warning(f"⚠️ GeminiAnalyzer初期化スキップ: {e}")
        logger.warning("→ GEMINI_API_KEY が設定されていません")
        analyzer = None
    except Exception as e:
        logger.error(f"⚠️ GeminiAnalyzer初期化エラー: {e}", exc_info=True)
        analyzer = None

    # 2. SocialPoster の初期化
    try:
        poster = SocialPoster()
        logger.info("✅ SocialPoster初期化成功")
    except Exception as e:
        logger.warning(f"⚠️ SocialPoster初期化エラー: {e}")
        logger.warning("→ POST_MODE=demo で起動するか、Bluesky認証情報を確認してください")
        poster = None

    # 3. WIRED Botスケジューラーの初期化と起動（Render前提）
    # 環境変数 DISABLE_WIRED_SCHEDULER=true で無効化可能
    disable_wired_scheduler = os.getenv("DISABLE_WIRED_SCHEDULER", "false").lower() == "true"
    
    if disable_wired_scheduler:
        logger.info("📝 WIRED Botスケジューラーは無効化されています（DISABLE_WIRED_SCHEDULER=true）")
    else:
        # WIRED Botスケジューラーをバックグラウンドで起動
        logger.info("⏳ WIRED Botスケジューラーを起動します...")
        threading.Thread(target=_start_wired_scheduler_delayed, daemon=True, name="WiredSchedulerStarter").start()
    
    # 標準スケジューラーは無効化
    scheduler = None
    
    _initialized = True
    logger.info("✅ アプリケーション初期化完了")


def _start_wired_scheduler_delayed():
    """
    WIRED Botスケジューラーを遅延起動（30秒後）
    
    【Render前提】
    - PCを起動していないときでも投稿できるように、RenderのWeb Service内で実行
    - 3時間に1回WIRED記事TOP5を自動投稿
    """
    time.sleep(30)  # 30秒待機（起動時間短縮のため）
    
    logger.info("🚀 WIRED Botスケジューラー起動を開始...")
    
    try:
        import schedule
        
        # 基本版か改良版かを選択
        use_advanced = os.getenv("USE_ADVANCED_BOT", "true").lower() == "true"
        
        if use_advanced:
            from wired_bluesky_bot_advanced import WiredBlueskyBotAdvanced as WiredBot
            bot_name = "改良版"
        else:
            from wired_bluesky_bot import WiredBlueskyBot as WiredBot
            bot_name = "基本版"
        
        def wired_job():
            """WIRED Botを実行するジョブ"""
            logger.info(f"⏰ WIRED Bot実行開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            try:
                bot = WiredBot()
                bot.run()
                logger.info("✅ WIRED Bot実行完了")
            except Exception as e:
                logger.error(f"⚠️ WIRED Bot実行エラー: {e}", exc_info=True)
        
        # 3時間に1回実行
        schedule.every(3).hours.do(wired_job)
        logger.info(f"✅ WIRED Botスケジューラー起動完了（3時間に1回、{bot_name}）")
        
        # スケジューラーをバックグラウンドで実行
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # 1分ごとにチェック
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True, name="WiredSchedulerThread")
        scheduler_thread.start()
        logger.info("✅ WIRED Botスケジューラースレッド起動完了")
        
        # テストモードの場合は即座に1回実行
        test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
        if test_mode:
            logger.info("🧪 テストモード: 今すぐ1回実行します")
            wired_job()
        
    except Exception as e:
        logger.error(f"⚠️ WIRED Botスケジューラー起動エラー: {e}", exc_info=True)
        logger.warning("→ WIRED Botスケジューラーなしで動作を続行します")


@app.on_event("startup")
async def startup_event():
    """
    FastAPIアプリ起動時の処理
    
    【最適化】
    - データベース初期化を startup イベントで実行
    - 非同期で処理されるため、起動時間が短縮される
    """
    global _startup_complete
    
    logger.info("🚀 FastAPI起動イベント開始...")
    
    # データベース初期化
    try:
        init_db()
        logger.info("✅ データベース初期化完了")
    except Exception as e:
        logger.error(f"⚠️ データベース初期化エラー: {e}", exc_info=True)
        # データベースエラーでもアプリは起動を続行
    
    # その他のコンポーネントを初期化
    initialize_app()
    
    _startup_complete = True
    logger.info("✅ FastAPI起動イベント完了")


# アプリ起動時の初期化はstartupイベントで実行
# initialize_app()  # ← コメントアウト（startupイベントで実行）

# 記事取得のインスタンス
article_fetcher = ArticleFetcher()

# WIREDのRSS URL
WIRED_RSS_URL = "https://www.wired.com/feed/rss"


# Pydanticモデル
class ArticleCreate(BaseModel):
    url: str
    title: str
    content: Optional[str] = None
    published_at: Optional[datetime] = None


class RSSFeedRequest(BaseModel):
    rss_url: Optional[str] = None  # デフォルトでWIRED RSSを使用
    max_items: int = 20


class URLFetchRequest(BaseModel):
    urls: List[str]


class ThemeResearchRequest(BaseModel):
    themes: str  # カンマ区切りのテーマリスト（例: "AI, ブロックチェーン, 量子コンピュータ"）


class PostRequest(BaseModel):
    confirm_password: str  # 投稿確認パスワード


class ArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    url: str
    title: str
    theme: Optional[str] = None
    summary: Optional[str] = None
    is_posted: bool


class PostQueueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    article_id: int
    post_text: str
    status: str
    created_at: datetime


# APIエンドポイント
@app.get("/")
async def root():
    """ヘルスチェック"""
    return {
        "message": "WIRED Bot API",
        "status": "running",
        "features": ["WIRED RSS取得", "未来の兆し生成"]
    }


# 記事管理機能は削除（WIRED RSSと未来の兆し生成のみ使用）
# @app.post("/articles", ...) - 削除
# @app.get("/articles", ...) - 削除
# @app.post("/articles/{article_id}/analyze", ...) - 削除
# @app.get("/post-queue", ...) - 削除
# @app.post("/post-queue/{queue_id}/approve", ...) - 削除
# @app.post("/post-queue/{queue_id}/post", ...) - 削除


@app.api_route("/healthz", methods=["GET", "HEAD"])
async def health_check():
    """
    ヘルスチェックエンドポイント（Render Health Check用）
    
    【仕様】
    - アプリが起動していれば常に 200 OK を返す
    - 各コンポーネントの状態も含める（オプション）
    - Render の Health Check Path に設定: /healthz
    - GET と HEAD メソッドの両方に対応（監視サービス用）
    """
    return {
        "status": "ok",
        "components": {
            "analyzer": "available" if analyzer else "unavailable",
            "poster": "available" if poster else "unavailable",
            "scheduler": "running" if scheduler and _scheduler_thread and _scheduler_thread.is_alive() else "stopped"
        }
    }


@app.get("/test/wired-bot")
@app.post("/test/wired-bot")
async def test_wired_bot():
    """
    動作確認用: WIRED Botを即座に実行
    
    【用途】
    - デプロイ後の動作確認
    - 手動でのテスト実行
    - ブラウザから簡単にアクセス可能（GET/POST両対応）
    
    【注意】
    - 実際にBlueskyに投稿されます（POST_MODE=blueskyの場合）
    - テスト実行後、スケジューラーは通常通り動作します
    
    【使い方】
    - ブラウザ: https://your-app.onrender.com/test/wired-bot
    - curl: curl -X POST https://your-app.onrender.com/test/wired-bot
    """
    logger.info("🧪 WIRED Botテスト実行開始（手動）")
    
    try:
        # 基本版か改良版かを選択
        use_advanced = os.getenv("USE_ADVANCED_BOT", "true").lower() == "true"
        
        if use_advanced:
            from wired_bluesky_bot_advanced import WiredBlueskyBotAdvanced as WiredBot
            bot_name = "改良版"
        else:
            from wired_bluesky_bot import WiredBlueskyBot as WiredBot
            bot_name = "基本版"
        
        logger.info(f"🤖 WIRED Bot ({bot_name}) を実行します...")
        
        # WIRED Botを実行
        bot = WiredBot()
        bot.run()
        
        logger.info("✅ WIRED Botテスト実行完了")
        
        return {
            "status": "success",
            "message": f"WIRED Bot ({bot_name}) の実行が完了しました",
            "timestamp": datetime.now().isoformat(),
            "note": "Blueskyで投稿を確認してください（POST_MODE=blueskyの場合）"
        }
        
    except Exception as e:
        logger.error(f"⚠️ WIRED Botテスト実行エラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"WIRED Bot実行エラー: {str(e)}"
        )


@app.get("/health")
async def health_check_detailed(db: Session = Depends(get_db)):
    """
    詳細ヘルスチェックエンドポイント（監視用）
    
    【仕様】
    - データベース接続状態も確認
    - 環境変数の設定状態を確認
    - より詳細な情報を返す
    """
    try:
        # データベース接続テスト
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
            "post_mode": os.getenv("POST_MODE", "demo"),
            "scheduler_enabled": os.getenv("DISABLE_SCHEDULER", "false") != "true"
        },
        "components": {
            "analyzer": "available" if analyzer else "unavailable",
            "poster": "available" if poster else "unavailable",
            "scheduler": "running" if scheduler and _scheduler_thread and _scheduler_thread.is_alive() else "stopped"
        }
    }


# 統計情報機能は削除（WIRED RSSと未来の兆し生成のみ使用）
# @app.get("/stats", ...) - 削除


@app.get("/latest-post")
async def get_latest_post(db: Session = Depends(get_db)):
    """
    最新の投稿時刻を取得
    
    Returns:
        最新の投稿記事情報（投稿時刻はUTCとJSTの両方で表示）
    """
    from database import get_latest_posted_article
    from zoneinfo import ZoneInfo
    from datetime import timezone
    
    latest = get_latest_posted_article(db)
    
    if not latest or not latest.posted_at:
        return {
            "status": "no_posts",
            "message": "投稿履歴がありません"
        }
    
    # UTC時刻を日本時間に変換
    jst = ZoneInfo('Asia/Tokyo')
    if latest.posted_at.tzinfo is None:
        # タイムゾーン情報がない場合はUTCとして扱う
        utc_time = latest.posted_at.replace(tzinfo=timezone.utc)
    else:
        utc_time = latest.posted_at.astimezone(timezone.utc)
    jst_time = utc_time.astimezone(jst)
    
    return {
        "status": "ok",
        "latest_post": {
            "id": latest.id,
            "title": latest.title,
            "url": latest.url,
            "posted_at_utc": latest.posted_at.isoformat() if latest.posted_at else None,
            "posted_at_jst": jst_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            "posted_at_jst_iso": jst_time.isoformat()
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
    try:
        # WIRED RSS URL（デフォルト）
        rss_url = request.rss_url or WIRED_RSS_URL
        articles = article_fetcher.fetch_from_rss(rss_url, request.max_items)
        
        logger.info(f"✅ {len(articles)}件のWIRED記事を取得しました")
        
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


# URL取得機能は削除（WIRED RSSのみ使用）
# @app.post("/fetch/url", ...) - 削除


@app.post("/fetch/research")
async def fetch_by_research(
    request: ThemeResearchRequest,
    db: Session = Depends(get_db)
):
    """Geminiを使用してテーマに基づく「未来の兆し」を生成"""
    if not analyzer:
        raise HTTPException(status_code=503, detail="GeminiAnalyzerが初期化されていません")
    
    try:
        # テーマに基づいて「未来の兆し」を生成（実際の記事は不要）
        themes_list = [t.strip() for t in request.themes.split(',') if t.strip()]
        generated_items = []
        
        for theme in themes_list:
            try:
                result = analyzer.generate_future_signal(theme)
                generated_items.append(result)
            except Exception as e:
                print(f"⚠️ テーマ '{theme}' の未来の兆し生成エラー: {e}")
                continue
        
        if not generated_items:
            raise HTTPException(status_code=500, detail="未来の兆しの生成に失敗しました")
        
        # 生成された「未来の兆し」を記事として保存
        articles = []
        for item in generated_items:
            articles.append({
                'title': item['title'],
                'summary': item['summary'],
                'future_signal': item['future_signal'],
                'theme': item['theme'],
                'url': '',  # 実際の記事URLは不要
                'content': item['summary'],  # 要約をコンテンツとして使用
                'published_at': datetime.now()
            })
    except HTTPException:
        raise
    except Exception as e:
        # Gemini APIのエラーを適切にハンドリング
        error_str = str(e).lower()
        
        # 503エラー（サービス一時利用不可）
        if "503" in error_str or "service unavailable" in error_str:
            headers = {"Retry-After": "10"}
            raise HTTPException(
                status_code=503,
                detail="Upstream service temporarily unavailable. Please retry later.",
                headers=headers
            )
        
        # 429エラー（レート制限）
        if "429" in error_str or "rate limit" in error_str or "quota" in error_str or "resource exhausted" in error_str:
            headers = {"Retry-After": "60"}
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please retry later.",
                headers=headers
            )
        
        # その他のエラーは500として返す
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    
    try:
        processed_count = 0
        posted_count = 0
        
        for article_data in articles:
            title = article_data.get('title', '')
            summary = article_data.get('summary', '')
            future_signal = article_data.get('future_signal', '')
            theme = article_data.get('theme', '')
            
            if not title or not summary or not future_signal:
                print(f"⚠️ 不完全なデータをスキップ: {title}")
                continue
            
            # 投稿テキストを生成（未来の兆しを含める、URLなし）
            summary = summary or ""
            future_signal = future_signal or ""
            
            # 280文字以内に収める（URLなし）
            # 構造: タイトル → 要約 → 未来の兆し
            future_label = "🔮 未来の兆し: "
            future_length = len(future_label) + len(future_signal or "") + 2  # +2は改行分
            title_length = len(title) + 2  # +2は改行分
            
            # 要約の最大長を計算
            max_summary_length = 280 - title_length - future_length - 10  # 余裕を持たせる
            
            if max_summary_length < 0:
                # 文字数が足りない場合は要約を短縮
                max_summary_length = 50
            
            if len(summary) > max_summary_length:
                summary = summary[:max_summary_length - 3] + "..."
            
            # 投稿テキストを構築（URLなし）
            post_text = f"{title}\n\n{summary}\n\n{future_label}{future_signal}"
            
            # 最終チェック（280文字以内）
            if len(post_text) > 280:
                # 未来の兆しを短縮
                base_length = len(f"{title}\n\n{summary}\n\n{future_label}")
                remaining_length = 280 - base_length
                if remaining_length > 0:
                    future_signal = future_signal[:remaining_length - 3] + "..."
                    post_text = f"{title}\n\n{summary}\n\n{future_label}{future_signal}"
                else:
                    # それでも長い場合は要約をさらに短縮
                    max_summary_length = 280 - title_length - len(future_label) - 20
                    summary = summary[:max_summary_length - 3] + "..."
                    post_text = f"{title}\n\n{summary}\n\n{future_label}{future_signal[:50]}"
            
            # DB保存せずに直接自動投稿（認証不要）
            if poster:
                try:
                    result = poster.post(post_text)
                    if result:
                        print(f"✅ 自動投稿完了: {title[:50]}... (Platform: {result.get('platform')})")
                        posted_count += 1
                    else:
                        print(f"⚠️ 投稿失敗: {title[:50]}...")
                except Exception as e:
                    print(f"⚠️ 自動投稿エラー ({title[:50]}...): {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"⚠️ ソーシャルポスターが利用できません。スキップします。")
            
            processed_count += 1
        
        return {
            "message": "未来の兆し生成・投稿完了",
            "processed": processed_count,
            "posted": posted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"エラー: {str(e)}")


# 自動取得・分析機能は削除（WIRED RSSと未来の兆し生成のみ使用）
# @app.post("/fetch/analyze", ...) - 削除


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

