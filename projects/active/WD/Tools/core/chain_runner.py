#!/usr/bin/env python3
"""
Chain Runner - Execute attack chains (one-click recipes)
"""

import os
import sys
import json
import yaml
import time
import subprocess
import threading
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Callable, Optional, Any
from datetime import datetime

sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import success, error, warning, info, banner

TOOLKIT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Tool path mapping
TOOL_PATHS = {
    'subdomain': '01-recon/passive/subdomain_enum.py',
    'dns': '01-recon/passive/dns_enum.py',
    'wayback': '01-recon/passive/wayback_urls.py',
    'headers': '01-recon/active/headers_analyzer.py',
    'tech': '01-recon/active/tech_detector.py',
    'dorks': '01-recon/osint/google_dorks.py',
    'port': '02-scanning/port-scan/port_scanner.py',
    'dir': '02-scanning/web-enum/dir_bruteforce.py',
    'param': '02-scanning/web-enum/param_finder.py',
    'fuzz': '02-scanning/fuzzing/fuzzer.py',
    'sqli': '03-vuln-assessment/sqli/sqli_scanner.py',
    'xss': '03-vuln-assessment/xss/xss_scanner.py',
    'lfi': '03-vuln-assessment/lfi-rfi/lfi_scanner.py',
    'ssrf': '03-vuln-assessment/ssrf/ssrf_scanner.py',
    'idor': '03-vuln-assessment/idor/idor_scanner.py',
    'payload': '04-exploitation/payloads/payload_generator.py',
    'encode': '04-exploitation/encoders/encoder.py',
    'bypass': '04-exploitation/bypass/waf_bypass.py',
    'exfil': '05-post-exploitation/exfil/data_exfil.py',
    'creds': '05-post-exploitation/cred-harvest/cred_finder.py',
    'report': '06-reporting/report_generator.py',
    'contract': '07-web3/smart-contracts/contract_analyzer.py',
    'token': '07-web3/defi/token_analyzer.py',
    'address': '07-web3/wallet/address_profiler.py',
    'rugpull': '07-web3/defi/rugpull_scanner.py',
}


@dataclass
class StepResult:
    step_name: str
    tool: str
    status: str  # pending, running, completed, failed, skipped
    start_time: float = 0
    end_time: float = 0
    output: Dict = field(default_factory=dict)
    error: str = ""


@dataclass
class ChainResult:
    chain_name: str
    target: str
    status: str  # pending, running, completed, failed, stopped
    start_time: str = ""
    end_time: str = ""
    steps: List[StepResult] = field(default_factory=list)
    aggregated_findings: List[Dict] = field(default_factory=list)


class ChainRunner:
    def __init__(self):
        self.chains = self.load_chains()
        self.running = False
        self.current_chain: Optional[ChainResult] = None
        self.step_outputs: Dict[str, Any] = {}

        # Callbacks
        self.on_step_start: Optional[Callable] = None
        self.on_step_complete: Optional[Callable] = None
        self.on_chain_complete: Optional[Callable] = None
        self.on_log: Optional[Callable] = None

    def load_chains(self) -> Dict:
        """Load attack chains from config."""
        config_path = os.path.join(TOOLKIT_DIR, 'config', 'attack_chains.yaml')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {'chains': {}, 'categories': {}}

    def get_chain(self, chain_id: str) -> Optional[Dict]:
        """Get chain definition by ID."""
        return self.chains.get('chains', {}).get(chain_id)

    def get_chains_by_category(self, category: str) -> List[Dict]:
        """Get all chains in a category."""
        cat_info = self.chains.get('categories', {}).get(category, {})
        chain_ids = cat_info.get('chains', [])
        return [
            {'id': cid, **self.get_chain(cid)}
            for cid in chain_ids
            if self.get_chain(cid)
        ]

    def list_chains(self) -> List[Dict]:
        """List all available chains."""
        result = []
        for chain_id, chain_def in self.chains.get('chains', {}).items():
            result.append({
                'id': chain_id,
                'name': chain_def.get('name', chain_id),
                'description': chain_def.get('description', ''),
                'category': chain_def.get('category', 'other'),
                'estimated_time': chain_def.get('estimated_time', 'Unknown'),
                'steps_count': len(chain_def.get('steps', []))
            })
        return result

    def log(self, msg: str, level: str = "info"):
        """Log message."""
        if self.on_log:
            self.on_log(msg, level)
        else:
            print(f"[{level.upper()}] {msg}")

    def build_command(self, tool: str, target: str, args: Dict = None) -> List[str]:
        """Build command for a tool."""
        tool_path = TOOL_PATHS.get(tool)
        if not tool_path:
            return []

        full_path = os.path.join(TOOLKIT_DIR, tool_path)
        if not os.path.exists(full_path):
            return []

        cmd = [sys.executable, full_path, target]

        if args:
            for key, value in args.items():
                if isinstance(value, bool):
                    if value:
                        cmd.append(f'--{key}')
                elif isinstance(value, list):
                    cmd.extend([f'--{key}', ','.join(map(str, value))])
                else:
                    cmd.extend([f'--{key}', str(value)])

        return cmd

    def run_step(self, step: Dict, target: str, step_result: StepResult) -> bool:
        """Execute a single step."""
        tool = step.get('tool')
        step_name = step.get('name', tool)
        args = step.get('args', {}).copy()

        step_result.status = "running"
        step_result.start_time = time.time()

        if self.on_step_start:
            self.on_step_start(step_result)

        self.log(f"Running: {step_name}", "info")

        # Check condition
        condition = step.get('condition')
        if condition and not self.check_condition(condition):
            step_result.status = "skipped"
            step_result.end_time = time.time()
            self.log(f"Skipped: {step_name} (condition not met)", "warning")
            return True

        # Build command
        cmd = self.build_command(tool, target, args)
        if not cmd:
            step_result.status = "failed"
            step_result.error = f"Tool not found: {tool}"
            step_result.end_time = time.time()
            self.log(f"Failed: {step_name} - Tool not found", "error")
            return False

        # Add output file
        output_file = f"/tmp/chain_{tool}_{int(time.time())}.json"
        cmd.extend(['-o', output_file])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=TOOLKIT_DIR
            )

            step_result.end_time = time.time()

            # Load output if exists
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r') as f:
                        step_result.output = json.load(f)

                    # Save for later steps
                    save_as = step.get('save_output')
                    if save_as:
                        self.step_outputs[save_as] = step_result.output
                except:
                    pass

            if result.returncode == 0:
                step_result.status = "completed"
                self.log(f"Completed: {step_name}", "success")

                if self.on_step_complete:
                    self.on_step_complete(step_result)
                return True
            else:
                step_result.status = "failed"
                step_result.error = result.stderr[:500] if result.stderr else "Unknown error"
                self.log(f"Failed: {step_name}", "error")
                return False

        except subprocess.TimeoutExpired:
            step_result.status = "failed"
            step_result.error = "Timeout"
            step_result.end_time = time.time()
            self.log(f"Timeout: {step_name}", "error")
            return False

        except Exception as e:
            step_result.status = "failed"
            step_result.error = str(e)
            step_result.end_time = time.time()
            self.log(f"Error: {step_name} - {e}", "error")
            return False

    def check_condition(self, condition: str) -> bool:
        """Check if condition is met based on previous outputs."""
        # Simple condition parsing
        if '.' in condition:
            parts = condition.split('.')
            key = parts[0]
            attr = parts[1] if len(parts) > 1 else None

            if key in self.step_outputs:
                data = self.step_outputs[key]
                if attr == 'found':
                    # Check if any findings
                    return bool(data.get('findings') or data.get('vulnerabilities'))
                elif attr:
                    return bool(data.get(attr))
                return bool(data)

        # Check simple key existence
        if condition.startswith('has_'):
            param = condition[4:]
            return param in self.step_outputs

        return True

    def run_chain(self, chain_id: str, target: str) -> ChainResult:
        """Execute an attack chain."""
        chain_def = self.get_chain(chain_id)
        if not chain_def:
            error(f"Chain not found: {chain_id}")
            return ChainResult(chain_name=chain_id, target=target, status="failed")

        self.running = True
        self.step_outputs = {}

        result = ChainResult(
            chain_name=chain_def.get('name', chain_id),
            target=target,
            status="running",
            start_time=datetime.now().isoformat()
        )
        self.current_chain = result

        self.log(f"\n{'='*60}", "info")
        self.log(f"Starting Chain: {result.chain_name}", "info")
        self.log(f"Target: {target}", "info")
        self.log(f"Steps: {len(chain_def.get('steps', []))}", "info")
        self.log(f"{'='*60}\n", "info")

        steps = chain_def.get('steps', [])
        for i, step in enumerate(steps):
            if not self.running:
                self.log("Chain stopped by user", "warning")
                result.status = "stopped"
                break

            step_result = StepResult(
                step_name=step.get('name', step.get('tool')),
                tool=step.get('tool'),
                status="pending"
            )
            result.steps.append(step_result)

            self.log(f"\n[Step {i+1}/{len(steps)}]", "info")
            success = self.run_step(step, target, step_result)

            # Aggregate findings
            if step_result.output:
                findings = step_result.output.get('findings') or step_result.output.get('vulnerabilities', [])
                if findings:
                    result.aggregated_findings.extend(findings)

        result.end_time = datetime.now().isoformat()

        # Determine final status
        if result.status != "stopped":
            failed_steps = sum(1 for s in result.steps if s.status == "failed")
            if failed_steps == 0:
                result.status = "completed"
            elif failed_steps < len(result.steps):
                result.status = "partial"
            else:
                result.status = "failed"

        self.log(f"\n{'='*60}", "info")
        self.log(f"Chain Complete: {result.chain_name}", "info")
        self.log(f"Status: {result.status.upper()}", "success" if result.status == "completed" else "warning")
        self.log(f"Total Findings: {len(result.aggregated_findings)}", "info")
        self.log(f"{'='*60}", "info")

        if self.on_chain_complete:
            self.on_chain_complete(result)

        self.running = False
        return result

    def stop(self):
        """Stop running chain."""
        self.running = False

    def get_progress(self) -> float:
        """Get current chain progress."""
        if not self.current_chain:
            return 0
        total = len(self.current_chain.steps)
        if total == 0:
            return 0
        done = sum(1 for s in self.current_chain.steps
                   if s.status in ("completed", "failed", "skipped"))
        return (done / total) * 100

    def export_results(self, result: ChainResult, output_file: str):
        """Export chain results to file."""
        data = {
            'chain': result.chain_name,
            'target': result.target,
            'status': result.status,
            'start_time': result.start_time,
            'end_time': result.end_time,
            'steps': [asdict(s) for s in result.steps],
            'findings': result.aggregated_findings,
            'summary': {
                'total_steps': len(result.steps),
                'completed': sum(1 for s in result.steps if s.status == "completed"),
                'failed': sum(1 for s in result.steps if s.status == "failed"),
                'skipped': sum(1 for s in result.steps if s.status == "skipped"),
                'total_findings': len(result.aggregated_findings)
            }
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        self.log(f"Results exported to: {output_file}", "success")


def main():
    """CLI interface for chain runner."""
    import argparse

    parser = argparse.ArgumentParser(description='Attack Chain Runner')
    parser.add_argument('chain', nargs='?', help='Chain ID to run')
    parser.add_argument('target', nargs='?', help='Target URL/address')
    parser.add_argument('--list', '-l', action='store_true', help='List available chains')
    parser.add_argument('--category', '-c', help='Filter by category')
    parser.add_argument('--output', '-o', help='Output file for results')

    args = parser.parse_args()

    runner = ChainRunner()

    if args.list:
        banner("Available Attack Chains")
        print()

        chains = runner.list_chains()
        if args.category:
            chains = [c for c in chains if c['category'] == args.category]

        for chain in chains:
            print(f"  [{chain['category']}] {chain['id']}")
            print(f"      {chain['name']}")
            print(f"      {chain['description']}")
            print(f"      Steps: {chain['steps_count']} | Time: {chain['estimated_time']}")
            print()
        return

    if not args.chain or not args.target:
        parser.print_help()
        return

    banner(f"Running Chain: {args.chain}")
    result = runner.run_chain(args.chain, args.target)

    if args.output:
        runner.export_results(result, args.output)


if __name__ == '__main__':
    main()
