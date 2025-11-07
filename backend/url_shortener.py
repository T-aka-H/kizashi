"""
URL短縮機能モジュール
"""
import os
import requests
from typing import Optional


class URLShortener:
    """URL短縮クラス"""
    
    def __init__(self):
        """初期化"""
        # TinyURL APIを使用（無料、APIキー不要）
        self.tinyurl_api = "https://tinyurl.com/api-create.php"
    
    def shorten(self, url: str) -> Optional[str]:
        """
        URLを短縮
        
        Args:
            url: 短縮するURL
        
        Returns:
            短縮されたURL、または元のURL（エラー時）
        """
        if not url:
            return None
        
        try:
            # TinyURL APIを使用
            response = requests.get(
                self.tinyurl_api,
                params={"url": url},
                timeout=10
            )
            
            if response.status_code == 200:
                short_url = response.text.strip()
                # TinyURLのレスポンスがURLで始まるか確認
                if short_url.startswith("http"):
                    print(f"✅ URL短縮成功: {url} -> {short_url}")
                    return short_url
                else:
                    print(f"⚠️ TinyURLレスポンスが不正: {short_url}")
                    return url
            else:
                print(f"⚠️ TinyURL APIエラー: {response.status_code}")
                return url
                
        except Exception as e:
            print(f"⚠️ URL短縮エラー: {e}")
            # エラー時は元のURLを返す
            return url
    
    def shorten_if_long(self, url: str, max_length: int = 50) -> str:
        """
        URLが長い場合のみ短縮
        
        Args:
            url: 短縮するURL
            max_length: この長さを超える場合のみ短縮
        
        Returns:
            短縮されたURL、または元のURL
        """
        if not url:
            return url
        
        if len(url) > max_length:
            return self.shorten(url) or url
        else:
            return url

