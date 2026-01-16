#!/usr/bin/env python3
"""
DNS Enumeration Tool
Comprehensive DNS record discovery.
"""

import sys
import argparse
import socket
import dns.resolver
import dns.zone
import dns.query
sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import success, error, warning, info, banner

RECORD_TYPES = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA', 'CNAME', 'PTR', 'SRV', 'CAA']

class DNSEnumerator:
    def __init__(self, domain: str, nameserver: str = None):
        self.domain = domain
        self.resolver = dns.resolver.Resolver()
        if nameserver:
            self.resolver.nameservers = [nameserver]
        self.resolver.timeout = 5
        self.resolver.lifetime = 10
        self.results = {}

    def query_record(self, record_type: str) -> list:
        """Query specific DNS record type."""
        records = []
        try:
            answers = self.resolver.resolve(self.domain, record_type)
            for rdata in answers:
                records.append(str(rdata))
        except dns.resolver.NoAnswer:
            pass
        except dns.resolver.NXDOMAIN:
            pass
        except Exception as e:
            pass
        return records

    def get_all_records(self) -> dict:
        """Get all DNS record types."""
        for rtype in RECORD_TYPES:
            records = self.query_record(rtype)
            if records:
                self.results[rtype] = records
                info(f"{rtype}: {len(records)} record(s)")
        return self.results

    def get_nameservers(self) -> list:
        """Get authoritative nameservers."""
        return self.query_record('NS')

    def check_zone_transfer(self) -> dict:
        """Attempt zone transfer on all nameservers."""
        zone_data = {}
        nameservers = self.get_nameservers()

        for ns in nameservers:
            ns = ns.rstrip('.')
            try:
                ns_ip = socket.gethostbyname(ns)
                zone = dns.zone.from_xfr(dns.query.xfr(ns_ip, self.domain, timeout=10))
                records = []
                for name, node in zone.nodes.items():
                    for rdataset in node.rdatasets:
                        records.append(f"{name} {rdataset}")
                if records:
                    zone_data[ns] = records
                    success(f"Zone transfer successful on {ns}!")
            except Exception as e:
                warning(f"Zone transfer failed on {ns}: {type(e).__name__}")

        return zone_data

    def reverse_lookup(self, ip: str) -> str:
        """Perform reverse DNS lookup."""
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return None

    def check_dnssec(self) -> bool:
        """Check if DNSSEC is enabled."""
        try:
            answers = self.resolver.resolve(self.domain, 'DNSKEY')
            return len(answers) > 0
        except:
            return False

    def check_spf(self) -> str:
        """Check SPF record."""
        txt_records = self.query_record('TXT')
        for record in txt_records:
            if 'v=spf1' in record.lower():
                return record
        return None

    def check_dmarc(self) -> str:
        """Check DMARC record."""
        try:
            dmarc_domain = f"_dmarc.{self.domain}"
            self_resolver = dns.resolver.Resolver()
            answers = self_resolver.resolve(dmarc_domain, 'TXT')
            for rdata in answers:
                record = str(rdata)
                if 'v=dmarc1' in record.lower():
                    return record
        except:
            pass
        return None


def main():
    parser = argparse.ArgumentParser(description='DNS Enumeration Tool')
    parser.add_argument('domain', help='Target domain')
    parser.add_argument('-n', '--nameserver', help='Custom nameserver')
    parser.add_argument('-z', '--zone-transfer', action='store_true', help='Attempt zone transfer')
    parser.add_argument('-o', '--output', help='Output file (JSON)')
    args = parser.parse_args()

    banner("DNS Enumerator")
    info(f"Target: {args.domain}")

    enum = DNSEnumerator(args.domain, args.nameserver)

    print("\n[DNS Records]")
    records = enum.get_all_records()

    print("\n[Security Checks]")
    dnssec = enum.check_dnssec()
    info(f"DNSSEC: {'Enabled' if dnssec else 'Not enabled'}")

    spf = enum.check_spf()
    if spf:
        info(f"SPF: {spf[:80]}...")
    else:
        warning("SPF: Not configured")

    dmarc = enum.check_dmarc()
    if dmarc:
        info(f"DMARC: {dmarc[:80]}...")
    else:
        warning("DMARC: Not configured")

    if args.zone_transfer:
        print("\n[Zone Transfer]")
        zone_data = enum.check_zone_transfer()
        if zone_data:
            for ns, data in zone_data.items():
                print(f"\n  {ns}:")
                for record in data[:20]:
                    print(f"    {record}")

    if args.output:
        import json
        output_data = {
            'domain': args.domain,
            'records': records,
            'dnssec': dnssec,
            'spf': spf,
            'dmarc': dmarc,
        }
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        success(f"Results saved to {args.output}")


if __name__ == '__main__':
    main()
