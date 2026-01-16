#!/usr/bin/env python3
"""
Contract Analyzer - Static analysis for Solidity smart contracts

USAGE:
    python contract_analyzer.py <source_file_or_address> [options]

EXAMPLES:
    python contract_analyzer.py contract.sol
    python contract_analyzer.py 0x742d35Cc6634C0532925a3b844Bc454e4438f44e --network ethereum
    python contract_analyzer.py contract.sol --preset deep -o results.json
"""

import sys
import os
import re
import json
import argparse
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from enum import Enum

sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import success, error, warning, info, banner

# Severity levels
class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

@dataclass
class Finding:
    title: str
    severity: str
    description: str
    line: int = 0
    code_snippet: str = ""
    recommendation: str = ""

@dataclass
class AnalysisResult:
    target: str
    findings: List[Finding] = field(default_factory=list)
    stats: Dict = field(default_factory=dict)

# Vulnerability patterns for Solidity
VULN_PATTERNS = {
    'reentrancy': {
        'pattern': r'\.call\s*\{?\s*value\s*:',
        'severity': Severity.CRITICAL,
        'title': 'Potential Reentrancy',
        'description': 'External call with value transfer before state update. Attacker can re-enter.',
        'recommendation': 'Use checks-effects-interactions pattern or ReentrancyGuard.'
    },
    'reentrancy_call': {
        'pattern': r'\.call\s*\(',
        'severity': Severity.HIGH,
        'title': 'Low-level call detected',
        'description': 'Low-level call can be exploited for reentrancy if not handled properly.',
        'recommendation': 'Prefer higher-level calls or use ReentrancyGuard.'
    },
    'tx_origin': {
        'pattern': r'tx\.origin',
        'severity': Severity.HIGH,
        'title': 'tx.origin Authentication',
        'description': 'Using tx.origin for authorization is vulnerable to phishing attacks.',
        'recommendation': 'Use msg.sender instead of tx.origin for authentication.'
    },
    'selfdestruct': {
        'pattern': r'selfdestruct\s*\(',
        'severity': Severity.HIGH,
        'title': 'Selfdestruct Present',
        'description': 'Contract can be destroyed, sending remaining ETH to specified address.',
        'recommendation': 'Ensure selfdestruct is properly protected with access control.'
    },
    'delegatecall': {
        'pattern': r'\.delegatecall\s*\(',
        'severity': Severity.HIGH,
        'title': 'Delegatecall Usage',
        'description': 'Delegatecall executes code in caller context. Can be dangerous with user input.',
        'recommendation': 'Validate target address and avoid user-controlled delegatecall targets.'
    },
    'unchecked_return': {
        'pattern': r'\.send\s*\(|\.transfer\s*\(',
        'severity': Severity.MEDIUM,
        'title': 'Unchecked Return Value',
        'description': 'Return value of send/transfer should be checked.',
        'recommendation': 'Check return value or use call with proper error handling.'
    },
    'timestamp_dependency': {
        'pattern': r'block\.timestamp|now',
        'severity': Severity.LOW,
        'title': 'Timestamp Dependency',
        'description': 'Block timestamp can be manipulated by miners within ~15 seconds.',
        'recommendation': 'Avoid using block.timestamp for critical logic or randomness.'
    },
    'block_number': {
        'pattern': r'block\.number',
        'severity': Severity.LOW,
        'title': 'Block Number Dependency',
        'description': 'Block number can be predicted and is not suitable for randomness.',
        'recommendation': 'Use Chainlink VRF or commit-reveal for randomness.'
    },
    'arbitrary_send': {
        'pattern': r'\.call\{value:\s*\w+\}\s*\(\s*""\s*\)',
        'severity': Severity.HIGH,
        'title': 'Arbitrary ETH Send',
        'description': 'Sending ETH to potentially untrusted address.',
        'recommendation': 'Validate recipient address and use pull payment pattern.'
    },
    'unprotected_function': {
        'pattern': r'function\s+\w+\s*\([^)]*\)\s+(public|external)\s+(?!view|pure)',
        'severity': Severity.INFO,
        'title': 'Public/External State-Changing Function',
        'description': 'State-changing function without explicit access control.',
        'recommendation': 'Consider adding access control modifiers (onlyOwner, etc.).'
    },
    'integer_overflow': {
        'pattern': r'(\+\+|\-\-|\+=|\-=|\*=)',
        'severity': Severity.MEDIUM,
        'title': 'Potential Integer Overflow/Underflow',
        'description': 'Arithmetic operation without SafeMath (if Solidity < 0.8.0).',
        'recommendation': 'Use Solidity 0.8+ or SafeMath library.'
    },
    'assembly': {
        'pattern': r'assembly\s*\{',
        'severity': Severity.INFO,
        'title': 'Inline Assembly',
        'description': 'Inline assembly bypasses Solidity safety checks.',
        'recommendation': 'Review assembly code carefully for security issues.'
    },
    'ecrecover': {
        'pattern': r'ecrecover\s*\(',
        'severity': Severity.MEDIUM,
        'title': 'ecrecover Usage',
        'description': 'ecrecover can return zero address for invalid signatures.',
        'recommendation': 'Check that recovered address is not zero and matches expected.'
    },
    'shadowing': {
        'pattern': r'(uint|int|address|bool|string|bytes)\s+(owner|balance|sender)',
        'severity': Severity.LOW,
        'title': 'Potential Variable Shadowing',
        'description': 'Common variable names that might shadow state variables.',
        'recommendation': 'Use unique variable names to avoid shadowing.'
    },
    'hardcoded_address': {
        'pattern': r'0x[a-fA-F0-9]{40}',
        'severity': Severity.INFO,
        'title': 'Hardcoded Address',
        'description': 'Hardcoded address found in contract.',
        'recommendation': 'Consider using configurable addresses for flexibility.'
    },
    'private_visibility': {
        'pattern': r'(private|internal)\s+\w+\s+password|secret|key',
        'severity': Severity.HIGH,
        'title': 'Sensitive Data in Storage',
        'description': 'Private variables are still visible on blockchain.',
        'recommendation': 'Never store sensitive data on-chain, even as private.'
    },
}

# DeFi-specific patterns
DEFI_PATTERNS = {
    'flash_loan_callback': {
        'pattern': r'(executeOperation|onFlashLoan|flashLoanSimple)',
        'severity': Severity.INFO,
        'title': 'Flash Loan Callback',
        'description': 'Flash loan callback function detected.',
        'recommendation': 'Ensure proper validation of loan parameters and sender.'
    },
    'price_oracle': {
        'pattern': r'(getPrice|latestAnswer|latestRoundData|getReserves)',
        'severity': Severity.MEDIUM,
        'title': 'Price Oracle Usage',
        'description': 'External price feed detected. Verify oracle manipulation resistance.',
        'recommendation': 'Use TWAP or multiple oracles, check for stale data.'
    },
    'slippage': {
        'pattern': r'(amountOutMin|minAmountOut|deadline)',
        'severity': Severity.INFO,
        'title': 'Slippage Protection',
        'description': 'Slippage protection parameters detected.',
        'recommendation': 'Ensure slippage tolerance is reasonable and enforced.'
    },
    'approval': {
        'pattern': r'\.approve\s*\(\s*\w+\s*,\s*(type\(uint256\)\.max|2\*\*256|uint256\(-1\))',
        'severity': Severity.MEDIUM,
        'title': 'Infinite Approval',
        'description': 'Unlimited token approval detected.',
        'recommendation': 'Consider using exact approval amounts or permit.'
    },
}


class ContractAnalyzer:
    def __init__(self, network: str = "ethereum", api_key: str = None):
        self.network = network
        self.api_key = api_key
        self.source_code = ""
        self.findings: List[Finding] = []
        self.lines: List[str] = []

        # API endpoints for fetching contract source
        self.explorers = {
            'ethereum': 'https://api.etherscan.io/api',
            'bsc': 'https://api.bscscan.com/api',
            'polygon': 'https://api.polygonscan.com/api',
            'arbitrum': 'https://api.arbiscan.io/api',
            'optimism': 'https://api-optimistic.etherscan.io/api',
            'avalanche': 'https://api.snowtrace.io/api',
        }

    def load_source(self, target: str) -> bool:
        """Load source code from file or address."""
        # Check if file
        if os.path.isfile(target):
            with open(target, 'r') as f:
                self.source_code = f.read()
            info(f"Loaded source from file: {target}")
            self.lines = self.source_code.split('\n')
            return True

        # Check if address
        if re.match(r'^0x[a-fA-F0-9]{40}$', target):
            return self.fetch_from_explorer(target)

        error(f"Invalid target: {target}")
        return False

    def fetch_from_explorer(self, address: str) -> bool:
        """Fetch contract source from block explorer."""
        if self.network not in self.explorers:
            error(f"Unsupported network: {self.network}")
            return False

        try:
            import urllib.request
            import urllib.parse

            base_url = self.explorers[self.network]
            params = {
                'module': 'contract',
                'action': 'getsourcecode',
                'address': address,
            }
            if self.api_key:
                params['apikey'] = self.api_key

            url = f"{base_url}?{urllib.parse.urlencode(params)}"

            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode())

            if data['status'] == '1' and data['result']:
                source = data['result'][0].get('SourceCode', '')
                if source:
                    # Handle JSON-encoded source (multiple files)
                    if source.startswith('{'):
                        try:
                            source_json = json.loads(source[1:-1] if source.startswith('{{') else source)
                            sources = source_json.get('sources', {})
                            self.source_code = '\n'.join(
                                s.get('content', '') for s in sources.values()
                            )
                        except:
                            self.source_code = source
                    else:
                        self.source_code = source

                    self.lines = self.source_code.split('\n')
                    info(f"Fetched source for {address} from {self.network}")
                    return True
                else:
                    warning(f"Contract not verified: {address}")
                    return False
            else:
                error(f"API error: {data.get('message', 'Unknown error')}")
                return False

        except Exception as e:
            error(f"Failed to fetch source: {e}")
            return False

    def find_line_number(self, match_pos: int) -> int:
        """Find line number for a match position."""
        text_before = self.source_code[:match_pos]
        return text_before.count('\n') + 1

    def get_code_snippet(self, line_num: int, context: int = 2) -> str:
        """Get code snippet around a line."""
        start = max(0, line_num - context - 1)
        end = min(len(self.lines), line_num + context)
        snippet_lines = []
        for i in range(start, end):
            marker = ">>>" if i == line_num - 1 else "   "
            snippet_lines.append(f"{marker} {i+1}: {self.lines[i]}")
        return '\n'.join(snippet_lines)

    def check_pattern(self, name: str, pattern_info: dict):
        """Check for a vulnerability pattern."""
        pattern = pattern_info['pattern']
        for match in re.finditer(pattern, self.source_code, re.IGNORECASE):
            line_num = self.find_line_number(match.start())
            snippet = self.get_code_snippet(line_num)

            finding = Finding(
                title=pattern_info['title'],
                severity=pattern_info['severity'].value,
                description=pattern_info['description'],
                line=line_num,
                code_snippet=snippet,
                recommendation=pattern_info['recommendation']
            )
            self.findings.append(finding)

    def analyze(self, target: str, checks: List[str] = None, include_defi: bool = True) -> AnalysisResult:
        """Run analysis on target."""
        self.findings = []

        if not self.load_source(target):
            return AnalysisResult(target=target, findings=[], stats={'error': 'Failed to load source'})

        info(f"Analyzing {len(self.lines)} lines of code...")

        # Determine which patterns to check
        patterns_to_check = {}

        if checks is None or 'all' in checks:
            patterns_to_check.update(VULN_PATTERNS)
            if include_defi:
                patterns_to_check.update(DEFI_PATTERNS)
        else:
            for check in checks:
                if check in VULN_PATTERNS:
                    patterns_to_check[check] = VULN_PATTERNS[check]
                if check in DEFI_PATTERNS:
                    patterns_to_check[check] = DEFI_PATTERNS[check]

        # Run checks
        for name, pattern_info in patterns_to_check.items():
            self.check_pattern(name, pattern_info)

        # Deduplicate findings by line
        seen = set()
        unique_findings = []
        for f in self.findings:
            key = (f.title, f.line)
            if key not in seen:
                seen.add(key)
                unique_findings.append(f)

        self.findings = unique_findings

        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
        self.findings.sort(key=lambda x: severity_order.get(x.severity, 5))

        # Stats
        stats = {
            'total_lines': len(self.lines),
            'total_findings': len(self.findings),
            'critical': sum(1 for f in self.findings if f.severity == 'CRITICAL'),
            'high': sum(1 for f in self.findings if f.severity == 'HIGH'),
            'medium': sum(1 for f in self.findings if f.severity == 'MEDIUM'),
            'low': sum(1 for f in self.findings if f.severity == 'LOW'),
            'info': sum(1 for f in self.findings if f.severity == 'INFO'),
        }

        return AnalysisResult(target=target, findings=self.findings, stats=stats)

    def print_results(self, result: AnalysisResult):
        """Print analysis results."""
        print()
        banner("CONTRACT ANALYSIS RESULTS")
        print()

        info(f"Target: {result.target}")
        info(f"Lines analyzed: {result.stats.get('total_lines', 0)}")
        print()

        # Summary
        stats = result.stats
        print(f"  CRITICAL: {stats.get('critical', 0)}")
        print(f"  HIGH:     {stats.get('high', 0)}")
        print(f"  MEDIUM:   {stats.get('medium', 0)}")
        print(f"  LOW:      {stats.get('low', 0)}")
        print(f"  INFO:     {stats.get('info', 0)}")
        print()

        if not result.findings:
            success("No issues found!")
            return

        # Detailed findings
        for i, finding in enumerate(result.findings, 1):
            severity_colors = {
                'CRITICAL': '\033[91m',  # Red
                'HIGH': '\033[93m',      # Yellow
                'MEDIUM': '\033[94m',    # Blue
                'LOW': '\033[96m',       # Cyan
                'INFO': '\033[90m',      # Gray
            }
            reset = '\033[0m'
            color = severity_colors.get(finding.severity, '')

            print(f"{color}[{finding.severity}]{reset} {finding.title}")
            print(f"  Line: {finding.line}")
            print(f"  {finding.description}")
            if finding.code_snippet:
                print(f"\n{finding.code_snippet}\n")
            print(f"  Recommendation: {finding.recommendation}")
            print("-" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Smart Contract Static Analyzer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python contract_analyzer.py contract.sol
  python contract_analyzer.py 0x742d35Cc6634C0532925a3b844Bc454e4438f44e --network ethereum
  python contract_analyzer.py contract.sol --checks reentrancy,tx_origin
  python contract_analyzer.py contract.sol --preset deep -o results.json
        """
    )

    parser.add_argument('target', help='Solidity file or contract address')
    parser.add_argument('--network', '-n', default='ethereum',
                       choices=['ethereum', 'bsc', 'polygon', 'arbitrum', 'optimism', 'avalanche'],
                       help='Blockchain network (default: ethereum)')
    parser.add_argument('--api-key', '-k', help='Block explorer API key')
    parser.add_argument('--checks', '-c', help='Comma-separated list of checks (or "all")')
    parser.add_argument('--preset', '-p', choices=['quick', 'standard', 'deep'],
                       default='standard', help='Analysis preset')
    parser.add_argument('--no-defi', action='store_true', help='Skip DeFi-specific checks')
    parser.add_argument('--output', '-o', help='Output JSON file')
    parser.add_argument('--quiet', '-q', action='store_true', help='Minimal output')

    args = parser.parse_args()

    if not args.quiet:
        banner("Contract Analyzer")

    # Determine checks based on preset
    checks = None
    if args.checks:
        checks = [c.strip() for c in args.checks.split(',')]
    elif args.preset == 'quick':
        checks = ['reentrancy', 'tx_origin', 'selfdestruct', 'delegatecall']
    elif args.preset == 'deep':
        checks = None  # All checks
    # standard = default patterns

    analyzer = ContractAnalyzer(network=args.network, api_key=args.api_key)
    result = analyzer.analyze(args.target, checks=checks, include_defi=not args.no_defi)

    if not args.quiet:
        analyzer.print_results(result)

    # Output JSON
    if args.output:
        output_data = {
            'target': result.target,
            'network': args.network,
            'stats': result.stats,
            'findings': [asdict(f) for f in result.findings]
        }
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        success(f"Results saved to {args.output}")

    # Exit code based on findings
    if result.stats.get('critical', 0) > 0 or result.stats.get('high', 0) > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
