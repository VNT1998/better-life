"""
Supabase Connection and Table Verification Script
Run: uv run python check_supabase.py
"""
import sys
import httpx
from app.config import SUPABASE_URL, SUPABASE_KEY

def check():
    print(f"Checking Supabase at: {SUPABASE_URL}")
    headers = {"apikey": SUPABASE_KEY}
    
    # 1. Check root rest endpoint
    try:
        with httpx.Client(timeout=5.0) as client:
            res = client.get(f"{SUPABASE_URL}/rest/v1/", headers=headers)
            print(f"✓ PostgREST Root status: {res.status_code}")
            tables = list(res.json().get("definitions", {}).keys())
            print(f"  Exposed tables in PostgREST: {tables}")
    except Exception as e:
        print(f"✗ Failed to connect to PostgREST root: {e}")
        return

    # 2. Check each table
    required_tables = ["users", "chat_sessions", "chat_messages"]
    all_ok = True
    for t in required_tables:
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{SUPABASE_URL}/rest/v1/{t}?limit=1", headers=headers)
                if res.status_code == 200:
                    print(f"✓ Table '{t}': OK (accessible)")
                elif res.status_code == 404 and "PGRST205" in res.text:
                    print(f"✗ Table '{t}': MISSING (PGRST205 - not found in schema cache)")
                    all_ok = False
                elif res.status_code == 401 or res.status_code == 403:
                    print(f"✗ Table '{t}': PERMISSION DENIED (status {res.status_code})")
                    all_ok = False
                else:
                    print(f"? Table '{t}': status {res.status_code} - {res.text[:100]}")
                    all_ok = False
        except Exception as e:
            print(f"✗ Table '{t}': Request error: {e}")
            all_ok = False

    if all_ok:
        print("\n🎉 SUCCESS: All required tables are present and queryable in Supabase!")
    else:
        print("\n⚠️ ACTION REQUIRED: Run the SQL in 'backend/init_supabase.sql' in your Supabase SQL Editor.")

if __name__ == "__main__":
    check()
