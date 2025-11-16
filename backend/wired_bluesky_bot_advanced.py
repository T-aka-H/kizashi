"""
WIRED記事TOP5を毎朝Blueskyに投稿するボット（改良版）
- 記事本文を取得してより詳細な要約を生成
"""
import os
import time
from typing import List, Dict
from datetime import datetime
from article_fetcher import ArticleFetcher
from gemini_analyzer import GeminiAnalyzer
from twitter_poster import SocialPoster


class WiredBlueskyBotAdvanced:
    """WIRED記事をBlueskyに投稿するボット（改良版）"""
    
    # WIREDのRSSフィード
    WIRED_RSS_URL = "https://www.wired.com/feed/rss"
    
    def __init__(self):
        """初期化"""
        self.fetcher = ArticleFetcher()
        self.analyzer = GeminiAnalyzer()
        self.poster = SocialPoster()
        print("✅ WiredBlueskyBotAdvanced初期化完了")
    
    def fetch_wired_articles(self, max_items: int = 20) -> List[Dict]:
        """
        WIREDのRSSフィードから記事を取得
        
        Args:
            max_items: 取得する最大記事数
        
        Returns:
            記事のリスト
        """
        print(f"\n📡 WIREDから記事を取得中... (最大{max_items}件)")
        articles = self.fetcher.fetch_from_rss(self.WIRED_RSS_URL, max_items)
        
        if not articles:
            print("⚠️ 記事の取得に失敗しました")
            return []
        
        print(f"✅ {len(articles)}件の記事を取得しました")
        return articles
    
    def fetch_article_content(self, article: Dict) -> Dict:
        """
        記事のURLから本文を取得
        
        Args:
            article: 記事の辞書
        
        Returns:
            本文を含む記事の辞書
        """
        url = article.get('url')
        if not url:
            return article
        
        try:
            full_article = self.fetcher.fetch_from_url(url)
            if full_article and full_article.get('content'):
                article['full_content'] = full_article['content']
                print(f"  ✓ 本文取得成功: {len(full_article['content'])}文字")
            else:
                print(f"  ⚠️ 本文取得失敗")
        except Exception as e:
            print(f"  ⚠️ 本文取得エラー: {e}")
        
        return article
    
    def select_top5_with_gemini(self, articles: List[Dict]) -> List[Dict]:
        """
        GeminiにTOP5を選定してもらう
        
        Args:
            articles: 記事のリスト
        
        Returns:
            TOP5の記事リスト
        """
        if not articles:
            return []
        
        print(f"\n🤖 Geminiで重要度TOP5を選定中...")
        
        # 記事リストを整形
        articles_text = ""
        for i, article in enumerate(articles, 1):
            title = article.get('title', '無題')
            content = article.get('content', '')[:300]  # 最初の300文字
            url = article.get('url', '')
            articles_text += f"{i}. タイトル: {title}\n   URL: {url}\n   概要: {content}\n\n"
        
        # Geminiに依頼
        prompt = f"""以下の{len(articles)}件のWIRED記事の中から、技術トレンド・イノベーション・未来への影響度を基準に重要度TOP5を選んでください。

{articles_text}

以下のJSON形式で回答してください（余計な説明は不要、JSONのみ）:
{{
    "top5": [
        {{
            "rank": 1,
            "article_number": 記事番号（1-{len(articles)}）,
            "reason": "選定理由（50文字以内）"
        }},
        ...
    ]
}}
"""
        
        try:
            import json
            response = self.analyzer.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # JSONを抽出
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            top5_indices = [item['article_number'] - 1 for item in result['top5']]
            
            top5_articles = []
            for i, idx in enumerate(top5_indices, 1):
                if 0 <= idx < len(articles):
                    article = articles[idx].copy()
                    article['rank'] = i
                    article['reason'] = result['top5'][i-1].get('reason', '')
                    top5_articles.append(article)
                    print(f"  {i}位: {article['title'][:50]}...")
            
            print(f"✅ TOP5を選定しました")
            return top5_articles
            
        except Exception as e:
            print(f"⚠️ TOP5選定エラー: {e}")
            # フォールバック: 最初の5件を返す
            print("⚠️ フォールバック: 最初の5件を使用します")
            return articles[:5]
    
    def create_detailed_summary(self, article: Dict) -> Dict:
        """
        記事本文から詳細な要約を生成
        
        Args:
            article: 記事の辞書
        
        Returns:
            要約を含む辞書
        """
        title = article.get('title', '')
        content = article.get('full_content') or article.get('content', '')
        
        if not content:
            return {'summary': '', 'key_point': ''}
        
        prompt = f"""以下のWIRED記事を日本語で要約してください。

タイトル: {title}
本文: {content[:2000]}

以下のJSON形式で回答してください（余計な説明は不要、JSONのみ）:
{{
    "summary": "記事の要旨（100文字以内）",
    "key_point": "最も重要なポイント（100文字以内）"
}}
"""
        
        try:
            import json
            response = self.analyzer.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # JSONを抽出
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            return {
                'summary': result.get('summary', ''),
                'key_point': result.get('key_point', '')
            }
            
        except Exception as e:
            print(f"⚠️ 要約エラー: {e}")
            return {
                'summary': content[:100] if content else '',
                'key_point': ''
            }
    
    def create_post_text_for_article(self, article: Dict, rank: int) -> str:
        """
        1つの記事の投稿用テキストを作成
        
        Args:
            article: 記事の辞書（要約付き）
            rank: ランキング順位
        
        Returns:
            投稿テキスト（280文字以内）
        """
        title = article.get('title', '無題')
        summary = article.get('summary', '')
        key_point = article.get('key_point', '')
        url = article.get('url', '')
        
        # ヘッダー（順位付き）
        today = datetime.now().strftime("%m/%d")
        text = f"📰 WIRED TOP{rank} ({today})\n\n"
        
        # タイトル
        text += f"【{title}】\n\n"
        
        # 要旨
        if summary:
            text += f"📝 {summary}\n\n"
        
        # ポイント
        if key_point:
            text += f"💡 {key_point}\n\n"
        
        # URL
        if url:
            text += f"🔗 {url}"
        
        # 280文字制限に収める
        if len(text) > 280:
            # URLの長さを確保
            url_length = len(url) + 5 if url else 0  # "🔗 " + URL
            max_content = 280 - url_length - 10  # 余裕を持たせる
            
            # タイトルを短縮
            title_short = title[:30] + "..." if len(title) > 30 else title
            
            # 要旨を短縮
            summary_short = summary[:50] + "..." if len(summary) > 50 else summary
            
            # ポイントを短縮
            key_point_short = key_point[:50] + "..." if len(key_point) > 50 else key_point
            
            # 再構成
            text = f"📰 WIRED TOP{rank} ({today})\n\n【{title_short}】\n\n"
            
            remaining = 280 - len(text) - url_length
            
            if summary_short and remaining > 10:
                text += f"📝 {summary_short}\n\n"
                remaining = 280 - len(text) - url_length
            
            if key_point_short and remaining > 10:
                key_point_fit = key_point_short[:remaining-5] + "..." if len(key_point_short) > remaining-5 else key_point_short
                text += f"💡 {key_point_fit}\n\n"
            
            if url:
                text += f"🔗 {url}"
            
            # 最終チェック
            if len(text) > 280:
                text = text[:277] + "..."
        
        return text
    
    def post_articles_to_bluesky(self, top5_articles: List[Dict]) -> Dict[str, int]:
        """
        TOP5の記事を個別にBlueskyに投稿
        
        Args:
            top5_articles: TOP5の記事リスト（要約付き）
        
        Returns:
            {"success": 成功数, "failed": 失敗数}
        """
        success_count = 0
        failed_count = 0
        
        print(f"\n{'='*60}")
        print(f"📤 TOP5を個別に投稿中...")
        print(f"{'='*60}")
        
        for i, article in enumerate(top5_articles, 1):
            rank = article.get('rank', i)
            title = article.get('title', '無題')
            
            print(f"\n[{i}/5] 投稿準備中: {title[:50]}...")
            
            # 投稿テキストを作成
            post_text = self.create_post_text_for_article(article, rank)
            
            print(f"投稿内容:\n{'-'*60}\n{post_text}\n{'-'*60}")
            print(f"文字数: {len(post_text)}/280")
            
            # 投稿
            result = self.poster.post(post_text)
            
            if result and result.get('success'):
                print(f"✅ TOP{rank} 投稿成功!")
                success_count += 1
            else:
                print(f"⚠️ TOP{rank} 投稿失敗")
                failed_count += 1
            
            # 連続投稿の間隔を空ける（スパム判定回避）
            if i < len(top5_articles):
                print(f"⏳ 次の投稿まで5秒待機...")
                time.sleep(5)
        
        print(f"\n{'='*60}")
        print(f"📊 投稿結果: 成功 {success_count}件 / 失敗 {failed_count}件")
        print(f"{'='*60}")
        
        return {"success": success_count, "failed": failed_count}
    
    def run(self):
        """メイン処理"""
        print(f"\n{'='*60}")
        print(f"🚀 WIRED記事TOP5投稿Bot（改良版）開始")
        print(f"⏰ 実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        try:
            # 1. WIRED記事を取得
            articles = self.fetch_wired_articles(max_items=20)
            if not articles:
                print("⚠️ 記事がありません。終了します。")
                return
            
            # 2. GeminiでTOP5を選定
            top5_articles = self.select_top5_with_gemini(articles)
            if not top5_articles:
                print("⚠️ TOP5の選定に失敗しました。終了します。")
                return
            
            # 3. TOP5の記事本文を取得
            print(f"\n📖 TOP5の記事本文を取得中...")
            for i, article in enumerate(top5_articles, 1):
                print(f"  {i}/5: {article['title'][:50]}...")
                self.fetch_article_content(article)
                time.sleep(1)  # サーバー負荷軽減のため
            
            # 4. TOP5の詳細要約を生成
            print(f"\n📝 TOP5の詳細要約を生成中...")
            for i, article in enumerate(top5_articles, 1):
                print(f"  {i}/5: 要約生成中...")
                summary_data = self.create_detailed_summary(article)
                article.update(summary_data)
            
            # 5. TOP5を個別にBlueskyに投稿
            result = self.post_articles_to_bluesky(top5_articles)
            
            # 6. 結果表示
            if result['success'] > 0:
                print(f"\n{'='*60}")
                print(f"✅ すべての処理が完了しました！")
                print(f"\n📊 投稿結果: {result['success']}/{len(top5_articles)}件成功")
                print(f"\n📝 投稿した記事:")
                for i, article in enumerate(top5_articles, 1):
                    print(f"\n{i}位: {article['title'][:50]}...")
                    print(f"  要旨: {article.get('summary', 'N/A')[:80]}")
                    print(f"  ポイント: {article.get('key_point', 'N/A')[:80]}")
                print(f"{'='*60}\n")
            else:
                print(f"\n{'='*60}")
                print(f"⚠️ 投稿に失敗しました")
                print(f"{'='*60}\n")
                
        except Exception as e:
            print(f"\n⚠️ エラーが発生しました: {e}")
            import traceback
            traceback.print_exc()


def main():
    """エントリーポイント"""
    bot = WiredBlueskyBotAdvanced()
    bot.run()


if __name__ == "__main__":
    main()

