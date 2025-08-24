#!/usr/bin/env python3
"""
Simple HTTP server to expose our working interactive_search_api.py backend
This allows the Next.js frontend to call our Python backend without subprocess issues
"""

import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our working backend
from interactive_search_api import process_single_query

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackendHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests for chat and search"""
        try:
            # Parse the request
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            # Set CORS headers
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            # Route the request
            if self.path == '/api/chat':
                response = self.handle_chat(request_data)
            elif self.path == '/api/search':
                response = self.handle_search(request_data)
            else:
                response = {'error': 'Unknown endpoint'}
            
            # Send response
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def handle_chat(self, request_data):
        """Handle chat requests using our working backend"""
        try:
            message = request_data.get('message', '')
            conversation_history = request_data.get('conversation_history', [])
            
            logger.info(f"Processing chat: {message}")
            logger.info(f"Conversation history length: {len(conversation_history)}")
            
            # Call our working backend
            result = process_single_query(message, conversation_history)
            
            logger.info(f"Backend result: {result}")
            
            # Format response for frontend
            if result.get('success'):
                return {
                    'response': result.get('response', ''),
                    'should_refresh_search': result.get('should_search', False),
                    'new_search_query': result.get('search_query', ''),
                    'results': result.get('results', []),
                    'total': result.get('total', 0)
                }
            else:
                return {
                    'response': result.get('response', 'Sorry, I encountered an error.'),
                    'should_refresh_search': False,
                    'error': result.get('error', 'Unknown error')
                }
                
        except Exception as e:
            logger.error(f"Error in handle_chat: {e}")
            return {
                'response': f'Sorry, I encountered an error: {str(e)}',
                'should_refresh_search': False,
                'error': str(e)
            }
    
    def handle_search(self, request_data):
        """Handle direct search requests"""
        try:
            query = request_data.get('query', '')
            
            logger.info(f"Processing search: {query}")
            
            # Call our working backend
            result = process_single_query(query, [])
            
            if result.get('success') and result.get('results'):
                return {
                    'results': result.get('results', []),
                    'total': result.get('total', 0),
                    'has_more': False,
                    'query': query
                }
            else:
                # Return empty results if search failed
                return {
                    'results': [],
                    'total': 0,
                    'has_more': False,
                    'query': query
                }
                
        except Exception as e:
            logger.error(f"Error in handle_search: {e}")
            return {
                'results': [],
                'total': 0,
                'has_more': False,
                'query': request_data.get('query', ''),
                'error': str(e)
            }

def run_server(port=8000):
    """Run the HTTP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, BackendHandler)
    logger.info(f"Starting backend server on port {port}")
    logger.info(f"Server running at http://localhost:{port}")
    logger.info("Available endpoints:")
    logger.info("  POST /api/chat - Chat with AI and get search results")
    logger.info("  POST /api/search - Direct search")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        httpd.shutdown()

if __name__ == '__main__':
    run_server() 