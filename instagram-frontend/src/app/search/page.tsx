'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Search, 
  MessageCircle, 
  Users, 
  TrendingUp, 
  Globe, 
  Heart,
  Star,
  ExternalLink,
  Loader2,
  Sparkles
} from 'lucide-react'

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
  const [currentSearchQuery, setCurrentSearchQuery] = useState('')
  const [chatMessages, setChatMessages] = useState([
    { 
      role: 'assistant', 
      content: 'Hi! I\'m your AI search assistant. I can help you find the perfect influencers for your brand or campaign. Just tell me what you\'re looking for and I\'ll search our database of Instagram profiles.\n\nTry asking things like:\n\n• "Find fitness influencers in Melbourne"\n• "Show me travel bloggers in Sydney"\n• "I need food content creators with 50K+ followers"\n\nWhat would you like to search for today?' 
    }
  ])
  const [chatInput, setChatInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)

  // Handle search (called from chat responses)
  const handleSearch = async (query: string, page: number = 1) => {
    if (!query.trim()) return
    
    setIsSearching(true)
    setCurrentPage(page)
    
    try {
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
      
      if (!response.ok) {
        throw new Error('Search failed')
      }
      
      const data: SearchResponse = await response.json()
      setSearchResults(data.results)
      setTotalResults(data.total)
      setHasSearched(true)
      setCurrentSearchQuery(query)
      
    } catch (error) {
      console.error('Search error:', error)
      setSearchResults([])
      setTotalResults(0)
    } finally {
      setIsSearching(false)
    }
  }

  // Handle chat send
  const handleChatSend = async () => {
    if (!chatInput.trim() || isTyping) return
    
    const userMessage = chatInput.trim()
    setChatInput('')
    setIsTyping(true)
    
    // Add user message to chat
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }])
    
    try {
      // Call chat API with conversation history
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          conversation_history: chatMessages
        }),
      })
      
      if (!response.ok) {
        throw new Error('Chat failed')
      }
      
      const data = await response.json()
      
      // Add assistant response to chat
      setChatMessages(prev => [...prev, { role: 'assistant', content: data.response }])
      
      // If search was triggered, display results
      if (data.should_refresh_search && data.results) {
        setSearchResults(data.results)
        setTotalResults(data.total || data.results.length)
        setHasSearched(true)
        setCurrentSearchQuery(data.new_search_query || userMessage)
        setIsSearching(false)
      }
      
    } catch (error) {
      console.error('Chat error:', error)
      setChatMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.' 
      }])
    } finally {
      setIsTyping(false)
    }
  }

  // Format follower count
  const formatFollowerCount = (count: number) => {
    if (count >= 1000000) {
      return `${(count / 1000000).toFixed(1)}M`
    } else if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}K`
    }
    return count.toString()
  }

  // Get influencer type color
  const getInfluencerTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'nano': return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'micro': return 'bg-green-100 text-green-800 border-green-200'
      case 'macro': return 'bg-purple-100 text-purple-800 border-purple-200'
      case 'mega': return 'bg-orange-100 text-orange-800 border-orange-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  // Get account type color
  const getAccountTypeColor = (type: string) => {
    return type === 'human' 
      ? 'bg-indigo-100 text-indigo-800 border-indigo-200' 
      : 'bg-pink-100 text-pink-800 border-pink-200'
  }

  // Calculate total pages
  const totalPages = Math.ceil(totalResults / 20)
  const canGoPrev = currentPage > 1
  const canGoNext = currentPage < totalPages

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-md border-b border-slate-200/50 sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg">
                <Sparkles className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Influencer Search
                </h1>
                <p className="text-sm text-slate-600">AI-Powered Instagram Profile Discovery</p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <Users className="h-4 w-4" />
              <span>{totalResults.toLocaleString()} profiles</span>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-200px)]">
          
          {/* Search Results - Left Side */}
          <div className="lg:col-span-2 overflow-hidden">
            <Card className="h-full flex flex-col border-0 shadow-lg bg-white/80 backdrop-blur-sm">
              <CardHeader className="border-b border-slate-200/50 bg-gradient-to-r from-slate-50 to-blue-50/30">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Search className="h-5 w-5 text-blue-600" />
                    <CardTitle className="text-lg font-semibold text-slate-800">
                      Search Results
                    </CardTitle>
                  </div>
                  {hasSearched && (
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="bg-blue-100 text-blue-800 border-blue-200">
                        {totalResults} results
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {searchResults.length > 0 && searchResults[0].username === 'melbourne_foodie' ? 'Mock Data' : 'Real Data'}
                      </Badge>
                    </div>
                  )}
                </div>
              </CardHeader>
              
              <ScrollArea className="flex-1 p-6">
                {!hasSearched ? (
                  <div className="text-center py-16">
                    <div className="mx-auto w-24 h-24 bg-gradient-to-r from-blue-100 to-purple-100 rounded-full flex items-center justify-center mb-6">
                      <Search className="h-12 w-12 text-blue-600" />
                    </div>
                    <h3 className="text-xl font-semibold text-slate-800 mb-2">
                      Ready to Discover Influencers?
                    </h3>
                    <p className="text-slate-600 mb-4">
                      Use the AI chat assistant on the right to search for Instagram profiles
                    </p>
                    <div className="flex items-center justify-center gap-4 text-sm text-slate-500">
                      <div className="flex items-center gap-2">
                        <TrendingUp className="h-4 w-4" />
                        <span>Real-time search</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Globe className="h-4 w-4" />
                        <span>Global database</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Heart className="h-4 w-4" />
                        <span>AI-powered</span>
                      </div>
                    </div>
                  </div>
                ) : isSearching ? (
                  <div className="text-center py-16">
                    <div className="mx-auto w-24 h-24 bg-gradient-to-r from-blue-100 to-purple-100 rounded-full flex items-center justify-center mb-6">
                      <Loader2 className="h-12 w-12 text-blue-600 animate-spin" />
                    </div>
                    <h3 className="text-xl font-semibold text-slate-800 mb-2">
                      Searching Our Database
                    </h3>
                    <p className="text-slate-600">This may take a few moments</p>
                  </div>
                ) : searchResults.length === 0 ? (
                  <div className="text-center py-16">
                    <div className="mx-auto w-24 h-24 bg-gradient-to-r from-red-100 to-pink-100 rounded-full flex items-center justify-center mb-6">
                      <Search className="h-12 w-12 text-red-600" />
                    </div>
                    <h3 className="text-xl font-semibold text-slate-800 mb-2">
                      No Results Found
                    </h3>
                    <p className="text-slate-600 mb-4">
                      Try refining your search or ask the AI assistant for help
                    </p>
                  </div>
                ) : (
                  <>
                    {/* Current Search Query */}
                    <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border border-blue-200/50">
                      <div className="flex items-center gap-3">
                        <Search className="h-5 w-5 text-blue-600" />
                        <div>
                          <p className="text-sm font-medium text-blue-800">
                            Current Search
                          </p>
                          <p className="text-blue-700 font-semibold">
                            {currentSearchQuery || 'Search query'}
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    {/* Results Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {searchResults.map((result, index) => (
                        <Card 
                          key={index} 
                          className="group hover:shadow-xl transition-all duration-300 border-slate-200/50 hover:border-blue-300/50 overflow-hidden"
                        >
                          <CardContent className="p-0">
                            {/* Header with avatar and badges */}
                            <div className="p-4 bg-gradient-to-r from-slate-50 to-blue-50/30 border-b border-slate-200/50">
                              <div className="flex items-start justify-between mb-3">
                                <div className="flex items-center gap-3">
                                  <Avatar className="h-12 w-12 border-2 border-white shadow-md">
                                    <AvatarImage src={result.profile_pic_url} />
                                    <AvatarFallback className="bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold">
                                      {result.full_name?.charAt(0) || result.username?.charAt(0) || '?'}
                                    </AvatarFallback>
                                  </Avatar>
                                  <div>
                                    <h3 className="font-bold text-lg text-slate-800 group-hover:text-blue-600 transition-colors">
                                      @{result.username}
                                    </h3>
                                    <p className="text-slate-600 font-medium text-sm">
                                      {result.full_name}
                                    </p>
                                  </div>
                                </div>
                                <div className="flex flex-col gap-2">
                                  <Badge 
                                    variant="outline" 
                                    className={`text-xs ${getAccountTypeColor(result.account_type)}`}
                                  >
                                    {result.account_type}
                                  </Badge>
                                  <Badge 
                                    variant="outline" 
                                    className={`text-xs ${getInfluencerTypeColor(result.influencer_type)}`}
                                  >
                                    {result.influencer_type}
                                  </Badge>
                                </div>
                              </div>
                            </div>

                            {/* Content */}
                            <div className="p-4">
                              {result.bio && (
                                <p className="text-sm text-slate-600 mb-4 line-clamp-2">
                                  {result.bio}
                                </p>
                              )}
                              
                              <div className="space-y-3">
                                {/* Follower count */}
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-2 text-slate-600">
                                    <Users className="h-4 w-4" />
                                    <span className="text-sm">Followers</span>
                                  </div>
                                  <span className="font-bold text-lg text-slate-800">
                                    {formatFollowerCount(result.follower_count)}
                                  </span>
                                </div>

                                {/* Score */}
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-2 text-slate-600">
                                    <Star className="h-4 w-4" />
                                    <span className="text-sm">Match Score</span>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <div className="w-16 bg-slate-200 rounded-full h-2">
                                      <div 
                                        className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-300"
                                        style={{ width: `${(result.score * 100)}%` }}
                                      />
                                    </div>
                                    <span className="font-bold text-sm text-slate-800">
                                      {(result.score * 100).toFixed(0)}%
                                    </span>
                                  </div>
                                </div>

                                <Separator />

                                {/* Actions */}
                                <div className="flex items-center justify-between pt-2">
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    className="hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 transition-colors"
                                    onClick={() => window.open(`https://www.instagram.com/${result.username}/`, '_blank')}
                                  >
                                    <ExternalLink className="h-4 w-4 mr-2" />
                                    View Profile
                                  </Button>
                                  
                                  {result.is_private && (
                                    <Badge variant="secondary" className="bg-amber-100 text-amber-800 border-amber-200">
                                      Private Account
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                    
                    {/* Pagination */}
                    {totalPages > 1 && (
                      <div className="flex items-center justify-center gap-2 mt-8">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleSearch('', currentPage - 1)}
                          disabled={!canGoPrev}
                          className="hover:bg-blue-50 hover:border-blue-300"
                        >
                          Previous
                        </Button>
                        <span className="text-sm text-slate-600 px-4 py-2 bg-slate-100 rounded-md">
                          Page {currentPage} of {totalPages}
                        </span>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleSearch('', currentPage + 1)}
                          disabled={!canGoNext}
                          className="hover:bg-blue-50 hover:border-blue-300"
                        >
                          Next
                        </Button>
                      </div>
                    )}
                  </>
                )}
              </ScrollArea>
            </Card>
          </div>

          {/* Chat Assistant - Right Side */}
          <div className="lg:col-span-1 overflow-hidden">
            <Card className="h-full flex flex-col border-0 shadow-lg bg-white/80 backdrop-blur-sm">
              <CardHeader className="border-b border-slate-200/50 bg-gradient-to-r from-slate-50 to-purple-50/30">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg">
                    <MessageCircle className="h-5 w-5 text-white" />
                  </div>
                  <CardTitle className="text-lg font-semibold text-slate-800">
                    AI Chat Assistant
                  </CardTitle>
                </div>
              </CardHeader>
              
              <CardContent className="flex-1 flex flex-col min-h-0 p-0">
                <ScrollArea className="flex-1 p-4">
                  <div className="space-y-4">
                    {chatMessages.map((message, index) => (
                      <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] p-4 rounded-2xl ${
                          message.role === 'user' 
                            ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white' 
                            : 'bg-slate-100 text-slate-800 border border-slate-200'
                        }`}>
                          <div className="flex items-start gap-3">
                            {message.role === 'assistant' && (
                              <div className="p-1 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full mt-1">
                                <Sparkles className="h-3 w-3 text-white" />
                              </div>
                            )}
                            <div className="whitespace-pre-wrap text-sm leading-relaxed">
                              {message.content}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                    
                    {isTyping && (
                      <div className="flex justify-start">
                        <div className="max-w-[85%] p-4 rounded-2xl bg-slate-100 text-slate-800 border border-slate-200">
                          <div className="flex items-center gap-2">
                            <div className="p-1 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full">
                              <Sparkles className="h-3 w-3 text-white" />
                            </div>
                            <div className="flex items-center gap-1">
                              <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" />
                              <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                              <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </ScrollArea>
                
                {/* Chat Input */}
                <div className="p-4 border-t border-slate-200/50 bg-slate-50/50">
                  <div className="flex gap-2">
                    <Input
                      placeholder="Ask me anything about your search..."
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleChatSend()}
                      className="flex-1 border-slate-200 focus:border-blue-300 focus:ring-blue-200 transition-colors"
                      disabled={isTyping}
                    />
                    <Button 
                      onClick={handleChatSend} 
                      size="sm"
                      disabled={isTyping || !chatInput.trim()}
                      className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-md hover:shadow-lg"
                    >
                      {isTyping ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <MessageCircle className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
} 