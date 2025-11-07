"""
Gemini APIを使用した記事分析
"""
import os
import json
import google.generativeai as genai
from typing import Dict, Optional

# Gemini API設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY環境変数が設定されていません")

genai.configure(api_key=GEMINI_API_KEY)


class GeminiAnalyzer:
    """Gemini APIを使用した記事分析クラス"""
    
    def __init__(self, model_name: str = "gemini-pro"):
        self.model = genai.GenerativeModel(model_name)
    
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
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
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
        X投稿用のテキストを生成
        
        Args:
            title: 記事タイトル
            summary: 記事要約
            theme: テーマ
            url: 記事URL
        
        Returns:
            投稿用テキスト（280文字以内）
        """
        prompt = f"""
以下の情報から、X（旧Twitter）に投稿するテキストを生成してください。

タイトル: {title}
テーマ: {theme}
要約: {summary}
URL: {url or "なし"}

要件:
- 280文字以内
- ハッシュタグを1-2個含める
- 興味を引く書き出し
- URLがある場合は最後に含める
- 日本語で記述

投稿テキストのみを出力してください（余計な説明は不要）:
"""
        
        try:
            response = self.model.generate_content(prompt)
            tweet_text = response.text.strip()
            
            # 280文字制限
            if len(tweet_text) > 280:
                tweet_text = tweet_text[:277] + "..."
            
            return tweet_text
            
        except Exception as e:
            print(f"⚠️ ツイート生成エラー: {e}")
            # フォールバック
            fallback = f"📰 {title}\n\n{summary[:200]}"
            if url:
                fallback += f"\n\n{url}"
            return fallback[:280]

