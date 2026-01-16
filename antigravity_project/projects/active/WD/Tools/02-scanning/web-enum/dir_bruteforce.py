#!/usr/bin/env python3
"""
Directory Bruteforcer
Web directory and file discovery tool.

USAGE:
    python dir_bruteforce.py <url> -w wordlist.txt [-t threads] [-x extensions]

EXAMPLES:
    python dir_bruteforce.py https://example.com -w common.txt
    python dir_bruteforce.py https://example.com -w dirs.txt -x php,html,txt
    python dir_bruteforce.py https://example.com -w dirs.txt -t 50 --follow-redirects
    python dir_bruteforce.py https://example.com -w dirs.txt -s 200,301,403
"""

import sys
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import success, error, warning, info, banner, HTTPClient, normalize_url

DEFAULT_WORDLIST = [
    'admin', 'administrator', 'login', 'wp-admin', 'wp-login.php',
    'phpmyadmin', 'dashboard', 'panel', 'api', 'v1', 'v2',
    'backup', 'backups', 'bak', 'old', 'test', 'dev', 'staging',
    'config', 'configuration', 'conf', 'settings',
    '.git', '.svn', '.env', '.htaccess', 'robots.txt', 'sitemap.xml',
    'uploads', 'images', 'img', 'css', 'js', 'static', 'assets',
    'includes', 'include', 'inc', 'lib', 'libs', 'vendor',
    'tmp', 'temp', 'cache', 'logs', 'log',
    'cgi-bin', 'scripts', 'bin',
    'wp-content', 'wp-includes',
    'user', 'users', 'account', 'accounts', 'profile',
    'download', 'downloads', 'files', 'file',
    'search', 'query', 'find',
    'xmlrpc.php', 'server-status', 'server-info',
]


class DirBruteforcer:
    def __init__(self, url: str, proxy: str = None, timeout: int = 10):
        self.base_url = normalize_url(url)
        self.client = HTTPClient(proxy=proxy, timeout=timeout)
        self.found = []
        self.errors = 0

    def check_path(self, path: str, follow_redirects: bool = False) -> dict:
        """Check if path exists."""
        url = urljoin(self.base_url + '/', path)

        try:
            resp = self.client.get(url, allow_redirects=follow_redirects)
            return {
                'path': path,
                'url': url,
                'status': resp.status_code,
                'size': len(resp.content),
                'redirect': resp.headers.get('Location', '') if resp.status_code in [301, 302, 307, 308] else None
            }
        except Exception as e:
            self.errors += 1
            return None

    def bruteforce(self, wordlist: list, threads: int = 30,
                   extensions: list = None, status_codes: list = None,
                   follow_redirects: bool = False) -> list:
        """Run bruteforce scan."""

        # Build paths with extensions
        paths = []
        for word in wordlist:
            paths.append(word)
            if extensions:
                for ext in extensions:
                    paths.append(f"{word}.{ext}")

        valid_status = status_codes or [200, 201, 204, 301, 302, 307, 308, 401, 403]

        info(f"Testing {len(paths)} paths...")

        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(self.check_path, path, follow_redirects): path for path in paths}

            for future in as_completed(futures):
                result = future.result()
                if result and result['status'] in valid_status:
                    self.found.append(result)

                    # Real-time output
                    status = result['status']
                    size = result['size']
                    path = result['path']

                    if status == 200:
                        success(f"[{status}] /{path} ({size} bytes)")
                    elif status in [301, 302, 307, 308]:
                        info(f"[{status}] /{path} -> {result['redirect']}")
                    elif status == 403:
                        warning(f"[{status}] /{path} (Forbidden)")
                    elif status == 401:
                        warning(f"[{status}] /{path} (Auth Required)")

        return self.found


def load_wordlist(filepath: str) -> list:
    """Load wordlist from file."""
    try:
        with open(filepath, 'r', errors='ignore') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        error(f"Wordlist not found: {filepath}")
        return []


def main():
    parser = argparse.ArgumentParser(
        description='Directory Bruteforcer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    %(prog)s https://example.com -w common.txt
    %(prog)s https://example.com -w dirs.txt -x php,html,txt
    %(prog)s https://example.com -w dirs.txt -t 50 --follow-redirects
    %(prog)s https://example.com -w dirs.txt -s 200,301,403
        """
    )
    parser.add_argument('url', help='Target URL')
    parser.add_argument('-w', '--wordlist', help='Wordlist file')
    parser.add_argument('-x', '--extensions', help='Extensions to append (comma-separated)')
    parser.add_argument('-t', '--threads', type=int, default=30, help='Number of threads (default: 30)')
    parser.add_argument('-s', '--status-codes', help='Valid status codes (comma-separated)')
    parser.add_argument('--follow-redirects', action='store_true', help='Follow redirects')
    parser.add_argument('-p', '--proxy', help='Proxy URL')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout (default: 10)')
    parser.add_argument('-o', '--output', help='Output file')
    args = parser.parse_args()

    banner("Directory Bruteforcer")
    info(f"Target: {args.url}")

    # Load wordlist
    if args.wordlist:
        wordlist = load_wordlist(args.wordlist)
        if not wordlist:
            sys.exit(1)
    else:
        info("Using default wordlist")
        wordlist = DEFAULT_WORDLIST

    # Parse extensions
    extensions = [e.strip().lstrip('.') for e in args.extensions.split(',')] if args.extensions else None

    # Parse status codes
    status_codes = [int(s.strip()) for s in args.status_codes.split(',')] if args.status_codes else None

    bruteforcer = DirBruteforcer(args.url, proxy=args.proxy, timeout=args.timeout)
    results = bruteforcer.bruteforce(
        wordlist,
        threads=args.threads,
        extensions=extensions,
        status_codes=status_codes,
        follow_redirects=args.follow_redirects
    )

    print()
    success(f"Found {len(results)} paths")

    if bruteforcer.errors > 0:
        warning(f"{bruteforcer.errors} errors occurred")

    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump({'url': args.url, 'found': results}, f, indent=2)
        success(f"Results saved to {args.output}")


if __name__ == '__main__':
    main()
