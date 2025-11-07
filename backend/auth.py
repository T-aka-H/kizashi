"""
認証機能モジュール
"""
import os
import base64
from fastapi import HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


# 環境変数から認証情報を取得
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "")
POST_PASSWORD = os.getenv("POST_PASSWORD", "")

# Basic認証が有効かどうか
AUTH_ENABLED = bool(AUTH_USERNAME and AUTH_PASSWORD)


def verify_basic_auth(credentials: HTTPBasicCredentials) -> bool:
    """
    Basic認証を検証
    
    Args:
        credentials: Basic認証の認証情報
    
    Returns:
        認証成功かどうか
    """
    if not AUTH_ENABLED:
        return True  # 認証が無効な場合は常に成功
    
    return (
        credentials.username == AUTH_USERNAME and
        credentials.password == AUTH_PASSWORD
    )


def verify_post_password(password: str) -> bool:
    """
    投稿確認パスワードを検証
    
    Args:
        password: 投稿確認パスワード
    
    Returns:
        認証成功かどうか
    """
    if not POST_PASSWORD:
        return True  # パスワードが設定されていない場合は常に成功
    
    return password == POST_PASSWORD


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """Basic認証ミドルウェア"""
    
    async def dispatch(self, request: Request, call_next):
        # ヘルスチェックエンドポイントは認証不要
        if request.url.path == "/" or request.url.path == "/docs" or request.url.path == "/openapi.json":
            return await call_next(request)
        
        # 認証が無効な場合はスキップ
        if not AUTH_ENABLED:
            return await call_next(request)
        
        # Authorizationヘッダーを確認
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Basic "):
            return Response(
                content="認証が必要です",
                status_code=401,
                headers={"WWW-Authenticate": "Basic"},
            )
        
        try:
            # Basic認証のデコード
            encoded = auth_header.split(" ")[1]
            decoded = base64.b64decode(encoded).decode("utf-8")
            username, password = decoded.split(":", 1)
            
            # 認証を検証
            if username == AUTH_USERNAME and password == AUTH_PASSWORD:
                return await call_next(request)
            else:
                return Response(
                    content="ユーザー名またはパスワードが間違っています",
                    status_code=401,
                    headers={"WWW-Authenticate": "Basic"},
                )
        except Exception as e:
            return Response(
                content="認証エラー",
                status_code=401,
                headers={"WWW-Authenticate": "Basic"},
            )

