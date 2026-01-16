#!/usr/bin/env python3
"""HTTP client utilities with common headers and session management."""

import requests
import urllib3
from typing import Dict, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

USER_AGENTS = {
    'chrome_win': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'firefox_win': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'safari_mac': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'edge_win': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'googlebot': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'curl': 'curl/8.4.0',
}

class HTTPClient:
    def __init__(self, proxy: Optional[str] = None, timeout: int = 30, verify_ssl: bool = False):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.verify = verify_ssl
        self.timeout = timeout

        if proxy:
            self.session.proxies = {'http': proxy, 'https': proxy}

        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def get(self, url: str, **kwargs) -> requests.Response:
        return self.session.get(url, timeout=self.timeout, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        return self.session.post(url, timeout=self.timeout, **kwargs)

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        return self.session.request(method, url, timeout=self.timeout, **kwargs)

    def set_header(self, key: str, value: str):
        self.session.headers[key] = value

    def set_cookie(self, name: str, value: str, domain: str = ''):
        self.session.cookies.set(name, value, domain=domain)

    def set_user_agent(self, agent_type: str):
        if agent_type in USER_AGENTS:
            self.session.headers['User-Agent'] = USER_AGENTS[agent_type]
