#!/usr/bin/env python3
"""
Subdomain Enumeration Tool
Passive subdomain discovery using multiple sources.

USAGE:
    python subdomain_enum.py <domain> [-o output.txt] [-t threads] [--timeout secs]

EXAMPLES:
    python subdomain_enum.py example.com
    python subdomain_enum.py example.com -o subs.txt -t 10
    python subdomain_enum.py example.com --timeout 20
"""

import sys
import argparse
import requests
import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import success, error, warning, info, banner, HTTPClient, extract_domain

class SubdomainEnumerator:
    def __init__(self, domain: str, timeout: int = 10):
        self.domain = domain
        self.client = HTTPClient(timeout=timeout)
        self.subdomains = set()

    def crtsh(self) -> set:
        """Query crt.sh certificate transparency logs."""
        found = set()
        try:
            url = f"https://crt.sh/?q=%.{self.domain}&output=json"
            resp = self.client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                for entry in data:
                    name = entry.get('name_value', '')
                    for sub in name.split('\n'):
                        sub = sub.strip().lower()
                        if sub.endswith(self.domain) and '*' not in sub:
                            found.add(sub)
        except Exception as e:
            warning(f"crt.sh error: {e}")
        return found

    def hackertarget(self) -> set:
        """Query HackerTarget API."""
        found = set()
        try:
            url = f"https://api.hackertarget.com/hostsearch/?q={self.domain}"
            resp = self.client.get(url)
            if resp.status_code == 200 and 'error' not in resp.text.lower():
                for line in resp.text.split('\n'):
                    if ',' in line:
                        sub = line.split(',')[0].strip().lower()
                        if sub.endswith(self.domain):
                            found.add(sub)
        except Exception as e:
            warning(f"HackerTarget error: {e}")
        return found

    def threatcrowd(self) -> set:
        """Query ThreatCrowd API."""
        found = set()
        try:
            url = f"https://www.threatcrowd.org/searchApi/v2/domain/report/?domain={self.domain}"
            resp = self.client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                for sub in data.get('subdomains', []):
                    found.add(sub.lower())
        except Exception as e:
            warning(f"ThreatCrowd error: {e}")
        return found

    def anubis(self) -> set:
        """Query Anubis-DB API."""
        found = set()
        try:
            url = f"https://jldc.me/anubis/subdomains/{self.domain}"
            resp = self.client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                for sub in data:
                    found.add(sub.lower())
        except Exception as e:
            warning(f"Anubis error: {e}")
        return found

    def alienvault(self) -> set:
        """Query AlienVault OTX."""
        found = set()
        try:
            url = f"https://otx.alienvault.com/api/v1/indicators/domain/{self.domain}/passive_dns"
            resp = self.client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                for entry in data.get('passive_dns', []):
                    hostname = entry.get('hostname', '').lower()
                    if hostname.endswith(self.domain):
                        found.add(hostname)
        except Exception as e:
            warning(f"AlienVault error: {e}")
        return found

    def urlscan(self) -> set:
        """Query urlscan.io."""
        found = set()
        try:
            url = f"https://urlscan.io/api/v1/search/?q=domain:{self.domain}"
            resp = self.client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                for result in data.get('results', []):
                    domain = result.get('task', {}).get('domain', '').lower()
                    if domain.endswith(self.domain):
                        found.add(domain)
        except Exception as e:
            warning(f"urlscan error: {e}")
        return found

    def enumerate(self, threads: int = 5) -> set:
        """Run all enumeration sources."""
        sources = [
            ('crt.sh', self.crtsh),
            ('HackerTarget', self.hackertarget),
            ('ThreatCrowd', self.threatcrowd),
            ('Anubis', self.anubis),
            ('AlienVault', self.alienvault),
            ('urlscan', self.urlscan),
        ]

        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(func): name for name, func in sources}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    results = future.result()
                    if results:
                        info(f"{name}: Found {len(results)} subdomains")
                        self.subdomains.update(results)
                except Exception as e:
                    warning(f"{name} failed: {e}")

        return self.subdomains


def main():
    parser = argparse.ArgumentParser(
        description='Passive Subdomain Enumeration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    %(prog)s example.com
    %(prog)s example.com -o subdomains.txt
    %(prog)s example.com -t 10 --timeout 20
        """
    )
    parser.add_argument('domain', help='Target domain')
    parser.add_argument('-o', '--output', help='Output file')
    parser.add_argument('-t', '--threads', type=int, default=5, help='Number of threads (default: 5)')
    parser.add_argument('--timeout', type=int, default=15, help='Request timeout in seconds (default: 15)')
    args = parser.parse_args()

    banner("Subdomain Enumerator")
    info(f"Target: {args.domain}")

    enum = SubdomainEnumerator(args.domain, timeout=args.timeout)
    subdomains = enum.enumerate(threads=args.threads)

    print()
    success(f"Total unique subdomains found: {len(subdomains)}")
    print()

    for sub in sorted(subdomains):
        print(f"  {sub}")

    if args.output:
        with open(args.output, 'w') as f:
            f.write('\n'.join(sorted(subdomains)))
        success(f"Results saved to {args.output}")


if __name__ == '__main__':
    main()
