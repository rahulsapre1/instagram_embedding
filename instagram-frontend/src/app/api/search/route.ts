import { NextRequest, NextResponse } from 'next/server'

// Types for search request and response
interface SearchRequest {
  query: string
  filters?: {
    follower_count?: [number, number?]
    account_type?: string
    influencer_type?: string
  }
  limit?: number
  offset?: number
}

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

interface SearchAPIResult {
  success: boolean
  data?: SearchResponse
  error?: string
}

export async function POST(request: NextRequest) {
  try {
    const { query, filters, limit = 20, offset = 0 } = await request.json()

    if (!query || query.trim() === '') {
      return NextResponse.json(
        { error: 'Query is required' },
        { status: 400 }
      )
    }

    console.log('Attempting to call Python search API...')
    console.log('Calling Python search API with query:', query)

    // Call the Python search API
    const searchResult = await callPythonSearchAPI(query, filters, limit, offset)
    
    // Return the search results directly
    return NextResponse.json(searchResult)

  } catch (error) {
    console.error('Search API error:', error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Search failed' },
      { status: 500 }
    )
  }
}

// Function to call Python search API
async function callPythonSearchAPI(query: string, filters: unknown, limit: number, offset: number): Promise<SearchResponse> {
  return new Promise((resolve, reject) => {
    const { spawn } = require('child_process')
    const path = require('path')
    
    // Path to the search API script
    const scriptPath = path.join(process.cwd(), '..', 'search_api.py')
    const pythonPath = path.join(process.cwd(), '..', 'venv', 'bin', 'python')
    
    console.log('Calling Python search API with query:', query)
    console.log('Script path:', scriptPath)
    console.log('Python path:', pythonPath)
    
    // Check if files exist
    try {
      const fs = require('fs')
      if (!fs.existsSync(scriptPath)) {
        console.error('Search API script not found at:', scriptPath)
        reject(new Error('Search API script not found'))
        return
      }
      if (!fs.existsSync(pythonPath)) {
        console.error('Python not found at:', pythonPath)
        reject(new Error('Python not found'))
        return
      }
    } catch (error) {
      reject(new Error('Failed to check file existence'))
      return
    }
    
    console.log('✅ Both script and Python found, proceeding with search...')
    
    // Spawn Python process
    const pythonProcess = spawn(pythonPath, [scriptPath], {
      cwd: path.join(process.cwd(), '..'),
      env: { 
        ...process.env, 
        PYTHONPATH: path.join(process.cwd(), '..'),
        PATH: `${path.join(process.cwd(), '..', 'venv', 'bin')}:${process.env.PATH}`
      }
    })
    
    let output = ''
    let errorOutput = ''
    
    // Handle stdout
    pythonProcess.stdout.on('data', (data: Buffer) => {
      output += data.toString()
    })
    
    // Handle stderr
    pythonProcess.stderr.on('data', (data: Buffer) => {
      errorOutput += data.toString()
    })
    
    // Handle process completion
    pythonProcess.on('close', (code: number | null) => {
      console.log('Python search API process closed with code:', code)
      
      if (code === 0) {
        try {
          const result = JSON.parse(output) as SearchResponse
          resolve(result)
        } catch (parseError) {
          console.error('Error parsing Python search API response:', parseError)
          throw new Error(`Failed to parse response: ${parseError}`)
        }
      } else {
        console.error('Python search API error:', errorOutput)
        throw new Error(`Python API failed with code ${code}`)
      }
    })
    
    // Handle process errors
    pythonProcess.on('error', (error: Error) => {
      console.error('Failed to start Python search API:', error)
      throw new Error(error.message)
    })
    
    // Send search parameters to Python
    const searchParams = {
      query,
      filters,
      limit,
      offset
    }
    
    pythonProcess.stdin.write(JSON.stringify(searchParams) + '\n')
    pythonProcess.stdin.end()
    
    // Set timeout to 2.5 minutes (150 seconds) to allow for vector DB processing
    setTimeout(() => {
      console.log('Python search API process timeout, killing...')
      pythonProcess.kill()
      reject(new Error('Python search API timeout (took longer than 2.5 minutes)'))
    }, 150000)
  })
}

// Fallback mock data function
function getMockSearchResults(query: string, filters: unknown, limit: number, offset: number): SearchResponse {
  const mockResults: InfluencerProfile[] = [
    {
      username: 'melbourne_foodie',
      full_name: 'Sarah Chen',
      bio: 'Melbourne food blogger sharing the best cafes and restaurants 🍕',
      follower_count: 125000,
      category: 'macro',
      account_type: 'human',
      influencer_type: 'food',
      score: 0.89,
      is_private: false
    },
    {
      username: 'sydney_fitness',
      full_name: 'Mike Johnson',
      bio: 'Sydney-based personal trainer helping you achieve your fitness goals 💪',
      follower_count: 89000,
      category: 'micro',
      account_type: 'human',
      influencer_type: 'fitness',
      score: 0.87,
      is_private: false
    },
    {
      username: 'brisbane_travel',
      full_name: 'Emma Davis',
      bio: 'Brisbane travel enthusiast exploring Queensland and beyond ✈️',
      follower_count: 156000,
      category: 'macro',
      account_type: 'human',
      influencer_type: 'travel',
      score: 0.85,
      is_private: false
    },
    {
      username: 'perth_lifestyle',
      full_name: 'Alex Rivera',
      bio: 'Perth lifestyle blogger sharing daily inspiration and local tips ✨',
      follower_count: 78000,
      category: 'micro',
      account_type: 'human',
      influencer_type: 'lifestyle',
      score: 0.83,
      is_private: false
    },
    {
      username: 'adelaide_fashion',
      full_name: 'Jordan Kim',
      bio: 'Adelaide fashion influencer sharing style tips and trends 👗',
      follower_count: 92000,
      category: 'micro',
      account_type: 'human',
      influencer_type: 'fashion',
      score: 0.81,
      is_private: false
    },
    {
      username: 'goldcoast_beauty',
      full_name: 'Maria Santos',
      bio: 'Gold Coast beauty and skincare expert 💄',
      follower_count: 134000,
      category: 'macro',
      account_type: 'human',
      influencer_type: 'beauty',
      score: 0.79,
      is_private: false
      }
    ]
  
  // Apply filters and pagination
  const filteredResults = mockResults
  const paginatedResults = filteredResults.slice(offset, offset + limit)
  const hasMore = offset + limit < filteredResults.length
  
  return {
    results: paginatedResults,
    total: filteredResults.length,
    has_more: hasMore,
    query
  }
} 