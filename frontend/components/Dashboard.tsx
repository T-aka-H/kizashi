'use client'

import { useEffect, useState } from 'react'
import { statsApi, Stats, researchApi, wiredApi } from '@/lib/api'
import { FileText, Send, Clock, Tag, Search, Loader2, Rss, Play } from 'lucide-react'

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statsAvailable, setStatsAvailable] = useState(true) // 統計情報が利用可能かどうか
  const [researchLoading, setResearchLoading] = useState(false)
  const [researchThemes, setResearchThemes] = useState('')
  const [researchResult, setResearchResult] = useState<string | null>(null)
  const [wiredLoading, setWiredLoading] = useState(false)
  const [wiredResult, setWiredResult] = useState<string | null>(null)
  const [wiredBotLoading, setWiredBotLoading] = useState(false)
  const [wiredBotResult, setWiredBotResult] = useState<string | null>(null)

  useEffect(() => {
    loadStats()
    // 統計情報が利用可能な場合のみ30秒ごとに更新
    if (statsAvailable) {
      const interval = setInterval(loadStats, 30000)
      return () => clearInterval(interval)
    }
  }, [statsAvailable])

  const loadStats = async () => {
    // 統計情報が利用不可の場合はスキップ
    if (!statsAvailable) {
      return
    }

    try {
      setLoading(true)
      const data = await statsApi.getStats()
      setStats(data)
      setError(null)
    } catch (err: any) {
      // 401エラーの場合は認証が必要（リダイレクトはapi.tsで処理）
      if (err.response?.status === 401) {
        setError('認証が必要です。ログインページにリダイレクトします...')
        return
      }
      
      // 404エラーの場合は統計情報エンドポイントが存在しない（削除されている）
      if (err.response?.status === 404) {
        setStatsAvailable(false)
        setStats(null)
        setError(null) // エラーを表示しない（正常な状態として扱う）
        return
      }
      
      // その他のエラー
      setError(err.message || '統計情報の取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  const handleResearch = async () => {
    if (!researchThemes.trim()) {
      setError('テーマを入力してください')
      return
    }

    try {
      setResearchLoading(true)
      setError(null)
      setResearchResult(null)
      
      const result = await researchApi.fetchByResearch(researchThemes.trim())
      
      setResearchResult(
        `✅ 取得完了: ${result.processed}件の記事を処理、${result.analyzed}件を分析、${result.queued}件をキューに追加しました`
      )
      
      // 統計情報を更新（利用可能な場合のみ）
      if (statsAvailable) {
        await loadStats()
      }
      
      // テーマ入力欄をクリア
      setResearchThemes('')
    } catch (err: any) {
      setError(err.message || '記事の取得に失敗しました')
    } finally {
      setResearchLoading(false)
    }
  }

  const handleWiredRSS = async () => {
    try {
      setWiredLoading(true)
      setError(null)
      setWiredResult(null)
      
      const result = await wiredApi.fetchWiredRSS(20)
      
      setWiredResult(
        `✅ WIRED RSS取得完了: ${result.articles_count}件の記事を取得しました`
      )
      
      // 統計情報を更新（利用可能な場合のみ）
      if (statsAvailable) {
        await loadStats()
      }
    } catch (err: any) {
      setError(err.message || 'WIRED RSSの取得に失敗しました')
    } finally {
      setWiredLoading(false)
    }
  }

  const handleWiredBotTest = async () => {
    if (!confirm('WIRED Botを実行しますか？実際にBlueskyに投稿されます。')) {
      return
    }

    try {
      setWiredBotLoading(true)
      setError(null)
      setWiredBotResult(null)
      
      const result = await wiredApi.testWiredBot()
      
      setWiredBotResult(
        `✅ ${result.message}${result.note ? `\n${result.note}` : ''}`
      )
      
      // 統計情報を更新（利用可能な場合のみ）
      if (statsAvailable) {
        await loadStats()
      }
    } catch (err: any) {
      setError(err.message || 'WIRED Botの実行に失敗しました')
    } finally {
      setWiredBotLoading(false)
    }
  }

  // 統計情報の読み込み中で、かつ統計情報が利用可能な場合のみローディング表示
  if (loading && statsAvailable && !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  // エラー表示（統計情報のエラーは表示しない、404の場合は正常な状態として扱う）
  if (error && statsAvailable) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
        <button
          onClick={loadStats}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          再試行
        </button>
      </div>
    )
  }

  const statCards = [
    {
      title: '総記事数',
      value: stats?.total_articles || 0,
      icon: FileText,
      color: 'bg-blue-500',
    },
    {
      title: '投稿済み',
      value: stats?.posted_articles || 0,
      icon: Send,
      color: 'bg-green-500',
    },
    {
      title: '承認待ち',
      value: stats?.pending_posts || 0,
      icon: Clock,
      color: 'bg-yellow-500',
    },
    {
      title: 'テーマ数',
      value: stats?.themes || 0,
      icon: Tag,
      color: 'bg-purple-500',
    },
  ]

  return (
    <div>
      {/* WIRED Botセクション */}
      <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200 mb-8">
        <h2 className="text-xl font-bold mb-4 text-gray-900 flex items-center gap-2">
          <Rss className="text-primary-600" size={24} />
          WIRED Bot
        </h2>
        <div className="space-y-4">
          <div className="flex gap-4">
            <button
              onClick={handleWiredRSS}
              disabled={wiredLoading}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
            >
              {wiredLoading ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  WIRED RSS取得中...
                </>
              ) : (
                <>
                  <Rss size={20} />
                  WIRED RSSから記事を取得
                </>
              )}
            </button>
            <button
              onClick={handleWiredBotTest}
              disabled={wiredBotLoading}
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
            >
              {wiredBotLoading ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  実行中...
                </>
              ) : (
                <>
                  <Play size={20} />
                  WIRED Botを実行（投稿）
                </>
              )}
            </button>
          </div>
          {wiredResult && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-blue-800 whitespace-pre-line">{wiredResult}</p>
            </div>
          )}
          {wiredBotResult && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-800 whitespace-pre-line">{wiredBotResult}</p>
            </div>
          )}
        </div>
      </div>

      {/* 記事取得セクション */}
      <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200 mb-8">
        <h2 className="text-xl font-bold mb-4 text-gray-900 flex items-center gap-2">
          <Search className="text-primary-600" size={24} />
          未来の兆し生成（Gemini Grounding）
        </h2>
        <div className="space-y-4">
          <div>
            <label htmlFor="themes" className="block text-sm font-medium text-gray-700 mb-2">
              テーマ（カンマ区切り）
            </label>
            <input
              id="themes"
              type="text"
              value={researchThemes}
              onChange={(e) => setResearchThemes(e.target.value)}
              placeholder="例: AI, ブロックチェーン, 量子コンピュータ"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              disabled={researchLoading}
            />
            <p className="mt-1 text-sm text-gray-500">
              複数のテーマをカンマで区切って入力してください
            </p>
          </div>
          <button
            onClick={handleResearch}
            disabled={researchLoading || !researchThemes.trim()}
            className="w-full md:w-auto px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
          >
            {researchLoading ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                取得中...
              </>
            ) : (
              <>
                <Search size={20} />
                記事を取得
              </>
            )}
          </button>
          {researchResult && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-800">{researchResult}</p>
            </div>
          )}
        </div>
      </div>

      {/* 統計情報セクション（利用可能な場合のみ表示） */}
      {statsAvailable && stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {statCards.map((card) => {
            const Icon = card.icon
            return (
              <div
                key={card.title}
                className="bg-white rounded-lg shadow-md p-6 border border-gray-200"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-600 text-sm font-medium">{card.title}</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{card.value}</p>
                  </div>
                  <div className={`${card.color} p-3 rounded-full`}>
                    <Icon className="text-white" size={24} />
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
        <h2 className="text-xl font-bold mb-4 text-gray-900">システム状態</h2>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-gray-600">API接続</span>
            <span className="text-green-600 font-medium">✓ 接続中</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-600">最終更新</span>
            <span className="text-gray-900">{new Date().toLocaleString('ja-JP')}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

