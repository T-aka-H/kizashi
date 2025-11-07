"""
記事取得モジュール（RSS/Webスクレイピング）
"""
import os
import re
import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
import time


class ArticleFetcher:
    """記事取得クラス"""
    
    def __init__(self, user_agent: str = None):
        """
        初期化
        
        Args:
            user_agent: リクエスト時のUser-Agent
        """
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent
        })
    
    def fetch_from_rss(self, rss_url: str, max_items: int = 10) -> List[Dict]:
        """
        RSSフィードから記事を取得
        
        Args:
            rss_url: RSSフィードのURL
            max_items: 取得する最大記事数
        
        Returns:
            記事のリスト（url, title, content, published_atを含む）
        """
        articles = []
        
        try:
            print(f"📡 RSSフィードを取得中: {rss_url}")
            feed = feedparser.parse(rss_url)
            
            if feed.bozo and feed.bozo_exception:
                print(f"⚠️ RSS解析エラー: {feed.bozo_exception}")
                return articles
            
            entries = feed.entries[:max_items]
            
            for entry in entries:
                try:
                    # 公開日時の取得
                    published_at = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_at = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published_at = datetime(*entry.updated_parsed[:6])
                    
                    # コンテンツの取得
                    content = ""
                    if hasattr(entry, 'content'):
                        content = entry.content[0].value if entry.content else ""
                    elif hasattr(entry, 'summary'):
                        content = entry.summary
                    elif hasattr(entry, 'description'):
                        content = entry.description
                    
                    # HTMLタグを除去
                    content = self._clean_html(content)
                    
                    article = {
                        'url': entry.link,
                        'title': entry.title,
                        'content': content[:5000] if content else None,  # 最初の5000文字
                        'published_at': published_at
                    }
                    articles.append(article)
                    print(f"  ✓ {entry.title[:50]}...")
                    
                except Exception as e:
                    print(f"  ⚠️ エントリ処理エラー: {e}")
                    continue
            
            print(f"✅ {len(articles)}件の記事を取得")
            
        except Exception as e:
            print(f"⚠️ RSS取得エラー: {e}")
        
        return articles
    
    def fetch_from_url(self, url: str) -> Optional[Dict]:
        """
        単一URLから記事を取得（Webスクレイピング）
        
        Args:
            url: 記事のURL
        
        Returns:
            記事の辞書（url, title, content, published_atを含む）またはNone
        """
        try:
            print(f"🌐 記事を取得中: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # タイトルの取得
            title = None
            if soup.find('title'):
                title = soup.find('title').get_text().strip()
            elif soup.find('h1'):
                title = soup.find('h1').get_text().strip()
            elif soup.find('meta', property='og:title'):
                title = soup.find('meta', property='og:title').get('content', '').strip()
            
            # 本文の取得
            content = None
            
            # articleタグを優先
            article_tag = soup.find('article')
            if article_tag:
                content = self._extract_text(article_tag)
            else:
                # mainタグ
                main_tag = soup.find('main')
                if main_tag:
                    content = self._extract_text(main_tag)
                else:
                    # body全体から不要な要素を除去
                    body = soup.find('body')
                    if body:
                        # スクリプト、スタイル、ナビゲーションなどを除去
                        for tag in body.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                            tag.decompose()
                        content = self._extract_text(body)
            
            # 公開日時の取得
            published_at = None
            time_tag = soup.find('time')
            if time_tag:
                datetime_attr = time_tag.get('datetime') or time_tag.get_text()
                try:
                    published_at = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                except:
                    pass
            
            if not title:
                print(f"⚠️ タイトルが見つかりません: {url}")
                return None
            
            if not content or len(content) < 100:
                print(f"⚠️ コンテンツが短すぎます: {url}")
                return None
            
            article = {
                'url': url,
                'title': title,
                'content': content[:5000],  # 最初の5000文字
                'published_at': published_at
            }
            
            print(f"✅ 記事取得完了: {title[:50]}...")
            return article
            
        except Exception as e:
            print(f"⚠️ 記事取得エラー ({url}): {e}")
            return None
    
    def fetch_from_urls(self, urls: List[str], delay: float = 1.0) -> List[Dict]:
        """
        複数URLから記事を取得
        
        Args:
            urls: URLのリスト
            delay: リクエスト間の遅延（秒）
        
        Returns:
            記事のリスト
        """
        articles = []
        
        for i, url in enumerate(urls):
            article = self.fetch_from_url(url)
            if article:
                articles.append(article)
            
            # 最後のリクエスト以外は遅延
            if i < len(urls) - 1:
                time.sleep(delay)
        
        return articles
    
    def _extract_text(self, element) -> str:
        """
        HTML要素からテキストを抽出
        
        Args:
            element: BeautifulSoup要素
        
        Returns:
            抽出されたテキスト
        """
        if not element:
            return ""
        
        # コピーを作成して操作
        element = element.__copy__()
        
        # 不要なタグを除去
        for tag in element.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
            tag.decompose()
        
        # テキストを取得
        text = element.get_text(separator='\n', strip=True)
        
        # 余分な空白を整理
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def _clean_html(self, html: str) -> str:
        """
        HTMLタグを除去してテキストのみを抽出
        
        Args:
            html: HTML文字列
        
        Returns:
            クリーンなテキスト
        """
        if not html:
            return ""
        
        soup = BeautifulSoup(html, 'html.parser')
        return self._extract_text(soup)


class RSSFeedManager:
    """RSSフィード管理クラス"""
    
    def __init__(self):
        self.fetcher = ArticleFetcher()
        self.feeds = []  # デフォルトのフィードリスト
    
    def add_feed(self, rss_url: str, max_items: int = 10):
        """
        RSSフィードを追加
        
        Args:
            rss_url: RSSフィードのURL
            max_items: 取得する最大記事数
        """
        self.feeds.append({
            'url': rss_url,
            'max_items': max_items
        })
    
    def fetch_all_feeds(self) -> List[Dict]:
        """
        登録されているすべてのRSSフィードから記事を取得
        
        Returns:
            記事のリスト
        """
        all_articles = []
        
        for feed_config in self.feeds:
            articles = self.fetcher.fetch_from_rss(
                feed_config['url'],
                feed_config['max_items']
            )
            all_articles.extend(articles)
            
            # フィード間の遅延
            time.sleep(1.0)
        
        return all_articles


# デフォルトのRSSフィード（例）
DEFAULT_FEEDS = [
    # 技術系ニュース
    {'url': 'https://techcrunch.com/feed/', 'max_items': 5},
    {'url': 'https://www.theverge.com/rss/index.xml', 'max_items': 5},
    # 日本語技術系
    {'url': 'https://zenn.dev/feed', 'max_items': 5},
    {'url': 'https://qiita.com/feed', 'max_items': 5},
]


def get_default_feed_manager() -> RSSFeedManager:
    """デフォルト設定のRSSフィードマネージャーを取得"""
    manager = RSSFeedManager()
    for feed in DEFAULT_FEEDS:
        manager.add_feed(feed['url'], feed['max_items'])
    return manager

