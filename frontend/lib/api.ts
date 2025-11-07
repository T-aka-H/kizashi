/**
 * APIクライアント
 */
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Basic認証ヘッダーを生成
const getAuthHeaders = () => {
  if (typeof window === 'undefined') {
    return { 'Content-Type': 'application/json' }
  }
  
  const username = localStorage.getItem('auth_username') || ''
  const password = localStorage.getItem('auth_password') || ''
  
  if (username && password) {
    const token = btoa(`${username}:${password}`)
    return {
      'Authorization': `Basic ${token}`,
      'Content-Type': 'application/json',
    }
  }
  
  return { 'Content-Type': 'application/json' }
}

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// リクエストインターセプターで認証ヘッダーを追加
api.interceptors.request.use(
  (config) => {
    const authHeaders = getAuthHeaders()
    config.headers = { ...config.headers, ...authHeaders }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// レスポンスインターセプターで401エラーを処理
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 認証エラーの場合、認証情報をクリア
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_username')
        localStorage.removeItem('auth_password')
        // ログインページにリダイレクト
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

// 型定義
export interface Article {
  id: number
  url: string
  title: string
  content?: string
  theme?: string
  summary?: string
  key_points?: string
  sentiment_score?: number
  relevance_score?: number
  is_posted: boolean
  posted_at?: string
  tweet_id?: string
  published_at?: string
  created_at: string
}

export interface PostQueue {
  id: number
  article_id: number
  post_text: string
  status: 'pending' | 'approved' | 'rejected' | 'posted'
  created_at: string
  approved_at?: string
}

export interface Stats {
  total_articles: number
  posted_articles: number
  pending_posts: number
  themes: number
}

export interface ArticleCreate {
  url: string
  title: string
  content?: string
  published_at?: string
}

// API関数
export const articleApi = {
  // 記事一覧取得
  getArticles: async (theme?: string, skip: number = 0, limit: number = 100): Promise<Article[]> => {
    const params: any = { skip, limit }
    if (theme) params.theme = theme
    const response = await api.get<Article[]>('/articles', { params })
    return response.data
  },

  // 記事取得
  getArticle: async (id: number): Promise<Article> => {
    const response = await api.get<Article>(`/articles/${id}`)
    return response.data
  },

  // 記事作成
  createArticle: async (data: ArticleCreate): Promise<Article> => {
    const response = await api.post<Article>('/articles', data)
    return response.data
  },

  // 記事分析
  analyzeArticle: async (id: number): Promise<Article> => {
    const response = await api.post<Article>(`/articles/${id}/analyze`)
    return response.data
  },
}

export const queueApi = {
  // 投稿キュー取得
  getQueue: async (status?: string): Promise<PostQueue[]> => {
    const params = status ? { status } : {}
    const response = await api.get<PostQueue[]>('/post-queue', { params })
    return response.data
  },

  // 投稿承認
  approvePost: async (queueId: number): Promise<void> => {
    await api.post(`/post-queue/${queueId}/approve`)
  },

  // 投稿実行（投稿確認パスワード必要）
  postTweet: async (queueId: number, confirmPassword: string): Promise<{ message: string; tweet_id: string }> => {
    const response = await api.post<{ message: string; tweet_id: string }>(`/post-queue/${queueId}/post`, {
      confirm_password: confirmPassword,
    })
    return response.data
  },
}

export const statsApi = {
  // 統計情報取得
  getStats: async (): Promise<Stats> => {
    const response = await api.get<Stats>('/stats')
    return response.data
  },
}

export interface ResearchRequest {
  themes: string  // カンマ区切りのテーマリスト
}

export interface ResearchResponse {
  message: string
  processed: number
  analyzed: number
  queued: number
}

export const researchApi = {
  // DeepResearchで記事を取得
  fetchByResearch: async (themes: string): Promise<ResearchResponse> => {
    const response = await api.post<ResearchResponse>('/fetch/research', {
      themes,
    })
    return response.data
  },
}

