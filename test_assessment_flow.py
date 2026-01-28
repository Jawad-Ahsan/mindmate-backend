import requests
import json
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler("test_run.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def log(msg):
    logging.info(msg)

# Configuration
API_URL = "http://localhost:8000"
ADMIN_EMAIL = "hammadmunir959@gmail.com"
ADMIN_PASSWORD = "MindMate#121" 
ADMIN_SECRET_KEY = "MindMateAdminKey#2025"

def run_test():
    log("🚀 Starting Assessment Flow Test")
    
    # 1. Login
    log("\n🔐 Logging in...")
    try:
        payload = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "user_type": "admin",
            "secret_key": ADMIN_SECRET_KEY
        }
        response = requests.post(f"{API_URL}/api/auth/login-user", json=payload)
        
        # Check if response is not 200
        if response.status_code != 200:
             log(f"Login failed logic: {response.text}")
             
        response.raise_for_status()
        data = response.json()
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        log(f"✅ Login successful. Token: {token[:10]}...")
    except Exception as e:
        log(f"❌ Login failed: {e}")
        return

    # 2. Get User/Profile
    log("\n👤 Fetching profile...")
    try:
        response = requests.get(f"{API_URL}/api/auth/get-current-user", headers=headers)
        response.raise_for_status()
        user_data = response.json()
        log(f"✅ Profile fetched: {user_data.get('email')}")
    except Exception as e:
        log(f"❌ Profile fetch failed: {e}")
        return

    # 3. Start Assessment
    log("\n📝 Starting Assessment...")
    try:
        # Use a demo patient ID or existing one
        patient_id = "550e8400-e29b-41d4-a716-446655440000" # Demo ID
        payload = {
            "patient_id": patient_id,
            "module_id": "MDD"
        }
        # Call start endpoint
        response = requests.post(f"{API_URL}/api/assessment/start", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        session_id = data["session_id"]
        question_id = data["first_question"]["question_id"]
        log(f"✅ Assessment started. Session ID: {session_id}")
    except Exception as e:
        log(f"❌ Start assessment failed: {e}")
        try:
             log(f"Response: {response.text}")
        except: pass
        return

    # 4. Respond to Question
    log("\n💬 Responding to Question...")
    try:
        payload = {
            "session_id": session_id,
            "question_id": question_id,
            "response": 1, # Index for yes/no? 1 = Yes usually in my code? No, usually 0 or 1.
            # Wait, SCIDAssessment logic: response is an index (int).
            # Question logic: "yes_no" -> 0=No, 1=Yes usually.
            # My frontend sends 0 or 1.
            "notes": "Test response"
        }
        # Wait, does backend expect int or string? 
        # API Schema says `response: Any`.
        # SCIDAssessment process_response expects `response` to match question type.
        # Let's send 1.
        
        response = requests.post(f"{API_URL}/api/assessment/respond", json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        log(f"✅ Response processed. Valid: {result['is_valid']}")
        if result['next_question']:
             log(f"➡️ Next Question: {result['next_question']['question_id']}")
    except Exception as e:
        log(f"❌ Respond failed: {e}")
        try:
             log(f"Response: {response.text}")
        except: pass
        return

    # 5. Check History
    log("\n📜 Checking History...")
    try:
        response = requests.get(f"{API_URL}/api/assessment/patient/history", headers=headers)
        response.raise_for_status()
        history = response.json()
        
        # Verify our session is in history
        found = False
        for session in history:
            if session["session_id"] == session_id:
                found = True
                log(f"✅ Found session {session_id} in history. Status: {session['status']}")
                break
        
        if not found:
            log("❌ Session not found in history!")
            log(f"History count: {len(history)}")
            # log(f"History: {json.dumps(history, indent=2)}")
    except Exception as e:
        log(f"❌ History fetch failed: {e}")
        try:
             log(f"Response: {response.text}")
        except: pass
        return

    log("\n🎉 Test Complete!")

if __name__ == "__main__":
    run_test()
