#!/usr/bin/env python3
"""
Address Profiler - Blockchain address analysis and profiling

USAGE:
    python address_profiler.py <address> [options]

EXAMPLES:
    python address_profiler.py 0x742d35Cc6634C0532925a3b844Bc454e4438f44e
    python address_profiler.py 0x... --network bsc --tx-history
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
class AddressProfile:
    address: str
    type: str = "unknown"  # eoa, contract, multisig
    balance_eth: str = "0"
    tx_count: int = 0
    first_seen: str = ""
    last_seen: str = ""
    is_contract: bool = False
    contract_name: str = ""
    labels: List[str] = field(default_factory=list)
    risk_score: int = 0  # 0-100

@dataclass
class Transaction:
    hash: str
    from_addr: str
    to_addr: str
    value: str
    timestamp: str
    method: str = ""


class AddressProfiler:
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

        # Known addresses (expandable)
        self.known_addresses = {
            '0x0000000000000000000000000000000000000000': ['Null Address', 'Burn'],
            '0x000000000000000000000000000000000000dead': ['Burn Address'],
            '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2': ['WETH', 'Wrapped Ether'],
            '0xdac17f958d2ee523a2206206994597c13d831ec7': ['USDT', 'Tether'],
            '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': ['USDC', 'Circle'],
        }

    def rpc_call(self, method: str, params: list) -> Optional[any]:
        """Make an RPC call."""
        if self.network not in self.rpc_endpoints:
            return None

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
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
        except:
            return None

    def explorer_call(self, params: dict) -> Optional[dict]:
        """Make an explorer API call."""
        if self.network not in self.explorers:
            return None

        if self.api_key:
            params['apikey'] = self.api_key

        try:
            url = f"{self.explorers[self.network]}?{urllib.parse.urlencode(params)}"
            with urllib.request.urlopen(url, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except:
            return None

    def is_contract(self, address: str) -> bool:
        """Check if address is a contract."""
        code = self.rpc_call('eth_getCode', [address, 'latest'])
        return code is not None and code != '0x' and len(code) > 2

    def get_balance(self, address: str) -> str:
        """Get ETH balance."""
        result = self.rpc_call('eth_getBalance', [address, 'latest'])
        if result:
            try:
                wei = int(result, 16)
                return f"{wei / 1e18:.6f}"
            except:
                pass
        return "0"

    def get_tx_count(self, address: str) -> int:
        """Get transaction count."""
        result = self.rpc_call('eth_getTransactionCount', [address, 'latest'])
        if result:
            try:
                return int(result, 16)
            except:
                pass
        return 0

    def get_tx_history(self, address: str, limit: int = 10) -> List[Transaction]:
        """Get recent transactions."""
        txs = []

        data = self.explorer_call({
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'page': 1,
            'offset': limit,
            'sort': 'desc'
        })

        if data and data.get('status') == '1':
            for tx in data.get('result', [])[:limit]:
                txs.append(Transaction(
                    hash=tx.get('hash', ''),
                    from_addr=tx.get('from', ''),
                    to_addr=tx.get('to', ''),
                    value=f"{int(tx.get('value', 0)) / 1e18:.6f}",
                    timestamp=tx.get('timeStamp', ''),
                    method=tx.get('functionName', '').split('(')[0] if tx.get('functionName') else ''
                ))

        return txs

    def get_contract_info(self, address: str) -> Dict:
        """Get contract information."""
        info_data = {'name': '', 'verified': False}

        data = self.explorer_call({
            'module': 'contract',
            'action': 'getsourcecode',
            'address': address
        })

        if data and data.get('status') == '1' and data.get('result'):
            contract = data['result'][0]
            info_data['name'] = contract.get('ContractName', '')
            info_data['verified'] = bool(contract.get('SourceCode'))

        return info_data

    def calculate_risk_score(self, profile: AddressProfile, txs: List[Transaction]) -> int:
        """Calculate risk score (0-100)."""
        score = 0

        # New address
        if profile.tx_count < 10:
            score += 20

        # Low balance
        try:
            if float(profile.balance_eth) < 0.01:
                score += 10
        except:
            pass

        # Contract without verification
        if profile.is_contract and not profile.contract_name:
            score += 30

        # High frequency recent txs (possible bot)
        if len(txs) >= 10:
            score += 15

        # Known labels reduce risk
        if profile.labels:
            score = max(0, score - 20)

        return min(100, score)

    def profile(self, address: str, include_txs: bool = False, tx_limit: int = 10) -> Dict:
        """Create full address profile."""
        address = address.lower()

        profile = AddressProfile(address=address)

        # Check if known address
        if address in self.known_addresses:
            profile.labels = self.known_addresses[address]

        # Basic info
        profile.is_contract = self.is_contract(address)
        profile.type = "contract" if profile.is_contract else "eoa"
        profile.balance_eth = self.get_balance(address)
        profile.tx_count = self.get_tx_count(address)

        # Contract info
        if profile.is_contract:
            contract_info = self.get_contract_info(address)
            profile.contract_name = contract_info.get('name', '')

        # Transactions
        txs = []
        if include_txs:
            txs = self.get_tx_history(address, tx_limit)
            if txs:
                profile.first_seen = txs[-1].timestamp
                profile.last_seen = txs[0].timestamp

        # Risk score
        profile.risk_score = self.calculate_risk_score(profile, txs)

        return {
            'profile': asdict(profile),
            'transactions': [asdict(tx) for tx in txs],
            'network': self.network
        }

    def print_results(self, results: Dict):
        """Print profile results."""
        print()
        banner("ADDRESS PROFILE")
        print()

        p = results['profile']

        info(f"Address: {p['address']}")
        info(f"Type: {p['type'].upper()}")
        info(f"Balance: {p['balance_eth']} ETH")
        info(f"TX Count: {p['tx_count']}")

        if p['is_contract']:
            info(f"Contract Name: {p['contract_name'] or 'Unverified'}")

        if p['labels']:
            info(f"Labels: {', '.join(p['labels'])}")

        print()
        risk = p['risk_score']
        if risk >= 70:
            error(f"Risk Score: {risk}/100 (HIGH)")
        elif risk >= 40:
            warning(f"Risk Score: {risk}/100 (MEDIUM)")
        else:
            success(f"Risk Score: {risk}/100 (LOW)")

        # Recent transactions
        txs = results.get('transactions', [])
        if txs:
            print()
            info("Recent Transactions:")
            for tx in txs[:5]:
                direction = "OUT" if tx['from_addr'].lower() == p['address'] else "IN"
                method = f"[{tx['method']}]" if tx['method'] else ""
                print(f"  {direction} {tx['value']} ETH {method}")
                print(f"      {tx['hash'][:20]}...")


def main():
    parser = argparse.ArgumentParser(description='Blockchain Address Profiler')
    parser.add_argument('address', help='Address to profile')
    parser.add_argument('--network', '-n', default='ethereum',
                       choices=['ethereum', 'bsc', 'polygon', 'arbitrum'])
    parser.add_argument('--api-key', '-k', help='Block explorer API key')
    parser.add_argument('--tx-history', '-t', action='store_true',
                       help='Include transaction history')
    parser.add_argument('--tx-limit', type=int, default=10,
                       help='Transaction history limit')
    parser.add_argument('--output', '-o', help='Output JSON file')
    parser.add_argument('--quiet', '-q', action='store_true')

    args = parser.parse_args()

    if not args.quiet:
        banner("Address Profiler")

    profiler = AddressProfiler(network=args.network, api_key=args.api_key)
    results = profiler.profile(
        args.address,
        include_txs=args.tx_history,
        tx_limit=args.tx_limit
    )

    if not args.quiet:
        profiler.print_results(results)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        success(f"Results saved to {args.output}")


if __name__ == '__main__':
    main()
