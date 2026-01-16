#!/usr/bin/env python3
"""
Rugpull Scanner - Detect potential rugpull patterns in DeFi contracts

USAGE:
    python rugpull_scanner.py <contract_address> [options]

EXAMPLES:
    python rugpull_scanner.py 0x... --network bsc
    python rugpull_scanner.py contract.sol --local
"""

import sys
import os
import re
import json
import argparse
import urllib.request
import urllib.parse
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from enum import Enum

sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import success, error, warning, info, banner

class RiskLevel(Enum):
    SAFE = "SAFE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class RiskFinding:
    category: str
    description: str
    severity: str
    details: str = ""

@dataclass
class RugpullAnalysis:
    address: str
    risk_level: str = "UNKNOWN"
    risk_score: int = 0
    findings: List[RiskFinding] = field(default_factory=list)
    is_verified: bool = False
    owner_renounced: bool = False
    liquidity_locked: bool = False

# Rugpull patterns to detect
RUGPULL_PATTERNS = {
    # Ownership control
    'hidden_mint': {
        'pattern': r'function\s+\w*mint\w*\s*\([^)]*\)\s+(internal|private)',
        'category': 'Token Supply',
        'description': 'Hidden mint function that can inflate supply',
        'severity': RiskLevel.HIGH
    },
    'unlimited_mint': {
        'pattern': r'_mint\s*\([^)]+,[^)]+\)|mint\s*\([^)]*\)\s+external',
        'category': 'Token Supply',
        'description': 'Mint function with potential unlimited minting',
        'severity': RiskLevel.HIGH
    },
    'owner_only_transfer': {
        'pattern': r'onlyOwner[^}]*transfer',
        'category': 'Transfer Control',
        'description': 'Owner can control transfers',
        'severity': RiskLevel.HIGH
    },

    # Trading restrictions
    'trading_enable': {
        'pattern': r'(tradingEnabled|canTrade|tradingActive)\s*=\s*(false|true)',
        'category': 'Trading Control',
        'description': 'Trading can be enabled/disabled by owner',
        'severity': RiskLevel.HIGH
    },
    'max_tx_changeable': {
        'pattern': r'function\s+setMaxTx|_maxTxAmount\s*=',
        'category': 'Trading Control',
        'description': 'Maximum transaction can be modified',
        'severity': RiskLevel.MEDIUM
    },
    'cooldown': {
        'pattern': r'cooldown|_cooldownTime',
        'category': 'Trading Control',
        'description': 'Cooldown mechanism that can prevent selling',
        'severity': RiskLevel.MEDIUM
    },

    # Fee manipulation
    'changeable_fee': {
        'pattern': r'function\s+set(Tax|Fee|Buy|Sell)\w*\s*\([^)]*uint',
        'category': 'Fee Control',
        'description': 'Fees can be changed after deployment',
        'severity': RiskLevel.HIGH
    },
    'high_fee_possible': {
        'pattern': r'(sellFee|buyFee|_tax)\s*>\s*[2-9][0-9]|require\([^)]*<\s*(50|60|70|80|90|99)',
        'category': 'Fee Control',
        'description': 'Fees can be set very high (potential 99% sell tax)',
        'severity': RiskLevel.CRITICAL
    },

    # Blacklist/Whitelist
    'blacklist': {
        'pattern': r'(blacklist|blocklist|isBlacklisted|_isBlocked)',
        'category': 'Access Control',
        'description': 'Blacklist functionality can prevent selling',
        'severity': RiskLevel.HIGH
    },
    'whitelist_only': {
        'pattern': r'(onlyWhitelisted|isWhitelisted|_whitelist)',
        'category': 'Access Control',
        'description': 'Whitelist-only trading possible',
        'severity': RiskLevel.MEDIUM
    },

    # Liquidity manipulation
    'remove_liquidity': {
        'pattern': r'removeLiquidity|withdrawLiquidity',
        'category': 'Liquidity',
        'description': 'Liquidity can be removed by owner',
        'severity': RiskLevel.CRITICAL
    },
    'add_liquidity_owner': {
        'pattern': r'onlyOwner[^}]*addLiquidity',
        'category': 'Liquidity',
        'description': 'Only owner can add liquidity',
        'severity': RiskLevel.MEDIUM
    },

    # Proxy/Upgrade patterns
    'upgradeable': {
        'pattern': r'(Upgradeable|upgradeTo|_implementation)',
        'category': 'Contract Control',
        'description': 'Contract is upgradeable - code can change',
        'severity': RiskLevel.HIGH
    },
    'delegatecall': {
        'pattern': r'\.delegatecall\(',
        'category': 'Contract Control',
        'description': 'Delegatecall can execute arbitrary code',
        'severity': RiskLevel.HIGH
    },

    # External calls
    'external_call_balance': {
        'pattern': r'\.call\{value:\s*address\(this\)\.balance',
        'category': 'Fund Control',
        'description': 'Can drain contract balance to external address',
        'severity': RiskLevel.CRITICAL
    },

    # Hidden functions
    'selfdestruct': {
        'pattern': r'selfdestruct\s*\(',
        'category': 'Contract Control',
        'description': 'Contract can be destroyed',
        'severity': RiskLevel.CRITICAL
    },
}

# Positive patterns (reduce risk)
SAFE_PATTERNS = {
    'renounced': r'renounceOwnership|owner\s*=\s*address\(0\)',
    'locked_liquidity': r'lock|timelock|vestingPeriod',
    'audit_comment': r'audited|audit|certik|hacken|slowmist',
}


class RugpullScanner:
    def __init__(self, network: str = "ethereum", api_key: str = None):
        self.network = network
        self.api_key = api_key
        self.source_code = ""

        self.explorers = {
            'ethereum': 'https://api.etherscan.io/api',
            'bsc': 'https://api.bscscan.com/api',
            'polygon': 'https://api.polygonscan.com/api',
            'arbitrum': 'https://api.arbiscan.io/api',
        }

    def load_source(self, target: str) -> bool:
        """Load source from file or fetch from explorer."""
        if os.path.isfile(target):
            with open(target, 'r') as f:
                self.source_code = f.read()
            return True

        if re.match(r'^0x[a-fA-F0-9]{40}$', target):
            return self.fetch_source(target)

        return False

    def fetch_source(self, address: str) -> bool:
        """Fetch contract source from explorer."""
        if self.network not in self.explorers:
            return False

        try:
            params = {
                'module': 'contract',
                'action': 'getsourcecode',
                'address': address,
            }
            if self.api_key:
                params['apikey'] = self.api_key

            url = f"{self.explorers[self.network]}?{urllib.parse.urlencode(params)}"

            with urllib.request.urlopen(url, timeout=15) as resp:
                data = json.loads(resp.read().decode())

            if data['status'] == '1' and data['result']:
                source = data['result'][0].get('SourceCode', '')
                if source:
                    if source.startswith('{'):
                        try:
                            src_json = json.loads(source[1:-1] if source.startswith('{{') else source)
                            sources = src_json.get('sources', {})
                            self.source_code = '\n'.join(s.get('content', '') for s in sources.values())
                        except:
                            self.source_code = source
                    else:
                        self.source_code = source
                    return True

        except Exception as e:
            error(f"Failed to fetch source: {e}")

        return False

    def scan(self, target: str) -> RugpullAnalysis:
        """Scan for rugpull patterns."""
        analysis = RugpullAnalysis(address=target)

        if not self.load_source(target):
            analysis.findings.append(RiskFinding(
                category="Verification",
                description="Contract source not available",
                severity=RiskLevel.HIGH.value,
                details="Unverified contracts are high risk"
            ))
            analysis.risk_level = RiskLevel.HIGH.value
            analysis.risk_score = 80
            return analysis

        analysis.is_verified = True
        source_lower = self.source_code.lower()

        # Check for rugpull patterns
        for name, pattern_info in RUGPULL_PATTERNS.items():
            matches = re.findall(pattern_info['pattern'], self.source_code, re.IGNORECASE)
            if matches:
                analysis.findings.append(RiskFinding(
                    category=pattern_info['category'],
                    description=pattern_info['description'],
                    severity=pattern_info['severity'].value,
                    details=f"Found {len(matches)} occurrence(s)"
                ))

        # Check for safe patterns
        for name, pattern in SAFE_PATTERNS.items():
            if re.search(pattern, self.source_code, re.IGNORECASE):
                if name == 'renounced':
                    analysis.owner_renounced = True
                elif name == 'locked_liquidity':
                    analysis.liquidity_locked = True

        # Calculate risk score
        analysis.risk_score = self.calculate_risk_score(analysis)
        analysis.risk_level = self.determine_risk_level(analysis.risk_score)

        return analysis

    def calculate_risk_score(self, analysis: RugpullAnalysis) -> int:
        """Calculate risk score 0-100."""
        score = 0

        severity_weights = {
            'CRITICAL': 25,
            'HIGH': 15,
            'MEDIUM': 8,
            'LOW': 3,
        }

        for finding in analysis.findings:
            score += severity_weights.get(finding.severity, 5)

        # Reductions for safe patterns
        if analysis.owner_renounced:
            score -= 20
        if analysis.liquidity_locked:
            score -= 15
        if analysis.is_verified:
            score -= 10

        return max(0, min(100, score))

    def determine_risk_level(self, score: int) -> str:
        """Determine risk level from score."""
        if score >= 70:
            return RiskLevel.CRITICAL.value
        elif score >= 50:
            return RiskLevel.HIGH.value
        elif score >= 30:
            return RiskLevel.MEDIUM.value
        elif score >= 10:
            return RiskLevel.LOW.value
        return RiskLevel.SAFE.value

    def print_results(self, analysis: RugpullAnalysis):
        """Print scan results."""
        print()
        banner("RUGPULL SCAN RESULTS")
        print()

        info(f"Target: {analysis.address}")
        info(f"Verified: {'Yes' if analysis.is_verified else 'No'}")
        info(f"Owner Renounced: {'Yes' if analysis.owner_renounced else 'No'}")
        info(f"Liquidity Locked: {'Yes' if analysis.liquidity_locked else 'Unknown'}")
        print()

        # Risk level with color
        level = analysis.risk_level
        score = analysis.risk_score

        if level == 'CRITICAL':
            error(f"RISK LEVEL: {level} ({score}/100)")
        elif level == 'HIGH':
            warning(f"RISK LEVEL: {level} ({score}/100)")
        elif level == 'MEDIUM':
            warning(f"RISK LEVEL: {level} ({score}/100)")
        else:
            success(f"RISK LEVEL: {level} ({score}/100)")

        if analysis.findings:
            print()
            info(f"Findings ({len(analysis.findings)}):")
            print()

            # Group by category
            by_category = {}
            for f in analysis.findings:
                by_category.setdefault(f.category, []).append(f)

            for category, findings in by_category.items():
                print(f"  [{category}]")
                for f in findings:
                    severity_marker = {
                        'CRITICAL': '\033[91m[!]\033[0m',
                        'HIGH': '\033[93m[!]\033[0m',
                        'MEDIUM': '\033[94m[-]\033[0m',
                        'LOW': '\033[96m[~]\033[0m',
                    }.get(f.severity, '[*]')
                    print(f"    {severity_marker} {f.description}")
                print()
        else:
            print()
            success("No rugpull patterns detected!")


def main():
    parser = argparse.ArgumentParser(description='Rugpull Pattern Scanner')
    parser.add_argument('target', help='Contract address or file')
    parser.add_argument('--network', '-n', default='ethereum',
                       choices=['ethereum', 'bsc', 'polygon', 'arbitrum'])
    parser.add_argument('--api-key', '-k', help='Explorer API key')
    parser.add_argument('--output', '-o', help='Output JSON file')
    parser.add_argument('--quiet', '-q', action='store_true')

    args = parser.parse_args()

    if not args.quiet:
        banner("Rugpull Scanner")

    scanner = RugpullScanner(network=args.network, api_key=args.api_key)
    analysis = scanner.scan(args.target)

    if not args.quiet:
        scanner.print_results(analysis)

    if args.output:
        output_data = {
            'address': analysis.address,
            'risk_level': analysis.risk_level,
            'risk_score': analysis.risk_score,
            'is_verified': analysis.is_verified,
            'owner_renounced': analysis.owner_renounced,
            'liquidity_locked': analysis.liquidity_locked,
            'findings': [asdict(f) for f in analysis.findings]
        }
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        success(f"Results saved to {args.output}")

    # Exit code based on risk
    if analysis.risk_level in ('CRITICAL', 'HIGH'):
        sys.exit(1)


if __name__ == '__main__':
    main()
