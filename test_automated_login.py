#!/usr/bin/env python3
"""
Test script for the automated Kite Connect login functionality
Based on: https://gist.github.com/sagamantus/949737c6cf3c94a9901a4830c4c5cf9b
"""

import requests
import re
from urllib.parse import urlparse, parse_qs
from kiteconnect import KiteConnect

def test_automated_login():
    """Test the automated login function"""
    
    # Test credentials (replace with your actual credentials)
    credentials = {
        "api_key": "YOUR_API_KEY",
        "username": "YOUR_USERNAME", 
        "password": "YOUR_PASSWORD",
        "totp_key": "YOUR_TOTP_KEY"  # Optional
    }
    
    try:
        kite = KiteConnect(api_key=credentials["api_key"])
        
        session = requests.Session()
        response = session.get(kite.login_url())
        
        print(f"✅ Kite Connect login URL: {kite.login_url()}")
        print(f"✅ Session started successfully")
        
        # User login POST request
        login_payload = {
            "user_id": credentials["username"],
            "password": credentials["password"],
        }
        
        print(f"🔄 Attempting login for user: {credentials['username']}")
        login_response = session.post("https://kite.zerodha.com/api/login", login_payload)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed with status: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False
        
        login_data = login_response.json()
        if login_data.get('status') != 'success':
            print(f"❌ Login failed: {login_data.get('message', 'Unknown error')}")
            return False
            
        print(f"✅ Login successful!")
        
        # TOTP POST request (if TOTP is provided)
        if credentials.get("totp_key"):
            try:
                import pyotp
                totp_payload = {
                    "user_id": credentials["username"],
                    "request_id": login_data["data"]["request_id"],
                    "twofa_value": pyotp.TOTP(credentials["totp_key"]).now(),
                    "twofa_type": "totp",
                    "skip_session": True,
                }
                totp_response = session.post("https://kite.zerodha.com/api/twofa", totp_payload)
                
                if totp_response.status_code != 200:
                    print(f"⚠️ TOTP failed: {totp_response.text}")
                else:
                    print(f"✅ TOTP verification successful!")
                    
            except ImportError:
                print(f"⚠️ pyotp not available, skipping TOTP")
            except Exception as e:
                print(f"⚠️ TOTP failed: {str(e)}")
        
        # Extract request token from redirect URL
        try:
            response = session.get(kite.login_url())
            parse_result = urlparse(response.url)
            query_params = parse_qs(parse_result.query)
        except Exception as e:
            pattern = r"request_token=[A-Za-z0-9]+"
            match = re.search(pattern, str(e))
            if match:
                query_params = parse_qs(match.group())
            else:
                print(f"❌ Could not extract request token: {str(e)}")
                return False
        
        if "request_token" not in query_params:
            print(f"❌ Request token not found in response")
            return False
            
        request_token = query_params["request_token"][0]
        print(f"✅ Request token obtained: {request_token[:10]}...")
        
        return request_token
        
    except Exception as e:
        print(f"❌ Automated login failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Automated Kite Connect Login")
    print("=" * 50)
    
    # Note: This is just a test structure
    # Replace with your actual credentials to test
    print("⚠️ Note: Replace credentials in the script with your actual values to test")
    print("✅ Test structure is ready!")
    
    # Uncomment the line below to run the actual test
    # result = test_automated_login()
