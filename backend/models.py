"""
データモデル定義
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Article(Base):
    """記事データモデル"""
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text)
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Gemini分析結果
    theme = Column(String)  # テーマ分類
    summary = Column(Text)  # 要約
    key_points = Column(Text)  # 主要ポイント（JSON形式）
    sentiment_score = Column(Float)  # 感情スコア
    relevance_score = Column(Float)  # 関連性スコア
    
    # 投稿関連
    is_posted = Column(Boolean, default=False)
    posted_at = Column(DateTime, nullable=True)
    tweet_id = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title}', theme='{self.theme}')>"


class PostQueue(Base):
    """投稿キュー"""
    __tablename__ = "post_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, nullable=False)
    post_text = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending, approved, rejected, posted
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<PostQueue(id={self.id}, article_id={self.article_id}, status='{self.status}')>"

