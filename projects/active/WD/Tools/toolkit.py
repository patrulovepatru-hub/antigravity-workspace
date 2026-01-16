#!/usr/bin/env python3
"""
WebExploit Toolkit - Main Launcher
Unified interface for web exploitation tools.

USAGE:
    python toolkit.py [module] [tool] [args]
    python toolkit.py --list
    python toolkit.py --interactive

EXAMPLES:
    python toolkit.py recon subdomain example.com
    python toolkit.py scan dir https://example.com -w wordlist.txt
    python toolkit.py vuln sqli "https://example.com/page?id=1"
    python toolkit.py exploit payload reverse-shell --ip 10.10.10.10 --port 4444 --lang bash
"""

import sys
import os
import argparse
import subprocess

# Add lib to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import banner, info, success, error, warning, Colors

TOOLKIT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Tool registry
TOOLS = {
    'recon': {
        'subdomain': ('01-recon/passive/subdomain_enum.py', 'Subdomain enumeration'),
        'dns': ('01-recon/passive/dns_enum.py', 'DNS enumeration'),
        'wayback': ('01-recon/passive/wayback_urls.py', 'Wayback URL extraction'),
        'headers': ('01-recon/active/headers_analyzer.py', 'HTTP headers analysis'),
        'tech': ('01-recon/active/tech_detector.py', 'Technology detection'),
        'dorks': ('01-recon/osint/google_dorks.py', 'Google dorks generator'),
    },
    'scan': {
        'port': ('02-scanning/port-scan/port_scanner.py', 'Port scanning'),
        'dir': ('02-scanning/web-enum/dir_bruteforce.py', 'Directory bruteforce'),
        'param': ('02-scanning/web-enum/param_finder.py', 'Parameter discovery'),
        'fuzz': ('02-scanning/fuzzing/fuzzer.py', 'Web fuzzing'),
    },
    'vuln': {
        'sqli': ('03-vuln-assessment/sqli/sqli_scanner.py', 'SQL injection scanner'),
        'xss': ('03-vuln-assessment/xss/xss_scanner.py', 'XSS scanner'),
        'lfi': ('03-vuln-assessment/lfi-rfi/lfi_scanner.py', 'LFI/RFI scanner'),
        'ssrf': ('03-vuln-assessment/ssrf/ssrf_scanner.py', 'SSRF scanner'),
        'idor': ('03-vuln-assessment/idor/idor_scanner.py', 'IDOR scanner'),
    },
    'exploit': {
        'payload': ('04-exploitation/payloads/payload_generator.py', 'Payload generator'),
        'encode': ('04-exploitation/encoders/encoder.py', 'Payload encoder'),
        'bypass': ('04-exploitation/bypass/waf_bypass.py', 'WAF bypass generator'),
    },
    'post': {
        'exfil': ('05-post-exploitation/exfil/data_exfil.py', 'Data exfiltration helper'),
        'creds': ('05-post-exploitation/cred-harvest/cred_finder.py', 'Credential finder'),
    },
    'report': {
        'generate': ('06-reporting/report_generator.py', 'Report generator'),
    },
    'web3': {
        'contract': ('07-web3/smart-contracts/contract_analyzer.py', 'Smart contract analyzer'),
        'reentrancy': ('07-web3/smart-contracts/reentrancy_detector.py', 'Reentrancy detector'),
        'flashloan': ('07-web3/defi/flash_loan_sim.py', 'Flash loan simulator'),
        'token': ('07-web3/defi/token_analyzer.py', 'Token/honeypot analyzer'),
        'rugpull': ('07-web3/defi/rugpull_scanner.py', 'Rugpull scanner'),
        'address': ('07-web3/wallet/address_profiler.py', 'Address profiler'),
    },
}


def print_banner():
    print(f"""{Colors.CYAN}{Colors.BOLD}
╦ ╦┌─┐┌┐ ╔═╗─┐ ┬┌─┐┬  ┌─┐┬┌┬┐  ╔╦╗┌─┐┌─┐┬  ┬┌─┬┌┬┐
║║║├┤ ├┴┐║╣ ┌┴┬┘├─┘│  │ ││ │    ║ │ ││ ││  ├┴┐│ │
╚╩╝└─┘└─┘╚═╝┴ └─┴  ┴─┘└─┘┴ ┴    ╩ └─┘└─┘┴─┘┴ ┴┴ ┴
{Colors.END}
{Colors.YELLOW}[ Web Exploitation Toolkit v1.0 ]{Colors.END}
{Colors.BLUE}[ github.com/yourrepo/webexploit ]{Colors.END}
""")


def list_tools():
    """List all available tools."""
    print_banner()

    for module, tools in TOOLS.items():
        print(f"\n{Colors.GREEN}[{module.upper()}]{Colors.END}")
        for tool_name, (path, desc) in tools.items():
            print(f"  {Colors.CYAN}{tool_name:<12}{Colors.END} - {desc}")

    print(f"\n{Colors.YELLOW}Usage:{Colors.END} python toolkit.py <module> <tool> [args]")
    print(f"{Colors.YELLOW}Help:{Colors.END}  python toolkit.py <module> <tool> --help")


def run_tool(module: str, tool: str, args: list):
    """Run a specific tool."""
    if module not in TOOLS:
        error(f"Unknown module: {module}")
        info(f"Available modules: {', '.join(TOOLS.keys())}")
        return 1

    if tool not in TOOLS[module]:
        error(f"Unknown tool: {tool} in module {module}")
        info(f"Available tools: {', '.join(TOOLS[module].keys())}")
        return 1

    tool_path = os.path.join(TOOLKIT_ROOT, TOOLS[module][tool][0])

    if not os.path.exists(tool_path):
        error(f"Tool not found: {tool_path}")
        return 1

    # Run the tool
    cmd = [sys.executable, tool_path] + args
    try:
        return subprocess.call(cmd)
    except KeyboardInterrupt:
        print("\nInterrupted")
        return 130


def interactive_mode():
    """Interactive menu mode."""
    print_banner()

    while True:
        print(f"\n{Colors.BOLD}Modules:{Colors.END}")
        modules = list(TOOLS.keys())
        for i, mod in enumerate(modules, 1):
            print(f"  {i}. {mod}")
        print(f"  0. Exit")

        try:
            choice = input(f"\n{Colors.CYAN}Select module [0-{len(modules)}]: {Colors.END}").strip()

            if choice == '0' or choice.lower() == 'exit':
                print("Goodbye!")
                break

            if not choice.isdigit() or int(choice) > len(modules):
                warning("Invalid choice")
                continue

            module = modules[int(choice) - 1]
            tools = TOOLS[module]

            print(f"\n{Colors.BOLD}Tools in {module}:{Colors.END}")
            tool_list = list(tools.keys())
            for i, (tool_name, (_, desc)) in enumerate(tools.items(), 1):
                print(f"  {i}. {tool_name} - {desc}")
            print(f"  0. Back")

            tool_choice = input(f"\n{Colors.CYAN}Select tool [0-{len(tool_list)}]: {Colors.END}").strip()

            if tool_choice == '0':
                continue

            if not tool_choice.isdigit() or int(tool_choice) > len(tool_list):
                warning("Invalid choice")
                continue

            tool = tool_list[int(tool_choice) - 1]

            args_input = input(f"{Colors.CYAN}Arguments (or press Enter for help): {Colors.END}").strip()

            if args_input:
                args = args_input.split()
            else:
                args = ['--help']

            print()
            run_tool(module, tool, args)

        except KeyboardInterrupt:
            print("\nUse 'exit' or '0' to quit")
        except EOFError:
            break


def main():
    parser = argparse.ArgumentParser(
        description='WebExploit Toolkit - Unified web exploitation tools',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        usage='%(prog)s [module] [tool] [args]',
        epilog="""
MODULES:
    recon    - Reconnaissance tools (subdomain, dns, wayback, headers, tech, dorks)
    scan     - Scanning tools (port, dir, param, fuzz)
    vuln     - Vulnerability scanners (sqli, xss, lfi, ssrf, idor)
    exploit  - Exploitation tools (payload, encode, bypass)
    post     - Post-exploitation (exfil, creds)
    report   - Reporting tools (generate)

EXAMPLES:
    %(prog)s recon subdomain example.com -o subs.txt
    %(prog)s scan dir https://example.com -w /usr/share/wordlists/common.txt
    %(prog)s vuln sqli "https://example.com/page?id=1"
    %(prog)s exploit payload reverse-shell --ip 10.10.10.10 --port 4444 --lang bash
    %(prog)s post creds ./config/ --recursive
    %(prog)s report generate --input results.json --format html -o report.html
        """
    )
    parser.add_argument('--list', '-l', action='store_true', help='List all tools')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('module', nargs='?', help='Module name')
    parser.add_argument('tool', nargs='?', help='Tool name')
    parser.add_argument('args', nargs=argparse.REMAINDER, help='Tool arguments')

    args = parser.parse_args()

    if args.list:
        list_tools()
        return 0

    if args.interactive:
        interactive_mode()
        return 0

    if not args.module:
        print_banner()
        parser.print_help()
        return 0

    if not args.tool:
        error(f"Specify a tool for module '{args.module}'")
        if args.module in TOOLS:
            info(f"Available tools: {', '.join(TOOLS[args.module].keys())}")
        return 1

    return run_tool(args.module, args.tool, args.args)


if __name__ == '__main__':
    sys.exit(main())
