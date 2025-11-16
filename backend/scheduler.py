"""
定期実行スケジューラー

【Render デプロイ対応】
- 環境変数は Render から直接取得
- .env ファイルが存在しない場合でもエラーにならない
"""
from pathlib import Path
from dotenv import load_dotenv

# .envファイルを読み込む（ローカル開発用、ファイルが存在する場合のみ）
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

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

# スケジューラーの無効化フラグ
DISABLE_SCHEDULER = os.getenv("DISABLE_SCHEDULER", "").lower() == "true"


class ArticleScheduler:
    """記事分析・投稿の定期実行スケジューラー"""
    
    def __init__(self, feed_manager: RSSFeedManager = None):
        try:
            self.analyzer = GeminiAnalyzer()
            print("✅ GeminiAnalyzer初期化成功")
        except Exception as e:
            print(f"⚠️ GeminiAnalyzer初期化エラー: {e}")
            self.analyzer = None
        try:
            self.poster = SocialPoster()
        except Exception as e:
            print(f"⚠️ ソーシャルポスター初期化エラー: {e}")
            self.poster = None
        self.feed_manager = feed_manager or get_default_feed_manager()
        self.url_shortener = URLShortener()
        # 固定テーマ
        self.fixed_themes = "AI,生成AI,AIエージェント"
    
    # Bluesky投稿テキスト用の定数とヘルパー関数
    ELLIPSIS = "…"
    MAX_LEN = 280
    
    def _fit(self, text: str, limit: int) -> str:
        """テキストを指定長に収める（省略記号付き）"""
        text = (text or "").strip()
        if len(text) <= limit:
            return text
        if limit <= 0:
            return ""
        return text[:max(0, limit - 1)] + self.ELLIPSIS
    
    def _has_ja(self, s: str) -> bool:
        """日本語文字（ひらがな・カタカナ・CJK）を含むかチェック"""
        import re
        return bool(re.search(r"[\u3040-\u30ff\u3400-\u9fff]", s or ""))
    
    def _build_bluesky_post(self, title: str, summary_ja: str, future_ja: str) -> str:
        """
        日本語 + 280文字以内で Bluesky 投稿文を生成（URLなし）
        
        形式:
          タイトル
          空行
          要約
          空行
          🔮 未来の兆し: ...
        
        Args:
            title: 記事タイトル
            summary_ja: 要約（日本語）
            future_ja: 未来の兆し（日本語）
        
        Returns:
            280文字以内の投稿テキスト
        """
        title = (title or "(無題)").strip()
        summary_ja = (summary_ja or "").strip()
        future_ja = (future_ja or "").strip()
        
        # 日本語でない場合でも落ちない（翻訳は別層で対応。ここでは体裁のみ）
        future_label = "🔮 未来の兆し: "
        
        # 先に固定部の長さを算出（改行も文字数にカウント）
        fixed_before_future = len(f"{title}\n\n{summary_ja}\n\n{future_label}")
        # 未来を入れる前にオーバーなら summary を短縮
        if fixed_before_future > self.MAX_LEN:
            # 残り枠 = MAX - (title + 2改行 + ラベル + 2改行)
            base = len(f"{title}\n\n") + len(f"\n\n{future_label}")
            remain_for_summary = self.MAX_LEN - base
            summary_ja = self._fit(summary_ja, max(0, remain_for_summary))
        
        # 未来の兆しを詰める
        post = f"{title}\n\n{summary_ja}\n\n{future_label}{future_ja}".strip()
        if len(post) > self.MAX_LEN:
            base = len(f"{title}\n\n{summary_ja}\n\n{future_label}")
            remain_for_future = self.MAX_LEN - base
            future_ja = self._fit(future_ja, max(0, remain_for_future))
            post = f"{title}\n\n{summary_ja}\n\n{future_label}{future_ja}".strip()
        
        # 念のため最終ガード（まれに1文字はみ出す場合）
        if len(post) > self.MAX_LEN:
            post = self._fit(post, self.MAX_LEN)
        
        return post
    
    def fetch_and_analyze_articles(self):
        """
        固定テーマに基づいて「未来の兆し」を生成
        """
        print(f"\n[{datetime.now()}] Geminiで「未来の兆し」生成を開始...")
        print(f"📌 固定テーマ: {self.fixed_themes}")
        
        try:
            # テーマに基づいて「未来の兆し」を生成
            themes_list = [t.strip() for t in self.fixed_themes.split(',') if t.strip()]
            generated_items = []
            
            for theme in themes_list:
                try:
                    result = self.analyzer.generate_future_signal(theme)
                    generated_items.append(result)
                    print(f"✅ テーマ '{theme}' の未来の兆しを生成")
                except Exception as e:
                    print(f"⚠️ テーマ '{theme}' の未来の兆し生成エラー: {e}")
                    # エラー時はスキップ（汎用テキストを保存しない）
                    continue
            
            if not generated_items:
                print("⚠️ 生成された未来の兆しがありません")
                return
            
            # 生成された「未来の兆し」を処理
            self._process_generated_signals(generated_items)
            
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
    
    def _process_generated_signals(self, generated_items: List[Dict]):
        """
        生成された「未来の兆し」を処理（DB保存なし、直接自動投稿）
        
        Args:
            generated_items: 生成された未来の兆しのリスト
        """
        try:
            processed_count = 0
            posted_count = 0
            
            for item in generated_items:
                title = item.get('title', '')
                summary = item.get('summary', '')
                future_signal = item.get('future_signal', '')
                theme = item.get('theme', '')
                
                if not title or not summary or not future_signal:
                    print(f"⚠️ 不完全なデータをスキップ: {title}")
                    continue
                
                # 投稿テキストを生成（未来の兆しを含める、URLなし）
                summary = summary or ""
                future_signal = future_signal or ""
                
                # ★ 日本語要約が空/英語でも、必ず日本語で作る
                if not summary or not any("\u3040" <= ch <= "\u30FF" or "\u4E00" <= ch <= "\u9FFF" for ch in summary):
                    # GeminiAnalyzerに日本語要約メソッドがあれば使用
                    if hasattr(self.analyzer, 'summarize_ja'):
                        ja = self.analyzer.summarize_ja(title, summary, "")
                        summary = ja.get("summary_ja", summary) or summary
                        future_signal = ja.get("future_ja", future_signal) or future_signal
                
                # ②Bluesky 280文字制約: 専用フォーマッタで確実に収める（URLなし）
                post_text = self._build_bluesky_post(title, summary, future_signal)
                
                # デバッグログ（動作確認用）
                print(f"DEBUG post_len={len(post_text)}: {post_text[:100]}...")
                
                # DB保存せずに直接自動投稿（認証不要）
                if self.poster:
                    try:
                        result = self.poster.post(post_text)
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
            
            print(f"✅ 処理完了: {processed_count}件処理, {posted_count}件投稿")
            
        except Exception as e:
            print(f"⚠️ エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def _process_research_articles(self, articles: List[Dict]):
        """
        取得した記事を処理（作成・キュー追加・自動投稿）
        
        Args:
            articles: 記事のリスト
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
                    summary = summary or ""
                    future_signal = future_signal or ""
                    
                    # ★ 日本語要約が空/英語でも、必ず日本語で作る（本体記事から再要約）
                    if not summary or not any("\u3040" <= ch <= "\u30FF" or "\u4E00" <= ch <= "\u9FFF" for ch in summary):
                        ja = self.analyzer.summarize_ja(title, content or "", url)
                        summary = ja.get("summary_ja", summary) or summary
                        future_signal = ja.get("future_ja", future_signal) or future_signal
                    else:
                        # summaryは日本語だが、未来だけ英語っぽい場合に保険翻訳
                        if future_signal and not any("\u3040" <= ch <= "\u30FF" or "\u4E00" <= ch <= "\u9FFF" for ch in future_signal):
                            future_signal = self.analyzer.translate_ja(future_signal)
                    
                    # ②Bluesky 280文字制約: 専用フォーマッタで確実に収める（URLなし）
                    post_text = self._build_bluesky_post(title, summary, future_signal)
                    
                    # デバッグログ（動作確認用）
                    print(f"DEBUG post_len={len(post_text)}: {post_text[:100]}...")
                    
                    # キューに追加（即座に自動投稿）
                    queue_item = add_to_post_queue(db, article.id, post_text)
                    queued_count += 1
                    print(f"📤 投稿キューに追加: {title[:50]}...")
                    
                    # 即座に自動投稿（認証不要）
                    if self.poster:
                        try:
                            result = self.poster.post(post_text)
                            if result:
                                # ステータスを更新
                                queue_item.status = "posted"
                                article.is_posted = True
                                article.posted_at = datetime.utcnow()
                                article.tweet_id = result.get("post_id")
                                db.commit()
                                print(f"✅ 自動投稿完了: {title[:50]}... (Platform: {result.get('platform')})")
                            else:
                                print(f"⚠️ 投稿失敗: {title[:50]}...")
                        except Exception as e:
                            print(f"⚠️ 自動投稿エラー ({title[:50]}...): {e}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f"⚠️ ソーシャルポスターが利用できません。キューに残します。")
                    
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
        
        # 既にスケジュールが登録されている場合はスキップ
        if schedule.jobs:
            print("⚠️ スケジューラーは既に起動しています")
            return
        
        print(f"🕐 スケジューラー開始: {interval_minutes}分間隔")
        
        # スケジュール設定（ジョブIDを指定して重複防止）
        schedule.every(interval_minutes).minutes.do(self.fetch_and_analyze_articles).tag("fetch_articles")  # 15分ごとに記事取得
        schedule.every(5).minutes.do(self.post_approved_articles).tag("post_articles")  # 15分ごとに承認済みを投稿
        
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

