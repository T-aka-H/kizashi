"""最新の投稿時刻を確認するスクリプト"""
from database import SessionLocal, get_latest_posted_article
from zoneinfo import ZoneInfo
from datetime import datetime

db = SessionLocal()
try:
    latest = get_latest_posted_article(db)
    if latest and latest.posted_at:
        # UTC時刻を日本時間に変換
        jst = ZoneInfo('Asia/Tokyo')
        # UTC時刻として扱う（データベースにはUTCで保存されている）
        if latest.posted_at.tzinfo is None:
            # タイムゾーン情報がない場合はUTCとして扱う
            from datetime import timezone
            utc_time = latest.posted_at.replace(tzinfo=timezone.utc)
        else:
            utc_time = latest.posted_at.astimezone(timezone.utc)
        jst_time = utc_time.astimezone(jst)
        print(f"最新投稿時刻 (UTC): {latest.posted_at}")
        print(f"最新投稿時刻 (JST): {jst_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"記事タイトル: {latest.title[:50]}...")
    else:
        print("投稿履歴がありません")
finally:
    db.close()

