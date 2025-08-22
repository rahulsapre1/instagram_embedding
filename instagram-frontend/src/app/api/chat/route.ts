import { NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'
import path from 'path'

// Types for chat request and response
interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

interface ChatRequest {
  message: string
  conversation_id?: string
  conversation_history: ChatMessage[]
}

interface ChatResponse {
  response: string
  conversation_id: string
  should_refresh_search: boolean
  new_search_query?: string
}

interface APIResult {
  success: boolean
  response: string
  should_search?: boolean
  search_query?: string
}

// SearchContext class - exact copy from CLI version
class SearchContext {
  base_query: string = ""
  filters: Record<string, unknown> = {}
  conversation_history: ChatMessage[] = []
  last_results: unknown[] = []

  add_conversation(role: string, content: string) {
    this.conversation_history.push({
      role: role as 'user' | 'assistant',
      content: content,
      timestamp: new Date().toISOString()
    })
  }

  update_filters(new_filters: Record<string, unknown>) {
    this.filters = { ...this.filters, ...new_filters }
  }

  get_filter_summary(): string {
    if (Object.keys(this.filters).length === 0) {
      return "No filters applied"
    }
    
    const summaries: string[] = []
    if (this.filters.follower_category) {
      summaries.push(`Follower category: ${this.filters.follower_category}`)
    }
    if (this.filters.account_type) {
      summaries.push(`Account type: ${this.filters.account_type}`)
    }
    if (this.filters.min_followers) {
      summaries.push(`Min followers: ${this.filters.min_followers}`)
    }
    if (this.filters.max_followers) {
      summaries.push(`Max followers: ${this.filters.max_followers}`)
    }
    
    return summaries.join(", ")
  }
}



// Function to call interactive_search_api.py
async function callInteractiveSearchAPI(userInput: string, searchContext: SearchContext): Promise<APIResult> {
  return new Promise((resolve) => {
    // Path to the interactive_search_api.py script
    const scriptPath = path.join(process.cwd(), '..', 'interactive_search_api.py')
    const pythonPath = path.join(process.cwd(), '..', 'venv', 'bin', 'python')
    
    console.log('Calling interactive search API with input:', userInput)
    console.log('Conversation history length:', searchContext.conversation_history.length)
    
    // Check if files exist
    try {
      const fs = require('fs')
      if (!fs.existsSync(scriptPath)) {
        resolve({ success: false, response: 'Interactive search API script not found' })
        return
      }
      if (!fs.existsSync(pythonPath)) {
        resolve({ success: false, response: 'Python not found' })
        return
      }
    } catch (error) {
      resolve({ success: false, response: 'Failed to check file existence' })
      return
    }
    
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
      console.log('Python API process closed with code:', code)
      console.log('Python API output:', output)
      
      if (code === 0) {
        try {
          const result = JSON.parse(output) as APIResult
          resolve(result)
        } catch (parseError) {
          console.error('Error parsing Python API response:', parseError)
          resolve({ success: false, response: 'Failed to parse API response' })
        }
      } else {
        console.error('Python API error:', errorOutput)
        resolve({ success: false, response: 'Python API failed' })
      }
    })
    
    // Handle process errors
    pythonProcess.on('error', (error: Error) => {
      console.error('Failed to start Python API:', error)
      resolve({ success: false, response: 'Failed to start Python API' })
    })
    
    // Send user input and conversation history to the Python script
    const inputData = {
      message: userInput,
      conversation_history: searchContext.conversation_history
    }
    pythonProcess.stdin.write(JSON.stringify(inputData) + '\n')
    pythonProcess.stdin.end()
    
    // Set timeout to prevent hanging
    setTimeout(() => {
      console.log('Python API process timeout, killing...')
      pythonProcess.kill()
      resolve({ success: false, response: 'Python API timeout' })
    }, 30000) // 30 second timeout
  })
}

export async function POST(request: NextRequest) {
  try {
    const { message, conversation_id, conversation_history } = await request.json() as ChatRequest

    if (!message || message.trim() === '') {
      return NextResponse.json(
        { error: 'Message is required' },
        { status: 400 }
      )
    }

    // Generate or use existing conversation ID
    const convId = conversation_id || `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    // Create a temporary SearchContext with the provided conversation history
    const searchContext = new SearchContext()
    
    // Load the existing conversation history from the frontend
    if (conversation_history && conversation_history.length > 0) {
      searchContext.conversation_history = conversation_history
    }

    // Add user message to conversation history
    searchContext.add_conversation('user', message)

    // Call the actual interactive_search.py script with proper context
    let response: string
    let should_refresh_search = false
    let new_search_query: string | undefined

    try {
      const apiResult = await callInteractiveSearchAPI(message, searchContext)
      
      if (apiResult.success) {
        response = apiResult.response
        should_refresh_search = apiResult.should_search || false
        new_search_query = apiResult.search_query
        
        console.log('AI response:', response)
        console.log('Should search:', should_refresh_search)
        console.log('Search query:', new_search_query)
      } else {
        // Handle API error
        response = apiResult.response || "I encountered an error processing your request."
      }
      
    } catch (error) {
      console.error('Interactive search API error:', error)
      
      // Fallback response if Python API fails
      response = "I'm having trouble processing your request right now. Please try again or rephrase your question."
    }

    // Add assistant response to conversation history (exact same as CLI version)
    searchContext.add_conversation('assistant', response)

    // Keep only last 20 messages to prevent memory issues (like CLI version)
    if (searchContext.conversation_history.length > 20) {
      searchContext.conversation_history = searchContext.conversation_history.slice(-20)
    }

    const chatResponse: ChatResponse = {
      response,
      conversation_id: convId,
      should_refresh_search,
      new_search_query: new_search_query
    }

    return NextResponse.json(chatResponse)

  } catch (error) {
    console.error('Chat API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
} 