"""
OpenAI Responses API + Web searchを使用した記事取得モジュール
"""
import os
import re
import time
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urlparse
from openai import OpenAI, NotFoundError, BadRequestError
import feedparser


class OpenAIResearcher:
    """OpenAI Responses API + Web searchを使用して記事を取得するクラス"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = None):
        """
        初期化
        
        Args:
            api_key: OpenAI APIキー（Noneの場合は環境変数から取得）
            model: 使用するモデル名（Noneの場合は環境変数から取得、デフォルト: gpt-4o-mini-search-preview）
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY環境変数が設定されていません")
        
        # 検索対応モデルを既定にする（必要なら環境変数で上書き）
        self.model_primary = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini-search-preview")
        self.model_fallback = os.getenv("OPENAI_MODEL_FALLBACK", "gpt-4o-search-preview")
        
        self.client = OpenAI(
            api_key=self.api_key,
            timeout=600.0  # 10分のタイムアウト
        )
        # リトライ設定
        self.max_retries = 3
        self.base_delay = 1.0  # 指数バックオフのベース遅延（秒）
    
    def run_deep_research(self, themes: str) -> str:
        """
        調査用プロンプトを Responses API（Web search有効）で実行し、検索結果に基づく出力を得る
        
        Args:
            themes: カンマ区切りのテーマリスト（例: "AI, ブロックチェーン, 量子コンピュータ"）
        
        Returns:
            調査結果のテキスト
        """
        theme_list = '\n'.join([f"- {t.strip()}" for t in themes.split(',')])
        theme_count = len(themes.split(','))
        
        # プロンプトを構築（Responses API + Web searchツールで実検索を実行）
        input_prompt = f"""1. 【最重要原則】厳格なフォーマットと**ファクトの厳守**

あなたの全タスクは、以下の**3つの優先原則**を厳守することに基づきます。

1) **🚨 ファクト厳守（最優先）**：

   - **必ずWeb検索の**検索結果から抽出された**実在するニュース記事・動画**のみを引用してください。

   - 検索結果に存在しない**架空の記事**、**架空のタイトル**、**架空のURL**を**創作することは絶対に禁止**します。

   - 記事タイトル、記事リンクは、**検索結果のスニペットに記載された情報をそのまま引用すること**を最優先とします。

   - **【緩和】掲載年月日と引用元:** 検索スニペットから**明確に**情報が得られない場合は、**推測せず**、その項目に「不明」や「検索結果未記載」と記述してください。ただし、**記事タイトルとURLの存在確認は絶対**です。

   - 検索結果に見当たらない場合は、件数を減らすか、該当テーマの記事を省略してください。

2) **厳格なフォーマットの遵守（次点）**:

   - 以下の出力構造を絶対的に遵守してください。

   出力構造: 必ずテーマごとにセクションを分け、以下の7項目を**指定された順序**で出力してください。

   【テーマX：(ここにテーマ名が入る)】

   記事タイトル: (元記事のタイトルをそのまま記載。検索結果からそのまま引用)

   引用元: (メディアの正式名称を記載。検索結果からそのまま引用、**不明な場合は「検索結果未記載」と明記**)

   掲載年月日: (記事が公開された年月日を明記。検索結果からそのまま引用、**不明な場合は「検索結果未記載」と明記**)

   記事リンク: (元記事へ直接アクセスできるURLを**必ず記載**。検索結果からそのまま引用)

クリッピング理由: (この記事が「Weak Signal」として重要だと判断した理由を簡潔に記述)

   記事要約 (150字以内): (記事の要点を150字以内で要約。**検索結果に記載の情報を超えて創作しない**)

未来の兆し (150字以内): (このニュースから読み取れる未来の兆し・示唆・発見を記述)

   区切り線: テーマとテーマの間には、必ず区切り線 --- を挿入してください。

   件数: テーマ数 × 2件という選定総数（今回は{theme_count}テーマなので{theme_count * 2}件）を満たすよう**努力**してください。

   禁止事項: 「レポート」形式での出力や、要約・序論・結論・考察といった指定外の文章は一切生成しないでください。挨拶も不要です。

3) **質の高い分析（第三位）**:

   - あなたの「未来学者」としての役割は、「クリッピング理由」と「未来の兆し」の**2つの項目を記述する際にのみ適用**してください。それ以外の項目や全体の構成には、一切の創造性を加えないでください。

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

情報源: 記事選択の**質のベンチマーク**として【指定メディアリスト】を**参照**し、**信頼性の高い**記事を選択してください。リスト外の記事であっても、客観性・検証性・編集価値が高いと判断できるものは許可します。

※以下のようなソースは使用禁止とします：
　　- 企業が発信するプレスリリース媒体（例：PR TIMES、@Press、ValuePressなど）
　　- 個人や企業による発信内容をそのまま掲載している広告・広報系メディア
　　- 一般ユーザーが執筆するブログ・エッセイ系プラットフォーム（例：note、アメブロ、はてなブログ、個人WordPressサイト等）
これらは客観性・検証性・編集価値に乏しく、未来洞察に必要な信頼性や示唆の深さを欠くため対象外とします。

鮮度: 掲載・公開日が現在から3ヶ月以内の最新ニュースに限定してください。

**【⚠️ 創作の絶対禁止と検証の強制 ⚠️】**

- **あなたのタスクは、検索で得られたファクトの「抽出」と「分析」であり、コンテンツの「創作」ではありません。**

- **記事タイトル、引用元、掲載年月日、記事リンク**は、**検索結果のテキストからそのまま引用**するフィールドであり、あなたの創造性を一切加えてはなりません。

- **検索結果に完全な情報（タイトル、URL、日付）が揃っていない記事は、不確実性があるため採用しないでください。**

- 必ず実在するニュース記事・動画のみを引用してください（Web検索の検索結果から抽出されたもの）

- 存在しない記事を創作・生成することは固く禁じます。これは絶対に禁止です。

- 推測や想像に基づいた記事を作成しないでください

- 実際に公開されている記事のURLのみを使用してください（検索結果からそのまま引用）

- 存在しない記事のURLを生成・創作することは絶対に禁止です

- 各記事のURLは、実際にそのメディアサイトで公開されている記事のURLである必要があります

- 推測や想像に基づいたURLを記載しないでください

- 記事タイトル、引用元、掲載年月日、記事リンクは、すべて検索結果のスニペットと一致している必要があります

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

1. **すべての情報（タイトル、URL、引用元、日付）がWeb検索の**検索結果からそのまま**引用**された実在する情報か。

2. **存在しない記事を創作していないか（最も重大な違反）。**

3. **推測や想像に基づいた情報（特にタイトルとURL）を含めていないか。**

4. すべてのURLが実際にアクセス可能か。

⚠️⚠️⚠️ 最重要：もし実際に存在する記事が見つからない場合は、**件数にこだわる必要はありません**。件数を減らすか、該当テーマの記事を省略してください。存在しない記事を創作することは**絶対に禁止**です。これは最も重大な違反です。⚠️⚠️⚠️

実際に存在する**Web検索で確認できた**記事のみを出力してください。"""
        
        try:
            # 検索対応モデル + Web search ツールで実行
            response = self._call_openai_with_retry(input_prompt)
            
            # Responses API は output_text が便利（なければ自力で組み立て）
            if hasattr(response, "output_text") and response.output_text:
                return response.output_text
            
            # 念のためのフォールバック（content配列を連結）
            if hasattr(response, "output") and response.output:
                try:
                    chunks = []
                    for item in response.output:
                        for c in getattr(item, "content", []) or []:
                            if getattr(c, "type", "") == "output_text":
                                chunks.append(c.text)
                    if chunks:
                        return "\n".join(chunks)
                except Exception:
                    pass
            
            # さらにフォールバック（choices互換）
            if hasattr(response, 'choices') and len(response.choices) > 0:
                choice = response.choices[0]
                if hasattr(choice, 'message'):
                    if hasattr(choice.message, 'content'):
                        return choice.message.content
                    elif hasattr(choice.message, 'text'):
                        return choice.message.text
                if hasattr(choice, 'content'):
                    return choice.content
                if hasattr(choice, 'text'):
                    return choice.text
                return str(choice)
            
            # 最後のフォールバック
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
    
    def _call_openai_with_retry(self, prompt: str, max_retries: Optional[int] = None, base_delay: Optional[float] = None):
        """
        OpenAI API呼び出しをリトライ付きで実行
        
        Args:
            prompt: プロンプトテキスト
            max_retries: 最大リトライ回数（Noneの場合はself.max_retriesを使用）
            base_delay: 指数バックオフのベース遅延（Noneの場合はself.base_delayを使用）
        
        Returns:
            chat.completions.createのレスポンス
        """
        max_retries = max_retries or self.max_retries
        base_delay = base_delay or self.base_delay
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    delay = base_delay * (2 ** (attempt - 1))  # 指数バックオフ
                    print(f"⏳ リトライ {attempt}/{max_retries} (待機時間: {delay:.1f}秒)")
                    time.sleep(delay)
                
                # 1) Responses API（web_searchツール）
                try:
                    response = self.client.responses.create(
                        model=self.model_primary,
                        input=[
                            {
                                "role": "system",
                                "content": "あなたは未来洞察の専門家です。必ず実在する記事だけを引用し、出典を明示してください。"
                            },
                            {"role": "user", "content": prompt},
                        ],
                        tools=[{"type": "web_search"}],
                        temperature=0.3,
                        max_output_tokens=4000,
                    )
                except BadRequestError as bre:
                    # 2) 「Responses API非対応」エラー → Chat Completions で同一モデルを叩く
                    if "not supported with the Responses API" in str(bre) or "400" in str(bre):
                        print(f"ℹ️ Responses API非対応のため、Chat Completionsで同一モデルを使用します")
                        # search-preview系モデルはtemperatureを受け付けないため削除
                        response = self.client.chat.completions.create(
                            model=self.model_primary,
                            messages=[
                                {
                                    "role": "system",
                                    "content": "あなたは未来洞察の専門家です。必ず実在する記事だけを引用し、出典を明示してください。"
                                },
                                {"role": "user", "content": prompt},
                            ],
                            max_tokens=4000,
                        )
                    else:
                        raise
                except NotFoundError:
                    # 3) モデル未開放 → フォールバックモデルに切替（Responses→ダメならChatへ）
                    print(f"⚠️ モデル {self.model_primary} へアクセス不可。{self.model_fallback} にフォールバックします")
                    try:
                        response = self.client.responses.create(
                            model=self.model_fallback,
                            input=[
                                {
                                    "role": "system",
                                    "content": "あなたは未来洞察の専門家です。必ず実在する記事だけを引用し、出典を明示してください。"
                                },
                                {"role": "user", "content": prompt},
                            ],
                            tools=[{"type": "web_search"}],
                            temperature=0.3,
                            max_output_tokens=4000,
                        )
                    except BadRequestError:
                        # Responses API非対応ならChat Completionsで試す
                        # search-preview系モデルはtemperatureを受け付けないため削除
                        response = self.client.chat.completions.create(
                            model=self.model_fallback,
                            messages=[
                                {
                                    "role": "system",
                                    "content": "あなたは未来洞察の専門家です。必ず実在する記事だけを引用し、出典を明示してください。"
                                },
                                {"role": "user", "content": prompt},
                            ],
                            max_tokens=4000,
                        )
                
                if attempt > 0:
                    print(f"✅ リトライ成功（試行回数: {attempt + 1}）")
                return response
                
            except Exception as e:
                last_exception = e
                error_type = type(e).__name__
                error_str = str(e).lower()
                
                # レート制限エラー（429）
                if "429" in error_str or "rate limit" in error_str or "quota" in error_str:
                    print(f"⚠️ レート制限エラー (429): {e}")
                    if attempt < max_retries:
                        continue
                    raise
                # サーバーエラー（500, 502, 503）
                elif "500" in error_str or "502" in error_str or "503" in error_str or "service unavailable" in error_str or "internal server error" in error_str:
                    print(f"⚠️ サーバーエラー: {e}")
                    if attempt < max_retries:
                        continue
                    raise
                # タイムアウト
                elif "timeout" in error_str or "timed out" in error_str:
                    print(f"⚠️ タイムアウトエラー: {e}")
                    if attempt < max_retries:
                        continue
                    raise
                else:
                    # リトライ不可なエラーは即座に再発生
                    print(f"❌ リトライ不可なエラー ({error_type}): {e}")
                    raise
        
        # すべてのリトライが失敗した場合
        print(f"❌ 最大リトライ回数 ({max_retries}) に達しました。最後のエラー: {last_exception}")
        raise last_exception
    
    def parse_research_results(self, research_text: str) -> List[Dict]:
        """
        DeepResearchの結果をパースして記事データのリストに変換
        
        Args:
            research_text: DeepResearchの結果テキスト
        
        Returns:
            記事データのリスト（url, title, content, published_at, theme, clipping_reason, summary, future_signalを含む）
        """
        articles = []
        
        # テーマごとにセクションを分割（全角/半角コロン両対応）
        theme_sections = re.split(r'【テーマ\d+[:：]', research_text)
        
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
    
    def _clean_url(self, url: str) -> str:
        """
        URLから装飾やマークダウンを除去
        
        Args:
            url: 元のURL文字列
        
        Returns:
            クリーンアップされたURL
        """
        if not url:
            return url
        
        u = url.strip()
        
        # 先頭の装飾除去
        for pref in ["**", "*", "<", "(", "[", "：", ":", "|"]:
            if u.startswith(pref):
                u = u[len(pref):].lstrip()
        
        # 末尾の装飾除去
        for suf in ["**", "*", ">", ")", "]", "|", "。", "、", ",", "."]:
            if u.endswith(suf):
                u = u[:-len(suf)].rstrip()
        
        # 余計な全角/半角スペース除去
        u = u.strip()
        
        return u
    
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
            url = self._clean_url(url) if url else None
            
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
        print(f"🔍 OpenAI Responses API ({self.model_primary}) で記事検索を実行中: {themes}")
        
        # まずはLLMの"DeepResearch風"出力を試す（互換維持）
        try:
            research_text = self.run_deep_research(themes)
            articles = self.parse_research_results(research_text)
        except Exception as e:
            print(f"⚠️ LLM出力解析に失敗: {e}")
            articles = []
        
        if articles:
            print(f"✅ {len(articles)}件の記事を取得（LLM）")
            return articles
        
        # ====== ここからフォールバック：RSSで必ず拾う ======
        print("ℹ️ LLM出力が空だったため、RSSフォールバックで取得します。")
        fb = self._fallback_fetch_from_rss(themes)
        print(f"✅ {len(fb)}件の記事を取得（RSSフォールバック）")
        return fb
    
    # ----------------------------
    # RSSフォールバック実装
    # ----------------------------
    def _fallback_fetch_from_rss(self, themes: str, max_items_per_feed: int = 10) -> List[Dict]:
        """
        RSSフィードから記事を取得（フォールバック用）
        
        Args:
            themes: カンマ区切りのテーマリスト
            max_items_per_feed: フィードごとの最大取得件数
        
        Returns:
            記事データのリスト
        """
        theme_list = [t.strip() for t in themes.split(",") if t.strip()]
        
        # テーマ別RSSフィードマップ
        rss_map = {
            "AI": [
                "https://openai.com/blog/rss.xml",
                "https://www.deepmind.com/blog/rss.xml",
                "https://arxiv.org/rss/cs.AI",
                "https://hnrss.org/newest?points=50&count=100",
            ],
            "生成AI": [
                "https://huggingface.co/blog/feed.xml",
                "https://stability.ai/blog?format=rss",
                "https://replicate.com/site/blog.atom",
            ],
            "AIエージェント": [
                "https://www.anthropic.com/news/rss.xml",
                "https://www.semianalysis.com/feed",
            ],
        }
        
        feeds: List[str] = []
        for t in theme_list:
            feeds.extend(rss_map.get(t, []))
        
        # テーマがマップ外でも最低限いくつか当てる
        if not feeds:
            feeds = [
                "https://www.technologyreview.com/feed/",
                "https://wired.jp/rssfeeder/",
                "https://techcrunch.com/feed/",
            ]
        
        seen = set()
        out: List[Dict] = []
        now = datetime.utcnow()
        
        for url in feeds:
            try:
                parsed = feedparser.parse(url)
                for e in parsed.entries[:max_items_per_feed]:
                    link = getattr(e, "link", "") or ""
                    if not link or link in seen or not self._validate_url(link):
                        continue
                    seen.add(link)
                    
                    title = (getattr(e, "title", "") or "").strip()
                    source = urlparse(link).netloc
                    
                    # 日付（なければNone）
                    published = None
                    for key in ("published_parsed", "updated_parsed"):
                        val = getattr(e, key, None)
                        if val:
                            try:
                                published = datetime(*val[:6])
                                break
                            except Exception:
                                pass
                    
                    # 3ヶ月制限（厳しめにUTCで判定）
                    if published and (now - published).days > 93:
                        continue
                    
                    theme_for_entry = self._guess_theme_for_entry(title, theme_list)
                    
                    # 本文代替（RSSのsummaryを薄く使う）
                    summary = (getattr(e, "summary", "") or "").strip()
                    content = summary[:5000] if summary else None
                    
                    out.append({
                        "url": link,
                        "title": title or "(無題)",
                        "content": content,
                        "published_at": published,
                        "theme": theme_for_entry,
                        "source": source,
                        "clipping_reason": None,
                        "summary": summary[:300] if summary else None,
                        "future_signal": None,
                    })
            except Exception as ex:
                print(f"⚠️ RSS取得失敗: {url} ({ex})")
                continue
        
        return out
    
    def _guess_theme_for_entry(self, title: str, theme_list: List[str]) -> str:
        """
        タイトルからテーマを推測
        
        Args:
            title: 記事タイトル
            theme_list: テーマリスト
        
        Returns:
            推測されたテーマ
        """
        t = title.lower()
        for theme in theme_list:
            k = theme.lower()
            if k in t:
                return theme
        
        # ヒューリスティック
        if any(k in t for k in ["agent", "autonomous", "tool use"]):
            return "AIエージェント" if "AIエージェント" in theme_list else (theme_list[0] if theme_list else "AI")
        if any(k in t for k in ["genai", "llm", "diffusion", "stable", "gpt", "o4", "4o"]):
            return "生成AI" if "生成AI" in theme_list else (theme_list[0] if theme_list else "AI")
        
        return theme_list[0] if theme_list else "AI"

