import ArticleList from '@/components/ArticleList'

export default function ArticlesPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8 text-gray-900">
        記事一覧
      </h1>
      <ArticleList />
    </div>
  )
}

