#!/usr/bin/env python3
"""
Data Collector for Personal LLM Fine-tuning
Collects code, conversations, and docs from the workspace
"""

import os
import json
import glob
from pathlib import Path
from datetime import datetime

# Configuration
WORKSPACE = Path(r"c:\Users\patri\Desktop\nuevo comienzo")
OUTPUT_DIR = WORKSPACE / "llm-personal" / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Patterns to collect
CODE_EXTENSIONS = ['.py', '.js', '.ts', '.sol', '.sh']
DOC_EXTENSIONS = ['.md', '.txt']
EXCLUDE_DIRS = ['node_modules', 'venv', '.git', '__pycache__', 'dist', 'build']

def should_exclude(path):
    """Check if path should be excluded"""
    for exc in EXCLUDE_DIRS:
        if exc in str(path):
            return True
    return False

def collect_code_samples():
    """Collect code files and format for training"""
    samples = []
    
    code_dirs = [
        WORKSPACE / "projects" / "active" / "fundex",
        WORKSPACE / "projects" / "active" / "binance",
        WORKSPACE / "pipeline",
        WORKSPACE / "cli",
    ]
    
    for code_dir in code_dirs:
        if not code_dir.exists():
            continue
            
        for ext in CODE_EXTENSIONS:
            for filepath in code_dir.rglob(f"*{ext}"):
                if should_exclude(filepath):
                    continue
                    
                try:
                    content = filepath.read_text(encoding='utf-8', errors='ignore')
                    if len(content) < 100 or len(content) > 50000:  # Skip tiny or huge files
                        continue
                        
                    # Create instruction-response pair
                    filename = filepath.name
                    rel_path = filepath.relative_to(WORKSPACE)
                    
                    sample = {
                        "instruction": f"Show me the code for {filename} which is part of the {filepath.parent.name} project.",
                        "input": "",
                        "output": f"Here's the code for `{rel_path}`:\n\n```{ext[1:]}\n{content}\n```"
                    }
                    samples.append(sample)
                    
                    # Also create explanation sample
                    sample2 = {
                        "instruction": f"What does the file {filename} do?",
                        "input": f"```{ext[1:]}\n{content[:2000]}\n```",
                        "output": f"This file `{filename}` is part of the {filepath.parent.name} project. Based on the code structure, it appears to handle {guess_purpose(content, filename)}."
                    }
                    samples.append(sample2)
                    
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
    
    return samples

def guess_purpose(content, filename):
    """Guess the purpose of a file based on content"""
    content_lower = content.lower()
    
    if 'trading' in content_lower or 'trade' in content_lower:
        return "trading operations and strategy execution"
    elif 'webhook' in content_lower:
        return "receiving and processing webhook requests"
    elif 'api' in content_lower or 'endpoint' in content_lower:
        return "API endpoints and request handling"
    elif 'test' in filename.lower():
        return "testing and validation"
    elif 'config' in filename.lower():
        return "configuration management"
    else:
        return "core application logic"

def collect_markdown_docs():
    """Collect markdown documentation"""
    samples = []
    
    for md_file in WORKSPACE.rglob("*.md"):
        if should_exclude(md_file):
            continue
            
        try:
            content = md_file.read_text(encoding='utf-8', errors='ignore')
            if len(content) < 50:
                continue
                
            # Create Q&A style samples from docs
            title = md_file.stem.replace('_', ' ').replace('-', ' ').title()
            
            sample = {
                "instruction": f"Tell me about {title}",
                "input": "",
                "output": content[:3000]  # Truncate long docs
            }
            samples.append(sample)
            
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
    
    return samples

def create_system_prompts():
    """Create samples that define the assistant's personality"""
    return [
        {
            "instruction": "Who are you?",
            "input": "",
            "output": "I'm Antigravity, your personal AI coding assistant. I've been trained on your code, your projects (Fundex, Binance audits, poker bots), and your way of thinking. I help you with programming, project management, and decision-making."
        },
        {
            "instruction": "What projects do you know about?",
            "input": "",
            "output": "I'm familiar with several of your projects:\n\n1. **Fundex** - Trading algoritmo with paper trading and TradingView integration\n2. **Binance Bug Bounty** - Security audits on BSC Genesis Contracts\n3. **Poker LLM** - Tournament system with AI agents\n4. **Pipeline** - Multi-model orchestration (GOAT/CORLEONE)\n5. **Command Center** - Dashboard for project management\n\nWhich one would you like to work on?"
        },
        {
            "instruction": "Help me with trading",
            "input": "",
            "output": "For trading, you have Fundex set up with:\n\n- **paper_trading.py** - Simulated trading with EMA + RSI strategy\n- **webhook_server.py** - Receives TradingView signals\n- **7 strategies** - SMA, RSI Bollinger, Triple EMA, etc.\n\nYour best performing strategy on backtests was **EMA Momentum on SOL-USD** with +44.8% return.\n\nWhat would you like to do? Run paper trading, adjust strategies, or deploy to production?"
        }
    ]

def save_jsonl(samples, filename):
    """Save samples to JSONL format"""
    output_path = OUTPUT_DIR / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    print(f"Saved {len(samples)} samples to {output_path}")
    return len(samples)

def main():
    print("=" * 60)
    print("PERSONAL LLM DATA COLLECTOR")
    print("=" * 60)
    print(f"Workspace: {WORKSPACE}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 60)
    
    total = 0
    
    # Collect code
    print("\n📦 Collecting code samples...")
    code_samples = collect_code_samples()
    total += save_jsonl(code_samples, "code_samples.jsonl")
    
    # Collect docs
    print("\n📄 Collecting documentation...")
    doc_samples = collect_markdown_docs()
    total += save_jsonl(doc_samples, "documentation.jsonl")
    
    # System prompts
    print("\n🤖 Creating system prompts...")
    system_samples = create_system_prompts()
    total += save_jsonl(system_samples, "system_prompts.jsonl")
    
    # Merge all into training file
    print("\n🔗 Merging all samples...")
    all_samples = code_samples + doc_samples + system_samples
    save_jsonl(all_samples, "training_data.jsonl")
    
    print("\n" + "=" * 60)
    print(f"✅ Total samples collected: {total}")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print("=" * 60)
    
    # Stats
    print("\n📊 Stats:")
    print(f"  - Code samples: {len(code_samples)}")
    print(f"  - Doc samples: {len(doc_samples)}")
    print(f"  - System prompts: {len(system_samples)}")

if __name__ == "__main__":
    main()
