"""
記事取得機能のテストスクリプト
"""
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

from article_fetcher import ArticleFetcher, RSSFeedManager, get_default_feed_manager


def test_rss_fetch():
    """RSSフィード取得テスト"""
    print("\n=== RSSフィード取得テスト ===")
    
    fetcher = ArticleFetcher()
    
    # テスト用RSSフィード（Zennのフィード）
    test_rss = "https://zenn.dev/feed"
    
    try:
        articles = fetcher.fetch_from_rss(test_rss, max_items=3)
        
        print(f"\n✅ {len(articles)}件の記事を取得")
        for i, article in enumerate(articles, 1):
            print(f"\n{i}. {article['title']}")
            print(f"   URL: {article['url']}")
            if article.get('content'):
                print(f"   コンテンツ: {article['content'][:100]}...")
            if article.get('published_at'):
                print(f"   公開日: {article['published_at']}")
        
    except Exception as e:
        print(f"⚠️ エラー: {e}")
        import traceback
        traceback.print_exc()


def test_url_fetch():
    """URL取得テスト"""
    print("\n=== URL取得テスト ===")
    
    fetcher = ArticleFetcher()
    
    # テスト用URL（実際の記事URLを指定）
    test_urls = [
        "https://example.com",  # テスト用（実際のURLに変更してください）
    ]
    
    print("⚠️ 実際の記事URLを指定してください")
    print("テストURL:", test_urls)
    
    # コメントアウト（実際のURLでテストする場合）
    # try:
    #     articles = fetcher.fetch_from_urls(test_urls)
    #     print(f"\n✅ {len(articles)}件の記事を取得")
    #     for article in articles:
    #         print(f"\nタイトル: {article['title']}")
    #         print(f"URL: {article['url']}")
    #         if article.get('content'):
    #             print(f"コンテンツ: {article['content'][:200]}...")
    # except Exception as e:
    #     print(f"⚠️ エラー: {e}")


def test_feed_manager():
    """RSSフィードマネージャーのテスト"""
    print("\n=== RSSフィードマネージャーテスト ===")
    
    manager = RSSFeedManager()
    
    # カスタムフィードを追加
    manager.add_feed("https://zenn.dev/feed", max_items=2)
    
    try:
        articles = manager.fetch_all_feeds()
        print(f"\n✅ {len(articles)}件の記事を取得")
        
        for i, article in enumerate(articles, 1):
            print(f"\n{i}. {article['title'][:60]}...")
            print(f"   URL: {article['url']}")
        
    except Exception as e:
        print(f"⚠️ エラー: {e}")
        import traceback
        traceback.print_exc()


def test_default_feeds():
    """デフォルトフィードのテスト"""
    print("\n=== デフォルトフィードテスト ===")
    
    manager = get_default_feed_manager()
    
    try:
        articles = manager.fetch_all_feeds()
        print(f"\n✅ {len(articles)}件の記事を取得")
        
        # フィード別に集計
        feed_counts = {}
        for article in articles:
            # URLからドメインを抽出（簡易版）
            domain = article['url'].split('/')[2] if '/' in article['url'] else 'unknown'
            feed_counts[domain] = feed_counts.get(domain, 0) + 1
        
        print("\nフィード別集計:")
        for domain, count in feed_counts.items():
            print(f"  {domain}: {count}件")
        
    except Exception as e:
        print(f"⚠️ エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 記事取得機能テスト開始\n")
    
    # テスト実行
    test_rss_fetch()
    test_url_fetch()
    test_feed_manager()
    # test_default_feeds()  # 時間がかかるのでコメントアウト
    
    print("\n✅ すべてのテスト完了")

