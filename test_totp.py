#!/usr/bin/env python3
"""
Simple TOTP validation test
"""

def test_totp_secret(totp_secret):
    """Test if TOTP secret is valid"""
    print(f"Testing TOTP secret: {totp_secret}")
    
    # Clean the secret
    clean_secret = totp_secret.strip().upper().replace(' ', '')
    print(f"Cleaned secret: {clean_secret}")
    
    # Check characters
    valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567')
    invalid_chars = set(clean_secret) - valid_chars
    
    if invalid_chars:
        print(f"❌ Invalid characters found: {invalid_chars}")
        print("TOTP secret should only contain: A-Z and 2-7")
        return False
    
    # Test Base32 validation
    import base64
    try:
        base64.b32decode(clean_secret)
        print("✅ Base32 validation passed")
    except Exception as e:
        print(f"❌ Base32 validation failed: {e}")
        return False
    
    # Test TOTP generation
    try:
        import pyotp
        totp = pyotp.TOTP(clean_secret).now()
        print(f"✅ TOTP generated successfully: {totp}")
        return True
    except Exception as e:
        print(f"❌ TOTP generation failed: {e}")
        return False

if __name__ == "__main__":
    print("TOTP Secret Validator")
    print("=" * 50)
    
    # Test with your secret (replace with your actual secret)
    your_secret = input("Enter your TOTP secret: ")
    
    if test_totp_secret(your_secret):
        print("\n🎉 Your TOTP secret is valid!")
    else:
        print("\n❌ Your TOTP secret is invalid!")
        print("\nTo get a valid TOTP secret:")
        print("1. Go to: https://smartapi.angelbroking.com/enable-totp")
        print("2. Enter your Angel One credentials")
        print("3. Copy the secret key (should be like: ABCDEFGHIJKLMNOPQRSTUVWXYZ234567)")
