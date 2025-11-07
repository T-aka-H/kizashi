'use client'

import { useEffect, useState } from 'react'
import { statsApi, Stats, researchApi } from '@/lib/api'
import { FileText, Send, Clock, Tag, Search, Loader2 } from 'lucide-react'

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [researchLoading, setResearchLoading] = useState(false)
  const [researchThemes, setResearchThemes] = useState('')
  const [researchResult, setResearchResult] = useState<string | null>(null)

  useEffect(() => {
    loadStats()
    // 30秒ごとに更新
    const interval = setInterval(loadStats, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadStats = async () => {
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
      
      // 統計情報を更新
      await loadStats()
      
      // テーマ入力欄をクリア
      setResearchThemes('')
    } catch (err: any) {
      setError(err.message || '記事の取得に失敗しました')
    } finally {
      setResearchLoading(false)
    }
  }

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error) {
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
      {/* 記事取得セクション */}
      <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200 mb-8">
        <h2 className="text-xl font-bold mb-4 text-gray-900 flex items-center gap-2">
          <Search className="text-primary-600" size={24} />
          Gemini Grounding（Google Search）で記事を取得
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

