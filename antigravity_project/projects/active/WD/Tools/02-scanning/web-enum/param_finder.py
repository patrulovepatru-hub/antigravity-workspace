#!/usr/bin/env python3
"""
Parameter Finder
Discover hidden GET/POST parameters.

USAGE:
    python param_finder.py <url> [-w wordlist] [-m method] [-t threads]

EXAMPLES:
    python param_finder.py https://example.com/page
    python param_finder.py https://example.com/page -w params.txt -m POST
    python param_finder.py https://example.com/search -t 50 --diff-threshold 50
"""

import sys
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import success, error, warning, info, banner, HTTPClient, normalize_url

DEFAULT_PARAMS = [
    'id', 'page', 'search', 'q', 'query', 'name', 'user', 'username',
    'password', 'pass', 'email', 'file', 'filename', 'path', 'dir',
    'url', 'uri', 'redirect', 'return', 'next', 'callback', 'data',
    'action', 'cmd', 'exec', 'command', 'type', 'cat', 'category',
    'lang', 'language', 'debug', 'test', 'admin', 'login', 'token',
    'key', 'api_key', 'apikey', 'secret', 'auth', 'session', 'sid',
    'view', 'template', 'format', 'output', 'json', 'xml',
    'sort', 'order', 'orderby', 'limit', 'offset', 'start', 'count',
    'filter', 'include', 'require', 'load', 'read', 'fetch',
    'src', 'source', 'ref', 'reference', 'target', 'dest', 'destination',
    'host', 'port', 'proxy', 'site', 'domain',
    'year', 'month', 'day', 'date', 'time', 'from', 'to',
    'min', 'max', 'size', 'width', 'height',
    'config', 'setting', 'settings', 'option', 'options',
]


class ParamFinder:
    def __init__(self, url: str, proxy: str = None, timeout: int = 10):
        self.url = normalize_url(url)
        self.client = HTTPClient(proxy=proxy, timeout=timeout)
        self.baseline = None
        self.found = []

    def get_baseline(self, method: str = 'GET') -> dict:
        """Get baseline response."""
        try:
            if method == 'GET':
                resp = self.client.get(self.url)
            else:
                resp = self.client.post(self.url)

            self.baseline = {
                'status': resp.status_code,
                'length': len(resp.text),
                'content': resp.text,
                'headers': dict(resp.headers)
            }
            return self.baseline
        except Exception as e:
            error(f"Failed to get baseline: {e}")
            return None

    def test_param(self, param: str, method: str = 'GET', value: str = 'test123') -> dict:
        """Test a single parameter."""
        try:
            if method == 'GET':
                resp = self.client.get(self.url, params={param: value})
            else:
                resp = self.client.post(self.url, data={param: value})

            return {
                'param': param,
                'status': resp.status_code,
                'length': len(resp.text),
                'content': resp.text,
            }
        except:
            return None

    def calculate_diff(self, response: dict) -> float:
        """Calculate difference from baseline."""
        if not self.baseline or not response:
            return 0

        # Status code difference
        if response['status'] != self.baseline['status']:
            return 100

        # Content length difference percentage
        len_diff = abs(response['length'] - self.baseline['length'])
        len_pct = (len_diff / max(self.baseline['length'], 1)) * 100

        # Content similarity
        similarity = SequenceMatcher(None, self.baseline['content'][:5000],
                                     response['content'][:5000]).ratio()
        content_diff = (1 - similarity) * 100

        return max(len_pct, content_diff)

    def discover(self, params: list, method: str = 'GET',
                 threads: int = 20, diff_threshold: float = 10) -> list:
        """Discover valid parameters."""

        if not self.get_baseline(method):
            return []

        info(f"Baseline: Status={self.baseline['status']}, Length={self.baseline['length']}")
        info(f"Testing {len(params)} parameters...")

        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(self.test_param, param, method): param for param in params}

            for future in as_completed(futures):
                param = futures[future]
                result = future.result()

                if result:
                    diff = self.calculate_diff(result)

                    if diff >= diff_threshold:
                        self.found.append({
                            'param': param,
                            'diff': round(diff, 2),
                            'status': result['status'],
                            'length': result['length']
                        })
                        success(f"[+] {param} (diff: {diff:.1f}%, status: {result['status']}, len: {result['length']})")

        return self.found


def load_wordlist(filepath: str) -> list:
    """Load wordlist from file."""
    try:
        with open(filepath, 'r', errors='ignore') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        return []


def main():
    parser = argparse.ArgumentParser(
        description='Hidden Parameter Finder',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    %(prog)s https://example.com/page
    %(prog)s https://example.com/page -w params.txt -m POST
    %(prog)s https://example.com/search -t 50 --diff-threshold 50
        """
    )
    parser.add_argument('url', help='Target URL')
    parser.add_argument('-w', '--wordlist', help='Parameter wordlist')
    parser.add_argument('-m', '--method', choices=['GET', 'POST'], default='GET', help='HTTP method (default: GET)')
    parser.add_argument('-t', '--threads', type=int, default=20, help='Number of threads (default: 20)')
    parser.add_argument('--diff-threshold', type=float, default=10, help='Difference threshold %% (default: 10)')
    parser.add_argument('-p', '--proxy', help='Proxy URL')
    parser.add_argument('-o', '--output', help='Output file')
    args = parser.parse_args()

    banner("Parameter Finder")
    info(f"Target: {args.url}")
    info(f"Method: {args.method}")

    # Load wordlist
    if args.wordlist:
        params = load_wordlist(args.wordlist)
        if not params:
            warning("Wordlist empty or not found, using defaults")
            params = DEFAULT_PARAMS
    else:
        params = DEFAULT_PARAMS

    finder = ParamFinder(args.url, proxy=args.proxy)
    results = finder.discover(params, method=args.method, threads=args.threads,
                              diff_threshold=args.diff_threshold)

    print()
    if results:
        success(f"Found {len(results)} potential parameters")
        print("\nResults sorted by difference:")
        for r in sorted(results, key=lambda x: x['diff'], reverse=True):
            print(f"  {r['param']}: diff={r['diff']}%, status={r['status']}, len={r['length']}")
    else:
        warning("No parameters found with significant difference")

    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump({'url': args.url, 'method': args.method, 'found': results}, f, indent=2)
        success(f"Results saved to {args.output}")


if __name__ == '__main__':
    main()
