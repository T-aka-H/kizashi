"""
データベース操作

【Render デプロイ対応】
- 環境変数 DATABASE_URL から接続情報を取得
- ローカル開発: SQLite (weak_signals.db)
- Render本番: PostgreSQL (DATABASE_URL が自動設定される)
- postgres:// → postgresql:// の自動変換対応
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
import logging

logger = logging.getLogger(__name__)

from models import Base, Article, PostQueue

# データベースURL（環境変数から取得）
# - ローカル開発: デフォルトで SQLite を使用
# - Render: DATABASE_URL が自動的に設定される（PostgreSQL）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./weak_signals.db")

# PostgreSQL用のURL変換（Renderが提供するpostgres://をpostgresql://に変換）
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    logger.info("✅ DATABASE_URL を PostgreSQL 形式に変換しました")

# SQLite用の設定
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL用の設定
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # 接続の有効性をチェック
        pool_size=5,
        max_overflow=10
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    データベース初期化
    
    【動作】
    - テーブルが存在しない場合は自動作成
    - Render では PostgreSQL に自動接続
    - ローカルでは SQLite ファイルを作成
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ データベース初期化完了")
        
        # 接続情報をログ出力（セキュリティのため URL は出力しない）
        db_type = "PostgreSQL" if "postgresql://" in DATABASE_URL else "SQLite"
        logger.info(f"📊 データベースタイプ: {db_type}")
    except Exception as e:
        logger.error(f"⚠️ データベース初期化エラー: {e}", exc_info=True)
        raise


def get_db():
    """データベースセッション取得"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_article(db: Session, url: str, title: str, content: str = None, published_at=None):
    """記事を作成"""
    article = Article(
        url=url,
        title=title,
        content=content,
        published_at=published_at
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def get_article_by_url(db: Session, url: str):
    """URLで記事を取得"""
    return db.query(Article).filter(Article.url == url).first()


def update_article_analysis(db: Session, article_id: int, analysis_result: dict):
    """記事の分析結果を更新"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if article:
        article.theme = analysis_result.get("theme")
        article.summary = analysis_result.get("summary")
        article.key_points = analysis_result.get("key_points")
        article.sentiment_score = analysis_result.get("sentiment_score")
        article.relevance_score = analysis_result.get("relevance_score")
        db.commit()
        db.refresh(article)
    return article


def add_to_post_queue(db: Session, article_id: int, post_text: str):
    """投稿キューに追加"""
    queue_item = PostQueue(
        article_id=article_id,
        post_text=post_text,
        status="pending"
    )
    db.add(queue_item)
    db.commit()
    db.refresh(queue_item)
    return queue_item


def get_pending_posts(db: Session):
    """承認待ちの投稿を取得"""
    return db.query(PostQueue).filter(PostQueue.status == "pending").all()

