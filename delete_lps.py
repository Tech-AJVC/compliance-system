import requests
import json
import sys
import time

# URL for the API
base_url = "http://localhost:8000/api/lps"

# Authentication credentials
auth_data = {
    'username': 'john@example.com',
    'password': 'your_password'
}

def authenticate():
    """Get authentication token"""
    # Use the correct authentication endpoint
    auth_url = "http://localhost:8000/api/auth/login"
    
    try:
        print(f"Authenticating with: {auth_url}")
        response = requests.post(auth_url, data=auth_data)
        
        print(f"Auth response status: {response.status_code}")
        if response.status_code == 200:
            token_data = response.json()
            if "access_token" in token_data:
                print(f"Successfully authenticated")
                return token_data.get("access_token")
            else:
                print(f"Response JSON: {token_data}")
        else:
            print(f"Authentication failed: {response.text}")
    except requests.RequestException as e:
        print(f"Error connecting to authentication endpoint: {str(e)}")
    
    print("Authentication failed with all endpoints. Please check your credentials and server status.")
    sys.exit(1)

def delete_lp(lp_id, token):
    """Delete a single LP record"""
    url = f"{base_url}/{lp_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.delete(url, headers=headers)
        
        if response.status_code == 204:
            print(f"Successfully deleted LP with ID: {lp_id}")
            return True
        else:
            print(f"Failed to delete LP with ID: {lp_id}. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"Error deleting LP with ID {lp_id}: {str(e)}")
        return False

def main():
    # Read the LP data JSON file
    with open('lp_records.json', 'r') as f:
        lp_records = json.load(f)
    
    # Get authentication token
    token = authenticate()
    
    # Track statistics
    total = len(lp_records)
    successful = 0
    failed = 0
    
    # Delete each LP record
    for lp in lp_records["lps"]:
        lp_id = lp.get("lp_id")
        if lp_id:
            result = delete_lp(lp_id, token)
            if result:
                successful += 1
            else:
                failed += 1
        else:
            print("Warning: LP record missing lp_id field")
            failed += 1
    
    # Print summary
    print(f"\nDeletion Summary:")
    print(f"Total records: {total}")
    print(f"Successfully deleted: {successful}")
    print(f"Failed to delete: {failed}")

if __name__ == "__main__":
    main()
