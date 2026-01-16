#!/usr/bin/env python3
"""
WebExploit Toolkit - GUI
Simple graphical interface for the toolkit.

USAGE:
    python gui.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import subprocess
import threading
import sys
import os
import yaml

# Import wizard and chain runner
sys.path.insert(0, os.path.dirname(__file__))
from core.wizard import AttackWizard, WizardPhase
from core.chain_runner import ChainRunner

# Tool registry (same as toolkit.py)
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

# Color scheme
COLORS = {
    'bg_dark': '#1a1a2e',
    'bg_medium': '#16213e',
    'bg_light': '#0f3460',
    'accent': '#e94560',
    'accent2': '#00d9ff',
    'text': '#eaeaea',
    'text_dim': '#888888',
    'success': '#00ff88',
    'warning': '#ffaa00',
    'error': '#ff4444',
}


def load_config(filename):
    """Load YAML config file."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', filename)
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}


PRESETS = load_config('presets.yaml')
TOOL_FORMS = load_config('tool_forms.yaml').get('forms', {})


class ToolkitGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WebExploit Toolkit")
        self.root.geometry("900x700")
        self.root.configure(bg=COLORS['bg_dark'])

        # Get toolkit directory
        self.toolkit_dir = os.path.dirname(os.path.abspath(__file__))

        # Current process
        self.current_process = None

        # Dynamic form fields storage
        self.form_fields = {}
        self.form_frame = None

        # Wizard
        self.wizard = AttackWizard(self.toolkit_dir)
        self.wizard.on_log = self.wizard_log
        self.wizard.on_step_update = self.wizard_step_update
        self.wizard_step_labels = []

        # Chain Runner
        self.chain_runner = ChainRunner()
        self.chain_runner.on_log = self.chain_log
        self.chain_runner.on_step_start = self.chain_step_start
        self.chain_runner.on_step_complete = self.chain_step_complete
        self.chain_runner.on_chain_complete = self.chain_complete

        # Configure styles
        self.setup_styles()

        # Build UI
        self.create_widgets()

    def setup_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure colors
        style.configure('TFrame', background=COLORS['bg_dark'])
        style.configure('TLabel', background=COLORS['bg_dark'], foreground=COLORS['text'])
        style.configure('TButton', background=COLORS['bg_light'], foreground='#ffffff')
        style.configure('Accent.TButton', background=COLORS['accent'], foreground='#ffffff')

        # Combobox - fondo oscuro con texto blanco
        style.configure('TCombobox',
            fieldbackground='#2d2d44',
            background=COLORS['bg_light'],
            foreground='#ffffff',
            arrowcolor='#ffffff',
            selectbackground=COLORS['accent'],
            selectforeground='#ffffff'
        )
        style.map('TCombobox',
            fieldbackground=[('readonly', '#2d2d44'), ('focus', '#3d3d54')],
            foreground=[('readonly', '#ffffff'), ('focus', '#ffffff')],
            selectbackground=[('focus', COLORS['accent'])],
            selectforeground=[('focus', '#ffffff')]
        )

        # Entry
        style.configure('TEntry',
            fieldbackground='#2d2d44',
            foreground='#ffffff',
            insertcolor='#ffffff'
        )

        # Notebook tabs
        style.configure('TNotebook', background=COLORS['bg_dark'])
        style.configure('TNotebook.Tab',
            background=COLORS['bg_medium'],
            foreground='#ffffff',
            padding=[15, 8]
        )
        style.map('TNotebook.Tab',
            background=[('selected', COLORS['accent'])],
            foreground=[('selected', '#ffffff')]
        )

        # LabelFrame
        style.configure('TLabelframe', background=COLORS['bg_dark'])
        style.configure('TLabelframe.Label',
            background=COLORS['bg_dark'],
            foreground=COLORS['accent2']
        )

    def create_widgets(self):
        """Create all UI widgets."""

        # === Header ===
        header_frame = tk.Frame(self.root, bg=COLORS['bg_medium'], pady=15)
        header_frame.pack(fill='x')

        title = tk.Label(
            header_frame,
            text="WebExploit Toolkit",
            font=('Consolas', 24, 'bold'),
            fg=COLORS['accent'],
            bg=COLORS['bg_medium']
        )
        title.pack()

        subtitle = tk.Label(
            header_frame,
            text="Web Exploitation Framework v1.0",
            font=('Consolas', 10),
            fg=COLORS['text_dim'],
            bg=COLORS['bg_medium']
        )
        subtitle.pack()

        # === Notebook (Tabs) ===
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)

        # Tab 1: Tools
        tools_tab = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(tools_tab, text='  TOOLS  ')

        # Tab 2: Wizard
        wizard_tab = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(wizard_tab, text='  WIZARD  ')

        # Tab 3: Attack Chains
        chains_tab = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(chains_tab, text='  CHAINS  ')

        # Build all tabs
        self.create_tools_tab(tools_tab)
        self.create_wizard_tab(wizard_tab)
        self.create_chains_tab(chains_tab)

    def create_tools_tab(self, parent):
        """Create the Tools tab content."""
        # === Main Container ===
        main_frame = tk.Frame(parent, bg=COLORS['bg_dark'], padx=20, pady=10)
        main_frame.pack(fill='both', expand=True)

        # === Tool Selection ===
        select_frame = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        select_frame.pack(fill='x', pady=10)

        # Module selection
        module_frame = tk.Frame(select_frame, bg=COLORS['bg_dark'])
        module_frame.pack(side='left', padx=(0, 20))

        tk.Label(
            module_frame,
            text="MODULE",
            font=('Consolas', 9, 'bold'),
            fg=COLORS['accent2'],
            bg=COLORS['bg_dark']
        ).pack(anchor='w')

        self.module_var = tk.StringVar()
        self.module_combo = ttk.Combobox(
            module_frame,
            textvariable=self.module_var,
            values=list(TOOLS.keys()),
            state='readonly',
            width=15,
            font=('Consolas', 11)
        )
        self.module_combo.pack(pady=5)
        self.module_combo.bind('<<ComboboxSelected>>', self.on_module_change)

        # Tool selection
        tool_frame = tk.Frame(select_frame, bg=COLORS['bg_dark'])
        tool_frame.pack(side='left', padx=(0, 20))

        tk.Label(
            tool_frame,
            text="TOOL",
            font=('Consolas', 9, 'bold'),
            fg=COLORS['accent2'],
            bg=COLORS['bg_dark']
        ).pack(anchor='w')

        self.tool_var = tk.StringVar()
        self.tool_combo = ttk.Combobox(
            tool_frame,
            textvariable=self.tool_var,
            state='readonly',
            width=20,
            font=('Consolas', 11)
        )
        self.tool_combo.pack(pady=5)
        self.tool_combo.bind('<<ComboboxSelected>>', self.on_tool_change)

        # Tool description
        self.tool_desc = tk.Label(
            select_frame,
            text="",
            font=('Consolas', 10, 'italic'),
            fg=COLORS['text_dim'],
            bg=COLORS['bg_dark']
        )
        self.tool_desc.pack(side='left', padx=20)

        # === Preset Selection ===
        preset_frame = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        preset_frame.pack(fill='x', pady=5)

        tk.Label(
            preset_frame,
            text="PRESET",
            font=('Consolas', 9, 'bold'),
            fg=COLORS['accent2'],
            bg=COLORS['bg_dark']
        ).pack(side='left', padx=(0, 10))

        self.preset_var = tk.StringVar(value='standard')
        self.preset_combo = ttk.Combobox(
            preset_frame,
            textvariable=self.preset_var,
            values=['quick', 'standard', 'deep', 'stealth'],
            state='readonly',
            width=15,
            font=('Consolas', 10)
        )
        self.preset_combo.pack(side='left')
        self.preset_combo.bind('<<ComboboxSelected>>', self.on_preset_change)

        self.preset_desc = tk.Label(
            preset_frame,
            text="",
            font=('Consolas', 9, 'italic'),
            fg=COLORS['text_dim'],
            bg=COLORS['bg_dark']
        )
        self.preset_desc.pack(side='left', padx=15)

        # === Dynamic Form Area ===
        self.form_container = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        self.form_container.pack(fill='x', pady=10)

        # Default target field (will be replaced by dynamic form)
        self.form_frame = tk.Frame(self.form_container, bg=COLORS['bg_dark'])
        self.form_frame.pack(fill='x')

        self.create_default_form()

        # === Buttons ===
        btn_frame = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        btn_frame.pack(fill='x', pady=15)

        self.run_btn = tk.Button(
            btn_frame,
            text="RUN",
            font=('Consolas', 12, 'bold'),
            bg=COLORS['accent'],
            fg='white',
            activebackground='#ff6680',
            activeforeground='white',
            relief='flat',
            padx=30,
            pady=8,
            cursor='hand2',
            command=self.run_tool
        )
        self.run_btn.pack(side='left', padx=(0, 10))

        self.stop_btn = tk.Button(
            btn_frame,
            text="STOP",
            font=('Consolas', 12, 'bold'),
            bg=COLORS['bg_light'],
            fg=COLORS['text'],
            activebackground=COLORS['error'],
            activeforeground='white',
            relief='flat',
            padx=30,
            pady=8,
            cursor='hand2',
            command=self.stop_tool,
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=(0, 10))

        self.clear_btn = tk.Button(
            btn_frame,
            text="CLEAR",
            font=('Consolas', 12),
            bg=COLORS['bg_light'],
            fg=COLORS['text'],
            activebackground=COLORS['bg_medium'],
            activeforeground=COLORS['text'],
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2',
            command=self.clear_output
        )
        self.clear_btn.pack(side='left', padx=(0, 10))

        self.help_btn = tk.Button(
            btn_frame,
            text="HELP",
            font=('Consolas', 12),
            bg=COLORS['bg_light'],
            fg=COLORS['text'],
            activebackground=COLORS['bg_medium'],
            activeforeground=COLORS['text'],
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2',
            command=self.show_help
        )
        self.help_btn.pack(side='left')

        # Status indicator
        self.status_label = tk.Label(
            btn_frame,
            text="Ready",
            font=('Consolas', 10),
            fg=COLORS['success'],
            bg=COLORS['bg_dark']
        )
        self.status_label.pack(side='right')

        # === Output Area ===
        output_frame = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        output_frame.pack(fill='both', expand=True, pady=10)

        tk.Label(
            output_frame,
            text="OUTPUT",
            font=('Consolas', 9, 'bold'),
            fg=COLORS['accent2'],
            bg=COLORS['bg_dark']
        ).pack(anchor='w')

        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            font=('Consolas', 10),
            bg='#1e1e2e',
            fg='#ffffff',
            insertbackground='#ffffff',
            relief='flat',
            highlightthickness=1,
            highlightbackground=COLORS['bg_light'],
            highlightcolor=COLORS['accent'],
            wrap='word'
        )
        self.output_text.pack(fill='both', expand=True, pady=5)

        # Configure output tags for colors
        self.output_text.tag_configure('success', foreground=COLORS['success'])
        self.output_text.tag_configure('error', foreground=COLORS['error'])
        self.output_text.tag_configure('warning', foreground=COLORS['warning'])
        self.output_text.tag_configure('info', foreground=COLORS['accent2'])

        # Set default values
        self.module_combo.set('recon')
        self.on_module_change(None)

    def create_wizard_tab(self, parent):
        """Create the Wizard tab content."""
        main_frame = tk.Frame(parent, bg=COLORS['bg_dark'], padx=20, pady=10)
        main_frame.pack(fill='both', expand=True)

        # === Target Input ===
        target_frame = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        target_frame.pack(fill='x', pady=10)

        tk.Label(
            target_frame,
            text="TARGET URL",
            font=('Consolas', 9, 'bold'),
            fg=COLORS['accent2'],
            bg=COLORS['bg_dark']
        ).pack(anchor='w')

        self.wizard_target = tk.Entry(
            target_frame,
            font=('Consolas', 12),
            bg='#2d2d44',
            fg='#ffffff',
            insertbackground='#ffffff',
            relief='flat',
            highlightthickness=1,
            highlightbackground=COLORS['bg_light'],
            highlightcolor=COLORS['accent']
        )
        self.wizard_target.pack(fill='x', pady=5, ipady=8)
        self.wizard_target.insert(0, "https://example.com")

        # === Mode Selection ===
        mode_frame = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        mode_frame.pack(fill='x', pady=10)

        tk.Label(
            mode_frame,
            text="MODE",
            font=('Consolas', 9, 'bold'),
            fg=COLORS['accent2'],
            bg=COLORS['bg_dark']
        ).pack(side='left', padx=(0, 10))

        self.wizard_mode = tk.StringVar(value='full')
        modes = [
            ('Full Audit', 'full', 'Complete recon + scan + vuln assessment'),
            ('Quick Scan', 'quick', 'Fast vulnerability check'),
            ('Stealth', 'stealth', 'Minimal footprint, slow scan'),
        ]

        for text, mode, desc in modes:
            rb = tk.Radiobutton(
                mode_frame,
                text=text,
                variable=self.wizard_mode,
                value=mode,
                bg=COLORS['bg_dark'],
                fg='#ffffff',
                selectcolor='#2d2d44',
                activebackground=COLORS['bg_dark'],
                activeforeground='#ffffff',
                font=('Consolas', 10)
            )
            rb.pack(side='left', padx=10)

        # === Wizard Flow Diagram ===
        flow_frame = tk.LabelFrame(
            main_frame,
            text=" ATTACK FLOW ",
            font=('Consolas', 9, 'bold'),
            fg=COLORS['accent2'],
            bg=COLORS['bg_dark'],
            bd=1
        )
        flow_frame.pack(fill='x', pady=10)

        # Flow steps visualization
        steps_frame = tk.Frame(flow_frame, bg=COLORS['bg_dark'], pady=10)
        steps_frame.pack(fill='x')

        self.wizard_step_labels = []
        phases = [
            ('1. RECON', WizardPhase.RECON),
            ('2. SCAN', WizardPhase.SCAN),
            ('3. VULN', WizardPhase.VULN),
            ('4. EXPLOIT', WizardPhase.EXPLOIT),
            ('5. POST', WizardPhase.POST),
            ('6. REPORT', WizardPhase.REPORT),
        ]

        for i, (name, phase) in enumerate(phases):
            lbl = tk.Label(
                steps_frame,
                text=name,
                font=('Consolas', 10, 'bold'),
                fg=COLORS['text_dim'],
                bg=COLORS['bg_medium'],
                padx=15,
                pady=8
            )
            lbl.pack(side='left', padx=2)
            self.wizard_step_labels.append((lbl, phase))

            if i < len(phases) - 1:
                arrow = tk.Label(
                    steps_frame,
                    text="→",
                    font=('Consolas', 14),
                    fg=COLORS['accent'],
                    bg=COLORS['bg_dark']
                )
                arrow.pack(side='left', padx=2)

        # Progress bar
        self.wizard_progress = ttk.Progressbar(
            flow_frame,
            mode='determinate',
            length=400
        )
        self.wizard_progress.pack(pady=10)

        # === Buttons ===
        btn_frame = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        btn_frame.pack(fill='x', pady=10)

        self.wizard_run_btn = tk.Button(
            btn_frame,
            text="START WIZARD",
            font=('Consolas', 12, 'bold'),
            bg=COLORS['accent'],
            fg='white',
            activebackground='#ff6680',
            relief='flat',
            padx=30,
            pady=8,
            cursor='hand2',
            command=self.run_wizard
        )
        self.wizard_run_btn.pack(side='left', padx=(0, 10))

        self.wizard_stop_btn = tk.Button(
            btn_frame,
            text="STOP",
            font=('Consolas', 12, 'bold'),
            bg=COLORS['bg_light'],
            fg=COLORS['text'],
            relief='flat',
            padx=30,
            pady=8,
            cursor='hand2',
            command=self.stop_wizard,
            state='disabled'
        )
        self.wizard_stop_btn.pack(side='left')

        self.wizard_status = tk.Label(
            btn_frame,
            text="Ready",
            font=('Consolas', 10),
            fg=COLORS['success'],
            bg=COLORS['bg_dark']
        )
        self.wizard_status.pack(side='right')

        # === Output ===
        output_frame = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        output_frame.pack(fill='both', expand=True, pady=10)

        tk.Label(
            output_frame,
            text="WIZARD OUTPUT",
            font=('Consolas', 9, 'bold'),
            fg=COLORS['accent2'],
            bg=COLORS['bg_dark']
        ).pack(anchor='w')

        self.wizard_output = scrolledtext.ScrolledText(
            output_frame,
            font=('Consolas', 10),
            bg='#1e1e2e',
            fg='#ffffff',
            relief='flat',
            height=12,
            wrap='word'
        )
        self.wizard_output.pack(fill='both', expand=True, pady=5)

        # Configure tags
        self.wizard_output.tag_configure('success', foreground=COLORS['success'])
        self.wizard_output.tag_configure('error', foreground=COLORS['error'])
        self.wizard_output.tag_configure('warning', foreground=COLORS['warning'])
        self.wizard_output.tag_configure('info', foreground=COLORS['accent2'])

    def create_chains_tab(self, parent):
        """Create the Attack Chains tab."""
        main_frame = tk.Frame(parent, bg=COLORS['bg_dark'], padx=20, pady=10)
        main_frame.pack(fill='both', expand=True)

        # === Target ===
        target_frame = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        target_frame.pack(fill='x', pady=5)

        tk.Label(target_frame, text="TARGET", font=('Consolas', 9, 'bold'),
                fg=COLORS['accent2'], bg=COLORS['bg_dark']).pack(anchor='w')

        self.chain_target = tk.Entry(target_frame, font=('Consolas', 12),
            bg='#2d2d44', fg='#ffffff', insertbackground='#ffffff',
            relief='flat', highlightthickness=1, highlightbackground=COLORS['bg_light'])
        self.chain_target.pack(fill='x', pady=5, ipady=8)
        self.chain_target.insert(0, "https://example.com")

        # === Chain Selection ===
        select_frame = tk.LabelFrame(main_frame, text=" SELECT CHAIN ",
            font=('Consolas', 9, 'bold'), fg=COLORS['accent2'], bg=COLORS['bg_dark'])
        select_frame.pack(fill='x', pady=10)

        # Category buttons
        cat_frame = tk.Frame(select_frame, bg=COLORS['bg_dark'])
        cat_frame.pack(fill='x', pady=5)

        self.chain_category = tk.StringVar(value='web')
        categories = [('Web', 'web'), ('Web3', 'web3'), ('Exploit', 'exploit'), ('Stealth', 'stealth')]

        for text, cat in categories:
            rb = tk.Radiobutton(cat_frame, text=text, variable=self.chain_category, value=cat,
                bg=COLORS['bg_dark'], fg='#ffffff', selectcolor='#2d2d44',
                activebackground=COLORS['bg_dark'], activeforeground='#ffffff',
                font=('Consolas', 10), command=self.update_chain_list)
            rb.pack(side='left', padx=10)

        # Chain listbox
        list_frame = tk.Frame(select_frame, bg=COLORS['bg_dark'])
        list_frame.pack(fill='x', pady=5, padx=10)

        self.chain_listbox = tk.Listbox(list_frame, font=('Consolas', 10),
            bg='#2d2d44', fg='#ffffff', selectbackground=COLORS['accent'],
            selectforeground='#ffffff', height=4, relief='flat')
        self.chain_listbox.pack(side='left', fill='x', expand=True)
        self.chain_listbox.bind('<<ListboxSelect>>', self.on_chain_select)

        # Chain info
        self.chain_info = tk.Label(select_frame, text="", font=('Consolas', 9),
            fg=COLORS['text_dim'], bg=COLORS['bg_dark'], wraplength=600, justify='left')
        self.chain_info.pack(pady=5)

        # === Progress ===
        progress_frame = tk.LabelFrame(main_frame, text=" PROGRESS ",
            font=('Consolas', 9, 'bold'), fg=COLORS['accent2'], bg=COLORS['bg_dark'])
        progress_frame.pack(fill='x', pady=10)

        self.chain_progress = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        self.chain_progress.pack(pady=10)

        self.chain_step_label = tk.Label(progress_frame, text="Ready",
            font=('Consolas', 10), fg=COLORS['text'], bg=COLORS['bg_dark'])
        self.chain_step_label.pack()

        # === Buttons ===
        btn_frame = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        btn_frame.pack(fill='x', pady=10)

        self.chain_run_btn = tk.Button(btn_frame, text="RUN CHAIN",
            font=('Consolas', 12, 'bold'), bg=COLORS['accent'], fg='white',
            relief='flat', padx=30, pady=8, cursor='hand2', command=self.run_chain)
        self.chain_run_btn.pack(side='left', padx=(0, 10))

        self.chain_stop_btn = tk.Button(btn_frame, text="STOP",
            font=('Consolas', 12, 'bold'), bg=COLORS['bg_light'], fg=COLORS['text'],
            relief='flat', padx=30, pady=8, cursor='hand2', command=self.stop_chain, state='disabled')
        self.chain_stop_btn.pack(side='left')

        self.chain_status = tk.Label(btn_frame, text="Ready", font=('Consolas', 10),
            fg=COLORS['success'], bg=COLORS['bg_dark'])
        self.chain_status.pack(side='right')

        # === Output ===
        output_frame = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        output_frame.pack(fill='both', expand=True, pady=10)

        tk.Label(output_frame, text="CHAIN OUTPUT", font=('Consolas', 9, 'bold'),
            fg=COLORS['accent2'], bg=COLORS['bg_dark']).pack(anchor='w')

        self.chain_output = scrolledtext.ScrolledText(output_frame, font=('Consolas', 10),
            bg='#1e1e2e', fg='#ffffff', relief='flat', height=10, wrap='word')
        self.chain_output.pack(fill='both', expand=True, pady=5)

        self.chain_output.tag_configure('success', foreground=COLORS['success'])
        self.chain_output.tag_configure('error', foreground=COLORS['error'])
        self.chain_output.tag_configure('warning', foreground=COLORS['warning'])
        self.chain_output.tag_configure('info', foreground=COLORS['accent2'])

        # Initialize chain list
        self.chain_data = {}
        self.update_chain_list()

    def update_chain_list(self):
        """Update chain listbox based on category."""
        self.chain_listbox.delete(0, 'end')
        category = self.chain_category.get()

        chains = self.chain_runner.get_chains_by_category(category)
        self.chain_data = {c['name']: c for c in chains}

        for chain in chains:
            self.chain_listbox.insert('end', f"{chain['name']} ({chain.get('estimated_time', '?')})")

        if chains:
            self.chain_listbox.selection_set(0)
            self.on_chain_select(None)

    def on_chain_select(self, event):
        """Handle chain selection."""
        sel = self.chain_listbox.curselection()
        if not sel:
            return
        name = self.chain_listbox.get(sel[0]).split(' (')[0]
        chain = self.chain_data.get(name, {})
        desc = chain.get('description', '')
        steps = len(chain.get('steps', []))
        self.chain_info.config(text=f"{desc}\nSteps: {steps}")

    def run_chain(self):
        """Run selected attack chain."""
        target = self.chain_target.get().strip()
        if not target:
            messagebox.showwarning("Warning", "Enter a target")
            return

        sel = self.chain_listbox.curselection()
        if not sel:
            messagebox.showwarning("Warning", "Select a chain")
            return

        name = self.chain_listbox.get(sel[0]).split(' (')[0]
        chain = self.chain_data.get(name)
        if not chain:
            return

        chain_id = chain.get('id')

        self.chain_output.delete(1.0, 'end')
        self.chain_progress['value'] = 0
        self.chain_run_btn.config(state='disabled')
        self.chain_stop_btn.config(state='normal')
        self.chain_status.config(text="Running...", fg=COLORS['warning'])

        thread = threading.Thread(target=self.chain_runner.run_chain, args=(chain_id, target))
        thread.daemon = True
        thread.start()

    def stop_chain(self):
        """Stop running chain."""
        self.chain_runner.stop()
        self.chain_run_btn.config(state='normal')
        self.chain_stop_btn.config(state='disabled')
        self.chain_status.config(text="Stopped", fg=COLORS['warning'])

    def chain_log(self, msg: str, level: str = "info"):
        """Chain runner log callback."""
        tag = level if level in ('success', 'error', 'warning', 'info') else None
        self.root.after(0, self._chain_append_output, msg + '\n', tag)

    def _chain_append_output(self, text, tag=None):
        self.chain_output.insert('end', text, tag)
        self.chain_output.see('end')

    def chain_step_start(self, step):
        """Chain step start callback."""
        self.root.after(0, self._update_chain_step, step, "running")

    def chain_step_complete(self, step):
        """Chain step complete callback."""
        self.root.after(0, self._update_chain_step, step, step.status)

    def _update_chain_step(self, step, status):
        progress = self.chain_runner.get_progress()
        self.chain_progress['value'] = progress
        self.chain_step_label.config(text=f"{step.step_name}: {status}")

    def chain_complete(self, result):
        """Chain complete callback."""
        self.root.after(0, self._chain_finished, result)

    def _chain_finished(self, result):
        self.chain_run_btn.config(state='normal')
        self.chain_stop_btn.config(state='disabled')
        self.chain_progress['value'] = 100

        if result.status == "completed":
            self.chain_status.config(text="Completed", fg=COLORS['success'])
        elif result.status == "partial":
            self.chain_status.config(text="Partial", fg=COLORS['warning'])
        else:
            self.chain_status.config(text="Failed", fg=COLORS['error'])

        self.chain_step_label.config(text=f"Findings: {len(result.aggregated_findings)}")

    def run_wizard(self):
        """Start the attack wizard."""
        target = self.wizard_target.get().strip()
        if not target:
            messagebox.showwarning("Warning", "Enter a target URL")
            return

        mode = self.wizard_mode.get()

        # Reset UI
        self.wizard_output.delete(1.0, 'end')
        self.wizard_progress['value'] = 0
        for lbl, _ in self.wizard_step_labels:
            lbl.config(fg=COLORS['text_dim'], bg=COLORS['bg_medium'])

        self.wizard_run_btn.config(state='disabled')
        self.wizard_stop_btn.config(state='normal')
        self.wizard_status.config(text="Running...", fg=COLORS['warning'])

        # Run in thread
        thread = threading.Thread(target=self.wizard.run_wizard, args=(target, mode))
        thread.daemon = True
        thread.start()

    def stop_wizard(self):
        """Stop the wizard."""
        self.wizard.stop()
        self.wizard_run_btn.config(state='normal')
        self.wizard_stop_btn.config(state='disabled')
        self.wizard_status.config(text="Stopped", fg=COLORS['warning'])

    def wizard_log(self, msg: str, level: str = "info"):
        """Callback for wizard logging."""
        tag = level if level in ('success', 'error', 'warning', 'info') else None
        self.root.after(0, self._wizard_append_output, msg + '\n', tag)

    def _wizard_append_output(self, text, tag=None):
        self.wizard_output.insert('end', text, tag)
        self.wizard_output.see('end')

    def wizard_step_update(self, step):
        """Callback for wizard step updates."""
        self.root.after(0, self._update_wizard_ui, step)

    def _update_wizard_ui(self, step):
        # Update progress
        progress = self.wizard.get_progress()
        self.wizard_progress['value'] = progress

        # Update phase indicators
        for lbl, phase in self.wizard_step_labels:
            if phase == step.phase:
                if step.status == "running":
                    lbl.config(fg='white', bg=COLORS['warning'])
                elif step.status == "completed":
                    lbl.config(fg='white', bg=COLORS['success'])
                elif step.status == "failed":
                    lbl.config(fg='white', bg=COLORS['error'])

        # Check if done
        if progress >= 100:
            self.wizard_run_btn.config(state='normal')
            self.wizard_stop_btn.config(state='disabled')
            self.wizard_status.config(text="Completed", fg=COLORS['success'])

    def on_module_change(self, event):
        """Handle module selection change."""
        module = self.module_var.get()
        if module in TOOLS:
            tools = list(TOOLS[module].keys())
            self.tool_combo['values'] = tools
            if tools:
                self.tool_combo.set(tools[0])
                self.on_tool_change(None)

    def on_tool_change(self, event):
        """Handle tool selection change."""
        module = self.module_var.get()
        tool = self.tool_var.get()
        if module in TOOLS and tool in TOOLS[module]:
            desc = TOOLS[module][tool][1]
            self.tool_desc.config(text=f"// {desc}")
            self.build_dynamic_form(tool)
            self.update_presets(tool)

    def on_preset_change(self, event):
        """Handle preset selection change."""
        tool = self.tool_var.get()
        preset = self.preset_var.get()
        self.apply_preset(tool, preset)

    def create_default_form(self):
        """Create default target form."""
        self.form_fields = {}
        tk.Label(
            self.form_frame,
            text="TARGET",
            font=('Consolas', 9, 'bold'),
            fg=COLORS['accent2'],
            bg=COLORS['bg_dark']
        ).pack(anchor='w')

        self.form_fields['target'] = tk.Entry(
            self.form_frame,
            font=('Consolas', 12),
            bg='#2d2d44',
            fg='#ffffff',
            insertbackground='#ffffff',
            relief='flat',
            highlightthickness=1,
            highlightbackground=COLORS['bg_light'],
            highlightcolor=COLORS['accent']
        )
        self.form_fields['target'].pack(fill='x', pady=5, ipady=8)
        self.form_fields['target'].insert(0, "example.com")

    def build_dynamic_form(self, tool_name):
        """Build form fields dynamically based on tool configuration."""
        # Clear existing form
        for widget in self.form_frame.winfo_children():
            widget.destroy()
        self.form_fields = {}

        # Check if tool has form definition
        form_def = TOOL_FORMS.get(tool_name) or TOOL_FORMS.get(tool_name.replace('_', ''))
        if not form_def:
            self.create_default_form()
            return

        fields = form_def.get('fields', [])
        for field in fields:
            if field.get('name') == 'preset':
                continue  # Preset handled separately

            frame = tk.Frame(self.form_frame, bg=COLORS['bg_dark'])
            frame.pack(fill='x', pady=3)

            label = field.get('label', field['name'].upper())
            tk.Label(
                frame,
                text=label,
                font=('Consolas', 9, 'bold'),
                fg=COLORS['accent2'],
                bg=COLORS['bg_dark'],
                width=12,
                anchor='w'
            ).pack(side='left')

            field_type = field.get('type', 'text')

            if field_type in ('text', 'url', 'number'):
                entry = tk.Entry(
                    frame,
                    font=('Consolas', 11),
                    bg='#2d2d44',
                    fg='#ffffff',
                    insertbackground='#ffffff',
                    relief='flat',
                    highlightthickness=1,
                    highlightbackground=COLORS['bg_light'],
                    highlightcolor=COLORS['accent']
                )
                entry.pack(side='left', fill='x', expand=True, ipady=4)
                if field.get('placeholder'):
                    entry.insert(0, field['placeholder'])
                if field.get('default'):
                    entry.delete(0, 'end')
                    entry.insert(0, str(field['default']))
                self.form_fields[field['name']] = entry

            elif field_type == 'select':
                var = tk.StringVar(value=field.get('default', ''))
                combo = ttk.Combobox(
                    frame,
                    textvariable=var,
                    values=field.get('options', []),
                    state='readonly',
                    width=20,
                    font=('Consolas', 10)
                )
                combo.pack(side='left')
                self.form_fields[field['name']] = var

            elif field_type == 'multiselect':
                var = tk.StringVar(value=','.join(field.get('default', [])))
                entry = tk.Entry(
                    frame,
                    font=('Consolas', 11),
                    bg='#2d2d44',
                    fg='#ffffff',
                    textvariable=var,
                    insertbackground='#ffffff',
                    relief='flat'
                )
                entry.pack(side='left', fill='x', expand=True, ipady=4)
                opts = ', '.join(field.get('options', []))
                tk.Label(frame, text=f"({opts})", font=('Consolas', 8),
                        fg=COLORS['text_dim'], bg=COLORS['bg_dark']).pack(side='left', padx=5)
                self.form_fields[field['name']] = var

            elif field_type == 'slider':
                var = tk.IntVar(value=field.get('default', 1))
                scale = tk.Scale(
                    frame,
                    from_=field.get('min', 1),
                    to=field.get('max', 100),
                    orient='horizontal',
                    variable=var,
                    bg=COLORS['bg_dark'],
                    fg='#ffffff',
                    highlightthickness=0,
                    troughcolor='#2d2d44',
                    activebackground=COLORS['accent'],
                    length=150
                )
                scale.pack(side='left')
                self.form_fields[field['name']] = var

            elif field_type == 'checkbox':
                var = tk.BooleanVar(value=field.get('default', False))
                cb = tk.Checkbutton(
                    frame,
                    variable=var,
                    bg=COLORS['bg_dark'],
                    fg='#ffffff',
                    selectcolor='#2d2d44',
                    activebackground=COLORS['bg_dark'],
                    activeforeground='#ffffff'
                )
                cb.pack(side='left')
                self.form_fields[field['name']] = var

    def update_presets(self, tool_name):
        """Update preset dropdown based on tool."""
        # Map tool to preset category
        preset_map = {
            'subdomain': ('recon', 'active'),
            'port_scan': ('scanning', 'port'),
            'port': ('scanning', 'port'),
            'dir_fuzzing': ('scanning', 'fuzzing'),
            'dir': ('scanning', 'fuzzing'),
            'sqli': ('vuln_assessment', 'sqli'),
            'xss': ('vuln_assessment', 'xss'),
            'lfi': ('vuln_assessment', 'lfi'),
            'ssrf': ('vuln_assessment', 'ssrf'),
        }

        if tool_name in preset_map:
            cat, subcat = preset_map[tool_name]
            if cat in PRESETS and subcat in PRESETS[cat]:
                presets = list(PRESETS[cat][subcat].keys())
                self.preset_combo['values'] = presets
                if presets:
                    self.preset_combo.set(presets[1] if len(presets) > 1 else presets[0])
                    self.apply_preset(tool_name, self.preset_var.get())
        else:
            self.preset_combo['values'] = ['quick', 'standard', 'deep']
            self.preset_combo.set('standard')

    def apply_preset(self, tool_name, preset_name):
        """Apply preset values to form fields."""
        preset_map = {
            'subdomain': ('recon', 'active'),
            'port_scan': ('scanning', 'port'),
            'port': ('scanning', 'port'),
            'dir_fuzzing': ('scanning', 'fuzzing'),
            'dir': ('scanning', 'fuzzing'),
            'sqli': ('vuln_assessment', 'sqli'),
            'xss': ('vuln_assessment', 'xss'),
            'lfi': ('vuln_assessment', 'lfi'),
            'ssrf': ('vuln_assessment', 'ssrf'),
        }

        if tool_name not in preset_map:
            return

        cat, subcat = preset_map[tool_name]
        if cat not in PRESETS or subcat not in PRESETS[cat]:
            return

        preset_data = PRESETS[cat][subcat].get(preset_name, {})
        if not preset_data:
            return

        # Update description
        desc = preset_data.get('description', '')
        self.preset_desc.config(text=f"// {desc}")

        # Apply values to form fields
        for key, value in preset_data.items():
            if key in self.form_fields:
                field = self.form_fields[key]
                if isinstance(field, tk.Entry):
                    field.delete(0, 'end')
                    field.insert(0, str(value))
                elif isinstance(field, (tk.StringVar, tk.IntVar, tk.BooleanVar)):
                    if isinstance(value, list):
                        field.set(','.join(map(str, value)))
                    else:
                        field.set(value)

    def append_output(self, text, tag=None):
        """Append text to output area."""
        self.output_text.config(state='normal')
        if tag:
            self.output_text.insert('end', text, tag)
        else:
            # Auto-detect tag based on content
            if '[+]' in text:
                self.output_text.insert('end', text, 'success')
            elif '[-]' in text or 'error' in text.lower():
                self.output_text.insert('end', text, 'error')
            elif '[!]' in text or 'warning' in text.lower():
                self.output_text.insert('end', text, 'warning')
            elif '[*]' in text:
                self.output_text.insert('end', text, 'info')
            else:
                self.output_text.insert('end', text)
        self.output_text.see('end')
        self.output_text.config(state='normal')

    def clear_output(self):
        """Clear output area."""
        self.output_text.config(state='normal')
        self.output_text.delete(1.0, 'end')

    def set_status(self, text, color=None):
        """Update status label."""
        self.status_label.config(text=text, fg=color or COLORS['text'])

    def get_form_values(self):
        """Get all form field values as dict."""
        values = {}
        for name, field in self.form_fields.items():
            if isinstance(field, tk.Entry):
                values[name] = field.get().strip()
            elif isinstance(field, (tk.StringVar, tk.IntVar)):
                values[name] = field.get()
            elif isinstance(field, tk.BooleanVar):
                values[name] = field.get()
        return values

    def build_args_from_form(self, values):
        """Convert form values to command line arguments."""
        args = []
        # Get target (url, target, or domain field)
        target = values.get('url') or values.get('target') or values.get('domain', '')
        if target:
            args.append(target)

        # Add preset
        preset = self.preset_var.get()
        if preset:
            args.extend(['--preset', preset])

        # Add other fields as arguments
        for key, val in values.items():
            if key in ('url', 'target', 'domain', 'preset'):
                continue
            if val is None or val == '':
                continue
            if isinstance(val, bool):
                if val:
                    args.append(f'--{key}')
            else:
                args.extend([f'--{key}', str(val)])
        return args

    def run_tool(self):
        """Execute selected tool."""
        module = self.module_var.get()
        tool = self.tool_var.get()

        if not module or not tool:
            messagebox.showwarning("Warning", "Select a module and tool")
            return

        # Get form values
        values = self.get_form_values()
        target = values.get('url') or values.get('target') or values.get('domain', '')

        if not target:
            messagebox.showwarning("Warning", "Enter a target")
            return

        # Get tool path
        tool_path = os.path.join(self.toolkit_dir, TOOLS[module][tool][0])

        if not os.path.exists(tool_path):
            messagebox.showerror("Error", f"Tool not found: {tool_path}")
            return

        # Build command from form values
        cmd = [sys.executable, tool_path]
        cmd.extend(self.build_args_from_form(values))

        # Update UI
        self.run_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.set_status("Running...", COLORS['warning'])

        self.append_output(f"\n{'='*60}\n", 'info')
        self.append_output(f"[*] Executing: {' '.join(cmd)}\n", 'info')
        self.append_output(f"{'='*60}\n\n", 'info')

        # Run in thread
        thread = threading.Thread(target=self.execute_command, args=(cmd,))
        thread.daemon = True
        thread.start()

    def execute_command(self, cmd):
        """Execute command in background thread."""
        try:
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=self.toolkit_dir
            )

            for line in self.current_process.stdout:
                self.root.after(0, self.append_output, line)

            self.current_process.wait()

            if self.current_process.returncode == 0:
                self.root.after(0, self.append_output, "\n[+] Completed successfully\n", 'success')
                self.root.after(0, self.set_status, "Completed", COLORS['success'])
            else:
                self.root.after(0, self.append_output, f"\n[-] Exited with code {self.current_process.returncode}\n", 'error')
                self.root.after(0, self.set_status, "Error", COLORS['error'])

        except Exception as e:
            self.root.after(0, self.append_output, f"\n[-] Error: {e}\n", 'error')
            self.root.after(0, self.set_status, "Error", COLORS['error'])
        finally:
            self.current_process = None
            self.root.after(0, self.reset_buttons)

    def reset_buttons(self):
        """Reset button states."""
        self.run_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

    def stop_tool(self):
        """Stop running tool."""
        if self.current_process:
            self.current_process.terminate()
            self.append_output("\n[!] Process terminated\n", 'warning')
            self.set_status("Stopped", COLORS['warning'])

    def show_help(self):
        """Show help for selected tool."""
        module = self.module_var.get()
        tool = self.tool_var.get()

        if not module or not tool:
            return

        tool_path = os.path.join(self.toolkit_dir, TOOLS[module][tool][0])
        cmd = [sys.executable, tool_path, '--help']

        self.append_output(f"\n{'='*60}\n", 'info')
        self.append_output(f"[*] Help: {tool}\n", 'info')
        self.append_output(f"{'='*60}\n\n", 'info')

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.toolkit_dir)
            self.append_output(result.stdout)
            if result.stderr:
                self.append_output(result.stderr, 'error')
        except Exception as e:
            self.append_output(f"Error: {e}\n", 'error')


def main():
    root = tk.Tk()

    # Center window
    root.update_idletasks()
    width = 900
    height = 700
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    # Set icon if available
    try:
        root.iconname('WebExploit')
    except:
        pass

    app = ToolkitGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
