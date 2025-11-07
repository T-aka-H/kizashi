"""
定期実行スケジューラー
"""
import os
import schedule
import time
from datetime import datetime
from typing import Callable, List, Dict

from database import SessionLocal, get_pending_posts
from gemini_analyzer import GeminiAnalyzer
from twitter_poster import SocialPoster
from article_fetcher import RSSFeedManager, get_default_feed_manager
from url_shortener import URLShortener

# Gemini Grounding用のリサーチャー（オプション）
try:
    from gemini_researcher import GeminiResearcher
    researcher = None
    try:
        researcher = GeminiResearcher()
    except Exception as e:
        print(f"⚠️ GeminiResearcher初期化エラー: {e}")
except ImportError:
    researcher = None

# スケジューラーの無効化フラグ
DISABLE_SCHEDULER = os.getenv("DISABLE_SCHEDULER", "").lower() == "true"


class ArticleScheduler:
    """記事分析・投稿の定期実行スケジューラー"""
    
    def __init__(self, feed_manager: RSSFeedManager = None):
        self.analyzer = GeminiAnalyzer()
        try:
            self.poster = SocialPoster()
        except Exception as e:
            print(f"⚠️ ソーシャルポスター初期化エラー: {e}")
            self.poster = None
        self.feed_manager = feed_manager or get_default_feed_manager()
        self.url_shortener = URLShortener()
        # 固定テーマ
        self.fixed_themes = "AI,生成AI,AIエージェント"
    
    def fetch_and_analyze_articles(self):
        """
        Gemini Groundingで固定テーマの記事を取得して分析
        """
        print(f"\n[{datetime.now()}] Gemini Groundingで記事取得・分析を開始...")
        print(f"📌 固定テーマ: {self.fixed_themes}")
        
        try:
            # Gemini Groundingで記事を取得
            if researcher:
                articles = researcher.fetch_articles_by_themes(self.fixed_themes)
                
                if not articles:
                    print("⚠️ 取得した記事がありません")
                    return
                
                self._process_research_articles(articles)
            else:
                print("⚠️ GeminiResearcherが利用できません。RSSフィードから取得します。")
                # フォールバック: RSSフィードから取得
                articles = self.feed_manager.fetch_all_feeds()
                if not articles:
                    print("⚠️ 取得した記事がありません")
                    return
                self._process_articles(articles)
            
        except Exception as e:
            print(f"⚠️ エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def analyze_new_articles(self, article_fetcher: Callable = None):
        """
        新しい記事を取得して分析
        
        Args:
            article_fetcher: 記事を取得する関数（オプション、指定しない場合はRSSフィードを使用）
        """
        if article_fetcher:
            # カスタム取得関数を使用
            articles = article_fetcher()
            self._process_articles(articles)
        else:
            # デフォルトのRSS取得を使用
            self.fetch_and_analyze_articles()
    
    def _process_articles(self, articles: List[Dict]):
        """
        記事リストを処理（作成・分析・キュー追加）
        
        Args:
            articles: 記事のリスト
        """
        db = SessionLocal()
        
        try:
            processed_count = 0
            skipped_count = 0
            
            for article_data in articles:
                url = article_data.get("url")
                title = article_data.get("title")
                content = article_data.get("content", "")
                published_at = article_data.get("published_at")
                
                # 既に存在するかチェック
                from database import get_article_by_url, create_article, update_article_analysis
                
                existing = get_article_by_url(db, url)
                if existing:
                    print(f"⏭️  スキップ: {title[:50]}... (既に存在)")
                    skipped_count += 1
                    continue
                
                # 記事を作成
                article = create_article(db, url, title, content, published_at)
                print(f"📝 記事作成: {title[:50]}...")
                
                # Geminiで分析
                try:
                    analysis = self.analyzer.analyze_article(title, content or "", url)
                    print(f"🔍 分析完了: テーマ={analysis.get('theme')}")
                    
                    # 分析結果を保存
                    update_article_analysis(db, article.id, analysis)
                    
                    # 投稿候補の場合、キューに追加
                    if analysis.get("should_post", False):
                        tweet_text = self.analyzer.generate_tweet_text(
                            title, analysis.get("summary"), analysis.get("theme"), url
                        )
                        from database import add_to_post_queue
                        add_to_post_queue(db, article.id, tweet_text)
                        print(f"📤 投稿キューに追加: {title[:50]}...")
                    
                    processed_count += 1
                    
                except Exception as e:
                    print(f"⚠️ 分析エラー ({title[:50]}...): {e}")
                    continue
            
            print(f"✅ 処理完了: {processed_count}件処理, {skipped_count}件スキップ")
            
        except Exception as e:
            print(f"⚠️ エラー: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()
    
    def _process_research_articles(self, articles: List[Dict]):
        """
        Gemini Groundingで取得した記事を処理（作成・キュー追加・自動投稿）
        
        Args:
            articles: 記事のリスト（Gemini Groundingから取得）
        """
        db = SessionLocal()
        
        try:
            processed_count = 0
            skipped_count = 0
            queued_count = 0
            
            from database import get_article_by_url, create_article, update_article_analysis, add_to_post_queue
            
            for article_data in articles:
                url = article_data.get("url")
                title = article_data.get("title")
                content = article_data.get("content", "")
                published_at = article_data.get("published_at")
                theme = article_data.get("theme")
                summary = article_data.get("summary", "")
                future_signal = article_data.get("future_signal", "")
                
                # 既に存在するかチェック
                existing = get_article_by_url(db, url)
                if existing:
                    print(f"⏭️  スキップ: {title[:50]}... (既に存在)")
                    skipped_count += 1
                    continue
                
                # 記事を作成
                article = create_article(db, url, title, content, published_at)
                print(f"📝 記事作成: {title[:50]}...")
                
                # テーマが既に設定されている場合はそのまま使用
                if theme:
                    analysis = {
                        "theme": theme,
                        "summary": summary,
                        "key_points": '[]',
                        "sentiment_score": 0.7,
                        "relevance_score": 0.9,
                        "should_post": True  # スケジュール実行時はすべて投稿
                    }
                    update_article_analysis(db, article.id, analysis)
                    
                    # 投稿テキストを生成（未来の兆しを含める）
                    short_url = self.url_shortener.shorten(url)
                    
                    # 280文字以内に収める（URL含む）
                    url_length = len(short_url) + 2
                    future_label = "🔮 未来の兆し: "
                    future_length = len(future_label) + len(future_signal) + 2
                    title_length = len(title) + 2
                    
                    # 要約の最大長を計算
                    max_summary_length = 280 - title_length - url_length - future_length - 10
                    
                    if max_summary_length < 0:
                        max_summary_length = 50
                    
                    if len(summary) > max_summary_length:
                        summary = summary[:max_summary_length - 3] + "..."
                    
                    # 投稿テキストを構築
                    post_text = f"{title}\n\n{summary}\n\n{short_url}\n\n{future_label}{future_signal}"
                    
                    # 最終チェック（280文字以内）
                    if len(post_text) > 280:
                        remaining_length = 280 - len(f"{title}\n\n{summary}\n\n{short_url}\n\n{future_label}")
                        if remaining_length > 0:
                            future_signal = future_signal[:remaining_length - 3] + "..."
                            post_text = f"{title}\n\n{summary}\n\n{short_url}\n\n{future_label}{future_signal}"
                        else:
                            max_summary_length = 280 - title_length - url_length - len(future_label) - 20
                            summary = summary[:max_summary_length - 3] + "..."
                            post_text = f"{title}\n\n{summary}\n\n{short_url}\n\n{future_label}{future_signal[:50]}"
                    
                    # キューに追加（承認不要で自動投稿）
                    add_to_post_queue(db, article.id, post_text)
                    queued_count += 1
                    print(f"📤 投稿キューに追加: {title[:50]}...")
                    
                    processed_count += 1
                else:
                    # テーマが設定されていない場合は分析を実行
                    try:
                        analysis = self.analyzer.analyze_article(title, content, url)
                        update_article_analysis(db, article.id, analysis)
                        
                        # スケジュール実行時はすべて投稿
                        short_url = self.url_shortener.shorten(url)
                        tweet_text = self.analyzer.generate_tweet_text(
                            title, analysis.get("summary"), analysis.get("theme"), short_url
                        )
                        add_to_post_queue(db, article.id, tweet_text)
                        queued_count += 1
                        print(f"📤 投稿キューに追加: {title[:50]}...")
                        
                        processed_count += 1
                    except Exception as e:
                        print(f"⚠️ 分析エラー ({title[:50]}...): {e}")
                        continue
            
            print(f"✅ 処理完了: {processed_count}件処理, {skipped_count}件スキップ, {queued_count}件をキューに追加")
            
        except Exception as e:
            print(f"⚠️ エラー: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()
    
    def post_approved_articles(self):
        """承認済みの記事を投稿（スケジュール実行時はパスワード確認なし）"""
        if not self.poster:
            print("⚠️ ソーシャルメディア設定がありません。スキップします。")
            return
        
        print(f"\n[{datetime.now()}] スケジュール投稿を開始（パスワード確認なし）...")
        
        db = SessionLocal()
        from database import get_pending_posts
        
        # pendingの投稿を取得して投稿（スケジュール実行時は承認不要）
        pending = get_pending_posts(db)
        
        if not pending:
            print("📭 投稿待ちの記事がありません")
            db.close()
            return
        
        posted_count = 0
        for queue_item in pending:
            try:
                result = self.poster.post(queue_item.post_text)
                if result:
                    # ステータスを更新
                    queue_item.status = "posted"
                    from models import Article
                    article = db.query(Article).filter(Article.id == queue_item.article_id).first()
                    if article:
                        article.is_posted = True
                        article.posted_at = datetime.utcnow()
                        article.tweet_id = result.get("post_id")
                    db.commit()
                    posted_count += 1
                    print(f"✅ 投稿完了: {queue_item.id} (Platform: {result.get('platform')})")
            except Exception as e:
                print(f"⚠️ 投稿エラー: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"✅ 投稿完了: {posted_count}件")
        db.close()
    
    def run_scheduler(self, interval_minutes: int = 15):
        """
        スケジューラーを実行
        
        Args:
            interval_minutes: 実行間隔（分）、デフォルトは15分
        """
        # スケジューラーが無効化されている場合は終了
        if DISABLE_SCHEDULER:
            print("⚠️ スケジューラーは無効化されています（DISABLE_SCHEDULER=true）")
            return
        
        print(f"🕐 スケジューラー開始: {interval_minutes}分間隔")
        
        # スケジュール設定
        schedule.every(interval_minutes).minutes.do(self.fetch_and_analyze_articles)  # 15分ごとに記事取得
        schedule.every(15).minutes.do(self.post_approved_articles)  # 15分ごとに承認済みを投稿
        
        # 初回実行
        print("🚀 初回実行を開始...")
        self.fetch_and_analyze_articles()
        
        # 無限ループ
        print(f"⏰ スケジューラー実行中... ({interval_minutes}分間隔)")
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1分ごとにチェック


if __name__ == "__main__":
    # テスト実行
    scheduler = ArticleScheduler()
    print("✅ スケジューラー初期化完了")
    
    # テスト: 記事取得と分析を1回実行
    print("\n=== テスト実行 ===")
    scheduler.fetch_and_analyze_articles()
    
    # 本番実行（コメントアウト）
    # scheduler.run_scheduler(interval_minutes=60)

