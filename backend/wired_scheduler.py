"""
WIRED記事TOP5を毎朝8時にBlueskyに投稿するスケジューラー
"""
import os
import schedule
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 環境変数を読み込む
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# 基本版か改良版かを選択
USE_ADVANCED = os.getenv("USE_ADVANCED_BOT", "true").lower() == "true"

if USE_ADVANCED:
    from wired_bluesky_bot_advanced import WiredBlueskyBotAdvanced as WiredBot
    BOT_NAME = "改良版"
else:
    from wired_bluesky_bot import WiredBlueskyBot as WiredBot
    BOT_NAME = "基本版"


def job():
    """定期実行するジョブ"""
    print(f"\n{'='*70}")
    print(f"⏰ 定期実行開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🤖 使用ボット: {BOT_NAME}")
    print(f"{'='*70}")
    
    try:
        bot = WiredBot()
        bot.run()
    except Exception as e:
        print(f"\n⚠️ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*70}")
    print(f"✅ 定期実行完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")


def main():
    """メイン処理"""
    print(f"\n{'='*70}")
    print(f"🚀 WIRED記事TOP5投稿スケジューラー 起動")
    print(f"⏰ 実行スケジュール: 毎朝 8:00")
    print(f"🤖 使用ボット: {BOT_NAME}")
    print(f"{'='*70}\n")
    
    # 毎朝8時に実行
    schedule.every().day.at("08:00").do(job)
    
    print("📅 次回実行予定:")
    for job_item in schedule.jobs:
        print(f"  - {job_item}")
    
    # テスト実行するかどうか
    test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    if test_mode:
        print("\n🧪 テストモード: 今すぐ1回実行します")
        job()
        print("\n⏸️  スケジューラーを停止します（テストモード）")
        return
    
    print("\n⏳ スケジューラー実行中... (Ctrl+Cで終了)\n")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1分ごとにチェック
    except KeyboardInterrupt:
        print("\n\n👋 スケジューラーを停止しました")


if __name__ == "__main__":
    main()

