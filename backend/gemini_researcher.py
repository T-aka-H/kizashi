"""
Gemini Grounding（Google Search）を使用した記事取得モジュール
"""
import os
import re
from typing import List, Dict, Optional
from datetime import datetime
import google.generativeai as genai


class GeminiResearcher:
    """Gemini Grounding（Google Search）を使用して記事を取得するクラス"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        """
        初期化
        
        Args:
            api_key: Gemini APIキー（Noneの場合は環境変数から取得）
            model: 使用するモデル名
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY環境変数が設定されていません")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model)
    
    def run_deep_research(self, themes: str) -> Dict:
        """
        調査用プロンプトを与えて、Gemini APIに生成を依頼する（Google Search Grounding使用）
        
        Args:
            themes: カンマ区切りのテーマリスト（例: "AI, ブロックチェーン, 量子コンピュータ"）
        
        Returns:
            調査結果の辞書（summary, sourcesを含む）
        """
        theme_list = '\n'.join([f"- {t.strip()}" for t in themes.split(',')])
        theme_count = len(themes.split(','))
        
        # プロンプトを構築（提供されたプロンプトを使用）
        prompt = f"""1. 【最重要指示】タスクの基本原則と優先順位

あなたのタスクは、以下の2つの原則で構成されます。AIとして、いかなる場合もこの優先順位を厳守してください。

1) 厳格なフォーマットの遵守（最優先）:

あなたの全タスクは、以下のフォーマットを絶対的に遵守することに基づきます。いかなる解釈よりもこのフォーマットが優先されます。

出力構造: 必ずテーマごとにセクションを分け、以下の7項目を指定された順序で出力してください。

【テーマX：(ここにテーマ名が入る)】

記事タイトル: (元記事のタイトルをそのまま記載)

引用元: (メディアの正式名称を記載)

掲載年月日: (記事が公開された年月日を明記)

記事リンク: (元記事へ直接アクセスできるURLを必ず記載)

クリッピング理由: (この記事が「Weak Signal」として重要だと判断した理由を簡潔に記述)

記事要約 (150字以内): (記事の要点を150字以内で要約)

未来の兆し (150字以内): (このニュースから読み取れる未来の兆し・示唆・発見を記述)

区切り線: テーマとテーマの間には、必ず区切り線 --- を挿入してください。

件数: テーマ数 × 2件という選定総数（今回は{theme_count}テーマなので{theme_count * 2}件）を厳守してください。

禁止事項: 「レポート」形式での出力や、要約・序論・結論・考察といった指定外の文章は一切生成しないでください。挨拶も不要です。

2) 質の高い分析の実践: 上記の厳格なフォーマットという枠組みの中で、あなたの能力を最大限に発揮してください。特に、あなたの「未来学者」としての役割は、「クリッピング理由」と「未来の兆し」の2つの項目を記述する際にのみ適用してください。それ以外の項目や全体の構成には、一切の創造性を加えないでください。

2. あなたの役割と協業目的

あなたの役割: 複雑な状況から新たな機会を見出す「デザイン思考」を専門とする未来学者として行動してください。

私の役割: 未来洞察研修のファシリテーターです。

協業目的: 私が実施する研修プログラムで使用する「未来の兆し（Weak Signals）」を捉えるためのニュース記事・動画を、あなたが収集・分析し、私に提示することが目的です。

3. クリップ対象の定義：Weak Signals（未来の兆し）

定義: 未来の大きな変化を示唆する、まだ不明確で小さな初期段階の兆候を指します。既存のトレンドや直線的な予測からは見過ごされがちな、非線形的な変化の始まりを捉える手がかりです。

クリッピングの要諦: 誰にでも予測できる明白なニュースではなく、注意深く考察しなければ見落としてしまうような、ユニークかつ微かな「Weak Signals」を含む記事・動画を厳選してください。テーマとの関連性が一見して不明確なものであっても、そこから新たな洞察を引き出すことを歓迎します。

4. 品質のインスピレーションとベンチマーク

模範事例: 選定のセンスや方法論のインスピレーション源として、武蔵野美術大学の岩嵜博論教授のスタイルを参考にしてください。具体的には、一見無関係に見えるAという事象とBという事象が、実はCという未来の兆候を示している、といった『発見』や『仮説』を提示することを意識してください。

NewsPicks: https://newspicks.com/user/134987/

X (旧Twitter): https://x.com/hriwsk

記事の流用: 上記の岩嵜氏のクリッピングの中に、本タスクのテーマ領域に合致する良質な記事があれば、それを選択・引用することを許可します。

5. クリップ対象ニュースの厳格な要件

情報源: 必ず、後述の【指定メディアリスト】から記事を優先的に選択してください。

※以下のようなソースは使用禁止とします：
　　- 企業が発信するプレスリリース媒体（例：PR TIMES、@Press、ValuePressなど）
　　- 個人や企業による発信内容をそのまま掲載している広告・広報系メディア
　　- 一般ユーザーが執筆するブログ・エッセイ系プラットフォーム（例：note、アメブロ、はてなブログ、個人WordPressサイト等）
これらは客観性・検証性・編集価値に乏しく、未来洞察に必要な信頼性や示唆の深さを欠くため対象外とします。

鮮度: 掲載・公開日が現在から3ヶ月以内の最新ニュースに限定してください。TT

【⚠️⚠️⚠️ 最重要：実在性の厳格な遵守 ⚠️⚠️⚠️】

🚨🚨🚨 絶対に守るべき原則（これ以上強調できないほど重要）🚨🚨🚨

- 必ず実在するニュース記事・動画のみを引用してください
- 存在しない記事を創作・生成することは固く禁じます。これは絶対に禁止です。
- 推測や想像に基づいた記事を作成しないでください
- 実際に公開されている記事のURLのみを使用してください
- 存在しない記事のURLを生成・創作することは絶対に禁止です
- 各記事のURLは、実際にそのメディアサイトで公開されている記事のURLである必要があります
- 推測や想像に基づいたURLを記載しないでください
- 記事タイトル、引用元、掲載年月日、記事リンクは、すべて実際の記事と一致している必要があります
- Google Searchで実際に検索して、存在する記事のみを選択してください
- 存在しない記事を創作して件数を満たすことは絶対に禁止です
- 実在する記事が見つからない場合は、件数を減らすか、該当テーマの記事を省略してください
- 存在しない記事を創作することは、このタスクの最も重大な違反です

信頼性: 信頼性の高いニュースソースに限定し、個人ブログのような記事は避けてください。

独自性: 広く知られたメジャーな記事よりも、まだ多くの人が気づいていない未来の兆しを示唆する、マイナーながらも示唆に富む記事や動画を優先してください。

6. 海外メディアの記事・動画を扱う場合の特記事項

翻訳タイトル: 英語の元タイトルと日本語訳を併記してください。

記事要約とクリッピング理由: 日本語で記述してください。

未来の兆し: 日本語訳に加え、原文（英語）も必ず併記してください。

【指定メディアリスト】

日本の未来志向メディア（50社）

Business Insider Japan — https://www.businessinsider.jp
Tokyoesque Insights — https://tokyoesque.com/insights
J‑Stories — https://jstories.media
日経 xTECH — https://xtech.nikkei.com
WIRED Japan — https://wired.jp
東洋経済オンライン — https://toyokeizai.net
ダイヤモンド・オンライン — https://diamond.jp
NewsPicks — https://newspicks.com
Forbes JAPAN — https://forbesjapan.com
ITmedia I-magazine — https://www.itmedia.co.jp/im
プレジデントオンライン — https://president.jp
日経 Social Innovation — https://project.nikkeibp.co.jp/innovation
日経未来完了形 — https://future.nikkei.com
東洋経済 FUTURE — https://toyokeizai.net/list/future
NHK 未来探検隊 — https://www.nhk.or.jp/miraiproject
Z世代ジャパン — https://genz-japan.com
TechCrunch Japan — https://jp.techcrunch.com
Foresight Japan（東洋経済） — https://foresight.toyokeizai.net
三菱総研 未来洞察 — https://www.mri.co.jp/knowledge/column/future.html
慶應SFC未来構想キャンパス — https://www.kri.sfc.keio.ac.jp
IFTF（翻訳記事含む） — https://www.iftf.org
Future Today Institute（Amy Webb） — https://futuretodayinstitute.com
Exponential View（Azeem Azhar） — https://www.exponentialview.co
Institute for the Future — https://www.iftf.org
日経BP未来レポート — https://www.nikkeibp.co.jp
日経Automotive NEXT — https://xtech.nikkei.com/atcl/nxt
日経BPヘルスケアイノベーション — https://health.nikkeibp.co.jp
日経グリーン — https://project.nikkeibp.co.jp/green
ITmedia エンタープライズ — https://www.itmedia.co.jp/enterprise
Impress Watch／＋D — https://www.watch.impress.co.jp/
ASCII.jp Open — https://ascii.jp
CNET Japan — https://japan.cnet.com
産経BizTech — https://www.sankeibiz.jp
日経ZEEK — https://zeek.jp
日経クロストレンド — https://xtrend.nikkei.com
日経FinTech — https://tech.nikkeibp.co.jp/IT/atcl/
日経Smart Manufacturing — https://smart-manufacturing.nikkei.com
日経モビリティInnovate — https://xtech.nikkei.com/atcl/nxt/
日経サイエンス — https://www.nikkei-science.com
Nature ダイジェスト（日・英） — https://www.natureasia.com/
サイエンス＆テクノロジー未来（東洋経済） — https://toyokeizai.net/category/tech
未来創造会議（内閣府） — https://www.miraicon.jp
国際協力銀行リサーチ — https://www.jica.go.jp
OECD Insights 日本語版 — https://www.oecd-ilibrary.org
環境ビジネスオンライン — https://www.kankyo-business.jp
エネルギーフォーラム — https://www.ef.or.jp
農業技術通信 — https://www.agridata.jp
医療・介護テックレビュー — https://medical-tribune.co.jp
ロボスタ（ロボットスタート） — https://robotstart.info
デジタル庁公開レポート — https://www.digital.go.jp

海外の未来志向メディア（20社）

WIRED (Global) — https://www.wired.com
MIT Technology Review — https://www.technologyreview.com
Rest of World — https://restofworld.org
Foresight (UK journal) — https://www.emerald.com/insight/publication/issn/1463-6689
TIME — https://time.com
Financial Times — https://www.ft.com
Axios Media Trends — https://www.axios.com/newsletters/axios-media-trends
The Guardian — https://www.theguardian.com
Le Monde (English版) — https://www.lemonde.fr/en
The Conversation — https://theconversation.com/global
Deloitte Insights (Tech & Media) — https://www.deloitte.com/insights
PwC Media & Entertainment Insights — https://www.pwc.com
EY Media & Entertainment Trends — https://www.ey.com/insights
Reuters Institute Trends — https://reutersinstitute.politics.ox.ac.uk
McKinsey Insights Tech & Media — https://www.mckinsey.com/industries/media
Gartner Emerging Tech — https://www.gartner.com/en/information-technology
Future Trends Group — https://www.future-trends.us
Global Broadcast Industry — https://www.globalbroadcastindustry.news
TechCrunch (Global) — https://techcrunch.com
Crunchbase News — https://news.crunchbase.com

日本の未来志向動画ニュースサイト（40社）

NHK WORLD-JAPAN — https://www.youtube.com/@NHKWORLDJAPAN
TBS NEWS DIG Powered by JNN — https://www.youtube.com/@tbsnewsdig
TBS CROSS DIG with Bloomberg — https://www.youtube.com/@tbs_bloomberg
ANNnewsCH（テレ朝ニュース） — https://www.youtube.com/@ANNnewsCH
日本経済新聞 — https://www.youtube.com/@nikkei
日経CNBC — https://www.youtube.com/@NikkeiCNBC
THE NIKKEI MAGAZINE — https://www.youtube.com/@thenikkeimagazine
The Asahi Shimbun Company — https://www.youtube.com/@asahicom
テレ東BIZ — https://www.youtube.com/@tvtokyobiz
WIRED Japan — https://www.youtube.com/@wiredjp
TechCrunch Japan — https://www.youtube.com/@TechCrunchJapan
ITmedia NEWS — https://www.youtube.com/@itmedia
ダイヤモンド公式チャンネル — https://www.youtube.com/@diamond-inc
ソーシャル・イノベーション・スクールチャンネル — https://www.youtube.com/@SocialInnovationSchool
ReHacQ−リハック−【公式】 — https://www.youtube.com/@rehacq
PIVOT 公式チャンネル — https://www.youtube.com/@pivot00
ABEMAニュース【公式】 — https://www.youtube.com/@News_ABEMA
ABEMA Prime #アベプラ【公式】 — https://www.youtube.com/@prime_ABEMA
中田敦彦のYouTube大学（NAKATA UNIVERSITY） — https://www.youtube.com/@NKTofficial
MIT テクノロジーレビュー[日本版] — https://www.youtube.com/@techreviewjp
nikkeibp（日経BP） — https://www.youtube.com/@nikkeibp
日経BP 日本経済新聞出版 — https://www.youtube.com/@bp4942
Impress Watch — https://www.youtube.com/@ImpressWatchChannel
BLOGOSチャンネル — https://www.youtube.com/@ldblogos
東洋経済オンライン — https://www.youtube.com/@toyokeizai
Forbes JAPAN — https://www.youtube.com/@ForbesJAPAN
NewsPicks — https://www.youtube.com/@newspicks
プレジデントオンライン — https://www.youtube.com/@presidentonline
ロボスタ（ロボットスタート） — https://www.youtube.com/@robotstart
デジタル庁 — https://www.youtube.com/@digitalgovjp
SCIENCE CHANNEL（JST） — https://www.youtube.com/@jst_science
朝日新聞LIVE — https://www.youtube.com/@LIVE-hr9eo
PAD : PC Watch & AKIBA PC Hotline! — https://www.youtube.com/@pad-impress
テクノロジーニュースジャパン — https://www.youtube.com/@technologynewsjapan
日経xTECH — https://www.youtube.com/@nikkeiatech
オリエンタルラジオ- Oriental Radio — https://www.youtube.com/@oriental_radio
CyberAgent — https://www.youtube.com/@CyberAgentOfficial
SoftBank — https://www.youtube.com/@SoftBankJapan
Future Design Shibuya — https://www.youtube.com/@futuredesignshibuya
NHK（総合） — https://www.youtube.com/@nhk

海外の未来志向動画ニュースサイト（30社）

BBC News — https://www.youtube.com/@BBCNews
CNN — https://www.youtube.com/@CNN
Reuters — https://www.youtube.com/@Reuters
Sky News — https://www.youtube.com/@SkyNews
The Wall Street Journal — https://www.youtube.com/@wsj
The New York Times — https://www.youtube.com/@nytimes
Washington Post — https://www.youtube.com/@washingtonpost
Bloomberg Technology — https://www.youtube.com/@BloombergTechnology
CNBC — https://www.youtube.com/@CNBC
MIT Technology Review — https://www.youtube.com/@MITTechnologyReview
The Verge — https://www.youtube.com/@theverge
TechCrunch — https://www.youtube.com/@TechCrunch
Ars Technica — https://www.youtube.com/@arstechnica
VICE News — https://www.youtube.com/@VICENews
Science Magazine — https://www.youtube.com/@ScienceMagazine
Nature Video — https://www.youtube.com/@naturevideo
TED — https://www.youtube.com/@TED
TED-Ed — https://www.youtube.com/@TEDEd
TEDx Talks — https://www.youtube.com/@TEDxTalks
Kurzgesagt – In a Nutshell — https://www.youtube.com/@Kurzgesagt
AsapSCIENCE — https://www.youtube.com/@AsapSCIENCE
AI Explained — https://www.youtube.com/@aiexplained-official
WIRED (Global) — https://www.youtube.com/@WIRED
Financial Times — https://www.youtube.com/@FinancialTimes
The Guardian — https://www.youtube.com/@TheGuardian
TIME — https://www.youtube.com/@TIME
Axios — https://www.youtube.com/@axios
Vox — https://www.youtube.com/@Vox
ColdFusion — https://www.youtube.com/@ColdFusion
World Economic Forum — https://www.youtube.com/@WorldEconomicForum

【今回のテーマ】

{theme_list}

【最終確認事項】

出力前に必ず以下を確認してください：

1. すべての記事が実際に存在するか（Google Searchで検証済みか）
2. すべてのURLが実際にアクセス可能か
3. 存在しない記事を創作していないか
4. 推測や想像に基づいた情報を含めていないか
5. すべての情報が検証可能か

⚠️⚠️⚠️ 最重要：もし実際に存在する記事が見つからない場合は、件数を減らすか、該当テーマの記事を省略してください。存在しない記事を創作することは絶対に禁止です。これは最も重大な違反です。⚠️⚠️⚠️

実際に存在する記事のみを出力してください。"""
        
        try:
            # Gemini APIでGoogle Search Groundingを使用
            # 方式A: 呼び出し時だけtoolsを渡す（モデル作成時には渡さない）
            # payload辞書を作成して、toolsを安全に追加
            tools = [{"google_search_retrieval": {}}]
            payload = {
                "contents": prompt,
                "tools": tools
            }
            
            # 再発防止ログ（デバッグ用）
            print(f"🔍 generate_content呼び出し: keys={list(payload.keys())}")
            
            response = self.model.generate_content(**payload)
            
            # レスポンスからテキストを取得
            summary = response.text
            
            # Groundingメタデータからソースを取得
            sources = []
            if hasattr(response, 'candidates') and len(response.candidates) > 0:
                candidate = response.candidates[0]
                
                # grounding_metadataの取得を試みる
                if hasattr(candidate, 'grounding_metadata'):
                    grounding_metadata = candidate.grounding_metadata
                    if hasattr(grounding_metadata, 'grounding_chunks'):
                        grounding_chunks = grounding_metadata.grounding_chunks
                        if isinstance(grounding_chunks, list):
                            # Webソースのみをフィルタリング
                            sources = [
                                chunk for chunk in grounding_chunks
                                if hasattr(chunk, 'web') and chunk.web
                            ]
                # 別の形式の可能性も確認
                elif hasattr(candidate, 'groundingMetadata'):
                    grounding_metadata = candidate.groundingMetadata
                    if hasattr(grounding_metadata, 'groundingChunks'):
                        grounding_chunks = grounding_metadata.groundingChunks
                        if isinstance(grounding_chunks, list):
                            sources = [
                                chunk for chunk in grounding_chunks
                                if hasattr(chunk, 'web') and chunk.web
                            ]
            
            return {
                'summary': summary,
                'sources': sources,
                'prompt': prompt
            }
                
        except TypeError as e:
            # toolsが二重に渡されている場合のエラーハンドリング
            if "multiple values for keyword argument 'tools'" in str(e):
                print(f"❌ エラー: toolsが二重に指定されています")
                print(f"   詳細: {e}")
                raise ValueError("Invalid request: tools specified multiple times. Please check generate_content call.")
            raise
        except Exception as e:
            print(f"⚠️ Gemini Groundingエラー: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def parse_research_results(self, research_text: str, sources: List = None) -> List[Dict]:
        """
        DeepResearchの結果をパースして記事データのリストに変換
        
        Args:
            research_text: DeepResearchの結果テキスト
            sources: Groundingソースのリスト（オプション）
        
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
                article = self._parse_article_block(block, theme, sources)
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
    
    def _parse_article_block(self, block: str, theme: str, sources: List = None) -> Optional[Dict]:
        """
        記事ブロックをパース
        
        Args:
            block: 記事ブロックのテキスト
            theme: テーマ名
            sources: Groundingソースのリスト（オプション）
        
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
            
            # URLが見つからない場合、Groundingソースから取得を試みる
            if not url and sources:
                # タイトルに基づいてソースを検索
                for source_chunk in sources:
                    if hasattr(source_chunk, 'web'):
                        web = source_chunk.web
                        # uriまたはurl属性を確認
                        source_url = None
                        if hasattr(web, 'uri'):
                            source_url = web.uri
                        elif hasattr(web, 'url'):
                            source_url = web.url
                        
                        if source_url:
                            # タイトルが一致するか、またはソース名が一致する場合
                            if title and (title.lower() in str(source_url).lower() or 
                                         (source and source.lower() in str(source_url).lower())):
                                url = source_url
                                break
            
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
        print(f"🔍 Gemini Grounding（Google Search）を実行中: {themes}")
        
        # DeepResearchを実行
        research_result = self.run_deep_research(themes)
        
        # 結果をパース（ソース情報も渡す）
        articles = self.parse_research_results(
            research_result['summary'],
            research_result.get('sources', [])
        )
        
        print(f"✅ {len(articles)}件の記事を取得")
        
        return articles
