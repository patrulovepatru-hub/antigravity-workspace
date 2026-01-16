#!/usr/bin/env python3
"""
Wayback Machine URL Extractor
Extract historical URLs from web.archive.org
"""

import sys
import argparse
import re
from urllib.parse import urlparse
sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import success, error, warning, info, banner, HTTPClient

class WaybackExtractor:
    def __init__(self, domain: str):
        self.domain = domain
        self.client = HTTPClient(timeout=30)
        self.urls = set()

    def fetch_urls(self, include_subdomains: bool = True) -> set:
        """Fetch URLs from Wayback Machine CDX API."""
        target = f"*.{self.domain}" if include_subdomains else self.domain

        url = f"https://web.archive.org/cdx/search/cdx?url={target}/*&output=text&fl=original&collapse=urlkey"

        try:
            info(f"Querying Wayback Machine for {target}...")
            resp = self.client.get(url)
            if resp.status_code == 200:
                for line in resp.text.split('\n'):
                    line = line.strip()
                    if line:
                        self.urls.add(line)
        except Exception as e:
            error(f"Wayback query failed: {e}")

        return self.urls

    def filter_by_extension(self, extensions: list) -> set:
        """Filter URLs by file extension."""
        filtered = set()
        for url in self.urls:
            path = urlparse(url).path.lower()
            for ext in extensions:
                if path.endswith(f'.{ext}'):
                    filtered.add(url)
                    break
        return filtered

    def filter_by_pattern(self, pattern: str) -> set:
        """Filter URLs by regex pattern."""
        filtered = set()
        regex = re.compile(pattern, re.IGNORECASE)
        for url in self.urls:
            if regex.search(url):
                filtered.add(url)
        return filtered

    def extract_parameters(self) -> dict:
        """Extract unique parameters from URLs."""
        params = {}
        for url in self.urls:
            parsed = urlparse(url)
            if parsed.query:
                for param in parsed.query.split('&'):
                    if '=' in param:
                        key = param.split('=')[0]
                        if key not in params:
                            params[key] = set()
                        params[key].add(url)
        return params

    def extract_paths(self) -> set:
        """Extract unique paths."""
        paths = set()
        for url in self.urls:
            path = urlparse(url).path
            if path and path != '/':
                paths.add(path)
        return paths


def main():
    parser = argparse.ArgumentParser(description='Wayback Machine URL Extractor')
    parser.add_argument('domain', help='Target domain')
    parser.add_argument('-o', '--output', help='Output file')
    parser.add_argument('--no-subs', action='store_true', help='Exclude subdomains')
    parser.add_argument('-e', '--extensions', help='Filter by extensions (comma-separated)')
    parser.add_argument('-p', '--params', action='store_true', help='Extract parameters')
    parser.add_argument('--paths', action='store_true', help='Extract unique paths')
    args = parser.parse_args()

    banner("Wayback URL Extractor")
    info(f"Target: {args.domain}")

    extractor = WaybackExtractor(args.domain)
    urls = extractor.fetch_urls(include_subdomains=not args.no_subs)

    success(f"Total URLs found: {len(urls)}")

    if args.extensions:
        ext_list = [e.strip() for e in args.extensions.split(',')]
        filtered = extractor.filter_by_extension(ext_list)
        print(f"\n[URLs with extensions: {', '.join(ext_list)}]")
        for url in sorted(filtered)[:50]:
            print(f"  {url}")
        if len(filtered) > 50:
            info(f"... and {len(filtered) - 50} more")

    if args.params:
        params = extractor.extract_parameters()
        print(f"\n[Unique Parameters: {len(params)}]")
        for param, examples in sorted(params.items())[:30]:
            print(f"  {param} ({len(examples)} occurrences)")

    if args.paths:
        paths = extractor.extract_paths()
        print(f"\n[Unique Paths: {len(paths)}]")
        for path in sorted(paths)[:50]:
            print(f"  {path}")

    if args.output:
        with open(args.output, 'w') as f:
            f.write('\n'.join(sorted(urls)))
        success(f"All URLs saved to {args.output}")


if __name__ == '__main__':
    main()
