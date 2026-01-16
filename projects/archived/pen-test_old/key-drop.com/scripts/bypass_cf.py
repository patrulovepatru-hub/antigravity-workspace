#!/usr/bin/env python3
"""
Cloudflare JS Challenge Bypass for key-drop.com
Uses Playwright with stealth to appear as real browser

Run with: source venv/bin/activate && python3 bypass_cf.py
"""

import json
import time
import sys
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

TARGET = "https://key-drop.com"
COOKIES_FILE = "/home/l0ve/pen-test/key-drop.com/scripts/cookies.json"
SESSION_FILE = "/home/l0ve/pen-test/key-drop.com/scripts/session.json"
HTML_FILE = "/home/l0ve/pen-test/key-drop.com/scripts/page_content.html"

def print_status(msg, status="*"):
    """Print colored status message"""
    colors = {"*": "\033[94m", "+": "\033[92m", "-": "\033[91m", "!": "\033[93m"}
    reset = "\033[0m"
    print(f"{colors.get(status, '')}{status}{reset} {msg}")

def save_cookies(context):
    """Save cookies to file for reuse"""
    cookies = context.cookies()
    with open(COOKIES_FILE, 'w') as f:
        json.dump(cookies, f, indent=2)
    print_status(f"Saved {len(cookies)} cookies to {COOKIES_FILE}", "+")
    return cookies

def save_session_data(page, cookies):
    """Save session data including localStorage"""
    session = {
        'cookies': cookies,
        'url': page.url,
        'title': page.title(),
    }
    try:
        local_storage = page.evaluate("() => JSON.stringify(localStorage)")
        session['localStorage'] = json.loads(local_storage) if local_storage else {}
    except:
        session['localStorage'] = {}

    with open(SESSION_FILE, 'w') as f:
        json.dump(session, f, indent=2)
    print_status(f"Saved session to {SESSION_FILE}", "+")

def bypass_challenge():
    """Main bypass function with visual display"""

    print("\n" + "="*60)
    print("   CLOUDFLARE BYPASS - key-drop.com")
    print("="*60 + "\n")

    print_status(f"Target: {TARGET}")
    print_status("Launching browser (visible mode)...")

    with sync_playwright() as p:
        # Launch visible browser with stealth settings
        browser = p.chromium.launch(
            headless=False,  # VISIBLE - CF detects headless
            slow_mo=50,      # Slow down for human-like behavior
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--disable-extensions',
                '--window-size=1280,800',
                '--window-position=100,100',
            ]
        )

        print_status("Browser launched", "+")

        # Create context with realistic fingerprint
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
        )

        page = context.new_page()

        # Inject stealth scripts BEFORE navigation
        page.add_init_script("""
            // Remove webdriver flag
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Add plugins (real browsers have these)
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Set languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });

            // Add chrome object
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };

            // Modify permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

        print_status("Stealth mode enabled", "+")
        print_status(f"Navigating to {TARGET}...")

        try:
            # Navigate to target
            page.goto(TARGET, wait_until='domcontentloaded', timeout=60000)

            print_status("Page loaded, waiting for Cloudflare challenge...")
            print("\n" + "-"*60)
            print("  WATCH THE BROWSER - Cloudflare challenge in progress")
            print("-"*60 + "\n")

            # Monitor challenge progress
            challenge_bypassed = False
            for i in range(20):  # Wait up to ~60 seconds
                time.sleep(3)

                try:
                    title = page.title()
                    url = page.url
                except:
                    title = "Loading..."
                    url = TARGET

                # Check if still on challenge
                if "just a moment" in title.lower() or "checking" in title.lower() or "attention" in title.lower():
                    print_status(f"[{i+1}/20] Challenge active: {title[:40]}...", "!")
                else:
                    print_status(f"Challenge BYPASSED!", "+")
                    print_status(f"Title: {title[:50]}", "+")
                    challenge_bypassed = True
                    break

            if not challenge_bypassed:
                print_status("Challenge may still be active - check browser", "-")

            # Wait a bit more for page to fully load
            time.sleep(3)

            # Save cookies
            print("\n" + "-"*60)
            cookies = save_cookies(context)
            save_session_data(page, cookies)

            # Save HTML
            html = page.content()
            with open(HTML_FILE, 'w') as f:
                f.write(html)
            print_status(f"Saved HTML ({len(html)} bytes) to {HTML_FILE}", "+")

            # Show cookies for manual use
            print("\n" + "-"*60)
            print("  COOKIES FOR CURL/REQUESTS")
            print("-"*60)

            cf_cookies = [f"{c['name']}={c['value']}" for c in cookies
                         if 'cf' in c['name'].lower() or 'key' in c['name'].lower()]

            cookie_string = "; ".join(cf_cookies)
            print(f"\n{cookie_string[:200]}...")

            # Show curl example
            print("\n" + "-"*60)
            print("  EXAMPLE CURL COMMAND")
            print("-"*60)
            print(f'\ncurl -H "Cookie: {cookie_string[:100]}..." https://key-drop.com/en\n')

            # Extract JS files
            print("-"*60)
            print("  JAVASCRIPT FILES FOUND")
            print("-"*60)
            scripts = page.query_selector_all('script[src]')
            for script in scripts[:10]:
                src = script.get_attribute('src')
                if src:
                    print(f"  {src[:70]}")

            # Keep browser open
            print("\n" + "="*60)
            print("  BROWSER STAYING OPEN - Press Ctrl+C to close")
            print("  You can interact with the page manually now")
            print("="*60 + "\n")

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print_status("\nClosing browser...", "*")

        except PlaywrightTimeout:
            print_status("Timeout waiting for page", "-")
        except Exception as e:
            print_status(f"Error: {e}", "-")
        finally:
            browser.close()
            print_status("Browser closed", "+")

if __name__ == "__main__":
    bypass_challenge()
