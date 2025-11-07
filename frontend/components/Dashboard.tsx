'use client'

import { useEffect, useState } from 'react'
import { statsApi, Stats } from '@/lib/api'
import { FileText, Send, Clock, Tag } from 'lucide-react'

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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
      setError(err.message || '統計情報の取得に失敗しました')
    } finally {
      setLoading(false)
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

