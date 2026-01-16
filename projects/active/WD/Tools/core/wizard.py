#!/usr/bin/env python3
"""
Attack Wizard - Automated exploitation flow with decision engine.
"""

import re
import json
import subprocess
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional
from enum import Enum


class WizardPhase(Enum):
    RECON = 1
    SCAN = 2
    VULN = 3
    EXPLOIT = 4
    POST = 5
    REPORT = 6


@dataclass
class WizardStep:
    name: str
    tool: str
    phase: WizardPhase
    args: Dict = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    condition: Optional[Callable] = None
    status: str = "pending"  # pending, running, completed, skipped, failed
    result: Dict = field(default_factory=dict)


@dataclass
class TargetProfile:
    url: str
    domain: str = ""
    ip: str = ""
    technologies: List[str] = field(default_factory=list)
    cms: str = ""
    waf: str = ""
    ports: List[int] = field(default_factory=list)
    subdomains: List[str] = field(default_factory=list)
    params: List[str] = field(default_factory=list)
    vulns: List[Dict] = field(default_factory=list)


# Technology detection patterns
TECH_SIGNATURES = {
    'wordpress': [r'wp-content', r'wp-includes', r'wordpress'],
    'drupal': [r'drupal', r'/sites/default/'],
    'joomla': [r'joomla', r'/components/com_'],
    'laravel': [r'laravel', r'XSRF-TOKEN'],
    'django': [r'csrfmiddlewaretoken', r'django'],
    'react': [r'react', r'_reactRoot', r'__REACT'],
    'angular': [r'ng-app', r'ng-controller', r'angular'],
    'vue': [r'vue', r'v-bind', r'v-model'],
    'nodejs': [r'express', r'node'],
    'asp.net': [r'__VIEWSTATE', r'aspnet', r'.aspx'],
    'php': [r'\.php', r'PHPSESSID'],
    'nginx': [r'nginx'],
    'apache': [r'apache', r'mod_'],
    'cloudflare': [r'cloudflare', r'cf-ray'],
    'web3': [r'web3', r'ethereum', r'metamask', r'0x[a-fA-F0-9]{40}'],
    'solidity': [r'solidity', r'pragma solidity'],
}

# Attack suggestions based on technology
TECH_ATTACKS = {
    'wordpress': ['wpscan', 'xmlrpc_bruteforce', 'plugin_vulns', 'sqli', 'xss'],
    'drupal': ['drupal_scan', 'sqli', 'rce'],
    'joomla': ['joomla_scan', 'sqli', 'xss'],
    'laravel': ['debug_mode', 'sqli', 'xss', 'ssrf'],
    'django': ['debug_mode', 'sqli', 'ssti'],
    'react': ['xss_dom', 'prototype_pollution', 'ssrf'],
    'angular': ['xss_dom', 'prototype_pollution', 'ssti'],
    'vue': ['xss_dom', 'prototype_pollution'],
    'nodejs': ['prototype_pollution', 'ssrf', 'rce', 'nosql'],
    'asp.net': ['viewstate_deser', 'sqli', 'xss'],
    'php': ['sqli', 'xss', 'lfi', 'rfi', 'rce'],
    'web3': ['smart_contract_audit', 'reentrancy', 'flash_loan'],
}

# WAF bypass techniques
WAF_BYPASS = {
    'cloudflare': ['cf_bypass', 'origin_ip'],
    'akamai': ['akamai_bypass'],
    'aws_waf': ['aws_bypass'],
    'generic': ['encoding', 'case_switch', 'comments'],
}


class AttackWizard:
    def __init__(self, toolkit_dir: str):
        self.toolkit_dir = toolkit_dir
        self.target: Optional[TargetProfile] = None
        self.steps: List[WizardStep] = []
        self.current_step = 0
        self.on_step_update: Optional[Callable] = None
        self.on_log: Optional[Callable] = None
        self.running = False

    def log(self, msg: str, level: str = "info"):
        if self.on_log:
            self.on_log(msg, level)

    def update_step(self, step: WizardStep):
        if self.on_step_update:
            self.on_step_update(step)

    def analyze_target(self, url: str) -> TargetProfile:
        """Analyze target and create profile."""
        from urllib.parse import urlparse

        parsed = urlparse(url if '://' in url else f'https://{url}')
        domain = parsed.netloc or parsed.path.split('/')[0]

        self.target = TargetProfile(url=url, domain=domain)
        self.log(f"[*] Analyzing target: {domain}")
        return self.target

    def detect_technologies(self, content: str, headers: Dict = None) -> List[str]:
        """Detect technologies from response content and headers."""
        detected = []
        headers = headers or {}

        # Combine content and headers for detection
        check_str = content.lower()
        for h, v in headers.items():
            check_str += f" {h}:{v}".lower()

        for tech, patterns in TECH_SIGNATURES.items():
            for pattern in patterns:
                if re.search(pattern, check_str, re.I):
                    detected.append(tech)
                    break

        if self.target:
            self.target.technologies = list(set(detected))

        return detected

    def suggest_attacks(self) -> List[str]:
        """Suggest attacks based on detected technologies."""
        if not self.target:
            return ['sqli', 'xss', 'lfi', 'ssrf']  # Default

        suggested = set()
        for tech in self.target.technologies:
            if tech in TECH_ATTACKS:
                suggested.update(TECH_ATTACKS[tech])

        # Always include basic scans
        suggested.update(['sqli', 'xss'])

        return list(suggested)

    def build_wizard_steps(self, mode: str = "full") -> List[WizardStep]:
        """Build wizard steps based on mode."""
        self.steps = []

        if mode == "full":
            # Phase 1: Recon
            self.steps.extend([
                WizardStep("Subdomain Enum", "subdomain", WizardPhase.RECON),
                WizardStep("Tech Detection", "tech", WizardPhase.RECON),
                WizardStep("WAF Detection", "waf_detect", WizardPhase.RECON),
            ])

            # Phase 2: Scanning
            self.steps.extend([
                WizardStep("Port Scan", "port", WizardPhase.SCAN,
                          args={"preset": "web"}),
                WizardStep("Directory Fuzzing", "dir", WizardPhase.SCAN,
                          args={"preset": "standard"}),
                WizardStep("Parameter Discovery", "param", WizardPhase.SCAN),
            ])

            # Phase 3: Vuln Assessment
            self.steps.extend([
                WizardStep("SQLi Scanner", "sqli", WizardPhase.VULN,
                          args={"preset": "standard"}),
                WizardStep("XSS Scanner", "xss", WizardPhase.VULN,
                          args={"preset": "standard"}),
                WizardStep("LFI Scanner", "lfi", WizardPhase.VULN,
                          condition=lambda: 'php' in (self.target.technologies if self.target else [])),
                WizardStep("SSRF Scanner", "ssrf", WizardPhase.VULN),
            ])

        elif mode == "quick":
            self.steps.extend([
                WizardStep("Tech Detection", "tech", WizardPhase.RECON),
                WizardStep("Quick Port Scan", "port", WizardPhase.SCAN,
                          args={"preset": "top20"}),
                WizardStep("SQLi Quick", "sqli", WizardPhase.VULN,
                          args={"preset": "quick"}),
                WizardStep("XSS Quick", "xss", WizardPhase.VULN,
                          args={"preset": "quick"}),
            ])

        elif mode == "stealth":
            self.steps.extend([
                WizardStep("Passive Recon", "passive_recon", WizardPhase.RECON),
                WizardStep("Stealth Scan", "port", WizardPhase.SCAN,
                          args={"preset": "stealth"}),
                WizardStep("SQLi Stealth", "sqli", WizardPhase.VULN,
                          args={"preset": "stealth"}),
            ])

        # Always add report at end
        self.steps.append(
            WizardStep("Generate Report", "report", WizardPhase.REPORT)
        )

        return self.steps

    def run_step(self, step: WizardStep) -> bool:
        """Execute a single wizard step."""
        # Check condition
        if step.condition and not step.condition():
            step.status = "skipped"
            self.log(f"[~] Skipped: {step.name} (condition not met)")
            self.update_step(step)
            return True

        step.status = "running"
        self.update_step(step)
        self.log(f"[*] Running: {step.name}")

        try:
            # Build tool path and command
            tool_map = {
                'subdomain': '01-recon/passive/subdomain_enum.py',
                'tech': '01-recon/active/tech_detector.py',
                'waf_detect': '01-recon/active/waf_detector.py',
                'port': '02-scanning/port-scan/port_scanner.py',
                'dir': '02-scanning/web-enum/dir_bruteforce.py',
                'param': '02-scanning/web-enum/param_finder.py',
                'sqli': '03-vuln-assessment/sqli/sqli_scanner.py',
                'xss': '03-vuln-assessment/xss/xss_scanner.py',
                'lfi': '03-vuln-assessment/lfi-rfi/lfi_scanner.py',
                'ssrf': '03-vuln-assessment/ssrf/ssrf_scanner.py',
                'report': '06-reporting/report_generator.py',
            }

            tool_path = tool_map.get(step.tool)
            if not tool_path:
                step.status = "skipped"
                self.log(f"[!] Tool not found: {step.tool}", "warning")
                return True

            import os
            full_path = os.path.join(self.toolkit_dir, tool_path)
            if not os.path.exists(full_path):
                step.status = "skipped"
                self.log(f"[!] Tool file not found: {tool_path}", "warning")
                return True

            # Build command
            import sys
            cmd = [sys.executable, full_path, self.target.url if self.target else ""]

            # Add preset if specified
            if 'preset' in step.args:
                cmd.extend(['--preset', step.args['preset']])

            # Add output
            cmd.extend(['-o', f'/tmp/wizard_{step.tool}.json'])

            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=self.toolkit_dir
            )

            step.result = {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }

            if result.returncode == 0:
                step.status = "completed"
                self.log(f"[+] Completed: {step.name}", "success")
            else:
                step.status = "failed"
                self.log(f"[-] Failed: {step.name}", "error")

        except subprocess.TimeoutExpired:
            step.status = "failed"
            self.log(f"[-] Timeout: {step.name}", "error")
        except Exception as e:
            step.status = "failed"
            step.result = {'error': str(e)}
            self.log(f"[-] Error: {step.name} - {e}", "error")

        self.update_step(step)
        return step.status in ("completed", "skipped")

    def run_wizard(self, url: str, mode: str = "full"):
        """Run complete wizard flow."""
        self.running = True
        self.analyze_target(url)
        self.build_wizard_steps(mode)

        self.log(f"\n{'='*50}")
        self.log(f"[*] Starting Attack Wizard - Mode: {mode.upper()}")
        self.log(f"[*] Target: {url}")
        self.log(f"[*] Steps: {len(self.steps)}")
        self.log(f"{'='*50}\n")

        for i, step in enumerate(self.steps):
            if not self.running:
                self.log("[!] Wizard stopped by user", "warning")
                break

            self.current_step = i
            self.run_step(step)

        # Summary
        completed = sum(1 for s in self.steps if s.status == "completed")
        failed = sum(1 for s in self.steps if s.status == "failed")
        skipped = sum(1 for s in self.steps if s.status == "skipped")

        self.log(f"\n{'='*50}")
        self.log(f"[*] Wizard Complete")
        self.log(f"    Completed: {completed} | Failed: {failed} | Skipped: {skipped}")
        self.log(f"{'='*50}")

        self.running = False

    def stop(self):
        """Stop wizard execution."""
        self.running = False

    def get_progress(self) -> float:
        """Get wizard progress as percentage."""
        if not self.steps:
            return 0
        done = sum(1 for s in self.steps if s.status in ("completed", "failed", "skipped"))
        return (done / len(self.steps)) * 100
