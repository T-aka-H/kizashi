"""
WIRED記事TOP5を毎朝Blueskyに投稿するボット
"""
import os
import time
from typing import List, Dict
from datetime import datetime
from article_fetcher import ArticleFetcher
from gemini_analyzer import GeminiAnalyzer
from twitter_poster import SocialPoster
from url_shortener import URLShortener
from database import SessionLocal, get_recently_posted_urls, mark_article_as_posted


class WiredBlueskyBot:
    """WIRED記事をBlueskyに投稿するボット"""
    
    # WIREDのRSSフィード
    WIRED_RSS_URL = "https://www.wired.com/feed/rss"
    
    def __init__(self):
        """初期化"""
        self.fetcher = ArticleFetcher()
        self.analyzer = GeminiAnalyzer()
        self.poster = SocialPoster()
        self.url_shortener = URLShortener()
        print("✅ WiredBlueskyBot初期化完了")
    
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
    
    def select_top5_with_gemini(self, articles: List[Dict]) -> List[Dict]:
        """
        GeminiにTOP5を選定してもらう（過去3時間以内に投稿した記事を除外）
        
        Args:
            articles: 記事のリスト
        
        Returns:
            TOP5の記事リスト
        """
        if not articles:
            return []
        
        # 過去3時間以内に投稿した記事を除外
        db = SessionLocal()
        try:
            recent_urls = get_recently_posted_urls(db, hours=3)
            if recent_urls:
                print(f"\n⏰ 過去3時間以内に投稿した記事を除外: {len(recent_urls)}件")
                articles = [a for a in articles if a.get('url') not in recent_urls]
                if not articles:
                    print("⚠️ すべての記事が過去3時間以内に投稿済みです")
                    return []
        finally:
            db.close()
        
        print(f"\n🤖 Geminiで重要度TOP5を選定中... (候補: {len(articles)}件)")
        
        # 記事リストを整形
        articles_text = ""
        for i, article in enumerate(articles, 1):
            title = article.get('title', '無題')
            content = article.get('content', '')[:200]  # 最初の200文字
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
    
    def create_summary_with_gemini(self, article: Dict) -> Dict:
        """
        Geminiで記事を要約
        
        Args:
            article: 記事の辞書
        
        Returns:
            要約を含む辞書
        """
        title = article.get('title', '')
        content = article.get('content', '')
        
        prompt = f"""以下のWIRED記事を日本語で要約してください。

タイトル: {title}
本文: {content[:1000]}

以下のJSON形式で回答してください（余計な説明は不要、JSONのみ）:
{{
    "summary": "記事の要旨（150文字以内、できるだけ詳しく）",
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
    
    def create_top5_summary_post(self, top5_articles: List[Dict]) -> str:
        """
        TOP5の一覧投稿を作成（題名のみ、リンクなし）
        
        Args:
            top5_articles: TOP5の記事リスト
        
        Returns:
            投稿テキスト（280文字以内）
        """
        header = "AI選定 WIRED注目記事5選"
        
        lines = [header]
        
        # 5位まで表示（リンクなし、タイトルのみ）
        for i, article in enumerate(top5_articles[:5], 1):
            title = article.get('title', '無題')
            lines.append(f"{i}位: {title}")
        
        post_text = "\n\n".join(lines)  # 改行あり（見やすくするため）
        
        # 280文字制限チェック
        if len(post_text) > 280:
            # タイトルを短縮
            post_text = header + "\n\n"
            base_length = len(post_text)
            
            for i, article in enumerate(top5_articles[:5], 1):
                title = article.get('title', '無題')
                
                # 残り文字数を計算
                remaining = 280 - len(post_text) - 10  # 余裕を持たせる
                if remaining < 15:  # 最低限の文字数
                    break
                
                # タイトルを短縮
                rank_prefix = f"{i}位: "
                max_title_length = remaining - len(rank_prefix) - 3  # "..."の分
                if len(title) > max_title_length:
                    title = title[:max_title_length - 3] + "..."
                
                post_text += f"{rank_prefix}{title}\n\n"
            
            # 最終チェック
            if len(post_text) > 280:
                post_text = post_text[:277] + "..."
        
        return post_text.strip()
    
    def create_detail_post(self, article: Dict, rank: int) -> str:
        """
        各記事の詳細要約投稿を作成（250文字の要約）
        
        Args:
            article: 記事の辞書
            rank: ランキング順位
        
        Returns:
            投稿テキスト（280文字以内、要約は250文字）
        """
        title = article.get('title', '無題')
        content = article.get('content', '')
        url = article.get('url', '')
        
        # ヘッダー
        header = "AI選定 WIRED注目記事5選"
        
        # URL短縮
        short_url = ""
        if url:
            try:
                short_url = self.url_shortener.shorten(url)
                if not short_url:
                    short_url = url
            except Exception as e:
                print(f"⚠️ URL短縮エラー: {e}")
                short_url = url
        
        # タイトル（改行なし）
        title_section = f"【{title}】"
        
        # URL（改行なし）
        url_section = short_url if short_url else ""
        
        # 要約は150文字を目標（ヘッダー、タイトル、URLを考慮して調整、改行なし）
        # ベース長: ヘッダー + タイトル + URL + スペース（改行の代わり）
        base_length = len(header) + 1 + len(title_section) + 1
        if url_section:
            base_length += len(url_section) + 1
        
        # 残り文字数で要約を決定（150文字を目標、ただし残り文字数が少ない場合は調整）
        remaining = 280 - base_length
        target_summary_length = min(150, remaining - 1)  # スペース1つ分を考慮
        
        if target_summary_length > 0:
            if len(content) > target_summary_length:
                summary_text = content[:target_summary_length - 3] + "..."
            else:
                summary_text = content
        else:
            # スペースが足りない場合はタイトルを短縮
            title_short = title[:20] + "..." if len(title) > 20 else title
            title_section = f"【{title_short}】"
            base_length = len(header) + 1 + len(title_section) + 1
            if url_section:
                base_length += len(url_section) + 1
            remaining = 280 - base_length
            target_summary_length = min(150, remaining - 1)
            if target_summary_length > 0:
                summary_text = content[:target_summary_length - 3] + "..." if len(content) > target_summary_length else content
            else:
                summary_text = ""
        
        # 投稿テキストを構築（改行なし、スペース区切り）
        parts = [header, title_section]
        if url_section:
            parts.append(url_section)
        if summary_text:
            parts.append(summary_text)
        
        post_text = " ".join(parts)
        
        # 最終チェック（280文字厳守）
        if len(post_text) > 280:
            # 要約をさらに短縮
            base_length = len(header) + 1 + len(title_section) + 1
            if url_section:
                base_length += len(url_section) + 1
            remaining = 280 - base_length
            if remaining > 0:
                summary_text = content[:remaining - 3] + "..." if len(content) > remaining else content
                parts = [header, title_section]
                if url_section:
                    parts.append(url_section)
                if summary_text:
                    parts.append(summary_text)
                post_text = " ".join(parts)
            else:
                # タイトルをさらに短縮
                title_short = title[:15] + "..." if len(title) > 15 else title
                parts = [header, f"【{title_short}】"]
                if url_section:
                    parts.append(url_section)
                remaining = 280 - sum(len(p) + 1 for p in parts)
                if remaining > 0:
                    summary_text = content[:remaining - 3] + "..." if len(content) > remaining else content
                    if summary_text:
                        parts.append(summary_text)
                post_text = " ".join(parts)
        
        # 最終チェック
        if len(post_text) > 280:
            post_text = post_text[:277] + "..."
        
        return post_text
    
    def create_post_text_for_article(self, article: Dict, rank: int) -> str:
        """
        1つの記事の投稿用テキストを作成（最適化版）
        
        【投稿テキスト最適化】
        - タイトルは必ず全文表示
        - URL短縮で文字数節約
        - 要約を優先表示（最低30文字確保）
        - 280文字制限厳守
        
        Args:
            article: 記事の辞書
            rank: ランキング順位
        
        Returns:
            投稿テキスト（280文字以内）
        """
        title = article.get('title', '無題')
        content = article.get('content', '')
        url = article.get('url', '')
        
        # ヘッダー（順位付き）
        today = datetime.now().strftime("%m/%d")
        header = f"📰 WIRED TOP{rank} ({today})"
        
        # URL短縮（利用可能な場合）
        short_url = ""
        if url:
            try:
                short_url = self.url_shortener.shorten(url)
                if not short_url:
                    short_url = url
            except Exception as e:
                print(f"⚠️ URL短縮エラー: {e}")
                short_url = url
        
        # 投稿テキスト構造の最適化
        # 【優先順位】
        # 1. ヘッダー（必須）
        # 2. タイトル（全文必須）
        # 3. URL（短縮版）
        # 4. 要約（最低30文字確保）
        
        header_length = len(header) + 2  # +2は改行2つ
        title_length = len(title) + 4  # "【" + title + "】" + 改行2つ
        url_length = len(short_url) + 2 if short_url else 0  # URL + 改行2つ
        
        # 残り文字数を計算
        base_length = header_length + title_length + url_length
        remaining = 280 - base_length
        
        # 要約に割り当てる文字数を決定
        min_summary_length = 30  # 要約の最低文字数
        
        if remaining < min_summary_length:
            # スペースが足りない場合は要約を最低限表示
            summary_text = content[:min_summary_length - 3] + "..." if len(content) > min_summary_length else content
        else:
            # 要約: 最大150文字
            max_summary = min(150, remaining - 3)  # "📝 " + 改行2つ
            if len(content) > max_summary:
                summary_text = content[:max_summary - 3] + "..."
            else:
                summary_text = content
        
        # 投稿テキストを構築
        parts = [header, f"【{title}】"]
        if short_url:
            parts.append(short_url)
        if summary_text:
            parts.append(f"📝 {summary_text}")
        
        post_text = "\n\n".join(parts)
        
        # 最終検証（280文字厳守）
        if len(post_text) > 280:
            print(f"⚠️ 投稿テキストが280文字超過({len(post_text)}文字): {title[:30]}...")
            # 緊急短縮: 要約を削減
            parts = [header, f"【{title}】"]
            if short_url:
                parts.append(short_url)
            
            # 要約を再計算
            base_length = sum(len(p) + 2 for p in parts)
            remaining = 280 - base_length
            if remaining > 0:
                summary_text = content[:remaining - 3] + "..." if len(content) > remaining else content
                if summary_text:
                    parts.append(f"📝 {summary_text}")
            
            post_text = "\n\n".join(parts)
            
            # 最終チェック
            if len(post_text) > 280:
                post_text = post_text[:277] + "..."
        
        return post_text
    
    def post_articles_to_bluesky(self, top5_articles: List[Dict]) -> Dict[str, int]:
        """
        TOP5の記事を投稿（新しい構造）
        
        【投稿構造】
        1. TOP5の一覧投稿（題名と短縮リンクのみ）
        2. 各記事の詳細要約投稿（250文字の要約、1位から5位まで）
        
        Args:
            top5_articles: TOP5の記事リスト
        
        Returns:
            {"success": 成功数, "failed": 失敗数}
        """
        success_count = 0
        failed_count = 0
        
        print(f"\n{'='*60}")
        print(f"📤 TOP5を投稿中（新しい構造）...")
        print(f"{'='*60}")
        
        # 1. TOP5の一覧投稿
        print(f"\n[0/6] TOP5一覧投稿を作成中...")
        summary_post = self.create_top5_summary_post(top5_articles)
        
        print(f"投稿内容:\n{'-'*60}\n{summary_post}\n{'-'*60}")
        print(f"文字数: {len(summary_post)}/280")
        
        result = self.poster.post(summary_post)
        if result and result.get('success'):
            print(f"✅ TOP5一覧投稿成功!")
            success_count += 1
        else:
            print(f"⚠️ TOP5一覧投稿失敗")
            failed_count += 1
        
        # 投稿間隔
        print(f"⏳ 次の投稿まで5秒待機...")
        time.sleep(5)
        
        # データベースセッションを準備（投稿記録用）
        db = SessionLocal()
        posted_urls = []  # 投稿成功した記事のURLを記録
        
        try:
            # 2. 各記事の詳細要約投稿（1位から5位まで）
            for i, article in enumerate(top5_articles, 1):
                rank = article.get('rank', i)
                title = article.get('title', '無題')
                url = article.get('url', '')
                
                print(f"\n[{i}/5] 詳細要約投稿準備中: {title[:50]}...")
                
                # 投稿テキストを作成（250文字の要約）
                post_text = self.create_detail_post(article, rank)
                
                print(f"投稿内容:\n{'-'*60}\n{post_text}\n{'-'*60}")
                print(f"文字数: {len(post_text)}/280")
                
                # 投稿
                result = self.poster.post(post_text)
                
                if result and result.get('success'):
                    print(f"✅ TOP{rank} 詳細要約投稿成功!")
                    success_count += 1
                    # 投稿成功した記事のURLを記録
                    if url:
                        posted_urls.append(url)
                else:
                    print(f"⚠️ TOP{rank} 詳細要約投稿失敗")
                    failed_count += 1
                
                # 連続投稿の間隔を空ける（スパム判定回避）
                if i < len(top5_articles):
                    print(f"⏳ 次の投稿まで5秒待機...")
                    time.sleep(5)
            
            # 投稿成功した記事をデータベースに記録
            if posted_urls:
                print(f"\n💾 投稿履歴をデータベースに記録中...")
                for url in posted_urls:
                    try:
                        mark_article_as_posted(db, url)
                    except Exception as e:
                        print(f"⚠️ 投稿履歴の記録エラー ({url[:50]}...): {e}")
                print(f"✅ {len(posted_urls)}件の投稿履歴を記録しました")
        finally:
            db.close()
        
        print(f"\n{'='*60}")
        print(f"📊 投稿結果: 成功 {success_count}件 / 失敗 {failed_count}件")
        print(f"   - 一覧投稿: 1件")
        print(f"   - 詳細要約投稿: {len(top5_articles)}件")
        print(f"{'='*60}")
        
        return {"success": success_count, "failed": failed_count}
    
    def run(self):
        """メイン処理"""
        print(f"\n{'='*60}")
        print(f"🚀 WIRED記事TOP5投稿Bot 開始")
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
            
            # 3. TOP5を個別にBlueskyに投稿
            result = self.post_articles_to_bluesky(top5_articles)
            
            # 4. 結果表示
            if result['success'] > 0:
                print(f"\n{'='*60}")
                print(f"✅ すべての処理が完了しました！")
                print(f"\n📊 投稿結果: {result['success']}/{len(top5_articles)}件成功")
                print(f"\n📝 投稿した記事:")
                for i, article in enumerate(top5_articles, 1):
                    print(f"{i}位: {article['title'][:50]}...")
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
    bot = WiredBlueskyBot()
    bot.run()


if __name__ == "__main__":
    main()

