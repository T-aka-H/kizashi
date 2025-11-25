"""最新投稿時刻と次回投稿予定を確認するスクリプト"""
from datetime import datetime
from zoneinfo import ZoneInfo
from database import SessionLocal, get_latest_posted_article

jst = ZoneInfo('Asia/Tokyo')
now = datetime.now(jst)

print(f"現在時刻 (JST): {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")

db = SessionLocal()
try:
    latest = get_latest_posted_article(db)
    if latest and latest.posted_at:
        # UTC時刻を日本時間に変換
        if latest.posted_at.tzinfo is None:
            from datetime import timezone
            utc_time = latest.posted_at.replace(tzinfo=timezone.utc)
        else:
            utc_time = latest.posted_at.astimezone(timezone.utc)
        last_post_jst = utc_time.astimezone(jst)
        
        print(f"\n最新投稿時刻 (JST): {last_post_jst.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"記事タイトル: {latest.title[:50]}...")
        
        # 経過時間を計算
        diff = now - last_post_jst
        hours = int(diff.total_seconds() // 3600)
        minutes = int((diff.total_seconds() % 3600) // 60)
        print(f"\n最後の投稿から: {hours}時間{minutes}分経過")
        
        # 次回投稿予定時刻を計算（3時間間隔）
        # 最後の投稿時刻から3時間ごとの区切りを計算
        next_post = last_post_jst
        while next_post <= now:
            from datetime import timedelta
            next_post = next_post + timedelta(hours=3)
        
        print(f"次回投稿予定: {next_post.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # 残り時間を計算
        remaining = next_post - now
        remaining_hours = int(remaining.total_seconds() // 3600)
        remaining_minutes = int((remaining.total_seconds() % 3600) // 60)
        print(f"残り時間: {remaining_hours}時間{remaining_minutes}分")
    else:
        print("\n投稿履歴がありません")
finally:
    db.close()

