/**
 * APIクライアント
 */
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

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

  // 投稿実行
  postTweet: async (queueId: number): Promise<{ message: string; tweet_id: string }> => {
    const response = await api.post<{ message: string; tweet_id: string }>(`/post-queue/${queueId}/post`)
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

