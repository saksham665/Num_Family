from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import requests
import json
import sys

def process_api_request(mobile_number):
    """Main API processing logic - Only returns id_number API results"""
    # First API call - Get mobile number info
    num_api_url = f"https://osinttx.karobetahack.workers.dev/?term={mobile_number}"
    
    try:
        num_response = requests.get(num_api_url, timeout=10)
        num_response.raise_for_status()
        num_data = num_response.json()
    except:
        return {"success": False, "error": "Service temporarily unavailable"}
    
    # Check if mobile API was successful
    if not num_data.get('success', False):
        return {"success": False, "error": "No data found"}
    
    # Check if result exists and has data
    results = num_data.get('result', [])
    if not results:
        return {"success": False, "error": "No data found"}
    
    # Process each result to get Aadhar info
    final_results = []
    for result in results:
        # Extract id_number (Aadhar) if available
        id_number = result.get('id_number', '').strip()
        
        # If id_number is available and valid (12 digits), call second API
        if id_number and id_number.isdigit() and len(id_number) == 12:
            try:
                # Second API call - Get family members info
                aadhar_api_url = f"https://family-members-info.vercel.app/fetch?key=paidkey&aadhar={id_number}"
                aadhar_response = requests.get(aadhar_api_url, timeout=10)
                aadhar_response.raise_for_status()
                aadhar_data = aadhar_response.json()
                
                # ONLY return the id_number API data (family_info)
                final_results.append(aadhar_data)
                
            except:
                # If second API fails, skip this result
                continue
        else:
            # If no valid id_number, skip this result
            continue
    
    # If no successful id_number API results
    if not final_results:
        return {"success": False, "error": "No family data available"}
    
    # Prepare final response - ONLY id_number API data
    final_response = {
        'success': True,
        'result': final_results
    }
    
    return final_response

class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse query parameters
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            # Get mobile number from query parameter
            mobile_numbers = query_params.get('num', [])
            
            if not mobile_numbers:
                self.send_error_response("Missing 'num' parameter")
                return
                
            mobile_number = mobile_numbers[0].strip()
            
            # Validate mobile number (10 digits)
            if not mobile_number.isdigit() or len(mobile_number) != 10:
                self.send_error_response("Invalid mobile number. Must be 10 digits.")
                return
            
            # Process the API request
            result = process_api_request(mobile_number)
            
            if result.get('success', False):
                self.send_success_response(result)
            else:
                self.send_error_response(result.get('error', 'Service temporarily unavailable'))
                
        except Exception as e:
            self.send_error_response("Service temporarily unavailable")
    
    def send_success_response(self, data):
        """Send successful JSON response - RAW JSON (no pretty print)"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # RAW JSON response (no indentation, no pretty print)
        response_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        self.wfile.write(response_json.encode('utf-8'))
    
    def send_error_response(self, message):
        """Send error JSON response - RAW JSON"""
        self.send_response(400)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        error_response = {
            'success': False,
            'error': message
        }
        # RAW JSON response
        response_json = json.dumps(error_response, ensure_ascii=False, separators=(',', ':'))
        self.wfile.write(response_json.encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Disable server logs to prevent any information leakage"""
        pass

def start_local_server(port=8000):
    """Start local server for Termux"""
    server = HTTPServer(('localhost', port), APIHandler)
    print(f"Server running on http://localhost:{port}")
    print(f"Test URL: http://localhost:{port}/?num=")
    print("Press Ctrl+C to stop the server")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")

# Vercel compatibility
if __name__ == "__main__":
    # This runs when executed directly (Termux)
    start_local_server()
else:
    # This runs on Vercel
    from http.server import BaseHTTPRequestHandler as VercelHandler
    globals()['Handler'] = type('Handler', (VercelHandler,), {
        'do_GET': APIHandler.do_GET,
        'do_OPTIONS': APIHandler.do_OPTIONS,
        'send_success_response': APIHandler.send_success_response,
        'send_error_response': APIHandler.send_error_response,
        'log_message': APIHandler.log_message
    })
