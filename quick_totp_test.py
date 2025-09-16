#!/usr/bin/env python3
"""
Quick TOTP test for your specific secret
"""

def test_your_totp():
    totp_secret = "QPIA4O3HRZIQLPBBAQ6VRS653I"
    
    print(f"Testing TOTP secret: {totp_secret}")
    print(f"Length: {len(totp_secret)}")
    
    # Check characters
    valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567')
    invalid_chars = set(totp_secret) - valid_chars
    
    if invalid_chars:
        print(f"❌ Invalid characters found: {invalid_chars}")
        return False
    else:
        print("✅ All characters are valid")
    
    # Test Base32 validation
    import base64
    try:
        decoded = base64.b32decode(totp_secret)
        print(f"✅ Base32 validation passed, decoded length: {len(decoded)}")
    except Exception as e:
        print(f"❌ Base32 validation failed: {e}")
        return False
    
    # Test TOTP generation
    try:
        import pyotp
        totp = pyotp.TOTP(totp_secret).now()
        print(f"✅ TOTP generated successfully: {totp}")
        return True
    except Exception as e:
        print(f"❌ TOTP generation failed: {e}")
        return False

if __name__ == "__main__":
    test_your_totp()
