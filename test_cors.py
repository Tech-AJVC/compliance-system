"""
Simple script to test CORS configuration of the compliance system API.
Run this script after starting the backend server.
"""
import requests
import json

def get_auth_token():
    """Get an authentication token from the API."""
    login_url = 'http://localhost:8000/api/auth/login'
    
    # Replace with valid credentials for your system
    login_data = {
        "username": "admin@example.com",  # This should be an email based on the code
        "password": "admin123"
    }
    
    try:
        response = requests.post(login_url, data=login_data)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            print(f"Failed to get auth token. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error getting auth token: {str(e)}")
        return None

def print_all_headers(response, title):
    """Print all headers from a response."""
    print(f"\n=== {title} ===")
    print(f"Status Code: {response.status_code}")
    print("All Headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    
    # Also print CORS headers specifically
    print("\nCORS Headers:")
    cors_headers_found = False
    for key, value in response.headers.items():
        if key.lower().startswith('access-control-'):
            print(f"  {key}: {value}")
            cors_headers_found = True
    
    if not cors_headers_found:
        print("  No CORS headers found in response")

def test_cors():
    # Get authentication token
    token = get_auth_token()
    auth_header = {}
    
    if token:
        print(f"Successfully obtained auth token")
        auth_header = {"Authorization": f"Bearer {token}"}
    else:
        print("Proceeding without authentication token")
    
    # Test with OPTIONS request (preflight)
    headers = {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Content-Type,Authorization'
    }
    
    # Use a public endpoint for testing CORS headers
    url = 'http://localhost:8000/api/tasks/'
    
    # Send OPTIONS request (preflight)
    options_response = requests.options(url, headers=headers)
    print_all_headers(options_response, "OPTIONS Request (Preflight)")
    
    # Send actual GET request with auth token
    get_headers = {'Origin': 'http://localhost:3000'}
    get_headers.update(auth_header)  # Add auth token if available
    
    get_response = requests.get(url, headers=get_headers)
    print_all_headers(get_response, "GET Request with Allowed Origin")
    
    # Test with disallowed origin (if configured to block some origins)
    blocked_headers = {'Origin': 'http://evil-site.com'}
    blocked_headers.update(auth_header)  # Add auth token if available
    
    blocked_response = requests.get(url, headers=blocked_headers)
    print_all_headers(blocked_response, "Request with Blocked Origin")
    print("\nNote: If you see no 'access-control-allow-origin' header in the response above, it means the origin was blocked as expected.")
    
    # Test a public endpoint that doesn't require authentication
    public_url = 'http://localhost:8000/docs'  # Swagger docs are typically public
    public_headers = {'Origin': 'http://localhost:3000'}
    
    public_response = requests.get(public_url, headers=public_headers)
    print_all_headers(public_response, "Public Endpoint Request")

if __name__ == "__main__":
    test_cors()
