"""
OpenAI o3-deep-researchを使用した記事取得モジュール
"""
import os
import re
from typing import List, Dict, Optional
from datetime import datetime
from openai import OpenAI


class OpenAIResearcher:
    """OpenAI o3-deep-researchを使用して記事を取得するクラス"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初期化
        
        Args:
            api_key: OpenAI APIキー（Noneの場合は環境変数から取得）
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY環境変数が設定されていません")
        
        self.client = OpenAI(
            api_key=self.api_key,
            timeout=3600 * 1000  # 1時間のタイムアウト
        )
    
    def run_deep_research(self, themes: str) -> str:
        """
        調査用プロンプトを与えて、OpenAI o3-deep-researchに生成を依頼する
        
        Args:
            themes: カンマ区切りのテーマリスト（例: "AI, ブロックチェーン, 量子コンピュータ"）
        
        Returns:
            調査結果のテキスト
        """
        theme_list = '\n'.join([f"- {t.strip()}" for t in themes.split(',')])
        
        # プロンプトを構築（既存のプロンプトを維持）
        input_prompt = f"""以下のテーマについて、Weak Signals（未来の兆し）を捉えるためのニュース記事を調査してください。

【今回のテーマ】
{theme_list}

【調査要件】

1. 【最重要警告：FakeNewsの生成を絶対に禁止】

⚠️ 絶対に守るべき原則：
- 実際に存在する記事・動画のみを引用してください
- 存在しない記事を創作・生成することは固く禁じます
- 推測や想像に基づいた記事を作成しないでください
- 実際にアクセス可能なURLのみを記載してください
- 検証不可能な情報源は使用しないでください

2. 出力フォーマット

以下のフォーマットを厳格に遵守してください：

【テーマX：(テーマ名)】

記事タイトル: (元記事のタイトルをそのまま記載)

引用元: (メディアの正式名称を記載)

掲載年月日: (記事が公開された年月日を明記)

記事リンク: (元記事へ直接アクセスできるURLを必ず記載)

クリッピング理由: (この記事が「Weak Signal」として重要だと判断した理由を簡潔に記述)

記事要約 (120字以内): (記事の要点を150字以内で要約)

未来の兆し (150字以内): (このニュースから読み取れる未来の兆し・示唆・発見を記述)

---

3. 調査要件

- 具体的な数値、トレンド、統計、測定可能な結果を含める
- 信頼性の高い最新の情報源を優先：査読付き研究、健康機関（WHO、CDCなど）、規制機関、製薬会社の業績報告など
- インライン引用を含め、すべてのソースメタデータを返す
- 分析的で、一般論を避け、各セクションがデータに基づく推論をサポートするようにする
- 各テーマにつき2件の記事を選定（テーマ数 × 2件）
- 掲載・公開日が現在から3ヶ月以内の最新ニュースに限定
- 実際に存在する記事のみを引用（存在しない記事を創作しない）

4. 指定メディアリスト（優先的に使用）

日本の未来志向メディア：
Business Insider Japan, Tokyoesque Insights, J‑Stories, 日経 xTECH, WIRED Japan, 東洋経済オンライン, ダイヤモンド・オンライン, NewsPicks, Forbes JAPAN, TechCrunch Japan, など

海外の未来志向メディア：
WIRED (Global), MIT Technology Review, Rest of World, TIME, Financial Times, The Guardian, TechCrunch (Global), など

5. 最終確認事項

出力前に必ず以下を確認：
- すべての記事が実際に存在するか
- すべてのURLが実際にアクセス可能か
- 存在しない記事を創作していないか
- 推測や想像に基づいた情報を含めていないか
- すべての情報が検証可能か

⚠️ もし実際に存在する記事が見つからない場合は、件数を減らすか、該当テーマの記事を省略してください。存在しない記事を創作することは絶対に禁止です。

実際に存在する記事のみを出力してください。"""
        
        try:
            response = self.client.responses.create(
                model="o3-deep-research",
                input=input_prompt,
                tools=[
                    {"type": "web_search_preview"},
                    {"type": "code_interpreter", "container": {"type": "auto"}},
                ],
            )
            
            # レスポンスからコンテンツを取得
            # OpenAI o3-deep-researchのレスポンス構造に合わせて処理
            if hasattr(response, 'choices') and len(response.choices) > 0:
                choice = response.choices[0]
                
                # messageオブジェクトがある場合
                if hasattr(choice, 'message'):
                    if hasattr(choice.message, 'content'):
                        return choice.message.content
                    elif hasattr(choice.message, 'text'):
                        return choice.message.text
                
                # 直接contentがある場合
                if hasattr(choice, 'content'):
                    return choice.content
                
                # textがある場合
                if hasattr(choice, 'text'):
                    return choice.text
                
                # その他の場合は文字列化
                return str(choice)
            else:
                # choicesがない場合はレスポンス全体を文字列化
                if hasattr(response, 'content'):
                    return response.content
                elif hasattr(response, 'text'):
                    return response.text
                else:
                    return str(response)
                
        except Exception as e:
            print(f"⚠️ OpenAI DeepResearchエラー: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def parse_research_results(self, research_text: str) -> List[Dict]:
        """
        DeepResearchの結果をパースして記事データのリストに変換
        
        Args:
            research_text: DeepResearchの結果テキスト
        
        Returns:
            記事データのリスト（url, title, content, published_at, theme, clipping_reason, summary, future_signalを含む）
        """
        articles = []
        
        # テーマごとにセクションを分割
        theme_sections = re.split(r'【テーマ\d+：', research_text)
        
        for section in theme_sections[1:]:  # 最初の要素は空の可能性があるのでスキップ
            # テーマ名を抽出
            theme_match = re.match(r'([^】]+)】', section)
            if not theme_match:
                continue
            
            theme = theme_match.group(1).strip()
            
            # 記事を抽出（区切り線---で分割）
            article_blocks = re.split(r'---', section)
            
            for block in article_blocks:
                article = self._parse_article_block(block, theme)
                if article:
                    articles.append(article)
        
        return articles
    
    def _validate_url(self, url: str) -> bool:
        """
        URLの妥当性を検証
        
        Args:
            url: 検証するURL
        
        Returns:
            妥当なURLかどうか
        """
        if not url:
            return False
        
        # URLの形式をチェック
        if not url.startswith(('http://', 'https://')):
            print(f"⚠️ 無効なURL形式: {url}")
            return False
        
        # 指定メディアリストのドメインかチェック（基本的な検証）
        # 完全な検証は難しいが、少なくとも形式は確認
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if not parsed.netloc:
                print(f"⚠️ 無効なURL（ドメインなし）: {url}")
                return False
        except Exception as e:
            print(f"⚠️ URL解析エラー: {e}")
            return False
        
        return True
    
    def _parse_article_block(self, block: str, theme: str) -> Optional[Dict]:
        """
        記事ブロックをパース
        
        Args:
            block: 記事ブロックのテキスト
            theme: テーマ名
        
        Returns:
            記事データの辞書またはNone
        """
        try:
            # 記事タイトル
            title_match = re.search(r'記事タイトル:\s*(.+?)(?=\n|引用元:)', block, re.DOTALL)
            title = title_match.group(1).strip() if title_match else None
            
            # 引用元
            source_match = re.search(r'引用元:\s*(.+?)(?=\n|掲載年月日:)', block, re.DOTALL)
            source = source_match.group(1).strip() if source_match else None
            
            # 掲載年月日
            date_match = re.search(r'掲載年月日:\s*(.+?)(?=\n|記事リンク:)', block, re.DOTALL)
            date_str = date_match.group(1).strip() if date_match else None
            published_at = self._parse_date(date_str) if date_str else None
            
            # 記事リンク
            url_match = re.search(r'記事リンク:\s*(.+?)(?=\n|クリッピング理由:)', block, re.DOTALL)
            url = url_match.group(1).strip() if url_match else None
            
            # URLの妥当性を検証
            if url and not self._validate_url(url):
                print(f"⚠️ 無効なURLをスキップ: {url}")
                return None
            
            # クリッピング理由
            reason_match = re.search(r'クリッピング理由:\s*(.+?)(?=\n|記事要約)', block, re.DOTALL)
            clipping_reason = reason_match.group(1).strip() if reason_match else None
            
            # 記事要約
            summary_match = re.search(r'記事要約\s*\(150字以内\):\s*(.+?)(?=\n|未来の兆し)', block, re.DOTALL)
            summary = summary_match.group(1).strip() if summary_match else None
            
            # 未来の兆し
            signal_match = re.search(r'未来の兆し\s*\(150字以内\):\s*(.+?)(?=\n|$)', block, re.DOTALL)
            future_signal = signal_match.group(1).strip() if signal_match else None
            
            # 必須フィールドのチェック
            if not title or not url:
                return None
            
            # コンテンツは要約とクリッピング理由を組み合わせる
            content = f"{summary or ''}\n\n{clipping_reason or ''}\n\n{future_signal or ''}".strip()
            
            return {
                'url': url,
                'title': title,
                'content': content[:5000] if content else None,  # 最初の5000文字
                'published_at': published_at,
                'theme': theme,
                'source': source,
                'clipping_reason': clipping_reason,
                'summary': summary,
                'future_signal': future_signal
            }
            
        except Exception as e:
            print(f"⚠️ 記事ブロックパースエラー: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        日付文字列をパース
        
        Args:
            date_str: 日付文字列
        
        Returns:
            datetimeオブジェクトまたはNone
        """
        if not date_str:
            return None
        
        # 様々な日付形式を試す
        date_formats = [
            '%Y年%m月%d日',
            '%Y/%m/%d',
            '%Y-%m-%d',
            '%Y年%m月%d日 %H:%M',
            '%Y/%m/%d %H:%M:%S',
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    def fetch_articles_by_themes(self, themes: str) -> List[Dict]:
        """
        テーマを指定して記事を取得
        
        Args:
            themes: カンマ区切りのテーマリスト
        
        Returns:
            記事データのリスト
        """
        print(f"🔍 OpenAI DeepResearchを実行中: {themes}")
        
        # DeepResearchを実行
        research_text = self.run_deep_research(themes)
        
        # 結果をパース
        articles = self.parse_research_results(research_text)
        
        print(f"✅ {len(articles)}件の記事を取得")
        
        return articles

