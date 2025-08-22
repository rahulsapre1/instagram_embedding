'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

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
  profile_pic_url?: string
  is_private: boolean
}

interface SearchResponse {
  results: InfluencerProfile[]
  total: number
  has_more: boolean
  query: string
}

export default function SearchPage() {
  const [searchResults, setSearchResults] = useState<InfluencerProfile[]>([])
  const [hasSearched, setHasSearched] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalResults, setTotalResults] = useState(0)
  const [isSearching, setIsSearching] = useState(false)
  const [searchProgress, setSearchProgress] = useState('')
  const [currentSearchQuery, setCurrentSearchQuery] = useState('')
  const [chatMessages, setChatMessages] = useState([
    { role: 'assistant', content: 'Hi! I can help you find the perfect Australian influencers. Just tell me what you&apos;re looking for and I&apos;ll search for you. Try asking things like:\n\n• "Find fitness influencers in Melbourne"\n• "Show me travel bloggers in Sydney"\n• "I need food content creators with 50K+ followers"\n\nWhat would you like to search for?' }
  ])
  const [chatInput, setChatInput] = useState('')
  const [conversationId, setConversationId] = useState<string>('')
  const [searchStartTime, setSearchStartTime] = useState<number | null>(null)

  // Handle search (called from chat responses)
  const handleSearch = async (query: string, page: number = 1) => {
    if (!query.trim()) return
    
    setIsSearching(true)
    setSearchProgress('Initializing search...')
    setCurrentPage(page)
    setSearchStartTime(Date.now()) // Start timer
    
    try {
      // Start progress updates
      const progressInterval = setInterval(() => {
        setSearchProgress(prev => {
          if (prev.includes('Searching vector database')) {
            return 'Searching vector database... (this may take up to 2 minutes)'
          } else if (prev.includes('Initializing')) {
            return 'Loading AI models...'
          } else if (prev.includes('Loading AI models')) {
            return 'Generating query embeddings...'
          } else if (prev.includes('Generating query embeddings')) {
            return 'Searching vector database...'
          }
          return prev
        })
      }, 3000)
      
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          limit: 20,
          offset: (page - 1) * 20
        }),
      })
      
      clearInterval(progressInterval)
      
      if (!response.ok) {
        throw new Error('Search failed')
      }
      
      const data: SearchResponse = await response.json()
      setSearchResults(data.results)
      setTotalResults(data.total)
      setHasSearched(true)
      setSearchProgress('')
      setCurrentSearchQuery(query) // Update current search query
      
    } catch (error) {
      console.error('Search error:', error)
      setSearchResults([])
      setTotalResults(0)
      setSearchProgress('')
      setCurrentSearchQuery('') // Clear current search query on error
    } finally {
      setIsSearching(false)
      setSearchStartTime(null) // Reset timer
    }
  }

  // Handle chat send
  const handleChatSend = async () => {
    if (!chatInput.trim()) return
    
    const userMessage = { role: 'user', content: chatInput }
    setChatMessages(prev => [...prev, userMessage])
    setChatInput('')
    
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: chatInput,
          conversation_id: conversationId,
          conversation_history: chatMessages // Send the full conversation history
        }),
      })
      
      if (!response.ok) {
        throw new Error('Chat failed')
      }
      
      const data = await response.json()
      
      // Add assistant response
      const assistantMessage = { role: 'assistant', content: data.response }
      setChatMessages(prev => [...prev, assistantMessage])
      
      // Update conversation ID
      if (data.conversation_id) {
        setConversationId(data.conversation_id)
      }
      
      // ALWAYS execute search for every chat message
      if (data.new_search_query) {
        console.log('Executing search for chat message:', data.new_search_query)
        handleSearch(data.new_search_query, 1)
      } else {
        // If no search query provided, use the user's input as fallback
        console.log('No search query provided, using user input as fallback')
        handleSearch(chatInput, 1)
      }
      
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage = { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }
      setChatMessages(prev => [...prev, errorMessage])
    }
  }






  // Calculate pagination
  const totalPages = Math.min(Math.ceil(totalResults / 20), 5) // Max 5 pages
  const canGoNext = currentPage < totalPages
  const canGoPrev = currentPage > 1

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Influencer Search</h1>
            <Button variant="outline" onClick={() => window.history.back()}>
              ← Back
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-200px)]">
          {/* Results Column (Left) */}
          <div className="lg:col-span-2 overflow-hidden">
            <Card className="h-full flex flex-col">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  Search Results
                  {hasSearched && (
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">
                        {totalResults} results
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {searchResults.length > 0 && searchResults[0].username === 'melbourne_foodie' ? 'Mock Data' : 'Real Data'}
                      </Badge>
                    </div>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto">
                {!hasSearched ? (
                  <div className="text-center py-12 text-gray-500">
                    <p>Use the chat on the right to search for Australian influencers</p>
                    <p className="text-sm mt-2">Just tell me what you're looking for and I'll find them for you!</p>
                  </div>
                ) : isSearching ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600 font-medium">{searchProgress}</p>
                    <p className="text-sm text-gray-500 mt-2">This may take up to 2 minutes for the first search</p>
                    
                    {/* Visual Progress Bar */}
                    <div className="mt-6 max-w-md mx-auto">
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div 
                          className="bg-blue-600 h-3 rounded-full transition-all duration-1000 ease-out"
                          style={{ 
                            width: `${Math.min((Date.now() - (searchStartTime || Date.now())) / 75000 * 100, 100)}%` 
                          }}
                        ></div>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        {Math.min(Math.round((Date.now() - (searchStartTime || Date.now())) / 75000 * 100), 100)}% Complete
                      </p>
                    </div>
                  </div>
                ) : searchResults.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <p>No results found for your search</p>
                    <p className="text-sm mt-2">Try refining your search or ask the AI assistant for help</p>
                  </div>
                ) : (
                  <>
                    {/* Show current search query */}
                    <div className="mb-4 p-3 bg-blue-50 rounded-lg border-l-4 border-blue-400">
                      <p className="text-sm text-blue-800">
                        <strong>Current Search:</strong> {currentSearchQuery || 'Search query'}
                      </p>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {searchResults.map((result, index) => (
                        <div key={index} className="p-4 border rounded-lg hover:shadow-md transition-shadow cursor-pointer">
                          <div className="space-y-3">
                            <div className="flex items-center gap-3">
                              <h3 className="font-semibold text-lg">@{result.username}</h3>
                              <Badge variant={result.account_type === 'human' ? 'default' : 'secondary'}>
                                {result.account_type}
                              </Badge>
                              <Badge variant="outline">{result.category}</Badge>
                            </div>
                            <p className="text-gray-600 font-medium">{result.full_name}</p>
                            <p className="text-sm text-gray-500 line-clamp-2">{result.bio}</p>
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-600">
                                <strong>{result.follower_count.toLocaleString()}</strong> followers
                              </span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-gray-600 text-sm">
                                Score: <strong>{(result.score * 100).toFixed(0)}%</strong>
                              </span>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => window.open(`https://www.instagram.com/${result.username}/`, '_blank')}
                              >
                                View Profile
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                    
                    {/* Pagination */}
                    {totalPages > 1 && (
                      <div className="flex items-center justify-center gap-2 mt-6">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleSearch('', currentPage - 1)}
                          disabled={!canGoPrev}
                        >
                          Previous
                        </Button>
                        <span className="text-sm text-gray-600">
                          Page {currentPage} of {totalPages}
                        </span>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleSearch('', currentPage + 1)}
                          disabled={!canGoNext}
                        >
                          Next
                        </Button>
                      </div>
                    )}
                  </>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Chat Column (Right) */}
          <div className="lg:col-span-1 overflow-hidden">
            <Card className="h-full flex flex-col">
              <CardHeader>
                <CardTitle>AI Chat Assistant</CardTitle>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col min-h-0">
                {/* Chat Messages - Scrollable Area */}
                <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
                  {chatMessages.map((message, index) => (
                    <div
                      key={index}
                      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[80%] p-3 rounded-lg ${
                          message.role === 'user'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-900'
                        }`}
                      >
                        {message.content}
                        {message.role === 'user' && (
                          <div className="text-xs text-blue-200 mt-2">
                            🔍 Searching for: {message.content}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Chat Input - Fixed at Bottom */}
                <div className="flex gap-2 mt-auto pt-2 border-t border-gray-200">
                  <Input
                    placeholder="Ask me anything about your search..."
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleChatSend()}
                  />
                  <Button onClick={handleChatSend} size="sm">
                    Send
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
} 