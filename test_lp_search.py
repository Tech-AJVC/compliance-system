"""
Test script for the LP details search API endpoint.
Run this script after starting the backend server.
"""
import requests
import json
import sys
from tabulate import tabulate

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

def search_lps(search_term, token):
    """
    Search for LPs by name using the search endpoint.
    
    Args:
        search_term (str): The name to search for
        token (str): Authentication token
        
    Returns:
        list: List of LP records matching the search criteria
    """
    search_url = f'http://localhost:8000/api/lps/search/?name={search_term}'
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(search_url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error searching LPs. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Exception during LP search: {str(e)}")
        return None

def get_all_lps(token):
    """
    Get all LP records to verify search results against.
    
    Args:
        token (str): Authentication token
        
    Returns:
        list: List of all LP records
    """
    url = 'http://localhost:8000/api/lps/'
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting all LPs. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Exception getting all LPs: {str(e)}")
        return None

def display_lps(lps, title):
    """
    Display LP records in a tabular format.
    
    Args:
        lps (list): List of LP records
        title (str): Title for the display
    """
    if not lps:
        print(f"\n{title}: No records found")
        return
    
    print(f"\n{title} ({len(lps)} records):")
    
    # Extract relevant fields for display
    table_data = []
    for lp in lps:
        table_data.append([
            lp.get('lp_id', 'N/A'),
            lp.get('lp_name', 'N/A'),
            lp.get('email', 'N/A'),
            lp.get('type', 'N/A'),
            lp.get('commitment_amount', 'N/A')
        ])
    
    # Display table
    headers = ["LP ID", "Name", "Email", "Type", "Commitment Amount"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def test_case_sensitivity(token):
    """Test that the search is case-insensitive"""
    print("\n\nTesting case sensitivity...")
    
    # Search with lowercase
    lowercase_results = search_lps("capital", token)
    print(f"Results for lowercase 'capital': {len(lowercase_results) if lowercase_results else 0} records")
    
    # Search with uppercase
    uppercase_results = search_lps("CAPITAL", token)
    print(f"Results for uppercase 'CAPITAL': {len(uppercase_results) if uppercase_results else 0} records")
    
    # Search with mixed case
    mixedcase_results = search_lps("CaPiTaL", token)
    print(f"Results for mixed case 'CaPiTaL': {len(mixedcase_results) if mixedcase_results else 0} records")
    
    # Results should be the same for all three searches
    if lowercase_results and uppercase_results and mixedcase_results:
        if len(lowercase_results) == len(uppercase_results) == len(mixedcase_results):
            print("✅ Case-insensitive search is working correctly!")
        else:
            print("❌ Case-insensitive search is NOT working correctly!")
    else:
        print("❌ Could not verify case-insensitivity due to missing results")

def main():
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("Authentication failed. Exiting.")
        sys.exit(1)
    
    print("Successfully authenticated.")
    
    # Get all LPs for reference
    all_lps = get_all_lps(token)
    if all_lps:
        display_lps(all_lps, "All LPs")
    
    # Test cases for search
    search_terms = [
        "Ltd",       # Search for companies with "Ltd" in the name
        "Anurag",    # Search for names containing "Invest"
        "Capital",   # Search for names containing "Capital"
        "XYZ"        # Should return no results if no LP has "XYZ" in the name
    ]
    
    for term in search_terms:
        print(f"\n\nSearching for LPs with name containing '{term}'...")
        results = search_lps(term, token)
        display_lps(results, f"Search Results for '{term}'")
        
        if results:
            print(f"Found {len(results)} LP(s) matching '{term}'")
        else:
            print(f"No LPs found matching '{term}'")
    
    # Test case sensitivity
    test_case_sensitivity(token)
    
    # Test pagination
    print("\n\nTesting pagination...")
    
    # Get first page with 2 results
    page1 = search_lps("&skip=0&limit=2", token)
    display_lps(page1, "Page 1 (First 2 results)")
    
    # Get second page with 2 results
    page2 = search_lps("&skip=2&limit=2", token)
    display_lps(page2, "Page 2 (Next 2 results)")
    
    if page1 and page2:
        # Check that the records are different
        page1_ids = [lp.get('lp_id') for lp in page1]
        page2_ids = [lp.get('lp_id') for lp in page2]
        
        if not any(id in page2_ids for id in page1_ids):
            print("✅ Pagination is working correctly!")
        else:
            print("❌ Pagination is NOT working correctly - found duplicate records!")
    else:
        print("❌ Could not verify pagination due to missing results")

if __name__ == "__main__":
    main()
