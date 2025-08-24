import { NextRequest, NextResponse } from 'next/server'

// Types
interface InfluencerProfile {
  username: string
  full_name: string
  bio: string
  follower_count: number
  category: string
  account_type: string
  influencer_type: string
  score: number
  is_private: boolean
}

interface SearchResponse {
  results: InfluencerProfile[]
  total: number
  has_more: boolean
  query: string
}

export async function POST(request: NextRequest) {
  try {
    const { query } = await request.json()

    if (!query || query.trim() === '') {
      return NextResponse.json(
        { error: 'Query is required' },
        { status: 400 }
      )
    }

    // Call our real backend server
    try {
      const response = await fetch('http://localhost:8000/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      })
      
      if (!response.ok) {
        throw new Error(`Backend server error: ${response.status}`)
      }
      
      const result = await response.json()
      return NextResponse.json(result)
      
    } catch (backendError) {
      console.error('Backend server error:', backendError)
      // Fallback to empty results if backend fails
      return NextResponse.json({
        results: [],
        total: 0,
        has_more: false,
        query: query
      })
    }

  } catch (error) {
    console.error('Search API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
} 