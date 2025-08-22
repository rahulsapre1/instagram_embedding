// Configuration for the application
export const config = {
  // Database configuration
  database: {
    qdrant: {
      host: process.env.QDRANT_HOST || 'http://localhost:6333',
      apiKey: process.env.QDRANT_API_KEY || '',
      collection: process.env.QDRANT_COLLECTION || 'instagram_profiles'
    }
  },
  
  // API configuration
  api: {
    search: {
      defaultLimit: 20,
      maxLimit: 100,
      maxPages: 5
    },
    chat: {
      maxConversationLength: 10,
      maxMessageLength: 1000
    }
  },
  
  // Example search queries for Australia
  examples: {
    searchQueries: [
      "Melbourne food bloggers and cafe reviewers",
      "Sydney fitness influencers and personal trainers",
      "Brisbane travel content creators",
      "Perth lifestyle and wellness bloggers",
      "Adelaide fashion and beauty influencers",
      "Gold Coast travel and lifestyle content",
      "Canberra food and culture bloggers",
      "Darwin adventure and travel influencers",
      "Hobart food and wine content creators",
      "Newcastle fitness and health coaches"
    ],
    
    categories: {
      food: ["Melbourne food bloggers", "Sydney cafe reviewers", "Brisbane food content"],
      fitness: ["Sydney personal trainers", "Brisbane fitness coaches", "Perth wellness influencers"],
      travel: ["Queensland travel guides", "Perth adventure content", "Darwin travel bloggers"],
      fashion: ["Adelaide style influencers", "Gold Coast fashion bloggers", "Canberra fashion content"],
      lifestyle: ["Perth lifestyle bloggers", "Brisbane family content", "Hobart lifestyle influencers"],
      beauty: ["Gold Coast beauty experts", "Sydney beauty influencers", "Melbourne skincare bloggers"]
    },
    
    cities: {
      melbourne: "Food, coffee, arts, fashion, culture",
      sydney: "Fitness, lifestyle, beauty, travel, business",
      brisbane: "Travel, food, family content, lifestyle",
      perth: "Lifestyle, fitness, local businesses, wellness",
      adelaide: "Fashion, food, wine, culture, arts",
      goldCoast: "Beauty, lifestyle, travel, fitness",
      canberra: "Food, culture, politics, lifestyle",
      darwin: "Adventure, travel, local culture, nature",
      hobart: "Food, wine, culture, lifestyle, nature",
      newcastle: "Fitness, health, lifestyle, local content"
    }
  }
}

// Helper function to get environment variable with fallback
export function getEnvVar(key: string, fallback: string = ''): string {
  return process.env[key] || fallback
}

// Helper function to validate configuration
export function validateConfig(): boolean {
  const requiredEnvVars = [
    'QDRANT_HOST'
  ]
  
  for (const envVar of requiredEnvVars) {
    if (!getEnvVar(envVar)) {
      console.warn(`Warning: ${envVar} not set, using default value`)
    }
  }
  
  return true
} 