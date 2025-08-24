import { NextRequest, NextResponse } from 'next/server'

// Types for chat request and response
interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

interface ChatRequest {
  message: string
  conversation_history: ChatMessage[]
}

interface ChatResponse {
  response: string
  should_search: boolean
  search_query?: string
  results?: InfluencerProfile[]
  total?: number
}

// Types for influencer profiles
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

// Function to call our real backend server
async function callInteractiveSearchAPI(userInput: string, conversationHistory: ChatMessage[]): Promise<ChatResponse> {
  try {
    // Call our real backend server
    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: userInput,
        conversation_history: conversationHistory
      }),
    })
    
    if (!response.ok) {
      throw new Error(`Backend server error: ${response.status}`)
    }
    
    const result = await response.json()
    
    return {
      response: result.response || 'Sorry, I encountered an error.',
      should_search: result.should_refresh_search || false,
      search_query: result.new_search_query || userInput,
      results: result.results || [],
      total: result.total || 0
    }
    
  } catch (error) {
    console.error('Error calling backend server:', error)
    return {
      response: 'Sorry, I encountered an error. Please try again.',
      should_search: false
    }
  }
}

export async function POST(request: NextRequest) {
  try {
    const { message, conversation_history } = await request.json() as ChatRequest

    if (!message || message.trim() === '') {
      return NextResponse.json(
        { error: 'Message is required' },
        { status: 400 }
      )
    }

    // Add user message to conversation history
    // This class is no longer needed as the backend handles context
    // For now, we'll just pass the history directly
    const updatedHistory: ChatMessage[] = [...conversation_history, {
      role: 'user' as const,
      content: message,
      timestamp: new Date().toISOString()
    }]

    // Call the actual interactive_search.py script with proper context
    let response: string
    let should_refresh_search = false
    let new_search_query: string | undefined
    let results: InfluencerProfile[] | undefined
    let total: number | undefined

    try {
      const chatResponse = await callInteractiveSearchAPI(message, updatedHistory)
      
      response = chatResponse.response
      should_refresh_search = chatResponse.should_search
      new_search_query = chatResponse.search_query
      results = chatResponse.results
      total = chatResponse.total
      
      console.log('AI response:', response)
      console.log('Should search:', should_refresh_search)
      console.log('Search query:', new_search_query)
      console.log('Results:', results)
      console.log('Total:', total)
    } catch (error) {
      console.error('Interactive search API error:', error)
      response = "I encountered an error processing your request."
      should_refresh_search = false
    }

    // Add assistant response to conversation history (exact same as CLI version)
    // This class is no longer needed as the backend handles context
    // For now, we'll just pass the history directly
    const finalHistory: ChatMessage[] = [...updatedHistory, {
      role: 'assistant' as const,
      content: response,
      timestamp: new Date().toISOString()
    }]

    // Keep only last 20 messages to prevent memory issues (like CLI version)
    if (finalHistory.length > 20) {
      finalHistory.slice(-20)
    }

    // Return the response with conversation context
    return NextResponse.json({
      response,
      should_refresh_search,
      new_search_query: new_search_query,
      results: results,
      total: total
    })

  } catch (error) {
    console.error('Chat API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
} 