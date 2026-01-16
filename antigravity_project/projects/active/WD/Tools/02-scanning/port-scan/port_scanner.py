#!/usr/bin/env python3
"""
Port Scanner
Fast TCP port scanner with service detection.

USAGE:
    python port_scanner.py <target> [-p ports] [-t threads] [--timeout ms]

EXAMPLES:
    python port_scanner.py 192.168.1.1
    python port_scanner.py example.com -p 80,443,8080
    python port_scanner.py 192.168.1.1 -p 1-1000 -t 100
    python port_scanner.py 192.168.1.1 --top-ports 100
"""

import sys
import socket
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import success, error, warning, info, banner

TOP_PORTS = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 995,
             1723, 3306, 3389, 5432, 5900, 8080, 8443, 8888, 27017]

COMMON_SERVICES = {
    21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS',
    80: 'HTTP', 110: 'POP3', 111: 'RPC', 135: 'MSRPC', 139: 'NetBIOS',
    143: 'IMAP', 443: 'HTTPS', 445: 'SMB', 993: 'IMAPS', 995: 'POP3S',
    1433: 'MSSQL', 1521: 'Oracle', 1723: 'PPTP', 3306: 'MySQL',
    3389: 'RDP', 5432: 'PostgreSQL', 5900: 'VNC', 6379: 'Redis',
    8080: 'HTTP-Proxy', 8443: 'HTTPS-Alt', 27017: 'MongoDB'
}


class PortScanner:
    def __init__(self, target: str, timeout: float = 1.0):
        self.target = target
        self.timeout = timeout
        self.open_ports = []

    def resolve_host(self) -> str:
        """Resolve hostname to IP."""
        try:
            return socket.gethostbyname(self.target)
        except socket.gaierror:
            return None

    def scan_port(self, port: int) -> dict:
        """Scan a single port."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)

        try:
            result = sock.connect_ex((self.target, port))
            if result == 0:
                service = COMMON_SERVICES.get(port, 'unknown')
                banner_grab = self._grab_banner(sock, port)
                return {
                    'port': port,
                    'state': 'open',
                    'service': service,
                    'banner': banner_grab
                }
        except socket.timeout:
            pass
        except Exception:
            pass
        finally:
            sock.close()

        return None

    def _grab_banner(self, sock: socket.socket, port: int) -> str:
        """Attempt to grab service banner."""
        try:
            if port in [80, 443, 8080, 8443]:
                return None

            sock.settimeout(2)
            sock.send(b'\r\n')
            banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
            return banner[:100] if banner else None
        except:
            return None

    def scan(self, ports: list, threads: int = 50) -> list:
        """Scan multiple ports."""
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(self.scan_port, port): port for port in ports}

            for future in as_completed(futures):
                result = future.result()
                if result:
                    self.open_ports.append(result)

        self.open_ports.sort(key=lambda x: x['port'])
        return self.open_ports


def parse_ports(port_str: str) -> list:
    """Parse port specification string."""
    ports = []
    for part in port_str.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            ports.extend(range(start, end + 1))
        else:
            ports.append(int(part))
    return sorted(set(ports))


def main():
    parser = argparse.ArgumentParser(
        description='TCP Port Scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    %(prog)s 192.168.1.1
    %(prog)s example.com -p 80,443,8080
    %(prog)s 192.168.1.1 -p 1-1000 -t 100
    %(prog)s 192.168.1.1 --top-ports 100
        """
    )
    parser.add_argument('target', help='Target IP or hostname')
    parser.add_argument('-p', '--ports', help='Ports to scan (e.g., 80,443 or 1-1000)')
    parser.add_argument('--top-ports', type=int, help='Scan top N common ports')
    parser.add_argument('-t', '--threads', type=int, default=50, help='Number of threads (default: 50)')
    parser.add_argument('--timeout', type=float, default=1.0, help='Timeout in seconds (default: 1.0)')
    parser.add_argument('-o', '--output', help='Output file')
    args = parser.parse_args()

    banner("Port Scanner")

    scanner = PortScanner(args.target, timeout=args.timeout)

    ip = scanner.resolve_host()
    if not ip:
        error(f"Could not resolve {args.target}")
        sys.exit(1)

    info(f"Target: {args.target} ({ip})")

    if args.ports:
        ports = parse_ports(args.ports)
    elif args.top_ports:
        ports = TOP_PORTS[:args.top_ports] if args.top_ports < len(TOP_PORTS) else TOP_PORTS
    else:
        ports = TOP_PORTS

    info(f"Scanning {len(ports)} ports with {args.threads} threads...")

    results = scanner.scan(ports, threads=args.threads)

    print()
    if results:
        print(f"{'PORT':<10}{'STATE':<10}{'SERVICE':<15}{'BANNER'}")
        print("-" * 60)
        for r in results:
            banner_str = r['banner'][:30] + '...' if r['banner'] and len(r['banner']) > 30 else (r['banner'] or '')
            print(f"{r['port']:<10}{'open':<10}{r['service']:<15}{banner_str}")

        success(f"\n{len(results)} open port(s) found")
    else:
        warning("No open ports found")

    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump({'target': args.target, 'ip': ip, 'ports': results}, f, indent=2)
        success(f"Results saved to {args.output}")


if __name__ == '__main__':
    main()
