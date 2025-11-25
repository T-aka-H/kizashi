# ⚡ Render起動時間の最適化ガイド

## 🕐 現状の問題

Renderで起動に5分かかることがあるという問題について、原因と対策を説明します。

---

## 📊 起動時間の内訳

### 1. Renderのコールドスタート（スリープからの復帰）
- **通常**: 30秒〜1分
- **遅い場合**: 2〜3分
- **原因**: 無料プランの制限（15分間アクセスがないとスリープ）

### 2. アプリケーションの初期化
現在の実装での初期化処理：
- データベース接続・初期化
- GeminiAnalyzer初期化（API接続テスト？）
- SocialPoster初期化（Bluesky認証）
- ArticleScheduler初期化と起動

**問題点**: 初期化時にAPI接続テストや重い処理をしている可能性

---

## 🔍 起動が遅い原因の特定

### 確認方法1: ログを見る

Renderダッシュボード → Logs で以下を確認：

```
2025-11-09 12:00:00 - Starting...
2025-11-09 12:00:30 - Application startup complete
```

**30秒以上**かかっている場合は、アプリケーション側の問題です。

### 確認方法2: Health Checkの設定

現在の設定:
- **Health Check Path**: `/healthz`
- **Health Check Grace Period**: デフォルト（おそらく60秒）

**問題**: 初期化に時間がかかると、ヘルスチェックが失敗してコンテナが再起動を繰り返す可能性があります。

---

## ✅ 改善策

### 1. 遅延初期化（Lazy Initialization）の実装

**現在の問題**: アプリ起動時にすべてを初期化している

**改善案**: 必要になったときに初期化する

```python
# main.py の改善版

# グローバル変数
_analyzer = None
_poster = None
_scheduler = None
_scheduler_lock = threading.Lock()

def get_analyzer():
    """GeminiAnalyzerを取得（遅延初期化）"""
    global _analyzer
    if _analyzer is None:
        try:
            _analyzer = GeminiAnalyzer()
            logger.info("✅ GeminiAnalyzer初期化成功")
        except Exception as e:
            logger.error(f"⚠️ GeminiAnalyzer初期化エラー: {e}")
            raise HTTPException(status_code=503, detail="GeminiAnalyzer初期化エラー")
    return _analyzer

def get_poster():
    """SocialPosterを取得（遅延初期化）"""
    global _poster
    if _poster is None:
        try:
            _poster = SocialPoster()
            logger.info("✅ SocialPoster初期化成功")
        except Exception as e:
            logger.error(f"⚠️ SocialPoster初期化エラー: {e}")
            raise HTTPException(status_code=503, detail="SocialPoster初期化エラー")
    return _poster

def initialize_app_minimal():
    """最小限の初期化（起動時）"""
    logger.info("🚀 最小限の初期化...")
    # データベースのみ初期化
    # その他は遅延初期化
    logger.info("✅ 最小限の初期化完了")

# アプリ起動時は最小限の初期化のみ
initialize_app_minimal()
```

**メリット**:
- 起動時間が大幅に短縮（データベース初期化のみ）
- ヘルスチェックがすぐに応答
- 必要な機能だけを初期化

**デメリット**:
- 最初のAPI呼び出し時に少し遅延

---

### 2. Health Check Grace Periodの延長

Renderの設定で調整：

1. Render ダッシュボード → Web Service
2. 「Settings」タブ
3. 「Health Check」セクション

**推奨設定**:
```
Health Check Path: /healthz
Health Check Grace Period: 180 秒（3分）
```

これにより、初期化に時間がかかってもコンテナが再起動しなくなります。

---

### 3. スケジューラーの遅延起動

**現在の問題**: アプリ起動時にスケジューラーも起動している

**改善案**: アプリが完全に起動してからスケジューラーを開始

```python
def start_scheduler_delayed():
    """スケジューラーを遅延起動（30秒後）"""
    time.sleep(30)  # アプリ起動後30秒待つ
    
    global scheduler, _scheduler_thread
    try:
        scheduler = ArticleScheduler()
        interval = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "15"))
        scheduler.run_scheduler(interval)
        logger.info(f"✅ スケジューラー起動完了（{interval}分間隔）")
    except Exception as e:
        logger.error(f"⚠️ スケジューラー起動エラー: {e}")

# バックグラウンドで遅延起動
threading.Thread(target=start_scheduler_delayed, daemon=True).start()
```

---

### 4. データベース接続の最適化

**現在の設定確認**:

```python
# database.py
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 接続確認（少し遅い）
    pool_size=5,         # コネクションプール
    max_overflow=10
)
```

**最適化案**:

```python
# 起動時の接続確認を無効化
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=False,  # 起動時は接続確認しない
    pool_size=2,          # プールサイズを小さく
    max_overflow=5,       # オーバーフローも小さく
    connect_args={
        "connect_timeout": 10,  # タイムアウトを設定
    }
)
```

---

### 5. 軽量なヘルスチェック

**現在の `/healthz`**:
```python
@app.get("/healthz")
async def health_check():
    return {
        "status": "ok",
        "components": {
            "analyzer": "available" if analyzer else "unavailable",
            "poster": "available" if poster else "unavailable",
            "scheduler": "running" if scheduler and _scheduler_thread.is_alive() else "stopped"
        }
    }
```

**問題**: スレッドの状態確認が少し重い

**改善版**:
```python
@app.get("/healthz")
async def health_check():
    """超軽量なヘルスチェック（Render用）"""
    return {"status": "ok"}

@app.get("/health/detailed")
async def health_check_detailed():
    """詳細なヘルスチェック（監視用）"""
    return {
        "status": "ok",
        "components": {
            "analyzer": "available" if _analyzer else "not_initialized",
            "poster": "available" if _poster else "not_initialized",
            "scheduler": "running" if _scheduler else "not_initialized"
        }
    }
```

---

## 🚀 推奨される実装

### 段階的な起動プロセス

```python
# main.py の改善版

import os
import sys
import logging
import threading
import time
from pathlib import Path
from dotenv import load_dotenv

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# .envファイル読み込み
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.info(f"✅ .envファイル読み込み完了")

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# FastAPIアプリ初期化
app = FastAPI(title="Weak Signals App", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# グローバル変数（遅延初期化用）
_analyzer = None
_poster = None
_scheduler = None
_initialized_components = set()

def get_analyzer():
    """GeminiAnalyzerを取得（遅延初期化）"""
    global _analyzer
    if _analyzer is None:
        from gemini_analyzer import GeminiAnalyzer
        _analyzer = GeminiAnalyzer()
        logger.info("✅ GeminiAnalyzer初期化完了")
    return _analyzer

def get_poster():
    """SocialPosterを取得（遅延初期化）"""
    global _poster
    if _poster is None:
        from twitter_poster import SocialPoster
        _poster = SocialPoster()
        logger.info("✅ SocialPoster初期化完了")
    return _poster

@app.on_event("startup")
async def startup_event():
    """アプリ起動時の処理（最小限）"""
    logger.info("🚀 アプリケーション起動中...")
    
    # データベース初期化のみ
    from database import init_db
    init_db()
    
    # スケジューラーは遅延起動（バックグラウンド）
    if os.getenv("DISABLE_SCHEDULER", "false").lower() != "true":
        threading.Thread(target=start_scheduler_delayed, daemon=True).start()
    
    logger.info("✅ アプリケーション起動完了")

def start_scheduler_delayed():
    """スケジューラーを遅延起動（30秒後）"""
    logger.info("⏳ スケジューラー起動を30秒後に開始...")
    time.sleep(30)
    
    global _scheduler
    try:
        from scheduler import ArticleScheduler
        _scheduler = ArticleScheduler()
        interval = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "15"))
        _scheduler.run_scheduler(interval)
    except Exception as e:
        logger.error(f"⚠️ スケジューラー起動エラー: {e}", exc_info=True)

# 超軽量なヘルスチェック
@app.get("/healthz")
async def health_check():
    """超軽量なヘルスチェック（Render用）"""
    return {"status": "ok"}

# APIエンドポイント（analyzerやposterを使う場合は遅延初期化）
@app.post("/articles/{article_id}/analyze")
async def analyze_article_endpoint(article_id: int, db: Session = Depends(get_db)):
    analyzer = get_analyzer()  # ここで初期化
    # 以降の処理...
```

---

## 📊 期待される改善

| 項目 | Before | After |
|------|--------|-------|
| 起動時間 | 2〜5分 | 30秒〜1分 |
| ヘルスチェック応答 | 遅い | 即座 |
| 初回API呼び出し | 速い | 少し遅い（初期化） |
| コンテナ再起動 | 頻繁 | 少ない |

---

## 🔧 すぐにできる対策

### 1. Health Check Grace Periodの延長（最優先）

Render設定で`180秒`に変更

### 2. スケジューラーの無効化テスト

```bash
# 環境変数に追加
DISABLE_SCHEDULER=true
```

これで起動が速くなるか確認。速くなれば、スケジューラーが原因。

### 3. ログで起動時間を確認

```
2025-11-09 12:00:00 - Starting...
2025-11-09 12:00:?? - Application startup complete
```

この時間差を確認して、どこで時間がかかっているか特定。

---

## 💡 追加の最適化

### UptimeRobotでスリープ対策

無料プランの制限（15分でスリープ）を回避：

1. UptimeRobotに登録（無料）: https://uptimerobot.com/
2. モニターを追加:
   - **Type**: HTTP(s)
   - **URL**: `https://your-app.onrender.com/healthz`
   - **Monitoring Interval**: 5分
3. これで常に起動状態を維持

---

## ⚠️ 注意点

### 遅延初期化のデメリット

- **最初のAPI呼び出しが遅い**: 初期化に時間がかかる
- **エラーハンドリングが複雑**: 遅延初期化のエラー処理が必要

### 対策

```python
# 最初のAPI呼び出し時に初期化状態を返す
@app.post("/articles/{article_id}/analyze")
async def analyze_article_endpoint(article_id: int):
    try:
        analyzer = get_analyzer()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="Analyzer is initializing. Please retry in a few seconds."
        )
    # 以降の処理...
```

---

## 📝 まとめ

### 起動時間5分の原因

1. ✅ **Renderのコールドスタート**: 30秒〜1分（正常）
2. ⚠️ **アプリケーション初期化**: 1〜4分（要改善）
   - GeminiAnalyzer初期化
   - SocialPoster初期化（Bluesky認証）
   - ArticleScheduler初期化
3. ⚠️ **ヘルスチェック失敗**: コンテナ再起動ループ

### 推奨される対策（優先順位順）

1. **Health Check Grace Period延長** → 180秒
2. **スケジューラーの遅延起動** → 30秒後に起動
3. **遅延初期化の実装** → 必要な時に初期化
4. **UptimeRobotでスリープ対策** → 5分間隔でアクセス

これで起動時間が**30秒〜1分**に短縮されるはずです。

---

**作成日**: 2025年11月09日

