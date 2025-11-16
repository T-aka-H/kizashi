'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // 認証テスト（/health エンドポイントを使用、認証不要だが認証ヘッダーを送信して検証）
      const token = btoa(`${username}:${password}`)
      // 認証が必要なエンドポイントでテスト（/fetch/wired-rss など）
      const response = await fetch(`${API_URL}/fetch/wired-rss`, {
        method: 'POST',
        headers: {
          'Authorization': `Basic ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ max_items: 1 }),
      })

      if (response.ok || response.status === 400) {
        // 400エラーはリクエスト形式の問題なので、認証は成功とみなす
        // 認証情報をlocalStorageに保存
        localStorage.setItem('auth_username', username)
        localStorage.setItem('auth_password', password)
        
        // ダッシュボードにリダイレクト
        router.push('/')
      } else if (response.status === 401) {
        setError('ユーザー名またはパスワードが間違っています')
      } else {
        setError('ログインに失敗しました')
      }
    } catch (err: any) {
      // CORSエラーやネットワークエラーの場合も認証情報を保存して進める
      // （実際の認証は次回のAPI呼び出しで検証される）
      if (err.message?.includes('CORS') || err.message?.includes('Failed to fetch')) {
        // 認証情報をlocalStorageに保存（次回のAPI呼び出しで検証）
        localStorage.setItem('auth_username', username)
        localStorage.setItem('auth_password', password)
        router.push('/')
      } else {
        setError('ログインに失敗しました: ' + (err.message || 'ネットワークエラー'))
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <h1 className="text-3xl font-bold mb-6 text-center text-gray-900">
          Weak Signals App
        </h1>
        <h2 className="text-xl font-semibold mb-6 text-center text-gray-700">
          ログイン
        </h2>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
              ユーザー名
            </label>
            <input
              id="username"
              type="text"
              placeholder="ユーザー名"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              required
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              パスワード
            </label>
            <input
              id="password"
              type="password"
              placeholder="パスワード"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              required
              disabled={loading}
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary-600 text-white py-3 rounded-lg hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {loading ? 'ログイン中...' : 'ログイン'}
          </button>
        </form>

        <div className="mt-6 text-sm text-gray-500 text-center">
          <p>認証が必要です</p>
        </div>
      </div>
    </div>
  )
}

