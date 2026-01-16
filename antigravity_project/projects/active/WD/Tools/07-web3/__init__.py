"""
WebExploit Toolkit - Web3/Blockchain Module
"""

from .smart_contracts import ContractAnalyzer, ReentrancyDetector
from .defi import TokenAnalyzer, RugpullScanner, FlashLoanSimulator
from .wallet import AddressProfiler

__all__ = [
    'ContractAnalyzer',
    'ReentrancyDetector',
    'TokenAnalyzer',
    'RugpullScanner',
    'FlashLoanSimulator',
    'AddressProfiler',
]
