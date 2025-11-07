"""
ソーシャルメディア投稿クラス（Bluesky対応）
"""
import os
from typing import Optional, Dict

# 投稿モード設定
POST_MODE = os.getenv("POST_MODE", "demo").lower()  # bluesky, demo

# Bluesky設定
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
            self.max_length = 300  # Blueskyの文字数制限
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
        self.max_length = 300  # Bluesky基準
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
    
    def _post_bluesky(self, text: str) -> Optional[Dict]:
        """Blueskyに投稿"""
        try:
            from atproto import Client, models
            
            # 投稿を作成
            response = self.client.send_post(text=text)
            
            # URIからpost_idを抽出
            post_id = response.uri.split("/")[-1] if hasattr(response, 'uri') else str(response.cid)
            
            print(f"✅ Bluesky投稿成功: ID={post_id}")
            return {
                "success": True,
                "post_id": post_id,
                "text": text,
                "platform": "bluesky"
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
