#!/usr/bin/env python3
"""
Simple script to get Kite Connect Access Token
Run this script to get your access token for the dashboard
"""

import hashlib
import requests
import webbrowser
from urllib.parse import urlparse, parse_qs

# Your Kite Connect credentials - REPLACE WITH YOUR OWN
API_KEY = "YOUR_API_KEY_HERE"
API_SECRET = "YOUR_API_SECRET_HERE"
REDIRECT_URL = "https://chartinkdashboardangelone-production.up.railway.app"

def generate_checksum(api_key, request_token, api_secret):
    """Generate SHA-256 checksum for Kite Connect"""
    return hashlib.sha256(f"{api_key}{request_token}{api_secret}".encode()).hexdigest()

def get_access_token():
    """Get access token from Kite Connect"""
    
    print("🚀 Kite Connect Access Token Generator")
    print("=" * 50)
    
    # Step 1: Generate login URL
    login_url = f"https://kite.zerodha.com/connect/login?v=3&api_key={API_KEY}"
    alt_login_url = f"https://kite.zerodha.com/connect/login?api_key={API_KEY}&v=3"
    
    print(f"📱 Step 1: Try these URLs in your browser:")
    print(f"   Primary: {login_url}")
    print(f"   Alternative: {alt_login_url}")
    print()
    print("⚠️  If you get 'Invalid api_key' error:")
    print("   1. Check if your app status is 'Active' in Kite Connect dashboard")
    print("   2. Wait a few minutes after creating the app")
    print("   3. Try the alternative URL format")
    print()
    
    # Open browser automatically
    try:
        webbrowser.open(login_url)
        print("✅ Browser opened automatically!")
    except:
        print("⚠️  Please open the URL manually in your browser")
    
    print()
    print("🔐 Step 2: Login with your Zerodha credentials")
    print("📋 Step 3: After login, you'll be redirected to a URL like:")
    print(f"   {REDIRECT_URL}?request_token=ABC123XYZ789")
    print()
    
    # Get request token from user
    request_token = input("📝 Enter the request_token from the redirect URL: ").strip()
    
    if not request_token:
        print("❌ No request token provided!")
        return
    
    # Step 4: Generate checksum
    checksum = generate_checksum(API_KEY, request_token, API_SECRET)
    print(f"🔒 Generated checksum: {checksum}")
    
    # Step 5: Get access token
    print("🔄 Getting access token...")
    
    try:
        response = requests.post(
            "https://api.kite.trade/session/token",
            headers={"X-Kite-Version": "3"},
            data={
                "api_key": API_KEY,
                "request_token": request_token,
                "checksum": checksum
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                access_token = data["data"]["access_token"]
                user_name = data["data"]["user_name"]
                
                print("✅ SUCCESS!")
                print("=" * 50)
                print(f"👤 User: {user_name}")
                print(f"🔑 Access Token: {access_token}")
                print("=" * 50)
                print()
                print("📋 Now use these credentials in your dashboard:")
                print(f"   API Key: {API_KEY}")
                print(f"   API Secret: {API_SECRET}")
                print(f"   Access Token: {access_token}")
                print()
                print("🎯 Go to your dashboard and click 'Setup Credentials'")
                
            else:
                print(f"❌ Error: {data}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    get_access_token()
