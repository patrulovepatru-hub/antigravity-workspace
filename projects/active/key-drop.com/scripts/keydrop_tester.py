#!/usr/bin/env python3
"""
Key-Drop.com Security Tester
Uses Playwright to test for vulnerabilities after bypassing CF
"""

import json
import time
import re
import sys
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

COOKIES_FILE = "/home/l0ve/pen-test/key-drop.com/scripts/cookies.json"
RESULTS_DIR = "/home/l0ve/pen-test/key-drop.com/results"
BASE_URL = "https://key-drop.com"

class KeyDropTester:
    def __init__(self):
        self.cookies = self.load_cookies()
        self.findings = []
        self.api_endpoints = set()
        self.page = None
        self.context = None

    def load_cookies(self):
        try:
            with open(COOKIES_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("[-] No cookies found. Run bypass_cf.py first!")
            sys.exit(1)

    def setup_browser(self, playwright, headless=False):
        """Setup browser with anti-detection"""
        browser = playwright.chromium.launch(
            executable_path="/usr/bin/chromium",
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
            ]
        )
        self.context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        )
        self.context.add_cookies(self.cookies)
        self.page = self.context.new_page()

        # Intercept network requests to find API calls
        self.page.on("request", self.intercept_request)
        self.page.on("response", self.intercept_response)

        return browser

    def intercept_request(self, request):
        """Capture API endpoints"""
        url = request.url
        if '/api/' in url or '/v1/' in url or '/v2/' in url:
            self.api_endpoints.add(url)

    def intercept_response(self, response):
        """Analyze responses for sensitive data"""
        url = response.url
        if '/api/' in url:
            try:
                if 'json' in response.headers.get('content-type', ''):
                    # Could log response bodies here
                    pass
            except:
                pass

    def extract_js_endpoints(self):
        """Extract API endpoints from JavaScript files"""
        print("\n[*] Extracting API endpoints from JavaScript...")

        # Get all script sources
        scripts = self.page.query_selector_all('script[src]')
        js_urls = []
        for script in scripts:
            src = script.get_attribute('src')
            if src and not 'cloudflare' in src:
                if src.startswith('/'):
                    src = urljoin(BASE_URL, src)
                js_urls.append(src)

        # Also check inline scripts
        inline_scripts = self.page.query_selector_all('script:not([src])')
        for script in inline_scripts:
            content = script.inner_text()
            # Look for API patterns
            api_patterns = re.findall(r'["\'](/api/[^"\']+)["\']', content)
            api_patterns += re.findall(r'["\']([^"\']*\.json)["\']', content)
            api_patterns += re.findall(r'fetch\(["\']([^"\']+)["\']', content)
            for pattern in api_patterns:
                self.api_endpoints.add(pattern)

        print(f"[+] Found {len(js_urls)} external JS files")
        return js_urls

    def test_idor(self, base_path="/user/profile/"):
        """Test for IDOR on user profiles"""
        print(f"\n[*] Testing IDOR on {base_path}")

        test_ids = ['1', '2', '100', '1000', '99999', 'admin', 'test']
        results = []

        for uid in test_ids:
            url = f"{BASE_URL}{base_path}{uid}"
            try:
                response = self.page.goto(url, timeout=10000)
                status = response.status if response else 'N/A'
                title = self.page.title()
                results.append({
                    'id': uid,
                    'url': url,
                    'status': status,
                    'title': title[:50]
                })
                print(f"    {uid}: {status} - {title[:30]}")
                time.sleep(1)
            except Exception as e:
                print(f"    {uid}: Error - {str(e)[:30]}")

        return results

    def test_xss_points(self):
        """Find potential XSS injection points"""
        print("\n[*] Looking for input fields (potential XSS points)...")

        self.page.goto(BASE_URL, timeout=30000)
        time.sleep(3)

        inputs = self.page.query_selector_all('input, textarea')
        forms = self.page.query_selector_all('form')

        input_data = []
        for inp in inputs:
            try:
                input_data.append({
                    'type': inp.get_attribute('type'),
                    'name': inp.get_attribute('name'),
                    'id': inp.get_attribute('id'),
                    'placeholder': inp.get_attribute('placeholder'),
                })
            except:
                pass

        print(f"[+] Found {len(inputs)} input fields, {len(forms)} forms")
        for i in input_data[:10]:
            print(f"    Input: {i}")

        return input_data

    def test_websocket(self):
        """Test WebSocket connection"""
        print("\n[*] Testing WebSocket at ws.key-drop.com...")

        ws_test_script = """
        return new Promise((resolve) => {
            try {
                const ws = new WebSocket('wss://ws.key-drop.com');
                ws.onopen = () => {
                    ws.close();
                    resolve({status: 'connected', error: null});
                };
                ws.onerror = (e) => {
                    resolve({status: 'error', error: 'connection failed'});
                };
                setTimeout(() => resolve({status: 'timeout', error: 'no response'}), 5000);
            } catch(e) {
                resolve({status: 'exception', error: e.toString()});
            }
        });
        """

        try:
            result = self.page.evaluate(ws_test_script)
            print(f"[+] WebSocket test: {result}")
            return result
        except Exception as e:
            print(f"[-] WebSocket test failed: {e}")
            return None

    def enumerate_pages(self):
        """Navigate through site to discover more endpoints"""
        print("\n[*] Enumerating site pages...")

        pages_to_visit = [
            '/',
            '/en',
            '/en/case-opening',
            '/en/case-battle/list',
            '/en/upgrader',
            '/en/contracts',
        ]

        for path in pages_to_visit:
            url = f"{BASE_URL}{path}"
            try:
                print(f"    Visiting: {path}")
                self.page.goto(url, timeout=15000)
                time.sleep(2)
            except Exception as e:
                print(f"    Error on {path}: {str(e)[:30]}")

        print(f"\n[+] Discovered {len(self.api_endpoints)} API endpoints:")
        for ep in sorted(self.api_endpoints)[:20]:
            print(f"    {ep}")

    def save_results(self):
        """Save all findings"""
        import os
        os.makedirs(RESULTS_DIR, exist_ok=True)

        # Save API endpoints
        with open(f"{RESULTS_DIR}/api_endpoints.txt", 'w') as f:
            for ep in sorted(self.api_endpoints):
                f.write(ep + '\n')

        # Save findings
        with open(f"{RESULTS_DIR}/findings.json", 'w') as f:
            json.dump(self.findings, f, indent=2)

        print(f"\n[+] Results saved to {RESULTS_DIR}/")

    def run_all_tests(self):
        """Run all security tests"""
        with sync_playwright() as p:
            browser = self.setup_browser(p, headless=False)

            try:
                # Navigate to home first
                print("[*] Navigating to site...")
                self.page.goto(BASE_URL, timeout=30000)
                time.sleep(5)

                # Run tests
                self.enumerate_pages()
                self.extract_js_endpoints()
                self.test_websocket()
                # self.test_idor()  # Uncomment if you want IDOR testing
                # self.test_xss_points()  # Uncomment for XSS point detection

                self.save_results()

                print("\n[!] Keeping browser open for 60s for manual testing...")
                print("[!] Press Ctrl+C to exit")
                time.sleep(60)

            except KeyboardInterrupt:
                print("\n[*] Interrupted")
            finally:
                browser.close()

if __name__ == "__main__":
    tester = KeyDropTester()
    tester.run_all_tests()
