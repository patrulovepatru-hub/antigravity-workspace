#!/usr/bin/env python3
"""Color utilities for terminal output."""

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def success(msg): print(f"{Colors.GREEN}[+]{Colors.END} {msg}")
def error(msg): print(f"{Colors.RED}[-]{Colors.END} {msg}")
def warning(msg): print(f"{Colors.YELLOW}[!]{Colors.END} {msg}")
def info(msg): print(f"{Colors.BLUE}[*]{Colors.END} {msg}")
def debug(msg): print(f"{Colors.MAGENTA}[D]{Colors.END} {msg}")

def banner(text):
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("=" * 60)
    print(f"  {text}")
    print("=" * 60)
    print(f"{Colors.END}")
