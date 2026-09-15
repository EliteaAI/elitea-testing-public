"""Test the alternative login form URL provided by admin."""
import sys
import requests
from pathlib import Path
from bs4 import BeautifulSoup

# Add automation to path
sys.path.insert(0, str(Path(__file__).parent))
from config import settings

print("=" * 80)
print("Testing Alternative Login URL: /forward-auth/auth_form/login")
print("=" * 80)

base_url = "https://dev.elitea.ai"
login_url = f"{base_url}/forward-auth/auth_form/login"

session = requests.Session()

print(f"\n1. Testing GET request to: {login_url}")
try:
    resp = session.get(login_url, allow_redirects=True, timeout=10)
    print(f"   Status: {resp.status_code}")
    print(f"   Final URL: {resp.url}")
    print(f"   Content-Type: {resp.headers.get('content-type')}")
    print(f"   Content length: {len(resp.text)} bytes")
    
    # Check if it's an HTML form
    if "text/html" in resp.headers.get('content-type', ''):
        soup = BeautifulSoup(resp.text, 'html.parser')
        forms = soup.find_all('form')
        
        if forms:
            print(f"   ✓ Found {len(forms)} form(s)")
            
            for i, form in enumerate(forms, 1):
                print(f"\n   Form #{i}:")
                action = form.get('action', 'No action')
                method = form.get('method', 'GET').upper()
                print(f"     Action: {action}")
                print(f"     Method: {method}")
                
                # Find input fields
                inputs = form.find_all('input')
                print(f"     Input fields ({len(inputs)}):")
                for inp in inputs:
                    name = inp.get('name', 'unnamed')
                    inp_type = inp.get('type', 'text')
                    value = inp.get('value', '')
                    print(f"       - {name} (type={inp_type}){' [value=' + value + ']' if value else ''}")
        else:
            print("   ⚠ No HTML form found in response")
    
    # Save response for inspection
    output_file = Path(__file__).parent.parent / "forward_auth_response.html"
    with open(output_file, "w") as f:
        f.write(resp.text)
    print(f"\n   Response saved to: {output_file}")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("2. Testing POST with credentials")
print("=" * 80)

try:
    # Try to POST credentials to the forward-auth endpoint
    print(f"\nAttempting login POST to: {login_url}")
    print(f"  Username: {settings.test_user_email}")
    print(f"  Password: {'*' * len(settings.test_user_password)}")
    
    login_data = {
        'username': settings.test_user_email,
        'password': settings.test_user_password,
    }
    
    resp = session.post(login_url, data=login_data, allow_redirects=True, timeout=10)
    print(f"\n   POST Status: {resp.status_code}")
    print(f"   Final URL: {resp.url}")
    
    # Check if we're authenticated
    if 'login' not in resp.url.lower() and 'auth' not in resp.url.lower():
        print("   ✓ SUCCESS - Redirected away from auth page!")
        print(f"   Landed on: {resp.url}")
        
        # Check cookies
        cookies = session.cookies
        print(f"\n   Cookies received: {len(cookies)}")
        for cookie in cookies:
            print(f"     - {cookie.name} = {cookie.value[:20]}...")
    else:
        print("   ✗ FAILED - Still on auth page")
        print(f"   URL: {resp.url}")
        
        # Check for error messages
        if "error" in resp.text.lower() or "invalid" in resp.text.lower():
            soup = BeautifulSoup(resp.text, 'html.parser')
            error_div = soup.find(['div', 'p', 'span'], class_=lambda x: x and 'error' in x.lower())
            if error_div:
                print(f"   Error message: {error_div.get_text(strip=True)}")
    
except Exception as e:
    print(f"   ✗ Error during POST: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("3. Comparison with current Keycloak flow")
print("=" * 80)

print(f"\nCurrent authentication flow:")
print(f"  1. GET {settings.elitea_url}")
print(f"  2. → Redirect to Keycloak: {settings.elitea_auth_url}/auth/realms/dev/...")
print(f"  3. → POST credentials to Keycloak login-actions/authenticate")
print(f"  4. → Redirect back to app (CURRENTLY FAILING)")

print(f"\nAlternative flow (forward-auth):")
print(f"  1. GET {login_url}")
print(f"  2. → POST credentials directly to forward-auth endpoint")
print(f"  3. → Redirect back to app (TEST ABOVE)")

print("\n" + "=" * 80)
print("Summary")
print("=" * 80)
print("\nIf the POST above succeeded, this alternative URL bypasses Keycloak")
print("and could be used for test authentication.")
print("\nNext step: Check if this works in our auth fixture (api_auth.py)")

