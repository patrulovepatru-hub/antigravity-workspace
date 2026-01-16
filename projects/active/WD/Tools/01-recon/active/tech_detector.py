#!/usr/bin/env python3
"""
Technology Stack Detector
Identify web technologies, frameworks, and CMS.
"""

import sys
import argparse
import re
sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import success, error, warning, info, banner, HTTPClient, normalize_url

TECH_SIGNATURES = {
    'cms': {
        'WordPress': [
            (r'/wp-content/', 'path'),
            (r'/wp-includes/', 'path'),
            (r'wp-json', 'body'),
            (r'<meta name="generator" content="WordPress', 'body'),
        ],
        'Drupal': [
            (r'Drupal', 'header:X-Generator'),
            (r'/sites/default/files', 'body'),
            (r'Drupal.settings', 'body'),
        ],
        'Joomla': [
            (r'/media/jui/', 'body'),
            (r'/components/com_', 'body'),
            (r'<meta name="generator" content="Joomla', 'body'),
        ],
        'Magento': [
            (r'/skin/frontend/', 'body'),
            (r'Mage.Cookies', 'body'),
            (r'/js/mage/', 'body'),
        ],
        'Shopify': [
            (r'cdn.shopify.com', 'body'),
            (r'Shopify.theme', 'body'),
        ],
    },
    'frameworks': {
        'React': [
            (r'react', 'body'),
            (r'_reactRootContainer', 'body'),
            (r'data-reactroot', 'body'),
        ],
        'Vue.js': [
            (r'vue\.js', 'body'),
            (r'data-v-[a-f0-9]', 'body'),
            (r'__vue__', 'body'),
        ],
        'Angular': [
            (r'ng-version', 'body'),
            (r'ng-app', 'body'),
            (r'angular\.js', 'body'),
        ],
        'jQuery': [
            (r'jquery[.-]?\d', 'body'),
            (r'jQuery', 'body'),
        ],
        'Bootstrap': [
            (r'bootstrap\.min\.(css|js)', 'body'),
            (r'class="[^"]*\b(container|row|col-)', 'body'),
        ],
        'Laravel': [
            (r'laravel_session', 'cookie'),
            (r'XSRF-TOKEN', 'cookie'),
        ],
        'Django': [
            (r'csrfmiddlewaretoken', 'body'),
            (r'__admin_media_prefix__', 'body'),
        ],
        'Rails': [
            (r'csrf-token', 'body'),
            (r'data-turbolinks', 'body'),
            (r'_session_id', 'cookie'),
        ],
        'Express': [
            (r'Express', 'header:X-Powered-By'),
        ],
        'ASP.NET': [
            (r'ASP\.NET', 'header:X-Powered-By'),
            (r'__VIEWSTATE', 'body'),
            (r'\.aspx', 'path'),
        ],
        'Next.js': [
            (r'_next/static', 'body'),
            (r'__NEXT_DATA__', 'body'),
        ],
        'Nuxt.js': [
            (r'_nuxt', 'body'),
            (r'__NUXT__', 'body'),
        ],
    },
    'servers': {
        'nginx': [(r'nginx', 'header:Server')],
        'Apache': [(r'Apache', 'header:Server')],
        'IIS': [(r'IIS', 'header:Server'), (r'Microsoft-IIS', 'header:Server')],
        'Cloudflare': [(r'cloudflare', 'header:Server'), (r'cf-ray', 'header:cf-ray')],
        'AWS': [(r'AmazonS3', 'header:Server'), (r'awselb', 'header:Server')],
        'Varnish': [(r'Varnish', 'header:Via'), (r'X-Varnish', 'header:X-Varnish')],
    },
    'security': {
        'WAF-Cloudflare': [(r'cf-ray', 'header:cf-ray')],
        'WAF-Akamai': [(r'AkamaiGHost', 'header:Server')],
        'WAF-Sucuri': [(r'Sucuri', 'header:Server'), (r'x-sucuri', 'header:x-sucuri-id')],
        'WAF-ModSecurity': [(r'Mod_Security', 'header:Server'), (r'NOYB', 'header:Server')],
    },
    'analytics': {
        'Google Analytics': [(r'google-analytics\.com/analytics', 'body'), (r'gtag\(', 'body')],
        'Google Tag Manager': [(r'googletagmanager\.com', 'body')],
        'Facebook Pixel': [(r'connect\.facebook\.net', 'body'), (r'fbq\(', 'body')],
        'Hotjar': [(r'hotjar\.com', 'body')],
    }
}


class TechDetector:
    def __init__(self, url: str, proxy: str = None):
        self.url = normalize_url(url)
        self.client = HTTPClient(proxy=proxy)
        self.detected = {}

    def scan(self) -> dict:
        """Scan target for technologies."""
        try:
            resp = self.client.get(self.url)
            body = resp.text
            headers = dict(resp.headers)
            cookies = dict(resp.cookies)

            for category, techs in TECH_SIGNATURES.items():
                self.detected[category] = []

                for tech_name, signatures in techs.items():
                    for pattern, location in signatures:
                        found = False

                        if location == 'body':
                            if re.search(pattern, body, re.IGNORECASE):
                                found = True
                        elif location == 'path':
                            if re.search(pattern, body, re.IGNORECASE):
                                found = True
                        elif location.startswith('header:'):
                            header_name = location.split(':')[1]
                            header_value = headers.get(header_name, '')
                            if re.search(pattern, header_value, re.IGNORECASE):
                                found = True
                        elif location == 'cookie':
                            for cookie_name in cookies:
                                if re.search(pattern, cookie_name, re.IGNORECASE):
                                    found = True
                                    break

                        if found:
                            if tech_name not in self.detected[category]:
                                self.detected[category].append(tech_name)
                            break

            # Additional checks
            self._check_robots_txt()
            self._check_sitemap()

            return self.detected

        except Exception as e:
            error(f"Scan failed: {e}")
            return {}

    def _check_robots_txt(self):
        """Check robots.txt for additional hints."""
        try:
            resp = self.client.get(f"{self.url}/robots.txt")
            if resp.status_code == 200:
                content = resp.text.lower()
                if 'wp-admin' in content or 'wp-content' in content:
                    if 'WordPress' not in self.detected.get('cms', []):
                        self.detected.setdefault('cms', []).append('WordPress')
        except:
            pass

    def _check_sitemap(self):
        """Check sitemap for hints."""
        try:
            resp = self.client.get(f"{self.url}/sitemap.xml")
            if resp.status_code == 200:
                self.detected.setdefault('features', []).append('Sitemap')
        except:
            pass


def main():
    parser = argparse.ArgumentParser(description='Technology Stack Detector')
    parser.add_argument('url', help='Target URL')
    parser.add_argument('-p', '--proxy', help='Proxy URL')
    parser.add_argument('-o', '--output', help='Output file (JSON)')
    args = parser.parse_args()

    banner("Technology Detector")
    info(f"Target: {args.url}")

    detector = TechDetector(args.url, proxy=args.proxy)
    results = detector.scan()

    for category, techs in results.items():
        if techs:
            print(f"\n[{category.upper()}]")
            for tech in techs:
                success(f"  {tech}")

    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump({'url': args.url, 'technologies': results}, f, indent=2)
        success(f"Results saved to {args.output}")


if __name__ == '__main__':
    main()
