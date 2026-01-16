#!/usr/bin/env python3
"""
HTTP Headers Security Analyzer
Analyze security headers and identify misconfigurations.
"""

import sys
import argparse
sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import success, error, warning, info, banner, HTTPClient, normalize_url

SECURITY_HEADERS = {
    'Strict-Transport-Security': {
        'description': 'HSTS - Forces HTTPS connections',
        'recommended': 'max-age=31536000; includeSubDomains; preload',
        'severity': 'HIGH'
    },
    'Content-Security-Policy': {
        'description': 'CSP - Prevents XSS and injection attacks',
        'recommended': "default-src 'self'",
        'severity': 'HIGH'
    },
    'X-Frame-Options': {
        'description': 'Prevents clickjacking attacks',
        'recommended': 'DENY or SAMEORIGIN',
        'severity': 'MEDIUM'
    },
    'X-Content-Type-Options': {
        'description': 'Prevents MIME type sniffing',
        'recommended': 'nosniff',
        'severity': 'MEDIUM'
    },
    'X-XSS-Protection': {
        'description': 'Legacy XSS filter (deprecated but still useful)',
        'recommended': '1; mode=block',
        'severity': 'LOW'
    },
    'Referrer-Policy': {
        'description': 'Controls referrer information',
        'recommended': 'strict-origin-when-cross-origin',
        'severity': 'MEDIUM'
    },
    'Permissions-Policy': {
        'description': 'Controls browser features',
        'recommended': 'geolocation=(), microphone=(), camera=()',
        'severity': 'MEDIUM'
    },
    'Cross-Origin-Opener-Policy': {
        'description': 'Isolates browsing context',
        'recommended': 'same-origin',
        'severity': 'LOW'
    },
    'Cross-Origin-Resource-Policy': {
        'description': 'Prevents cross-origin reads',
        'recommended': 'same-origin',
        'severity': 'LOW'
    },
    'Cross-Origin-Embedder-Policy': {
        'description': 'Controls cross-origin embedding',
        'recommended': 'require-corp',
        'severity': 'LOW'
    },
}

INFO_DISCLOSURE_HEADERS = [
    'Server', 'X-Powered-By', 'X-AspNet-Version', 'X-AspNetMvc-Version',
    'X-Generator', 'X-Drupal-Cache', 'X-Drupal-Dynamic-Cache'
]

class HeadersAnalyzer:
    def __init__(self, url: str, proxy: str = None):
        self.url = normalize_url(url)
        self.client = HTTPClient(proxy=proxy)
        self.headers = {}
        self.findings = []

    def fetch_headers(self) -> dict:
        """Fetch HTTP headers from target."""
        try:
            resp = self.client.get(self.url)
            self.headers = dict(resp.headers)
            return self.headers
        except Exception as e:
            error(f"Failed to fetch headers: {e}")
            return {}

    def analyze_security_headers(self) -> list:
        """Analyze security headers."""
        results = []

        for header, details in SECURITY_HEADERS.items():
            value = self.headers.get(header)
            if value:
                results.append({
                    'header': header,
                    'status': 'PRESENT',
                    'value': value,
                    'description': details['description'],
                    'severity': None
                })
            else:
                results.append({
                    'header': header,
                    'status': 'MISSING',
                    'value': None,
                    'description': details['description'],
                    'recommended': details['recommended'],
                    'severity': details['severity']
                })
                self.findings.append({
                    'type': 'missing_security_header',
                    'header': header,
                    'severity': details['severity'],
                    'description': f"Missing {header}: {details['description']}"
                })

        return results

    def check_info_disclosure(self) -> list:
        """Check for information disclosure headers."""
        disclosed = []

        for header in INFO_DISCLOSURE_HEADERS:
            value = self.headers.get(header)
            if value:
                disclosed.append({'header': header, 'value': value})
                self.findings.append({
                    'type': 'info_disclosure',
                    'header': header,
                    'value': value,
                    'severity': 'INFO',
                    'description': f"Information disclosure via {header}: {value}"
                })

        return disclosed

    def check_cookies(self) -> list:
        """Analyze Set-Cookie headers."""
        cookies = []
        cookie_headers = self.headers.get('Set-Cookie', '')

        if isinstance(cookie_headers, str):
            cookie_headers = [cookie_headers]

        for cookie in cookie_headers:
            if not cookie:
                continue

            analysis = {
                'cookie': cookie.split('=')[0] if '=' in cookie else cookie,
                'secure': 'Secure' in cookie,
                'httponly': 'HttpOnly' in cookie,
                'samesite': 'SameSite' in cookie,
            }

            issues = []
            if not analysis['secure']:
                issues.append('Missing Secure flag')
            if not analysis['httponly']:
                issues.append('Missing HttpOnly flag')
            if not analysis['samesite']:
                issues.append('Missing SameSite attribute')

            analysis['issues'] = issues
            cookies.append(analysis)

            if issues:
                self.findings.append({
                    'type': 'insecure_cookie',
                    'cookie': analysis['cookie'],
                    'severity': 'MEDIUM',
                    'issues': issues
                })

        return cookies

    def check_cors(self) -> dict:
        """Check CORS configuration."""
        cors = {
            'Access-Control-Allow-Origin': self.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Credentials': self.headers.get('Access-Control-Allow-Credentials'),
            'Access-Control-Allow-Methods': self.headers.get('Access-Control-Allow-Methods'),
        }

        if cors['Access-Control-Allow-Origin'] == '*':
            self.findings.append({
                'type': 'insecure_cors',
                'severity': 'HIGH' if cors['Access-Control-Allow-Credentials'] == 'true' else 'MEDIUM',
                'description': 'CORS allows all origins'
            })

        return cors


def main():
    parser = argparse.ArgumentParser(description='HTTP Headers Security Analyzer')
    parser.add_argument('url', help='Target URL')
    parser.add_argument('-p', '--proxy', help='Proxy URL (e.g., http://127.0.0.1:8080)')
    parser.add_argument('-o', '--output', help='Output file (JSON)')
    args = parser.parse_args()

    banner("Headers Security Analyzer")
    info(f"Target: {args.url}")

    analyzer = HeadersAnalyzer(args.url, proxy=args.proxy)
    headers = analyzer.fetch_headers()

    if not headers:
        error("No headers received")
        sys.exit(1)

    print("\n[All Headers]")
    for key, value in sorted(headers.items()):
        print(f"  {key}: {value[:80]}{'...' if len(str(value)) > 80 else ''}")

    print("\n[Security Headers Analysis]")
    security = analyzer.analyze_security_headers()
    for item in security:
        if item['status'] == 'PRESENT':
            success(f"{item['header']}: {item['value'][:60]}...")
        else:
            error(f"{item['header']}: MISSING [{item['severity']}]")

    print("\n[Information Disclosure]")
    disclosed = analyzer.check_info_disclosure()
    if disclosed:
        for item in disclosed:
            warning(f"{item['header']}: {item['value']}")
    else:
        success("No information disclosure headers found")

    print("\n[Cookie Analysis]")
    cookies = analyzer.check_cookies()
    if cookies:
        for cookie in cookies:
            if cookie['issues']:
                warning(f"{cookie['cookie']}: {', '.join(cookie['issues'])}")
            else:
                success(f"{cookie['cookie']}: Properly secured")
    else:
        info("No cookies found")

    print("\n[CORS Configuration]")
    cors = analyzer.check_cors()
    for key, value in cors.items():
        if value:
            info(f"{key}: {value}")

    if analyzer.findings:
        print(f"\n[Summary: {len(analyzer.findings)} findings]")
        for finding in analyzer.findings:
            severity = finding.get('severity', 'INFO')
            print(f"  [{severity}] {finding.get('description', finding.get('type'))}")

    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump({
                'url': args.url,
                'headers': headers,
                'findings': analyzer.findings
            }, f, indent=2)
        success(f"Results saved to {args.output}")


if __name__ == '__main__':
    main()
