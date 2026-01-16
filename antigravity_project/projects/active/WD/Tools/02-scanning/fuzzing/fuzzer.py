#!/usr/bin/env python3
"""
Web Fuzzer
Multi-purpose fuzzing tool for web applications.

USAGE:
    python fuzzer.py <url> -w wordlist.txt [-p position] [-t threads]

EXAMPLES:
    python fuzzer.py "https://example.com/FUZZ" -w wordlist.txt
    python fuzzer.py "https://example.com/api/FUZZ/info" -w ids.txt
    python fuzzer.py "https://example.com/page?id=FUZZ" -w numbers.txt -mc 200
    python fuzzer.py "https://example.com/login" -w users.txt -d "user=FUZZ&pass=test" -X POST
"""

import sys
import argparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import success, error, warning, info, banner, HTTPClient

class Fuzzer:
    def __init__(self, proxy: str = None, timeout: int = 10):
        self.client = HTTPClient(proxy=proxy, timeout=timeout)
        self.results = []
        self.baseline = None

    def set_baseline(self, status: int = None, length: int = None):
        """Set baseline for filtering."""
        self.baseline = {'status': status, 'length': length}

    def fuzz_request(self, url: str, method: str, payload: str,
                     data: str = None, headers: dict = None) -> dict:
        """Make a single fuzz request."""
        # Replace FUZZ keyword
        fuzzed_url = url.replace('FUZZ', payload)
        fuzzed_data = data.replace('FUZZ', payload) if data else None
        fuzzed_headers = {}
        if headers:
            for k, v in headers.items():
                fuzzed_headers[k] = v.replace('FUZZ', payload)

        try:
            if method == 'GET':
                resp = self.client.get(fuzzed_url, headers=fuzzed_headers)
            elif method == 'POST':
                # Parse data string to dict
                post_data = {}
                if fuzzed_data:
                    for pair in fuzzed_data.split('&'):
                        if '=' in pair:
                            k, v = pair.split('=', 1)
                            post_data[k] = v
                resp = self.client.post(fuzzed_url, data=post_data, headers=fuzzed_headers)
            else:
                resp = self.client.request(method, fuzzed_url, data=fuzzed_data, headers=fuzzed_headers)

            # Check for interesting patterns in response
            reflection = payload in resp.text

            return {
                'payload': payload,
                'url': fuzzed_url,
                'status': resp.status_code,
                'length': len(resp.text),
                'words': len(resp.text.split()),
                'lines': resp.text.count('\n'),
                'reflection': reflection,
                'content_type': resp.headers.get('Content-Type', ''),
            }
        except Exception as e:
            return {
                'payload': payload,
                'url': fuzzed_url,
                'status': 0,
                'error': str(e)
            }

    def run(self, url: str, wordlist: list, method: str = 'GET',
            data: str = None, headers: dict = None, threads: int = 30,
            match_codes: list = None, filter_codes: list = None,
            match_length: int = None, filter_length: int = None) -> list:
        """Run fuzzing attack."""

        info(f"Fuzzing with {len(wordlist)} payloads...")

        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {
                executor.submit(self.fuzz_request, url, method, payload, data, headers): payload
                for payload in wordlist
            }

            for future in as_completed(futures):
                result = future.result()

                # Apply filters
                if result.get('error'):
                    continue

                status = result['status']
                length = result['length']

                # Match/filter by status code
                if match_codes and status not in match_codes:
                    continue
                if filter_codes and status in filter_codes:
                    continue

                # Match/filter by length
                if match_length and length != match_length:
                    continue
                if filter_length and length == filter_length:
                    continue

                self.results.append(result)

                # Real-time output
                reflection = " [REFLECTED]" if result['reflection'] else ""
                print(f"[{status}] {result['payload']:<30} (len: {length}, words: {result['words']}){reflection}")

        return self.results


def load_wordlist(filepath: str) -> list:
    """Load wordlist from file."""
    try:
        with open(filepath, 'r', errors='ignore') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        error(f"Wordlist not found: {filepath}")
        return []


def parse_headers(header_list: list) -> dict:
    """Parse header arguments to dict."""
    headers = {}
    if header_list:
        for h in header_list:
            if ':' in h:
                key, value = h.split(':', 1)
                headers[key.strip()] = value.strip()
    return headers


def main():
    parser = argparse.ArgumentParser(
        description='Web Fuzzer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    %(prog)s "https://example.com/FUZZ" -w wordlist.txt
    %(prog)s "https://example.com/api/FUZZ/info" -w ids.txt
    %(prog)s "https://example.com/page?id=FUZZ" -w numbers.txt -mc 200
    %(prog)s "https://example.com/login" -w users.txt -d "user=FUZZ&pass=test" -X POST
    %(prog)s "https://example.com/api" -w payloads.txt -H "X-Custom: FUZZ"
        """
    )
    parser.add_argument('url', help='Target URL with FUZZ keyword')
    parser.add_argument('-w', '--wordlist', required=True, help='Wordlist file')
    parser.add_argument('-X', '--method', default='GET', help='HTTP method (default: GET)')
    parser.add_argument('-d', '--data', help='POST data with FUZZ keyword')
    parser.add_argument('-H', '--header', action='append', help='Custom header (can be repeated)')
    parser.add_argument('-t', '--threads', type=int, default=30, help='Number of threads (default: 30)')
    parser.add_argument('-mc', '--match-codes', help='Match status codes (comma-separated)')
    parser.add_argument('-fc', '--filter-codes', help='Filter status codes (comma-separated)')
    parser.add_argument('-ml', '--match-length', type=int, help='Match response length')
    parser.add_argument('-fl', '--filter-length', type=int, help='Filter response length')
    parser.add_argument('-p', '--proxy', help='Proxy URL')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout (default: 10)')
    parser.add_argument('-o', '--output', help='Output file')
    args = parser.parse_args()

    if 'FUZZ' not in args.url and (not args.data or 'FUZZ' not in args.data):
        error("FUZZ keyword not found in URL or data")
        sys.exit(1)

    banner("Web Fuzzer")
    info(f"Target: {args.url}")
    info(f"Method: {args.method}")

    wordlist = load_wordlist(args.wordlist)
    if not wordlist:
        sys.exit(1)

    headers = parse_headers(args.header)
    match_codes = [int(c) for c in args.match_codes.split(',')] if args.match_codes else None
    filter_codes = [int(c) for c in args.filter_codes.split(',')] if args.filter_codes else None

    fuzzer = Fuzzer(proxy=args.proxy, timeout=args.timeout)
    results = fuzzer.run(
        args.url,
        wordlist,
        method=args.method,
        data=args.data,
        headers=headers,
        threads=args.threads,
        match_codes=match_codes,
        filter_codes=filter_codes,
        match_length=args.match_length,
        filter_length=args.filter_length
    )

    print()
    success(f"Total results: {len(results)}")

    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump({'url': args.url, 'results': results}, f, indent=2)
        success(f"Results saved to {args.output}")


if __name__ == '__main__':
    main()
