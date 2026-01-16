#!/usr/bin/env python3
"""
Token Analyzer - ERC20/ERC721 token analysis and honeypot detection

USAGE:
    python token_analyzer.py <token_address> [options]

EXAMPLES:
    python token_analyzer.py 0xdAC17F958D2ee523a2206206994597C13D831ec7 --network ethereum
    python token_analyzer.py 0x... --check-honeypot
"""

import sys
import json
import argparse
import urllib.request
import urllib.parse
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import success, error, warning, info, banner

@dataclass
class TokenInfo:
    address: str
    name: str = ""
    symbol: str = ""
    decimals: int = 18
    total_supply: str = ""
    owner: str = ""
    is_verified: bool = False
    is_proxy: bool = False
    holders_count: int = 0

@dataclass
class HoneypotResult:
    is_honeypot: bool = False
    buy_tax: float = 0.0
    sell_tax: float = 0.0
    transfer_pausable: bool = False
    can_blacklist: bool = False
    hidden_owner: bool = False
    anti_whale: bool = False
    warnings: List[str] = field(default_factory=list)

# Suspicious function signatures
SUSPICIOUS_FUNCTIONS = {
    'setFee': 'Can change transaction fees',
    'setTax': 'Can change tax rates',
    'blacklist': 'Can blacklist addresses',
    'pause': 'Can pause transfers',
    'setMaxTx': 'Can limit transaction size',
    'setMaxWallet': 'Can limit wallet holdings',
    'renounceOwnership': 'Ownership functions present',
    'excludeFromFee': 'Fee exclusions possible',
    'includeInFee': 'Fee inclusions possible',
    '_burn': 'Can burn tokens',
    'mint': 'Can mint new tokens',
}

# Known honeypot patterns in bytecode
HONEYPOT_BYTECODE_PATTERNS = [
    ('0x23b872dd', 'transferFrom - check for modifications'),
    ('0xa9059cbb', 'transfer - check for modifications'),
    ('0x095ea7b3', 'approve - check for modifications'),
]


class TokenAnalyzer:
    def __init__(self, network: str = "ethereum", api_key: str = None):
        self.network = network
        self.api_key = api_key

        self.rpc_endpoints = {
            'ethereum': 'https://eth.llamarpc.com',
            'bsc': 'https://bsc-dataseed.binance.org',
            'polygon': 'https://polygon-rpc.com',
            'arbitrum': 'https://arb1.arbitrum.io/rpc',
        }

        self.explorers = {
            'ethereum': 'https://api.etherscan.io/api',
            'bsc': 'https://api.bscscan.com/api',
            'polygon': 'https://api.polygonscan.com/api',
            'arbitrum': 'https://api.arbiscan.io/api',
        }

    def eth_call(self, to: str, data: str) -> Optional[str]:
        """Make an eth_call to the RPC endpoint."""
        if self.network not in self.rpc_endpoints:
            return None

        payload = {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [{"to": to, "data": data}, "latest"],
            "id": 1
        }

        try:
            req = urllib.request.Request(
                self.rpc_endpoints[self.network],
                data=json.dumps(payload).encode(),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                return result.get('result')
        except Exception as e:
            return None

    def get_token_info(self, address: str) -> TokenInfo:
        """Get basic token information."""
        token = TokenInfo(address=address)

        # name()
        result = self.eth_call(address, '0x06fdde03')
        if result and len(result) > 2:
            try:
                # Decode string from ABI
                token.name = bytes.fromhex(result[2:]).decode('utf-8', errors='ignore').strip('\x00').strip()
            except:
                pass

        # symbol()
        result = self.eth_call(address, '0x95d89b41')
        if result and len(result) > 2:
            try:
                token.symbol = bytes.fromhex(result[2:]).decode('utf-8', errors='ignore').strip('\x00').strip()
            except:
                pass

        # decimals()
        result = self.eth_call(address, '0x313ce567')
        if result and len(result) > 2:
            try:
                token.decimals = int(result, 16)
            except:
                pass

        # totalSupply()
        result = self.eth_call(address, '0x18160ddd')
        if result and len(result) > 2:
            try:
                supply = int(result, 16)
                token.total_supply = str(supply / (10 ** token.decimals))
            except:
                pass

        # owner()
        result = self.eth_call(address, '0x8da5cb5b')
        if result and len(result) >= 66:
            token.owner = '0x' + result[-40:]

        return token

    def check_honeypot_patterns(self, address: str) -> HoneypotResult:
        """Check for common honeypot patterns."""
        result = HoneypotResult()

        # Try to get source code and ABI from explorer
        if self.network not in self.explorers:
            return result

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
                contract_data = data['result'][0]
                source = contract_data.get('SourceCode', '').lower()
                abi = contract_data.get('ABI', '')

                result.is_verified = bool(source)

                # Check for suspicious patterns in source
                if source:
                    if 'blacklist' in source or 'blocklist' in source:
                        result.can_blacklist = True
                        result.warnings.append('Contract has blacklist functionality')

                    if 'pause' in source and 'whennotpaused' in source:
                        result.transfer_pausable = True
                        result.warnings.append('Transfers can be paused')

                    if 'maxwallet' in source or 'maxtx' in source:
                        result.anti_whale = True
                        result.warnings.append('Anti-whale mechanisms present')

                    if 'settax' in source or 'setfee' in source:
                        result.warnings.append('Fees can be modified by owner')

                    if '_isexcludedfromfee' in source:
                        result.warnings.append('Some addresses excluded from fees')

                    # Check for hidden owner patterns
                    if 'renounceownership' not in source and 'owner' in source:
                        result.hidden_owner = True
                        result.warnings.append('Ownership not renounced')

                # Analyze ABI for suspicious functions
                if abi and abi != 'Contract source code not verified':
                    try:
                        abi_json = json.loads(abi)
                        for item in abi_json:
                            if item.get('type') == 'function':
                                func_name = item.get('name', '').lower()
                                for suspicious, desc in SUSPICIOUS_FUNCTIONS.items():
                                    if suspicious.lower() in func_name:
                                        result.warnings.append(f'{desc}: {item.get("name")}()')
                    except:
                        pass

        except Exception as e:
            result.warnings.append(f'Analysis error: {str(e)}')

        # Determine if likely honeypot
        if result.can_blacklist and result.transfer_pausable:
            result.is_honeypot = True
        elif len(result.warnings) >= 4:
            result.is_honeypot = True

        return result

    def analyze(self, address: str, check_honeypot: bool = True) -> Dict:
        """Full token analysis."""
        info(f"Analyzing token: {address}")

        token_info = self.get_token_info(address)
        honeypot = HoneypotResult()

        if check_honeypot:
            honeypot = self.check_honeypot_patterns(address)

        return {
            'token': asdict(token_info),
            'honeypot': asdict(honeypot),
            'network': self.network
        }

    def print_results(self, results: Dict):
        """Print analysis results."""
        print()
        banner("TOKEN ANALYSIS")
        print()

        token = results['token']
        honeypot = results['honeypot']

        info(f"Address: {token['address']}")
        info(f"Name: {token['name'] or 'Unknown'}")
        info(f"Symbol: {token['symbol'] or 'Unknown'}")
        info(f"Decimals: {token['decimals']}")
        info(f"Total Supply: {token['total_supply'] or 'Unknown'}")
        info(f"Owner: {token['owner'] or 'Unknown'}")

        print()
        if honeypot['is_honeypot']:
            error("HONEYPOT DETECTED!")
        else:
            success("No obvious honeypot patterns")

        if honeypot['warnings']:
            print()
            warning("Warnings:")
            for w in honeypot['warnings']:
                print(f"  - {w}")

        print()
        info(f"Blacklist: {'Yes' if honeypot['can_blacklist'] else 'No'}")
        info(f"Pausable: {'Yes' if honeypot['transfer_pausable'] else 'No'}")
        info(f"Anti-whale: {'Yes' if honeypot['anti_whale'] else 'No'}")


def main():
    parser = argparse.ArgumentParser(description='ERC20/ERC721 Token Analyzer')
    parser.add_argument('address', help='Token contract address')
    parser.add_argument('--network', '-n', default='ethereum',
                       choices=['ethereum', 'bsc', 'polygon', 'arbitrum'],
                       help='Network (default: ethereum)')
    parser.add_argument('--api-key', '-k', help='Block explorer API key')
    parser.add_argument('--check-honeypot', '-c', action='store_true', default=True,
                       help='Check for honeypot patterns')
    parser.add_argument('--output', '-o', help='Output JSON file')
    parser.add_argument('--quiet', '-q', action='store_true')

    args = parser.parse_args()

    if not args.quiet:
        banner("Token Analyzer")

    analyzer = TokenAnalyzer(network=args.network, api_key=args.api_key)
    results = analyzer.analyze(args.address, check_honeypot=args.check_honeypot)

    if not args.quiet:
        analyzer.print_results(results)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        success(f"Results saved to {args.output}")

    if results['honeypot']['is_honeypot']:
        sys.exit(1)


if __name__ == '__main__':
    main()
