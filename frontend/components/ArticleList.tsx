'use client'

import { useEffect, useState } from 'react'
import { articleApi, Article } from '@/lib/api'
import { format } from 'date-fns'
import { ja } from 'date-fns/locale/ja'
import { ExternalLink, Sparkles, TrendingUp, Tag } from 'lucide-react'

export default function ArticleList() {
  const [articles, setArticles] = useState<Article[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedTheme, setSelectedTheme] = useState<string>('')

  useEffect(() => {
    loadArticles()
  }, [selectedTheme])

  const loadArticles = async () => {
    try {
      setLoading(true)
      const data = await articleApi.getArticles(selectedTheme || undefined)
      setArticles(data)
      setError(null)
    } catch (err: any) {
      setError(err.message || '記事の取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyze = async (articleId: number) => {
    try {
      await articleApi.analyzeArticle(articleId)
      alert('分析が完了しました')
      loadArticles()
    } catch (err: any) {
      alert(`分析エラー: ${err.message}`)
    }
  }

  if (loading && articles.length === 0) {
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

  // テーマ一覧を取得
  const themes = Array.from(new Set(articles.map(a => a.theme).filter(Boolean))) as string[]

  return (
    <div>
      {/* フィルター */}
      <div className="mb-6 flex items-center space-x-4">
        <label className="text-sm font-medium text-gray-700">テーマでフィルター:</label>
        <select
          value={selectedTheme}
          onChange={(e) => setSelectedTheme(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="">すべて</option>
          {themes.map((theme) => (
            <option key={theme} value={theme}>
              {theme}
            </option>
          ))}
        </select>
        <button
          onClick={loadArticles}
          className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
        >
          更新
        </button>
      </div>

      {/* 記事一覧 */}
      <div className="space-y-4">
        {articles.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-8 text-center border border-gray-200">
            <p className="text-gray-600">記事がありません</p>
          </div>
        ) : (
          articles.map((article) => (
            <div
              key={article.id}
              className="bg-white rounded-lg shadow-md p-6 border border-gray-200 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-xl font-bold text-gray-900">{article.title}</h3>
                    {article.is_posted && (
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
                        投稿済み
                      </span>
                    )}
                  </div>
                  
                  {article.theme && (
                    <div className="flex items-center space-x-2 mb-2">
                      <Tag className="text-primary-600" size={16} />
                      <span className="text-sm text-primary-600 font-medium">{article.theme}</span>
                    </div>
                  )}

                  {article.summary && (
                    <p className="text-gray-600 mb-3 line-clamp-2">{article.summary}</p>
                  )}

                  <div className="flex items-center space-x-4 text-sm text-gray-500 mb-3">
                    {article.created_at && (
                      <span>
                        {format(new Date(article.created_at), 'yyyy年MM月dd日 HH:mm', { locale: ja })}
                      </span>
                    )}
                    {article.sentiment_score !== undefined && (
                      <div className="flex items-center space-x-1">
                        <TrendingUp size={14} />
                        <span>感情: {(article.sentiment_score * 100).toFixed(0)}%</span>
                      </div>
                    )}
                    {article.relevance_score !== undefined && (
                      <div className="flex items-center space-x-1">
                        <Sparkles size={14} />
                        <span>関連性: {(article.relevance_score * 100).toFixed(0)}%</span>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center space-x-2">
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-600 hover:text-primary-700 text-sm flex items-center space-x-1"
                    >
                      <ExternalLink size={14} />
                      <span>元記事を見る</span>
                    </a>
                    {!article.theme && (
                      <button
                        onClick={() => handleAnalyze(article.id)}
                        className="ml-4 px-4 py-2 bg-primary-600 text-white text-sm rounded hover:bg-primary-700"
                      >
                        分析する
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

