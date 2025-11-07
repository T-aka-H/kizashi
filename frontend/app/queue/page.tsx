import PostApproval from '@/components/PostApproval'

export default function QueuePage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8 text-gray-900">
        投稿キュー
      </h1>
      <PostApproval />
    </div>
  )
}

