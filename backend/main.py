"""
FastAPI メインアプリケーション
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db, init_db, create_article, get_article_by_url, update_article_analysis
from database import add_to_post_queue, get_pending_posts
from gemini_analyzer import GeminiAnalyzer
from gemini_researcher import GeminiResearcher
from twitter_poster import SocialPoster
from article_fetcher import ArticleFetcher, RSSFeedManager, get_default_feed_manager
from url_shortener import URLShortener
from models import Article, PostQueue

# FastAPIアプリ初期化
app = FastAPI(title="Weak Signals App", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に設定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# データベース初期化
init_db()

# アナライザーとポスターのインスタンス
analyzer = GeminiAnalyzer()
try:
    researcher = GeminiResearcher()
except Exception as e:
    print(f"⚠️ GeminiResearcher初期化エラー: {e}")
    researcher = None

try:
    poster = SocialPoster()
except Exception as e:
    print(f"⚠️ ソーシャルポスター初期化エラー: {e}")
    poster = None

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


class ArticleResponse(BaseModel):
    id: int
    url: str
    title: str
    theme: Optional[str]
    summary: Optional[str]
    is_posted: bool
    
    class Config:
        from_attributes = True


class PostQueueResponse(BaseModel):
    id: int
    article_id: int
    post_text: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


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
    db: Session = Depends(get_db)
):
    """ソーシャルメディアに投稿"""
    if not poster:
        raise HTTPException(status_code=503, detail="ソーシャルメディア設定がありません")
    
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
    """Gemini DeepResearchを使用して記事を取得・分析"""
    if not researcher:
        raise HTTPException(status_code=503, detail="GeminiResearcherが初期化されていません")
    
    try:
        # DeepResearchで記事を取得
        articles = researcher.fetch_articles_by_themes(request.themes)
        
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
            
            # テーマが既に設定されている場合はそのまま使用、なければ分析
            if article_data.get('theme'):
                # DeepResearchで既にテーマが設定されている場合
                analysis = {
                    "theme": article_data.get('theme'),
                    "summary": article_data.get('summary', ''),
                    "key_points": '[]',
                    "sentiment_score": 0.7,  # Weak Signalなので中立的に高め
                    "relevance_score": 0.9,  # Weak Signalなので関連性が高い
                    "should_post": True  # Weak Signalなので投稿候補
                }
                update_article_analysis(db, article.id, analysis)
                analyzed_count += 1
                
                # 投稿テキストを生成（未来の兆しを含める）
                # URLを短縮
                short_url = url_shortener.shorten(url)
                future_signal = article_data.get('future_signal', '')
                post_text = f"{title}\n\n{article_data.get('summary', '')}\n\n🔮 未来の兆し: {future_signal}\n\n{short_url}"
                add_to_post_queue(db, article.id, post_text)
                queued_count += 1
            else:
                # テーマが設定されていない場合は分析を実行
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
            "message": "DeepResearch取得・分析完了",
            "processed": processed_count,
            "analyzed": analyzed_count,
            "queued": queued_count
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
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

