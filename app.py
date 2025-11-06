# app.py
from flask import Flask, request, jsonify, make_response
import requests
import json

app = Flask(__name__)

def process_api_request(mobile_number):
    """Return only family-info (id_number API) results."""
    num_api_url = f"https://osinttx.karobetahack.workers.dev/?term={mobile_number}"
    try:
        num_response = requests.get(num_api_url, timeout=10)
        num_response.raise_for_status()
        num_data = num_response.json()
    except Exception:
        return {"success": False, "error": "Service temporarily unavailable"}

    if not num_data.get('success', False):
        return {"success": False, "error": "No data found"}

    results = num_data.get('result', [])
    if not results:
        return {"success": False, "error": "No data found"}

    final_results = []
    for result in results:
        id_number = result.get('id_number', '').strip()
        if id_number and id_number.isdigit() and len(id_number) == 12:
            try:
                aadhar_api_url = f"https://family-members-info.vercel.app/fetch?key=paidkey&aadhar={id_number}"
                aadhar_response = requests.get(aadhar_api_url, timeout=10)
                aadhar_response.raise_for_status()
                aadhar_data = aadhar_response.json()
                final_results.append(aadhar_data)
            except Exception:
                continue

    if not final_results:
        return {"success": False, "error": "No family data available"}

    return {"success": True, "result": final_results}


@app.route("/", methods=["GET", "OPTIONS"])
def main():
    if request.method == "OPTIONS":
        resp = make_response("")
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    mobile_number = request.args.get("num", "").strip()
    if not mobile_number:
        return make_error("Missing 'num' parameter")
    if not (mobile_number.isdigit() and len(mobile_number) == 10):
        return make_error("Invalid mobile number. Must be 10 digits.")

    result = process_api_request(mobile_number)
    if result.get("success", False):
        resp = make_response(json.dumps(result, ensure_ascii=False, separators=(',', ':')))
        resp.headers["Content-Type"] = "application/json"
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    else:
        return make_error(result.get("error", "Service temporarily unavailable"))


def make_error(message):
    payload = {"success": False, "error": message}
    resp = make_response(json.dumps(payload, ensure_ascii=False, separators=(',', ':')), 400)
    resp.headers["Content-Type"] = "application/json"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


# This is required for Vercel
def handler(event, context):
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    from werkzeug.wrappers import Response
    return DispatcherMiddleware(app)


if __name__ == "__main__":
    # Run locally for testing
    app.run(host="0.0.0.0", port=8000)                # Second API call - Get family members info
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

# Vercel serverless function handler
def handler(request, context):
    """Vercel serverless function handler"""
    from io import BytesIO
    
    class VercelWrapper:
        def __init__(self, request):
            self.request = request
            self.headers = {}
            self.status_code = 200
            
        def send_response(self, code):
            self.status_code = code
            
        def send_header(self, key, value):
            self.headers[key] = value
            
        def end_headers(self):
            pass
            
        def get_wfile(self):
            return BytesIO()
    
    # Create wrapper and process request
    wrapper = VercelWrapper(request)
    handler_instance = APIHandler(wrapper.get_wfile(), request, None)
    handler_instance.wfile = BytesIO()
    
    # Process the request
    handler_instance.do_GET()
    
    # Return response
    return {
        'statusCode': wrapper.status_code,
        'headers': wrapper.headers,
        'body': handler_instance.wfile.getvalue().decode('utf-8')
    }

# Local execution
if __name__ == "__main__":
    start_local_server()
