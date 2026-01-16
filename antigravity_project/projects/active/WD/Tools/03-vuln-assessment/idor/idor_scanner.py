#!/usr/bin/env python3
"""
IDOR Scanner
Insecure Direct Object Reference vulnerability scanner.

USAGE:
    python idor_scanner.py <url> [-p param] [--range start-end] [--wordlist file]

EXAMPLES:
    python idor_scanner.py "https://example.com/user?id=100" -p id --range 1-200
    python idor_scanner.py "https://example.com/doc?file=report.pdf" -p file -w docs.txt
    python idor_scanner.py "https://example.com/api/user/100" --path-param --range 1-500
"""

import sys
import argparse
import re
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs, urlencode
sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import success, error, warning, info, banner, HTTPClient

class IDORScanner:
    def __init__(self, proxy: str = None, timeout: int = 10):
        self.client = HTTPClient(proxy=proxy, timeout=timeout)
        self.baseline = None
        self.findings = []
        self.seen_hashes = set()

    def get_baseline(self, url: str, param: str = None, method: str = 'GET') -> dict:
        """Get baseline response."""
        try:
            resp = self.client.get(url)
            content_hash = hashlib.md5(resp.text.encode()).hexdigest()

            self.baseline = {
                'status': resp.status_code,
                'length': len(resp.text),
                'hash': content_hash,
                'content': resp.text
            }
            self.seen_hashes.add(content_hash)
            return self.baseline
        except Exception as e:
            error(f"Baseline failed: {e}")
            return None

    def test_id(self, url: str, param: str, value: str, method: str = 'GET', is_path: bool = False) -> dict:
        """Test a single ID value."""
        try:
            if is_path:
                # Replace path parameter
                test_url = re.sub(r'/\d+(/|$)', f'/{value}\\1', url)
            else:
                parsed = urlparse(url)
                params = parse_qs(parsed.query)
                params[param] = [value]
                test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(params, doseq=True)}"

            resp = self.client.get(test_url)
            content_hash = hashlib.md5(resp.text.encode()).hexdigest()

            return {
                'value': value,
                'url': test_url,
                'status': resp.status_code,
                'length': len(resp.text),
                'hash': content_hash,
                'is_new': content_hash not in self.seen_hashes,
                'content_preview': resp.text[:200]
            }
        except:
            return None

    def analyze_response(self, result: dict) -> dict:
        """Analyze if response indicates accessible object."""
        if not result:
            return None

        # Skip if same as baseline
        if result['hash'] == self.baseline['hash']:
            return None

        # Skip error responses
        if result['status'] in [400, 404, 500]:
            return None

        # New unique response
        if result['is_new'] and result['status'] == 200:
            self.seen_hashes.add(result['hash'])
            return {
                'type': 'unique_object',
                'value': result['value'],
                'status': result['status'],
                'length': result['length'],
                'url': result['url']
            }

        # Access to different object (different length, same status)
        if result['status'] == self.baseline['status']:
            len_diff = abs(result['length'] - self.baseline['length'])
            if len_diff > 50:
                return {
                    'type': 'different_object',
                    'value': result['value'],
                    'status': result['status'],
                    'length': result['length'],
                    'len_diff': len_diff,
                    'url': result['url']
                }

        return None

    def scan_range(self, url: str, param: str, start: int, end: int,
                   method: str = 'GET', is_path: bool = False, threads: int = 20) -> list:
        """Scan a range of numeric IDs."""

        info(f"Testing IDs from {start} to {end}...")

        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {
                executor.submit(self.test_id, url, param, str(i), method, is_path): i
                for i in range(start, end + 1)
            }

            for future in as_completed(futures):
                result = future.result()
                finding = self.analyze_response(result)

                if finding:
                    self.findings.append(finding)
                    success(f"[IDOR] id={finding['value']} | status={finding['status']} | len={finding['length']}")

        return self.findings

    def scan_wordlist(self, url: str, param: str, wordlist: list,
                      method: str = 'GET', is_path: bool = False, threads: int = 20) -> list:
        """Scan using wordlist."""

        info(f"Testing {len(wordlist)} values...")

        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {
                executor.submit(self.test_id, url, param, word, method, is_path): word
                for word in wordlist
            }

            for future in as_completed(futures):
                result = future.result()
                finding = self.analyze_response(result)

                if finding:
                    self.findings.append(finding)
                    success(f"[IDOR] value={finding['value']} | status={finding['status']} | len={finding['length']}")

        return self.findings

    def scan_uuid_patterns(self, url: str, param: str, sample_uuid: str = None) -> list:
        """Test common UUID manipulation patterns."""

        patterns = []

        if sample_uuid:
            # Increment/decrement last characters
            if sample_uuid[-1].isdigit():
                for i in range(10):
                    patterns.append(sample_uuid[:-1] + str(i))

            # Zero out parts
            parts = sample_uuid.split('-')
            if len(parts) == 5:
                patterns.append('00000000-0000-0000-0000-000000000000')
                patterns.append('00000000-0000-0000-0000-000000000001')
                patterns.append(f"{parts[0]}-0000-0000-0000-000000000000")

        return self.scan_wordlist(url, param, patterns)


def load_wordlist(filepath: str) -> list:
    """Load wordlist from file."""
    try:
        with open(filepath, 'r', errors='ignore') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []


def main():
    parser = argparse.ArgumentParser(
        description='IDOR Scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    %(prog)s "https://example.com/user?id=100" -p id --range 1-200
    %(prog)s "https://example.com/doc?file=report.pdf" -p file -w docs.txt
    %(prog)s "https://example.com/api/user/100" --path-param --range 1-500
        """
    )
    parser.add_argument('url', help='Target URL')
    parser.add_argument('-p', '--param', help='Parameter to test')
    parser.add_argument('--range', help='ID range to test (e.g., 1-1000)')
    parser.add_argument('-w', '--wordlist', help='Wordlist file')
    parser.add_argument('--path-param', action='store_true', help='Parameter is in URL path')
    parser.add_argument('-t', '--threads', type=int, default=20, help='Number of threads (default: 20)')
    parser.add_argument('--proxy', help='Proxy URL')
    parser.add_argument('-o', '--output', help='Output file')
    args = parser.parse_args()

    banner("IDOR Scanner")
    info(f"Target: {args.url}")

    if not args.range and not args.wordlist:
        error("Specify either --range or --wordlist")
        sys.exit(1)

    scanner = IDORScanner(proxy=args.proxy)

    # Get baseline
    if not scanner.get_baseline(args.url, args.param):
        sys.exit(1)

    info(f"Baseline: status={scanner.baseline['status']}, length={scanner.baseline['length']}")

    results = []

    if args.range:
        start, end = map(int, args.range.split('-'))
        results = scanner.scan_range(
            args.url, args.param, start, end,
            is_path=args.path_param, threads=args.threads
        )

    if args.wordlist:
        wordlist = load_wordlist(args.wordlist)
        if wordlist:
            results.extend(scanner.scan_wordlist(
                args.url, args.param, wordlist,
                is_path=args.path_param, threads=args.threads
            ))

    print()
    if results:
        success(f"Found {len(results)} accessible object(s)")
        print("\nUnique objects found:")
        for r in results[:20]:
            print(f"  {r['value']}: status={r['status']}, len={r['length']}")
        if len(results) > 20:
            info(f"... and {len(results) - 20} more")
    else:
        warning("No IDOR vulnerabilities detected")

    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump({'url': args.url, 'findings': results}, f, indent=2)
        success(f"Results saved to {args.output}")


if __name__ == '__main__':
    main()
