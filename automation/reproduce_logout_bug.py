"""Reproduce logout bug on DEV environment for issue filing.

Steps:
1. Navigate to DEV environment
2. Login with test user
3. Click Settings → Profile → Logout
4. Capture error page and network logs
5. Try to navigate back to DEV to verify still logged in
"""
import sys
from pathlib import Path
from datetime import datetime
import json

# Add automation to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from playwright.sync_api import sync_playwright, Page, BrowserContext
from config import settings
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Output directory for evidence
EVIDENCE_DIR = Path(__file__).parent.parent / "logout_bug_evidence"
EVIDENCE_DIR.mkdir(exist_ok=True)

def capture_network_logs(page: Page) -> list:
    """Capture network requests/responses."""
    logs = []
    
    def on_request(request):
        logs.append({
            "type": "request",
            "url": request.url,
            "method": request.method,
            "headers": dict(request.headers)
        })
    
    def on_response(response):
        logs.append({
            "type": "response", 
            "url": response.url,
            "status": response.status,
            "headers": dict(response.headers)
        })
    
    page.on("request", on_request)
    page.on("response", on_response)
    return logs

def reproduce_logout_bug():
    """Reproduce the logout bug and collect evidence."""
    logger.info("Starting logout bug reproduction on DEV")
    
    with sync_playwright() as p:
        # Launch browser in headed mode to see what happens
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        
        # Create context with storage state (authenticated)
        from api_auth import get_playwright_storage_state
        
        logger.info("Authenticating via API...")
        storage_state = get_playwright_storage_state(
            base_url=settings.elitea_auth_url,
            username=settings.test_user_email,
            password=settings.test_user_password
        )
        
        context = browser.new_context(
            storage_state=storage_state,
            viewport=None,  # Use full window size
            record_video_dir=str(EVIDENCE_DIR)
        )
        
        page = context.new_page()
        network_logs = capture_network_logs(page)
        
        # Enable console logging
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
        
        try:
            # Step 1: Navigate to DEV
            logger.info("Step 1: Navigate to DEV environment")
            page.goto(settings.elitea_url, wait_until="networkidle", timeout=30000)
            page.screenshot(path=EVIDENCE_DIR / "01_logged_in.png")
            logger.info(f"✓ Loaded: {page.url}")
            
            # Wait for app to load
            page.wait_for_timeout(2000)
            
            # Step 2: Click Settings
            logger.info("Step 2: Navigate to Settings → Profile")
            
            # Look for Settings navigation item
            page.screenshot(path=EVIDENCE_DIR / "02_before_settings_click.png")
            
            # Try different selectors for Settings
            settings_link = None
            selectors = [
                'a[href*="settings"]',
                'text=Settings',
                '[data-testid*="settings"]',
                'nav a:has-text("Settings")'
            ]
            
            for selector in selectors:
                try:
                    settings_link = page.locator(selector).first
                    if settings_link.is_visible(timeout=2000):
                        logger.info(f"Found Settings with selector: {selector}")
                        break
                except:
                    continue
            
            if not settings_link:
                logger.error("Could not find Settings link")
                page.screenshot(path=EVIDENCE_DIR / "ERROR_no_settings_link.png")
                # Take a snapshot to see what's available
                with open(EVIDENCE_DIR / "page_snapshot.txt", "w") as f:
                    f.write(page.content())
                return
            
            settings_link.click()
            page.wait_for_load_state("networkidle", timeout=10000)
            page.screenshot(path=EVIDENCE_DIR / "03_settings_page.png")
            logger.info("✓ Opened Settings")
            
            # Step 3: Click Profile (if needed)
            current_url = page.url
            if "profile" not in current_url.lower():
                logger.info("Navigating to Profile section...")
                profile_link = page.locator('text=Profile').first
                if profile_link.is_visible(timeout=2000):
                    profile_link.click()
                    page.wait_for_load_state("networkidle", timeout=10000)
                    page.screenshot(path=EVIDENCE_DIR / "04_profile_page.png")
            
            # Step 4: Click Logout button
            logger.info("Step 3: Click Logout button")
            page.screenshot(path=EVIDENCE_DIR / "05_before_logout_click.png")
            
            # Find logout button
            logout_button = None
            logout_selectors = [
                'button:has-text("Logout")',
                'button:has-text("Log out")',
                'button:has-text("Sign out")',
                '[data-testid*="logout"]',
                'button[type="button"]:has-text("Logout")'
            ]
            
            for selector in logout_selectors:
                try:
                    logout_button = page.locator(selector).first
                    if logout_button.is_visible(timeout=2000):
                        logger.info(f"Found Logout button with selector: {selector}")
                        break
                except:
                    continue
            
            if not logout_button:
                logger.error("Could not find Logout button")
                page.screenshot(path=EVIDENCE_DIR / "ERROR_no_logout_button.png")
                return
            
            # Click logout and wait for navigation
            logger.info("Clicking Logout...")
            logout_button.click()
            
            # Wait for navigation or error page
            page.wait_for_timeout(3000)
            page.screenshot(path=EVIDENCE_DIR / "06_after_logout_click.png")
            
            current_url = page.url
            logger.info(f"After logout, URL: {current_url}")
            
            # Check if we're on error page
            page_text = page.content()
            if "sorry" in page_text.lower() or "invalid parameter" in page_text.lower():
                logger.error("⚠ BUG CONFIRMED: Redirected to error page")
                page.screenshot(path=EVIDENCE_DIR / "07_ERROR_PAGE.png", full_page=True)
                
                # Extract error message
                error_msg = page.locator('body').inner_text()
                with open(EVIDENCE_DIR / "error_message.txt", "w") as f:
                    f.write(f"URL: {current_url}\n\n")
                    f.write(error_msg)
                
            # Step 5: Try to navigate back to DEV to verify still logged in
            logger.info("Step 4: Navigate back to DEV to verify session")
            page.goto(settings.elitea_url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            
            final_url = page.url
            page.screenshot(path=EVIDENCE_DIR / "08_after_navigating_back.png")
            
            # Check if still logged in (not on login page)
            if "login" not in final_url.lower() and "auth" not in final_url.lower():
                logger.error("⚠ BUG CONFIRMED: Still logged in after logout!")
                page.screenshot(path=EVIDENCE_DIR / "09_STILL_LOGGED_IN.png", full_page=True)
            else:
                logger.info("✓ Successfully logged out - on login page")
            
            # Save network logs
            with open(EVIDENCE_DIR / "network_logs.json", "w") as f:
                json.dump(network_logs, f, indent=2)
            
            # Save console logs
            with open(EVIDENCE_DIR / "console_logs.txt", "w") as f:
                f.write("\n".join(console_logs))
            
            logger.info(f"\nEvidence collected in: {EVIDENCE_DIR}")
            logger.info("Press Enter to close browser...")
            input()
            
        except Exception as e:
            logger.error(f"Error during reproduction: {e}")
            import traceback
            traceback.print_exc()
            page.screenshot(path=EVIDENCE_DIR / "ERROR_exception.png")
            
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    reproduce_logout_bug()
