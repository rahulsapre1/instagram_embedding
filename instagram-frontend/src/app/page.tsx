import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-20">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
            Discover Instagram{' '}
            <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Influencers
            </span>
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 mb-8 leading-relaxed">
            Find the perfect influencers for your brand using AI-powered search. 
            Natural language queries, smart filtering, and real-time discovery.
          </p>
          
          <Link href="/search">
            <Button size="lg" className="text-lg px-8 py-6 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
              Let&apos;s Search 🚀
            </Button>
          </Link>
        </div>

        {/* Feature Cards */}
        <div className="grid md:grid-cols-3 gap-8 mt-20">
          <Card className="border-0 shadow-lg bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <span className="text-2xl">🔍</span>
              </div>
              <CardTitle className="text-xl">Smart Search</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-gray-600">
                Use natural language to find influencers. No more complex filters or hashtag hunting.
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                <span className="text-2xl">💬</span>
              </div>
              <CardTitle className="text-xl">AI Chat</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-gray-600">
                Refine your search with intelligent chat. Get personalized recommendations and insights.
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                <span className="text-2xl">📊</span>
              </div>
              <CardTitle className="text-xl">Rich Data</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-gray-600">
                Access detailed profiles with follower counts, engagement rates, and content analysis.
              </CardDescription>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
