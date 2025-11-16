"""
ソーシャルメディア投稿クラス（Bluesky対応）

【Render デプロイ対応】
- 環境変数から投稿モードとBluesky認証情報を取得
- POST_MODE=demo でテスト実行可能（デフォルト）
- POST_MODE=bluesky で実際に投稿
"""
import os
import re
from typing import Optional, Dict, List
from urllib.parse import urlparse

# 投稿モード設定（環境変数から取得、デフォルトはdemo）
POST_MODE = os.getenv("POST_MODE", "demo").lower()  # bluesky, demo

# Bluesky設定（環境変数から取得）
BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE")
BLUESKY_PASSWORD = os.getenv("BLUESKY_PASSWORD")  # アプリパスワード


class SocialPoster:
    """ソーシャルメディア投稿クラス（Bluesky / デモモード）"""
    
    def __init__(self, mode: Optional[str] = None):
        """
        初期化
        
        Args:
            mode: 投稿モード（bluesky, demo）。Noneの場合は環境変数から取得
        """
        self.mode = (mode or POST_MODE).lower()
        
        if self.mode == "bluesky":
            self._init_bluesky()
        else:
            self._init_demo()
    
    def _init_bluesky(self):
        """Blueskyを初期化"""
        try:
            from atproto import Client
            
            if not BLUESKY_HANDLE or not BLUESKY_PASSWORD:
                raise ValueError("Bluesky認証情報が不足しています。BLUESKY_HANDLEとBLUESKY_PASSWORDを設定してください。")
            
            self.client = Client()
            self.client.login(login=BLUESKY_HANDLE, password=BLUESKY_PASSWORD)
            self.max_length = 280  # Blueskyの文字数制限（280文字）
            print(f"✅ Bluesky接続成功: @{BLUESKY_HANDLE}")
            
        except ImportError:
            raise ImportError("atprotoパッケージがインストールされていません。pip install atproto を実行してください。")
        except Exception as e:
            print(f"⚠️ Bluesky初期化エラー: {e}")
            print("デモモードにフォールバックします。")
            self._init_demo()
    
    def _init_demo(self):
        """デモモードを初期化"""
        self.client = None
        self.mode = "demo"
        self.max_length = 280  # Bluesky基準（280文字）
        print("📝 デモモード: 実際には投稿しません")
    
    def post(self, text: str) -> Optional[Dict]:
        """
        ソーシャルメディアに投稿
        
        Args:
            text: 投稿テキスト
        
        Returns:
            投稿結果の辞書（post_idを含む）またはNone
        """
        # 文字数制限チェック
        if len(text) > self.max_length:
            print(f"⚠️ テキストが{self.max_length}文字を超えています: {len(text)}文字")
            text = text[:self.max_length - 3] + "..."
        
        if self.mode == "bluesky":
            return self._post_bluesky(text)
        else:
            return self._post_demo(text)
    
    def _extract_urls(self, text: str) -> List[Dict]:
        """
        テキストからURLを抽出して、バイト位置とURL情報を返す
        
        Args:
            text: 投稿テキスト
            
        Returns:
            URL情報のリスト（byteStart, byteEnd, urlを含む）
        """
        urls = []
        # URLパターン（http://, https://で始まるURL）
        url_pattern = r'https?://[^\s]+'
        
        # テキストをUTF-8バイト列に変換
        text_bytes = text.encode('utf-8')
        
        for match in re.finditer(url_pattern, text):
            url = match.group(0)
            # URLの開始位置（バイト単位）
            byte_start = len(text[:match.start()].encode('utf-8'))
            # URLの終了位置（バイト単位）
            byte_end = byte_start + len(url.encode('utf-8'))
            
            urls.append({
                'url': url,
                'byteStart': byte_start,
                'byteEnd': byte_end
            })
        
        return urls
    
    def _create_facets(self, text: str) -> Optional[List[Dict]]:
        """
        テキストからfacetsを作成（URLをハイパーリンク化）
        
        Args:
            text: 投稿テキスト
            
        Returns:
            facetsのリストまたはNone
        """
        urls = self._extract_urls(text)
        
        if not urls:
            return None
        
        facets = []
        for url_info in urls:
            facets.append({
                'index': {
                    'byteStart': url_info['byteStart'],
                    'byteEnd': url_info['byteEnd']
                },
                'features': [
                    {
                        '$type': 'app.bsky.richtext.facet#link',
                        'uri': url_info['url']
                    }
                ]
            })
        
        return facets
    
    def _post_bluesky(self, text: str) -> Optional[Dict]:
        """Blueskyに投稿（URLをハイパーリンク化）"""
        try:
            from atproto import Client, models
            
            # facetsを作成（URLをハイパーリンク化）
            facets = self._create_facets(text)
            
            # 投稿を作成
            if facets:
                # facetsを含めて投稿
                response = self.client.send_post(text=text, facets=facets)
                print(f"✅ Bluesky投稿成功（{len(facets)}個のリンクを含む）")
            else:
                # facetsなしで投稿
                response = self.client.send_post(text=text)
                print(f"✅ Bluesky投稿成功")
            
            # URIからpost_idを抽出
            post_id = response.uri.split("/")[-1] if hasattr(response, 'uri') else str(response.cid)
            
            return {
                "success": True,
                "post_id": post_id,
                "text": text,
                "platform": "bluesky",
                "facets_count": len(facets) if facets else 0
            }
        except Exception as e:
            print(f"⚠️ Bluesky投稿エラー: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _post_demo(self, text: str) -> Dict:
        """デモモード（実際には投稿しない）"""
        print("\n【デモモード: BLUESKY 投稿プレビュー】")
        print("=" * 50)
        print(text)
        print("=" * 50)
        print(f"文字数: {len(text)} / {self.max_length}")
        
        return {
            "success": True,
            "post_id": "demo_" + str(hash(text)),
            "text": text,
            "platform": "demo"
        }
    
    def verify_credentials(self) -> bool:
        """
        API認証情報を検証
        
        Returns:
            認証成功時True
        """
        if self.mode == "demo":
            print("📝 デモモード: 認証スキップ")
            return True
        
        try:
            if self.mode == "bluesky":
                # Blueskyの認証確認
                profile = self.client.get_profile()
                handle = profile.handle if hasattr(profile, 'handle') else BLUESKY_HANDLE
                print(f"✅ Bluesky認証成功: @{handle}")
                return True
        except Exception as e:
            print(f"⚠️ 認証失敗: {e}")
            return False


# 後方互換性のため
TwitterPoster = SocialPoster
