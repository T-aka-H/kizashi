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
app = FastAPI(title="Weak Signals App", version="1.0.0")

# CORS設定（必ず最初に追加、順序重要）
# 401/403エラーでもCORSヘッダが付くように、Basic認証より前に配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
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

    # 3. ArticleScheduler の初期化と起動（遅延起動）
    # 環境変数 DISABLE_SCHEDULER=true でスケジューラーを無効化可能
    disable_scheduler = os.getenv("DISABLE_SCHEDULER", "false").lower() == "true"
    
    if disable_scheduler:
        logger.info("📝 スケジューラーは無効化されています（DISABLE_SCHEDULER=true）")
        scheduler = None
    else:
        # スケジューラーは30秒後に起動（起動時間短縮のため）
        logger.info("⏳ スケジューラーを30秒後に起動します...")
        threading.Thread(target=_start_scheduler_delayed, daemon=True, name="SchedulerStarter").start()
    
    _initialized = True
    logger.info("✅ アプリケーション初期化完了")


def _start_scheduler_delayed():
    """
    スケジューラーを遅延起動（30秒後）
    
    【理由】
    - 起動時間を短縮するため
    - Renderのヘルスチェックを早く通過させるため
    """
    global scheduler, _scheduler_thread
    
    time.sleep(30)  # 30秒待機
    
    logger.info("🚀 スケジューラー起動を開始...")
    
    try:
        scheduler = ArticleScheduler()
        interval = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "15"))
        _scheduler_thread = threading.Thread(
            target=scheduler.run_scheduler,
            args=(interval,),
            daemon=True,
            name="ArticleSchedulerThread"
        )
        _scheduler_thread.start()
        logger.info(f"✅ スケジューラー起動完了（{interval}分間隔）")
    except Exception as e:
        logger.error(f"⚠️ スケジューラー起動エラー: {e}", exc_info=True)
        logger.warning("→ スケジューラーなしで動作を続行します")
        scheduler = None


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
feed_manager = get_default_feed_manager()

# URL短縮のインスタンス
url_shortener = URLShortener()


# Pydanticモデル
class ArticleCreate(BaseModel):
    url: str
    title: str
    content: Optional[str] = None
    published_at: Optional[datetime] = None


class RSSFeedRequest(BaseModel):
    rss_url: str
    max_items: int = 10


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
    return {"message": "Weak Signals App API", "status": "running"}


@app.post("/articles", response_model=ArticleResponse)
async def create_article_endpoint(
    article: ArticleCreate,
    db: Session = Depends(get_db)
):
    """記事を作成"""
    # 既存チェック
    existing = get_article_by_url(db, article.url)
    if existing:
        raise HTTPException(status_code=400, detail="記事は既に存在します")
    
    # 記事作成
    db_article = create_article(
        db, article.url, article.title, article.content, article.published_at
    )
    
    return db_article


@app.post("/articles/{article_id}/analyze", response_model=ArticleResponse)
async def analyze_article_endpoint(
    article_id: int,
    db: Session = Depends(get_db)
):
    """記事を分析"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="記事が見つかりません")
    
    # Geminiで分析
    analysis = analyzer.analyze_article(article.title, article.content or "", article.url)
    
    # 結果を保存
    updated_article = update_article_analysis(db, article_id, analysis)
    
    # 投稿候補の場合、キューに追加
    if analysis.get("should_post", False):
        # URLを短縮
        short_url = url_shortener.shorten(article.url)
        tweet_text = analyzer.generate_tweet_text(
            article.title, analysis.get("summary"), analysis.get("theme"), short_url
        )
        add_to_post_queue(db, article_id, tweet_text)
    
    return updated_article


@app.get("/articles", response_model=List[ArticleResponse])
async def list_articles(
    skip: int = 0,
    limit: int = 100,
    theme: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """記事一覧を取得"""
    query = db.query(Article)
    
    if theme:
        query = query.filter(Article.theme == theme)
    
    articles = query.order_by(Article.created_at.desc()).offset(skip).limit(limit).all()
    return articles


@app.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int, db: Session = Depends(get_db)):
    """記事を取得"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="記事が見つかりません")
    return article


@app.get("/post-queue", response_model=List[PostQueueResponse])
async def list_post_queue(
    status: Optional[str] = "pending",
    db: Session = Depends(get_db)
):
    """投稿キューを取得"""
    query = db.query(PostQueue)
    if status:
        query = query.filter(PostQueue.status == status)
    
    queue_items = query.order_by(PostQueue.created_at.desc()).all()
    return queue_items


@app.post("/post-queue/{queue_id}/approve")
async def approve_post(
    queue_id: int,
    db: Session = Depends(get_db)
):
    """投稿を承認"""
    queue_item = db.query(PostQueue).filter(PostQueue.id == queue_id).first()
    if not queue_item:
        raise HTTPException(status_code=404, detail="キューアイテムが見つかりません")
    
    queue_item.status = "approved"
    queue_item.approved_at = datetime.utcnow()
    db.commit()
    
    return {"message": "承認完了", "queue_id": queue_id}


@app.post("/post-queue/{queue_id}/post")
async def post_to_social(
    queue_id: int,
    request: PostRequest,
    db: Session = Depends(get_db)
):
    """ソーシャルメディアに投稿（投稿確認パスワード必要）"""
    if not poster:
        raise HTTPException(status_code=503, detail="ソーシャルメディア設定がありません")
    
    # 投稿確認パスワードを検証
    if not verify_post_password(request.confirm_password):
        raise HTTPException(status_code=403, detail="投稿パスワードが間違っています")
    
    queue_item = db.query(PostQueue).filter(PostQueue.id == queue_id).first()
    if not queue_item:
        raise HTTPException(status_code=404, detail="キューアイテムが見つかりません")
    
    # ソーシャルメディアに投稿
    result = poster.post(queue_item.post_text)
    if not result:
        raise HTTPException(status_code=500, detail="投稿に失敗しました")
    
    # ステータス更新
    queue_item.status = "posted"
    article = db.query(Article).filter(Article.id == queue_item.article_id).first()
    if article:
        article.is_posted = True
        article.posted_at = datetime.utcnow()
        article.tweet_id = result.get("post_id")  # post_idに統一
    
    db.commit()
    
    return {"message": "投稿完了", "post_id": result.get("post_id"), "platform": result.get("platform")}


@app.get("/healthz")
async def health_check():
    """
    ヘルスチェックエンドポイント（Render Health Check用）
    
    【仕様】
    - アプリが起動していれば常に 200 OK を返す
    - 各コンポーネントの状態も含める（オプション）
    - Render の Health Check Path に設定: /healthz
    """
    return {
        "status": "ok",
        "components": {
            "analyzer": "available" if analyzer else "unavailable",
            "poster": "available" if poster else "unavailable",
            "scheduler": "running" if scheduler and _scheduler_thread and _scheduler_thread.is_alive() else "stopped"
        }
    }


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


@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """統計情報を取得"""
    total_articles = db.query(Article).count()
    posted_articles = db.query(Article).filter(Article.is_posted == True).count()
    pending_posts = db.query(PostQueue).filter(PostQueue.status == "pending").count()
    
    # テーマ別集計
    themes = db.query(Article.theme).distinct().all()
    theme_count = len([t for t in themes if t[0]])
    
    return {
        "total_articles": total_articles,
        "posted_articles": posted_articles,
        "pending_posts": pending_posts,
        "themes": theme_count
    }


@app.post("/fetch/rss")
async def fetch_from_rss(
    request: RSSFeedRequest,
    db: Session = Depends(get_db)
):
    """RSSフィードから記事を取得"""
    try:
        articles = article_fetcher.fetch_from_rss(request.rss_url, request.max_items)
        
        created_count = 0
        for article_data in articles:
            # 既存チェック
            existing = get_article_by_url(db, article_data['url'])
            if not existing:
                create_article(
                    db,
                    article_data['url'],
                    article_data['title'],
                    article_data.get('content'),
                    article_data.get('published_at')
                )
                created_count += 1
        
        return {
            "message": "記事取得完了",
            "fetched": len(articles),
            "created": created_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得エラー: {str(e)}")


@app.post("/fetch/url")
async def fetch_from_url(
    request: URLFetchRequest,
    db: Session = Depends(get_db)
):
    """URLから記事を取得"""
    try:
        articles = article_fetcher.fetch_from_urls(request.urls)
        
        created_count = 0
        for article_data in articles:
            # 既存チェック
            existing = get_article_by_url(db, article_data['url'])
            if not existing:
                create_article(
                    db,
                    article_data['url'],
                    article_data['title'],
                    article_data.get('content'),
                    article_data.get('published_at')
                )
                created_count += 1
        
        return {
            "message": "記事取得完了",
            "fetched": len(articles),
            "created": created_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得エラー: {str(e)}")


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


@app.post("/fetch/analyze")
async def fetch_and_analyze(
    rss_url: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """記事を取得して自動分析（RSSフィードまたはデフォルト）"""
    try:
        if rss_url:
            # 指定されたRSSフィードから取得
            articles = article_fetcher.fetch_from_rss(rss_url)
        else:
            # デフォルトのフィードから取得
            articles = feed_manager.fetch_all_feeds()
        
        processed_count = 0
        analyzed_count = 0
        queued_count = 0
        
        for article_data in articles:
            url = article_data['url']
            title = article_data['title']
            content = article_data.get('content', '')
            
            # 既存チェック
            existing = get_article_by_url(db, url)
            if existing:
                continue
            
            # 記事作成
            article = create_article(
                db,
                url,
                title,
                content,
                article_data.get('published_at')
            )
            processed_count += 1
            
            # 分析
            try:
                analysis = analyzer.analyze_article(title, content, url)
                update_article_analysis(db, article.id, analysis)
                analyzed_count += 1
                
                # 投稿候補の場合、キューに追加
                if analysis.get("should_post", False):
                    # URLを短縮
                    short_url = url_shortener.shorten(url)
                    tweet_text = analyzer.generate_tweet_text(
                        title, analysis.get("summary"), analysis.get("theme"), short_url
                    )
                    add_to_post_queue(db, article.id, tweet_text)
                    queued_count += 1
            except Exception as e:
                print(f"分析エラー: {e}")
                continue
        
        return {
            "message": "取得・分析完了",
            "processed": processed_count,
            "analyzed": analyzed_count,
            "queued": queued_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"エラー: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

