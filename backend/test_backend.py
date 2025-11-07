"""
バックエンドテストスクリプト
"""
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

from database import init_db, create_article, get_article_by_url, update_article_analysis
from gemini_analyzer import GeminiAnalyzer
from twitter_poster import SocialPoster


def test_database():
    """データベーステスト"""
    print("\n=== データベーステスト ===")
    init_db()
    print("✅ データベース初期化完了")


def test_gemini_analyzer():
    """Gemini分析テスト"""
    print("\n=== Gemini分析テスト ===")
    
    try:
        analyzer = GeminiAnalyzer()
        
        # テスト記事
        test_title = "AI技術の最新動向：生成AIがもたらす変革"
        test_content = """
        生成AI技術は急速に発展しており、ChatGPTやGeminiなどの大規模言語モデルが
        様々な分野で活用されています。特にクリエイティブな作業や情報分析において
        大きな変革をもたらしています。今後も技術の進化が期待されます。
        """
        
        print(f"📝 テスト記事: {test_title}")
        result = analyzer.analyze_article(test_title, test_content)
        
        print(f"✅ 分析完了:")
        print(f"  テーマ: {result.get('theme')}")
        print(f"  要約: {result.get('summary')}")
        print(f"  感情スコア: {result.get('sentiment_score')}")
        print(f"  関連性スコア: {result.get('relevance_score')}")
        print(f"  投稿推奨: {result.get('should_post')}")
        
        # ソーシャル投稿テキスト生成テスト
        post_text = analyzer.generate_tweet_text(
            test_title, result.get('summary'), result.get('theme')
        )
        print(f"\n📤 生成された投稿テキスト:")
        print(f"   {post_text}")
        print(f"   文字数: {len(post_text)}")
        
    except Exception as e:
        print(f"⚠️ エラー: {e}")


def test_social_poster():
    """ソーシャルメディア投稿テスト（認証のみ）"""
    print("\n=== ソーシャルメディア認証テスト ===")
    
    try:
        poster = SocialPoster()
        mode = poster.mode
        
        print(f"📱 投稿モード: {mode.upper()}")
        
        if mode == "demo":
            print("📝 デモモード: 実際には投稿しません")
            # デモ投稿テスト
            result = poster.post("テスト投稿 🔮 #未来の兆し")
            if result:
                print(f"✅ デモ投稿成功: {result.get('post_id')}")
        else:
            if poster.verify_credentials():
                print(f"✅ {mode.upper()}認証成功")
                # テスト投稿（実際には投稿しない）
                print("⚠️ テスト投稿はスキップします")
            else:
                print(f"⚠️ {mode.upper()}認証失敗")
    except ValueError as e:
        print(f"⚠️ {e}")
        print("   環境変数を設定してください")
    except Exception as e:
        print(f"⚠️ エラー: {e}")
        import traceback
        traceback.print_exc()


def test_full_workflow():
    """完全なワークフローテスト"""
    print("\n=== 完全ワークフローテスト ===")
    
    from database import SessionLocal, add_to_post_queue
    
    db = SessionLocal()
    
    try:
        # 1. 記事作成
        test_url = "https://example.com/test-article-1"
        article = create_article(
            db,
            url=test_url,
            title="テスト記事：AI技術の未来",
            content="これはテスト記事です。AI技術について説明しています。"
        )
        print(f"✅ 記事作成: ID={article.id}")
        
        # 2. 分析
        analyzer = GeminiAnalyzer()
        analysis = analyzer.analyze_article(article.title, article.content, article.url)
        print(f"✅ 分析完了: テーマ={analysis.get('theme')}")
        
        # 3. 分析結果を保存
        update_article_analysis(db, article.id, analysis)
        print(f"✅ 分析結果を保存")
        
        # 4. 投稿キューに追加（投稿推奨の場合）
        if analysis.get('should_post', False):
            post_text = analyzer.generate_tweet_text(
                article.title, analysis.get('summary'), analysis.get('theme'), article.url
            )
            queue_item = add_to_post_queue(db, article.id, post_text)
            print(f"✅ 投稿キューに追加: ID={queue_item.id}")
            print(f"   投稿テキスト: {post_text[:100]}...")
        
        print("\n✅ ワークフローテスト完了")
        
    except Exception as e:
        print(f"⚠️ エラー: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 バックエンドテスト開始\n")
    
    # 環境変数チェック
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️ GEMINI_API_KEYが設定されていません")
        print("   .envファイルを作成して設定してください\n")
    
    # テスト実行
    test_database()
    test_gemini_analyzer()
    test_social_poster()
    test_full_workflow()
    
    print("\n✅ すべてのテスト完了")

