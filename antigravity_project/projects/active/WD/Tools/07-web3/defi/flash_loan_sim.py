#!/usr/bin/env python3
"""
Flash Loan Simulator - Analyze and simulate flash loan attack vectors

USAGE:
    python flash_loan_sim.py <contract_address> [options]
"""

import sys
import os
import re
import json
import argparse
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import success, error, warning, info, banner


@dataclass
class FlashLoanVector:
    name: str
    severity: str
    description: str
    attack_flow: List[str]
    profit_potential: str
    requirements: List[str]
    mitigation: str


# Known flash loan providers
FLASH_LOAN_PROVIDERS = {
    'aave_v2': {
        'name': 'Aave V2',
        'function': 'flashLoan',
        'callback': 'executeOperation',
        'fee': '0.09%',
        'max_assets': 'Multiple',
    },
    'aave_v3': {
        'name': 'Aave V3',
        'function': 'flashLoanSimple',
        'callback': 'executeOperation',
        'fee': '0.05%',
        'max_assets': 'Single',
    },
    'uniswap_v2': {
        'name': 'Uniswap V2',
        'function': 'swap',
        'callback': 'uniswapV2Call',
        'fee': '0.3%',
        'max_assets': 'Pair tokens',
    },
    'uniswap_v3': {
        'name': 'Uniswap V3',
        'function': 'flash',
        'callback': 'uniswapV3FlashCallback',
        'fee': 'Variable',
        'max_assets': 'Pair tokens',
    },
    'dydx': {
        'name': 'dYdX',
        'function': 'operate',
        'callback': 'callFunction',
        'fee': '0 (2 wei)',
        'max_assets': 'ETH, USDC, DAI',
    },
    'balancer': {
        'name': 'Balancer',
        'function': 'flashLoan',
        'callback': 'receiveFlashLoan',
        'fee': '0%',
        'max_assets': 'Multiple',
    },
}

# Attack patterns
ATTACK_PATTERNS = {
    'price_manipulation': {
        'name': 'Price Oracle Manipulation',
        'description': 'Use flash loan to manipulate on-chain price oracles',
        'indicators': ['getReserves', 'getPrice', 'latestAnswer', 'slot0'],
        'severity': 'CRITICAL',
    },
    'governance_attack': {
        'name': 'Governance Attack',
        'description': 'Flash borrow tokens to manipulate governance votes',
        'indicators': ['delegate', 'castVote', 'propose', 'votingPower'],
        'severity': 'HIGH',
    },
    'collateral_swap': {
        'name': 'Collateral Swap Attack',
        'description': 'Manipulate collateral values in lending protocols',
        'indicators': ['borrow', 'deposit', 'withdraw', 'liquidate'],
        'severity': 'CRITICAL',
    },
    'arbitrage': {
        'name': 'Arbitrage Exploitation',
        'description': 'Exploit price differences across DEXes',
        'indicators': ['swap', 'exchange', 'trade'],
        'severity': 'MEDIUM',
    },
    'reentrancy_flash': {
        'name': 'Flash Loan Reentrancy',
        'description': 'Combine flash loan with reentrancy attack',
        'indicators': ['.call{value:', 'receive()', 'fallback()'],
        'severity': 'CRITICAL',
    },
}


class FlashLoanSimulator:
    def __init__(self, network: str = "ethereum"):
        self.network = network
        self.source_code = ""
        self.vectors: List[FlashLoanVector] = []

    def load_source(self, path: str) -> bool:
        """Load contract source."""
        if os.path.isfile(path):
            with open(path, 'r') as f:
                self.source_code = f.read()
            return True
        return False

    def detect_flash_loan_usage(self) -> Dict[str, bool]:
        """Detect if contract uses flash loans."""
        detected = {}

        for provider_id, provider in FLASH_LOAN_PROVIDERS.items():
            patterns = [
                provider['callback'],
                provider['function'],
            ]
            for pattern in patterns:
                if re.search(pattern, self.source_code, re.IGNORECASE):
                    detected[provider_id] = True
                    break

        return detected

    def analyze_attack_surface(self) -> List[str]:
        """Analyze potential attack vectors."""
        vulnerable_patterns = []

        for pattern_id, pattern in ATTACK_PATTERNS.items():
            for indicator in pattern['indicators']:
                if re.search(indicator, self.source_code, re.IGNORECASE):
                    vulnerable_patterns.append(pattern_id)
                    break

        return list(set(vulnerable_patterns))

    def check_protections(self) -> Dict[str, bool]:
        """Check for flash loan protections."""
        protections = {
            'block_delay': bool(re.search(r'block\.number|block\.timestamp.*require', self.source_code)),
            'reentrancy_guard': bool(re.search(r'nonReentrant|ReentrancyGuard', self.source_code)),
            'access_control': bool(re.search(r'onlyOwner|require.*msg\.sender', self.source_code)),
            'twap_oracle': bool(re.search(r'TWAP|consult|observe', self.source_code)),
            'flashloan_check': bool(re.search(r'isContract|extcodesize|tx\.origin', self.source_code)),
        }
        return protections

    def generate_attack_vectors(self, patterns: List[str]) -> List[FlashLoanVector]:
        """Generate potential attack vectors."""
        vectors = []

        for pattern_id in patterns:
            pattern = ATTACK_PATTERNS.get(pattern_id)
            if not pattern:
                continue

            if pattern_id == 'price_manipulation':
                vectors.append(FlashLoanVector(
                    name="Price Oracle Manipulation via Flash Loan",
                    severity=pattern['severity'],
                    description="Flash borrow large amount to manipulate spot price, exploit vulnerable oracle, profit from mispriced assets",
                    attack_flow=[
                        "1. Flash borrow large amount of token A",
                        "2. Swap token A for token B on target DEX (moves price)",
                        "3. Interact with victim contract using manipulated price",
                        "4. Extract value (borrow more, liquidate positions, etc.)",
                        "5. Swap back and repay flash loan",
                        "6. Keep profit"
                    ],
                    profit_potential="HIGH - Can drain entire protocol",
                    requirements=["Low-liquidity pool as oracle", "No TWAP protection", "Sufficient flash loan liquidity"],
                    mitigation="Use Chainlink oracles, implement TWAP, add price deviation checks"
                ))

            elif pattern_id == 'governance_attack':
                vectors.append(FlashLoanVector(
                    name="Flash Loan Governance Attack",
                    severity=pattern['severity'],
                    description="Borrow governance tokens to pass malicious proposals or swing votes",
                    attack_flow=[
                        "1. Flash borrow governance tokens",
                        "2. Delegate voting power to attacker",
                        "3. Vote on active proposal / create malicious proposal",
                        "4. Return tokens in same transaction",
                        "5. Wait for proposal execution (if time-locked)"
                    ],
                    profit_potential="MEDIUM - Depends on governance actions available",
                    requirements=["Flash-borrowable governance token", "No snapshot-based voting", "Active proposal or instant execution"],
                    mitigation="Use voting snapshots before proposal, add time delays"
                ))

            elif pattern_id == 'collateral_swap':
                vectors.append(FlashLoanVector(
                    name="Collateral Manipulation Attack",
                    severity=pattern['severity'],
                    description="Manipulate collateral values to extract excess borrows or cause bad liquidations",
                    attack_flow=[
                        "1. Flash borrow asset",
                        "2. Deposit as collateral in lending protocol",
                        "3. Borrow maximum against inflated collateral",
                        "4. Manipulate collateral price if using spot oracle",
                        "5. Withdraw original collateral",
                        "6. Repay flash loan, keep borrowed assets"
                    ],
                    profit_potential="CRITICAL - Can drain lending pool",
                    requirements=["Same-block collateral operations", "Spot price oracle", "Sufficient collateral factor"],
                    mitigation="Add deposit-borrow delays, use time-weighted prices"
                ))

            elif pattern_id == 'reentrancy_flash':
                vectors.append(FlashLoanVector(
                    name="Flash Loan + Reentrancy Combo",
                    severity=pattern['severity'],
                    description="Combine flash loan capital with reentrancy to amplify attack",
                    attack_flow=[
                        "1. Flash borrow large amount",
                        "2. Deposit into vulnerable contract",
                        "3. Trigger withdrawal with callback",
                        "4. Re-enter during callback to withdraw again",
                        "5. Repeat until drained",
                        "6. Repay flash loan"
                    ],
                    profit_potential="CRITICAL - Full contract drain",
                    requirements=["Reentrancy vulnerability", "External calls before state update"],
                    mitigation="Add ReentrancyGuard, use checks-effects-interactions"
                ))

        return vectors

    def simulate(self, source_path: str) -> Dict:
        """Run full simulation analysis."""
        if not self.load_source(source_path):
            return {'error': 'Could not load source'}

        info("Analyzing flash loan attack surface...")

        # Detect flash loan usage
        fl_usage = self.detect_flash_loan_usage()

        # Find attack patterns
        patterns = self.analyze_attack_surface()

        # Check protections
        protections = self.check_protections()

        # Generate vectors
        self.vectors = self.generate_attack_vectors(patterns)

        # Calculate risk score
        risk_score = 0
        if patterns:
            risk_score += len(patterns) * 15
        if not protections.get('twap_oracle'):
            risk_score += 20
        if not protections.get('reentrancy_guard'):
            risk_score += 15
        if not protections.get('block_delay'):
            risk_score += 10

        risk_score = min(100, risk_score)

        return {
            'file': source_path,
            'flash_loan_providers': fl_usage,
            'attack_patterns': patterns,
            'protections': protections,
            'vectors': [asdict(v) for v in self.vectors],
            'risk_score': risk_score,
            'risk_level': 'CRITICAL' if risk_score >= 70 else 'HIGH' if risk_score >= 50 else 'MEDIUM' if risk_score >= 30 else 'LOW'
        }

    def print_results(self, results: Dict):
        """Print simulation results."""
        print()
        banner("FLASH LOAN ATTACK SIMULATION")
        print()

        info(f"File: {results['file']}")
        info(f"Risk Score: {results['risk_score']}/100 ({results['risk_level']})")
        print()

        # Flash loan providers
        if results['flash_loan_providers']:
            info("Flash Loan Providers Detected:")
            for provider_id in results['flash_loan_providers']:
                provider = FLASH_LOAN_PROVIDERS.get(provider_id, {})
                print(f"  - {provider.get('name', provider_id)}")
        else:
            print("  No flash loan integration detected")
        print()

        # Protections
        info("Protections:")
        for protection, present in results['protections'].items():
            status = '\033[92m[+]\033[0m' if present else '\033[91m[-]\033[0m'
            print(f"  {status} {protection.replace('_', ' ').title()}")
        print()

        # Attack vectors
        if results['vectors']:
            warning(f"Potential Attack Vectors ({len(results['vectors'])}):")
            print()
            for v in results['vectors']:
                severity_color = '\033[91m' if v['severity'] == 'CRITICAL' else '\033[93m'
                print(f"{severity_color}[{v['severity']}]\033[0m {v['name']}")
                print(f"  {v['description']}")
                print()
                print("  Attack Flow:")
                for step in v['attack_flow']:
                    print(f"    {step}")
                print()
                print(f"  Profit Potential: {v['profit_potential']}")
                print(f"  Mitigation: {v['mitigation']}")
                print("-" * 60)
        else:
            success("No obvious flash loan attack vectors detected")


def main():
    parser = argparse.ArgumentParser(description='Flash Loan Attack Simulator')
    parser.add_argument('file', help='Solidity source file')
    parser.add_argument('--network', '-n', default='ethereum')
    parser.add_argument('--output', '-o', help='Output JSON file')
    parser.add_argument('--quiet', '-q', action='store_true')

    args = parser.parse_args()

    if not args.quiet:
        banner("Flash Loan Simulator")

    simulator = FlashLoanSimulator(network=args.network)
    results = simulator.simulate(args.file)

    if not args.quiet:
        simulator.print_results(results)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        success(f"Results saved to {args.output}")

    if results.get('risk_level') in ('CRITICAL', 'HIGH'):
        sys.exit(1)


if __name__ == '__main__':
    main()
