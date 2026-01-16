#!/usr/bin/env python3
"""
Reentrancy Detector - Deep analysis for reentrancy vulnerabilities

USAGE:
    python reentrancy_detector.py <contract.sol> [options]
"""

import sys
import os
import re
import json
import argparse
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional

sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import success, error, warning, info, banner


@dataclass
class ReentrancyFinding:
    function_name: str
    line_number: int
    vulnerability_type: str  # classic, cross-function, read-only
    severity: str
    description: str
    code_snippet: str
    state_variables: List[str] = field(default_factory=list)
    external_calls: List[str] = field(default_factory=list)
    recommendation: str = ""


class ReentrancyDetector:
    def __init__(self):
        self.source = ""
        self.lines = []
        self.findings: List[ReentrancyFinding] = []
        self.functions: Dict[str, Dict] = {}
        self.state_vars: Set[str] = set()

    def load_source(self, path: str) -> bool:
        """Load Solidity source file."""
        if not os.path.exists(path):
            error(f"File not found: {path}")
            return False

        with open(path, 'r') as f:
            self.source = f.read()
        self.lines = self.source.split('\n')
        return True

    def extract_functions(self):
        """Extract all functions from source."""
        # Pattern for function declarations
        func_pattern = r'function\s+(\w+)\s*\(([^)]*)\)\s*(public|external|internal|private)?[^{]*\{'

        for match in re.finditer(func_pattern, self.source, re.MULTILINE):
            func_name = match.group(1)
            func_start = match.start()
            line_num = self.source[:func_start].count('\n') + 1

            # Find function body (simplified - count braces)
            brace_count = 0
            func_end = func_start
            in_func = False

            for i, char in enumerate(self.source[func_start:]):
                if char == '{':
                    brace_count += 1
                    in_func = True
                elif char == '}':
                    brace_count -= 1
                    if in_func and brace_count == 0:
                        func_end = func_start + i + 1
                        break

            func_body = self.source[func_start:func_end]

            self.functions[func_name] = {
                'name': func_name,
                'line': line_num,
                'body': func_body,
                'visibility': match.group(3) or 'public'
            }

    def extract_state_variables(self):
        """Extract state variables."""
        # Pattern for state variable declarations
        var_pattern = r'(uint\d*|int\d*|address|bool|bytes\d*|string|mapping)[^;]*\s+(\w+)\s*[;=]'

        for match in re.finditer(var_pattern, self.source):
            var_name = match.group(2)
            # Check if it's at contract level (not inside a function)
            pos = match.start()
            before = self.source[:pos]
            # Simple heuristic: count braces
            if before.count('{') - before.count('}') <= 1:
                self.state_vars.add(var_name)

    def find_external_calls(self, code: str) -> List[Dict]:
        """Find external calls in code."""
        calls = []

        patterns = [
            (r'(\w+)\.call\{?[^}]*\}?\s*\(', 'call'),
            (r'(\w+)\.delegatecall\s*\(', 'delegatecall'),
            (r'(\w+)\.transfer\s*\(', 'transfer'),
            (r'(\w+)\.send\s*\(', 'send'),
            (r'(\w+)\.(\w+)\s*\(', 'function_call'),
        ]

        for pattern, call_type in patterns:
            for match in re.finditer(pattern, code):
                calls.append({
                    'target': match.group(1),
                    'type': call_type,
                    'position': match.start()
                })

        return calls

    def find_state_changes(self, code: str) -> List[Dict]:
        """Find state variable modifications."""
        changes = []

        for var in self.state_vars:
            # Assignment patterns
            patterns = [
                rf'{var}\s*=\s*',
                rf'{var}\s*\+=',
                rf'{var}\s*\-=',
                rf'{var}\s*\+\+',
                rf'{var}\s*\-\-',
                rf'\+\+\s*{var}',
                rf'\-\-\s*{var}',
            ]

            for pattern in patterns:
                for match in re.finditer(pattern, code):
                    changes.append({
                        'variable': var,
                        'position': match.start()
                    })

        return changes

    def analyze_function(self, func_name: str, func_data: Dict):
        """Analyze a function for reentrancy."""
        body = func_data['body']
        line = func_data['line']

        external_calls = self.find_external_calls(body)
        state_changes = self.find_state_changes(body)

        if not external_calls:
            return

        # Check for classic reentrancy: external call before state change
        for call in external_calls:
            if call['type'] in ('call', 'delegatecall'):
                # Find state changes after this call
                for change in state_changes:
                    if change['position'] > call['position']:
                        # Potential reentrancy!
                        snippet = self.get_code_snippet(line, 5)

                        finding = ReentrancyFinding(
                            function_name=func_name,
                            line_number=line,
                            vulnerability_type="classic",
                            severity="CRITICAL",
                            description=f"External call to {call['target']} before state variable {change['variable']} is updated. Attacker can re-enter.",
                            code_snippet=snippet,
                            state_variables=[change['variable']],
                            external_calls=[f"{call['target']}.{call['type']}()"],
                            recommendation="Use checks-effects-interactions pattern. Update state before external calls, or use ReentrancyGuard."
                        )
                        self.findings.append(finding)

        # Check for cross-function reentrancy
        for call in external_calls:
            if call['type'] == 'call':
                # Check if other functions modify same state
                for other_func, other_data in self.functions.items():
                    if other_func == func_name:
                        continue

                    other_changes = self.find_state_changes(other_data['body'])
                    for change in state_changes:
                        for other_change in other_changes:
                            if change['variable'] == other_change['variable']:
                                snippet = self.get_code_snippet(line, 3)

                                finding = ReentrancyFinding(
                                    function_name=func_name,
                                    line_number=line,
                                    vulnerability_type="cross-function",
                                    severity="HIGH",
                                    description=f"Cross-function reentrancy: {func_name} and {other_func} both modify {change['variable']}",
                                    code_snippet=snippet,
                                    state_variables=[change['variable']],
                                    external_calls=[f"{call['target']}.{call['type']}()"],
                                    recommendation="Use ReentrancyGuard modifier on all functions that share state."
                                )
                                self.findings.append(finding)

    def get_code_snippet(self, line_num: int, context: int = 3) -> str:
        """Get code snippet around line."""
        start = max(0, line_num - context - 1)
        end = min(len(self.lines), line_num + context)
        snippet_lines = []
        for i in range(start, end):
            marker = ">>>" if i == line_num - 1 else "   "
            snippet_lines.append(f"{marker} {i+1}: {self.lines[i]}")
        return '\n'.join(snippet_lines)

    def check_reentrancy_guard(self) -> bool:
        """Check if contract uses ReentrancyGuard."""
        patterns = [
            r'ReentrancyGuard',
            r'nonReentrant',
            r'_notEntered',
            r'_status',
        ]
        for pattern in patterns:
            if re.search(pattern, self.source):
                return True
        return False

    def analyze(self, path: str) -> List[ReentrancyFinding]:
        """Run full reentrancy analysis."""
        if not self.load_source(path):
            return []

        info(f"Analyzing {path} for reentrancy vulnerabilities...")

        self.extract_state_variables()
        self.extract_functions()

        info(f"Found {len(self.functions)} functions, {len(self.state_vars)} state variables")

        # Check for ReentrancyGuard
        has_guard = self.check_reentrancy_guard()
        if has_guard:
            info("ReentrancyGuard detected - some issues may be mitigated")

        # Analyze each function
        for func_name, func_data in self.functions.items():
            self.analyze_function(func_name, func_data)

        # Deduplicate
        seen = set()
        unique = []
        for f in self.findings:
            key = (f.function_name, f.vulnerability_type, tuple(f.state_variables))
            if key not in seen:
                seen.add(key)
                unique.append(f)
        self.findings = unique

        return self.findings

    def print_results(self):
        """Print analysis results."""
        print()
        banner("REENTRANCY ANALYSIS RESULTS")
        print()

        if not self.findings:
            success("No reentrancy vulnerabilities detected!")
            return

        warning(f"Found {len(self.findings)} potential reentrancy issues")
        print()

        for i, finding in enumerate(self.findings, 1):
            severity_color = {
                'CRITICAL': '\033[91m',
                'HIGH': '\033[93m',
                'MEDIUM': '\033[94m',
            }.get(finding.severity, '\033[0m')
            reset = '\033[0m'

            print(f"{severity_color}[{finding.severity}]{reset} {finding.vulnerability_type.upper()} Reentrancy")
            print(f"  Function: {finding.function_name} (line {finding.line_number})")
            print(f"  {finding.description}")
            print()
            print(finding.code_snippet)
            print()
            print(f"  Recommendation: {finding.recommendation}")
            print("-" * 60)


def main():
    parser = argparse.ArgumentParser(description='Reentrancy Vulnerability Detector')
    parser.add_argument('file', help='Solidity source file')
    parser.add_argument('--output', '-o', help='Output JSON file')
    parser.add_argument('--quiet', '-q', action='store_true')

    args = parser.parse_args()

    if not args.quiet:
        banner("Reentrancy Detector")

    detector = ReentrancyDetector()
    findings = detector.analyze(args.file)

    if not args.quiet:
        detector.print_results()

    if args.output:
        data = {
            'file': args.file,
            'findings': [asdict(f) for f in findings],
            'summary': {
                'total': len(findings),
                'critical': sum(1 for f in findings if f.severity == 'CRITICAL'),
                'high': sum(1 for f in findings if f.severity == 'HIGH'),
            }
        }
        with open(args.output, 'w') as f:
            json.dump(data, f, indent=2)
        success(f"Results saved to {args.output}")

    if any(f.severity == 'CRITICAL' for f in findings):
        sys.exit(1)


if __name__ == '__main__':
    main()
