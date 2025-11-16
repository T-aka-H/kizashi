"""
OpenAI APIを使用した記事分析（gpt-4o-mini使用）
"""
import os
import json
from openai import OpenAI
from typing import Dict, Optional

# OpenAI API設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY環境変数が設定されていません")

client = OpenAI(api_key=OPENAI_API_KEY)


class OpenAIAnalyzer:
    """OpenAI APIを使用した記事分析クラス（gpt-4o-mini使用）"""
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = model_name
        self.model = model_name  # 互換性のため
        self.client = client
    
    def analyze_article(self, title: str, content: str, url: str = None) -> Dict:
        """
        記事を分析してテーマ、要約、主要ポイントを抽出
        
        Args:
            title: 記事タイトル
            content: 記事本文
            url: 記事URL（オプション）
        
        Returns:
            分析結果の辞書
        """
        prompt = f"""
以下の記事を分析してください。

タイトル: {title}

本文:
{content[:5000]}  # 長い記事の場合は最初の5000文字

以下の形式でJSONで回答してください：
{{
    "theme": "記事の主要テーマ（1-2語）",
    "summary": "記事の要約（100-150文字）",
    "key_points": ["主要ポイント1", "主要ポイント2", "主要ポイント3"],
    "sentiment_score": 0.0-1.0の数値（0.5が中立、1.0が最もポジティブ）,
    "relevance_score": 0.0-1.0の数値（1.0が最も関連性が高い）,
    "should_post": true/false（Xに投稿すべきかどうか）
}}

回答はJSON形式のみで、余計な説明は不要です。
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "あなたは記事分析の専門家です。JSON形式で正確に分析結果を返してください。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # JSONを抽出（```json```で囲まれている場合がある）
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            
            # キーポイントをJSON文字列に変換
            if isinstance(result.get("key_points"), list):
                result["key_points"] = json.dumps(result["key_points"], ensure_ascii=False)
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON解析エラー: {e}")
            print(f"レスポンス: {response_text}")
            # フォールバック
            return {
                "theme": "未分類",
                "summary": content[:150] if content else "要約生成失敗",
                "key_points": json.dumps(["分析エラー"], ensure_ascii=False),
                "sentiment_score": 0.5,
                "relevance_score": 0.5,
                "should_post": False
            }
        except Exception as e:
            print(f"⚠️ 分析エラー: {e}")
            return {
                "theme": "エラー",
                "summary": "分析に失敗しました",
                "key_points": json.dumps([], ensure_ascii=False),
                "sentiment_score": 0.0,
                "relevance_score": 0.0,
                "should_post": False
            }
    
    def generate_tweet_text(self, title: str, summary: str, theme: str, url: str = None) -> str:
        """
        ソーシャルメディア投稿用のテキストを生成
        
        Args:
            title: 記事タイトル
            summary: 記事要約
            theme: テーマ
            url: 記事URL（短縮済み）
        
        Returns:
            投稿用テキスト（280文字以内、URL含む）
        """
        prompt = f"""
以下の情報から、ソーシャルメディア（Bluesky/X）に投稿するテキストを生成してください。

タイトル: {title}
テーマ: {theme}
要約: {summary}
URL: {url or "なし"}

要件:
- 280文字以内（URLを含む）
- ハッシュタグを1-2個含める
- 興味を引く書き出し
- URLがある場合は必ず含める（短縮リンク）
- 日本語で記述

投稿テキストのみを出力してください（余計な説明は不要）:
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "あなたはソーシャルメディア投稿文の作成の専門家です。280文字以内で魅力的な投稿文を作成してください。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            tweet_text = response.choices[0].message.content.strip()
            
            # URLが含まれていない場合、追加（未来の兆しの前）
            if url and url not in tweet_text:
                # 未来の兆しのマーカーを探す
                if "🔮" in tweet_text or "未来" in tweet_text:
                    # 未来の兆しの前にURLを挿入
                    parts = tweet_text.split("🔮")
                    if len(parts) > 1:
                        tweet_text = f"{parts[0]}\n\n{url}\n\n🔮{parts[1]}"
                    else:
                        # 🔮がない場合は最後に追加
                        tweet_text = f"{tweet_text}\n\n{url}"
                else:
                    # 未来の兆しがない場合は最後に追加
                    tweet_text = f"{tweet_text}\n\n{url}"
            
            # 280文字制限（URLを含む）
            if len(tweet_text) > 280:
                # URLを抽出
                url_part = ""
                if url and url in tweet_text:
                    url_part = url
                    tweet_text_without_url = tweet_text.replace(url, "").replace("\n\n\n", "\n\n")
                else:
                    tweet_text_without_url = tweet_text
                
                # URLの長さを考慮して本文を調整
                url_length = len(url_part) + 2 if url_part else 0  # +2は改行分
                max_body_length = 280 - url_length
                
                if len(tweet_text_without_url) > max_body_length:
                    tweet_text_without_url = tweet_text_without_url[:max_body_length - 3] + "..."
                
                # URLを未来の兆しの前に配置
                if "🔮" in tweet_text_without_url:
                    parts = tweet_text_without_url.split("🔮")
                    if len(parts) > 1:
                        tweet_text = f"{parts[0]}\n\n{url_part}\n\n🔮{parts[1]}" if url_part else f"{parts[0]}\n\n🔮{parts[1]}"
                    else:
                        tweet_text = f"{tweet_text_without_url}\n\n{url_part}" if url_part else tweet_text_without_url
                else:
                    tweet_text = f"{tweet_text_without_url}\n\n{url_part}" if url_part else tweet_text_without_url
            
            return tweet_text
        except Exception as e:
            print(f"⚠️ ツイート生成エラー: {e}")
            # フォールバック（URLを必ず含める、280文字以内）
            if url:
                url_length = len(url) + 2  # +2は改行分
                max_summary_length = 280 - len(title) - url_length - 10  # 余裕を持たせる
                fallback = f"📰 {title}\n\n{summary[:max_summary_length]}"
                if len(fallback) + url_length > 280:
                    fallback = f"📰 {title}\n\n{summary[:max_summary_length - url_length - 3]}..."
                fallback = f"{fallback}\n\n{url}"
            else:
                fallback = f"📰 {title}\n\n{summary[:250]}"
                if len(fallback) > 280:
                    fallback = fallback[:277] + "..."
            return fallback
    
    def summarize_ja(self, title: str, content: str, url: str) -> dict:
        """
        記事を日本語で要約し、'未来の兆し'も日本語で1行抽出する。
        
        Args:
            title: 記事タイトル
            content: 記事本文
            url: 記事URL
        
        Returns:
            {"summary_ja": "...", "future_ja": "..."}
        """
        sys = "あなたは日本語の編集者です。出力は必ず日本語。絵文字は🔮のみ許可。"
        
        user = f"""以下の記事を短く日本語で要約し、最後に1行で「未来の兆し」を書いてください。

- どちらも短文。合計で後段の280文字制約に収まりやすいよう簡潔に。
- 専門用語は過度に難しくしない。
- URLやハンドル名は出力に含めない。

[タイトル]
{title or ''}

[本文(先頭抜粋)]
{(content or '')[:2000]}
"""
        
        # Chat Completions/Responses どちらでもOKなよう既存の呼び出しに揃える
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": sys},
                    {"role": "user", "content": user},
                ],
                # search-preview系に温度NGなことがあるので一切渡さない
                max_tokens=500,
            )
            text = resp.choices[0].message.content.strip()
        except Exception as e:
            # 失敗しても英語のままにしない。最小限の整形で返す
            print(f"⚠️ 日本語要約生成エラー: {e}")
            text = "（要約）" + (title or "").strip()
        
        # 非構造→構造化
        # 形式: 先に要約、改行、"未来の兆し: ..."
        lines = [x.strip() for x in text.splitlines() if x.strip()]
        future = ""
        summary = ""
        
        for ln in lines:
            if "未来の兆し" in ln or "未来" in ln:
                future = ln.replace("未来の兆し", "").replace("未来", "").lstrip(":：").strip()
            else:
                # 最初の1行を要約として採用
                if not summary:
                    summary = ln
        
        if not future:
            # ない場合は要約から1フレーズ抽出
            future = "小さな変化が将来の方向を示唆"
        
        return {"summary_ja": summary, "future_ja": future}
    
    def translate_ja(self, text: str) -> str:
        """
        任意の短文を日本語化（保険）。空なら空を返す。
        
        Args:
            text: 翻訳するテキスト
        
        Returns:
            日本語化されたテキスト
        """
        if not text:
            return ""
        
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "必ず自然な日本語に翻訳してください。出力は日本語のみ。"},
                    {"role": "user", "content": text},
                ],
                max_tokens=200,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ 日本語翻訳エラー: {e}")
            return text  # 失敗時は原文を返す（壊さない）

