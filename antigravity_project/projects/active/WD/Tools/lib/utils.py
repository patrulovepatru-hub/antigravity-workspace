#!/usr/bin/env python3
"""Common utilities for the toolkit."""

import re
import os
import json
import hashlib
import base64
from urllib.parse import urlparse, urljoin, parse_qs, urlencode
from typing import List, Dict, Optional, Tuple
from datetime import datetime

def normalize_url(url: str) -> str:
    """Normalize URL with scheme."""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url.rstrip('/')

def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    parsed = urlparse(normalize_url(url))
    return parsed.netloc

def extract_base_url(url: str) -> str:
    """Extract base URL (scheme + domain)."""
    parsed = urlparse(normalize_url(url))
    return f"{parsed.scheme}://{parsed.netloc}"

def extract_path(url: str) -> str:
    """Extract path from URL."""
    parsed = urlparse(url)
    return parsed.path or '/'

def extract_params(url: str) -> Dict[str, List[str]]:
    """Extract query parameters from URL."""
    parsed = urlparse(url)
    return parse_qs(parsed.query)

def build_url(base: str, path: str, params: Optional[Dict] = None) -> str:
    """Build URL from components."""
    url = urljoin(base, path)
    if params:
        url += '?' + urlencode(params, doseq=True)
    return url

def is_valid_url(url: str) -> bool:
    """Check if URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def is_same_origin(url1: str, url2: str) -> bool:
    """Check if two URLs have the same origin."""
    p1, p2 = urlparse(url1), urlparse(url2)
    return (p1.scheme == p2.scheme and p1.netloc == p2.netloc)

def read_file_lines(filepath: str) -> List[str]:
    """Read lines from file, stripping whitespace."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def write_results(filepath: str, data: any, format: str = 'json'):
    """Write results to file."""
    os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
    with open(filepath, 'w') as f:
        if format == 'json':
            json.dump(data, f, indent=2, default=str)
        else:
            f.write(str(data))

def generate_timestamp() -> str:
    """Generate timestamp for filenames."""
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()

def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def b64encode(text: str) -> str:
    return base64.b64encode(text.encode()).decode()

def b64decode(text: str) -> str:
    return base64.b64decode(text.encode()).decode()

def extract_emails(text: str) -> List[str]:
    """Extract email addresses from text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(pattern, text)))

def extract_urls(text: str) -> List[str]:
    """Extract URLs from text."""
    pattern = r'https?://[^\s<>"\'}\])]+'
    return list(set(re.findall(pattern, text)))

def extract_ips(text: str) -> List[str]:
    """Extract IP addresses from text."""
    pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    return list(set(re.findall(pattern, text)))
