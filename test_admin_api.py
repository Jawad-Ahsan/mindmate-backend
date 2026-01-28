import requests
import os
from pprint import pprint

# Config
BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "hammadmunir959@gmail.com"
ADMIN_PASSWORD = "MindMate#121"
ADMIN_SECRET_KEY = "MindMateAdminKey#2025"

def test_admin_api():
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
        print("Login successful! Token received.")
    except Exception as e:
        print(f"Login failed: {e}")
        if 'resp' in locals():
            print(resp.text)
        return

    # 2. Get Specialists
    specialists_url = f"{BASE_URL}/admin/specialists"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\nFetching specialists from {specialists_url}...")
    try:
        resp = requests.get(specialists_url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            print(f"Success! Received {len(data)} specialists.")
            pprint(data)
        else:
            print(f"Failed with status {resp.status_code}")
            print(resp.text)
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_admin_api()
