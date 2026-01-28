import requests
import os
from pprint import pprint

# Config
BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "hammadmunir959@gmail.com"
ADMIN_PASSWORD = "MindMate#121"
ADMIN_SECRET_KEY = "MindMateAdminKey#2025"

def test_admin_details():
    # 1. Login
    login_url = f"{BASE_URL}/auth/login-user"
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "user_type": "admin",
        "secret_key": ADMIN_SECRET_KEY
    }
    
    print(f"Logging in to {login_url}...")
    try:
        resp = requests.post(login_url, json=payload)
        resp.raise_for_status()
        token = resp.json()["access_token"]
        print("Login successful.")
    except Exception as e:
        print(f"Login failed: {e}")
        return

    # 2. Get All Specialists to find the ID
    specialists_url = f"{BASE_URL}/admin/specialists"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        resp = requests.get(specialists_url, headers=headers)
        specialists = resp.json()
        target = next((s for s in specialists if s['approval_status'] == 'under_review' or s['approval_status'] == 'pending'), None)
        
        if not target:
            print("No pending/under_review specialist found.")
            return

        specialist_id = target['id']
        print(f"\nFound target specialist ID: {specialist_id}")

        # 3. Get Details
        details_url = f"{BASE_URL}/admin/specialists/{specialist_id}/details"
        print(f"Fetching details from {details_url}...")
        
        detail_resp = requests.get(details_url, headers=headers)
        if detail_resp.status_code == 200:
            details = detail_resp.json()
            print("\n--- Details Response (Documents Section) ---")
            docs = details.get('documents')
            with open("explicit_output.txt", "w") as f:
                import json
                json.dump(docs, f, indent=2)
            pprint(docs)
            print("--------------------------------------------")
            if not docs:
                print("WARNING: 'documents' list is empty or None.")
        else:
            print(f"Failed to get details: {detail_resp.status_code}")
            print(detail_resp.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_admin_details()
