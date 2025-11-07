import ThemeSelector from '@/components/ThemeSelector'

export default function ThemesPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8 text-gray-900">
        テーマ分析
      </h1>
      <ThemeSelector />
    </div>
  )
}

