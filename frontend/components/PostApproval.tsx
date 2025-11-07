'use client'

import { useEffect, useState } from 'react'
import { queueApi, articleApi, PostQueue, Article } from '@/lib/api'
import { format } from 'date-fns'
import { ja } from 'date-fns/locale'
import { Check, X, Send, RefreshCw } from 'lucide-react'

export default function PostApproval() {
  const [queueItems, setQueueItems] = useState<PostQueue[]>([])
  const [articles, setArticles] = useState<Record<number, Article>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadQueue()
  }, [])

  const loadQueue = async () => {
    try {
      setLoading(true)
      const queueData = await queueApi.getQueue('pending')
      setQueueItems(queueData)

      // 記事情報も取得
      const articlePromises = queueData.map(item =>
        articleApi.getArticle(item.article_id)
      )
      const articleData = await Promise.all(articlePromises)
      const articleMap: Record<number, Article> = {}
      articleData.forEach(article => {
        articleMap[article.id] = article
      })
      setArticles(articleMap)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'キュー情報の取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (queueId: number) => {
    try {
      await queueApi.approvePost(queueId)
      alert('承認しました')
      loadQueue()
    } catch (err: any) {
      alert(`承認エラー: ${err.message}`)
    }
  }

  const handlePost = async (queueId: number) => {
    if (!confirm('このツイートを投稿しますか？')) return

    // 投稿確認パスワードを入力
    const confirmPassword = prompt('投稿確認パスワードを入力してください:')
    if (!confirmPassword) {
      return // キャンセルされた場合
    }

    try {
      const result = await queueApi.postTweet(queueId, confirmPassword)
      alert(`投稿完了！ツイートID: ${result.tweet_id}`)
      loadQueue()
    } catch (err: any) {
      if (err.response?.status === 403) {
        alert('投稿パスワードが間違っています')
      } else {
        alert(`投稿エラー: ${err.message}`)
      }
    }
  }

  const handleReject = async (queueId: number) => {
    // 実装は後で追加（APIエンドポイントが必要）
    alert('却下機能は実装中です')
  }

  if (loading && queueItems.length === 0) {
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
          onClick={loadQueue}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          再試行
        </button>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <p className="text-gray-600">
          {queueItems.length}件の承認待ち投稿があります
        </p>
        <button
          onClick={loadQueue}
          className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
        >
          <RefreshCw size={16} />
          <span>更新</span>
        </button>
      </div>

      <div className="space-y-4">
        {queueItems.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-8 text-center border border-gray-200">
            <p className="text-gray-600">承認待ちの投稿はありません</p>
          </div>
        ) : (
          queueItems.map((item) => {
            const article = articles[item.article_id]
            return (
              <div
                key={item.id}
                className="bg-white rounded-lg shadow-md p-6 border border-gray-200"
              >
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-bold text-gray-900">
                      {article?.title || `記事ID: ${item.article_id}`}
                    </h3>
                    <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded">
                      {item.status}
                    </span>
                  </div>
                  {article?.theme && (
                    <p className="text-sm text-primary-600 mb-2">テーマ: {article.theme}</p>
                  )}
                  <p className="text-xs text-gray-500">
                    {format(new Date(item.created_at), 'yyyy年MM月dd日 HH:mm', { locale: ja })}
                  </p>
                </div>

                <div className="bg-gray-50 rounded-lg p-4 mb-4">
                  <p className="text-sm font-medium text-gray-700 mb-2">投稿テキスト:</p>
                  <p className="text-gray-900 whitespace-pre-wrap">{item.post_text}</p>
                  <p className="text-xs text-gray-500 mt-2">
                    {item.post_text.length} / 280 文字
                  </p>
                </div>

                {article?.summary && (
                  <div className="mb-4">
                    <p className="text-sm font-medium text-gray-700 mb-1">記事要約:</p>
                    <p className="text-sm text-gray-600">{article.summary}</p>
                  </div>
                )}

                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => handleApprove(item.id)}
                    className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    <Check size={16} />
                    <span>承認</span>
                  </button>
                  <button
                    onClick={() => handlePost(item.id)}
                    className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
                  >
                    <Send size={16} />
                    <span>投稿</span>
                  </button>
                  <button
                    onClick={() => handleReject(item.id)}
                    className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                  >
                    <X size={16} />
                    <span>却下</span>
                  </button>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

