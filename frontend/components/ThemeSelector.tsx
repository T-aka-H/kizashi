'use client'

import { useEffect, useState } from 'react'
import { articleApi, Article } from '@/lib/api'
import { BarChart3, TrendingUp } from 'lucide-react'

export default function ThemeSelector() {
  const [articles, setArticles] = useState<Article[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedTheme, setSelectedTheme] = useState<string | null>(null)

  useEffect(() => {
    loadArticles()
  }, [])

  const loadArticles = async () => {
    try {
      setLoading(true)
      const data = await articleApi.getArticles()
      setArticles(data)
      setError(null)
    } catch (err: any) {
      setError(err.message || '記事の取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  // テーマ別集計
  const themeStats = articles.reduce((acc, article) => {
    if (!article.theme) return acc
    if (!acc[article.theme]) {
      acc[article.theme] = {
        count: 0,
        avgSentiment: 0,
        avgRelevance: 0,
        articles: [],
      }
    }
    acc[article.theme].count++
    if (article.sentiment_score) {
      acc[article.theme].avgSentiment += article.sentiment_score
    }
    if (article.relevance_score) {
      acc[article.theme].avgRelevance += article.relevance_score
    }
    acc[article.theme].articles.push(article)
    return acc
  }, {} as Record<string, { count: number; avgSentiment: number; avgRelevance: number; articles: Article[] }>)

  // 平均値を計算
  Object.keys(themeStats).forEach(theme => {
    const stat = themeStats[theme]
    stat.avgSentiment = stat.avgSentiment / stat.count
    stat.avgRelevance = stat.avgRelevance / stat.count
  })

  const themes = Object.entries(themeStats).sort((a, b) => b[1].count - a[1].count)

  if (loading) {
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
          onClick={loadArticles}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          再試行
        </button>
      </div>
    )
  }

  const filteredArticles = selectedTheme
    ? themeStats[selectedTheme]?.articles || []
    : []

  return (
    <div>
      {/* テーマ一覧 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {themes.map(([theme, stats]) => (
          <div
            key={theme}
            onClick={() => setSelectedTheme(selectedTheme === theme ? null : theme)}
            className={`bg-white rounded-lg shadow-md p-6 border-2 cursor-pointer transition-all ${
              selectedTheme === theme
                ? 'border-primary-500 shadow-lg'
                : 'border-gray-200 hover:shadow-lg'
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900">{theme}</h3>
              <BarChart3 className="text-primary-600" size={24} />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-gray-600 text-sm">記事数</span>
                <span className="text-xl font-bold text-gray-900">{stats.count}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600 text-sm">平均感情スコア</span>
                <span className="text-lg font-semibold text-primary-600">
                  {(stats.avgSentiment * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600 text-sm">平均関連性</span>
                <span className="text-lg font-semibold text-green-600">
                  {(stats.avgRelevance * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 選択されたテーマの記事一覧 */}
      {selectedTheme && (
        <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900">
              「{selectedTheme}」の記事一覧
            </h2>
            <button
              onClick={() => setSelectedTheme(null)}
              className="text-gray-600 hover:text-gray-900"
            >
              ✕
            </button>
          </div>
          <div className="space-y-3">
            {filteredArticles.map((article) => (
              <div
                key={article.id}
                className="border-b border-gray-200 pb-3 last:border-b-0"
              >
                <h4 className="font-semibold text-gray-900 mb-1">{article.title}</h4>
                {article.summary && (
                  <p className="text-sm text-gray-600 mb-2">{article.summary}</p>
                )}
                <div className="flex items-center space-x-4 text-xs text-gray-500">
                  {article.sentiment_score !== undefined && (
                    <div className="flex items-center space-x-1">
                      <TrendingUp size={12} />
                      <span>感情: {(article.sentiment_score * 100).toFixed(0)}%</span>
                    </div>
                  )}
                  {article.relevance_score !== undefined && (
                    <div className="flex items-center space-x-1">
                      <span>関連性: {(article.relevance_score * 100).toFixed(0)}%</span>
                    </div>
                  )}
                  {article.is_posted && (
                    <span className="text-green-600">✓ 投稿済み</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {themes.length === 0 && (
        <div className="bg-white rounded-lg shadow-md p-8 text-center border border-gray-200">
          <p className="text-gray-600">テーマデータがありません</p>
        </div>
      )}
    </div>
  )
}

