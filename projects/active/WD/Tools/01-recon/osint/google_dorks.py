#!/usr/bin/env python3
"""
Google Dorks Generator
Generate targeted Google search queries for reconnaissance.
"""

import sys
import argparse
from urllib.parse import quote_plus
sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')
from lib import banner, info, success

DORK_CATEGORIES = {
    'sensitive_files': [
        ('Configuration files', 'site:{domain} ext:xml | ext:conf | ext:cnf | ext:reg | ext:inf | ext:rdp | ext:cfg | ext:txt | ext:ora | ext:ini | ext:env'),
        ('Database files', 'site:{domain} ext:sql | ext:dbf | ext:mdb'),
        ('Log files', 'site:{domain} ext:log'),
        ('Backup files', 'site:{domain} ext:bkf | ext:bkp | ext:bak | ext:old | ext:backup'),
        ('PHP errors/config', 'site:{domain} ext:php intitle:phpinfo "published by the PHP Group"'),
        ('Login pages', 'site:{domain} inurl:login | inurl:signin | intitle:Login | intitle:"sign in" | inurl:auth'),
        ('Open redirects', 'site:{domain} inurl:redir | inurl:url= | inurl:return= | inurl:next= | inurl:redirect='),
        ('API endpoints', 'site:{domain} inurl:api | site:{domain} intitle:api'),
    ],
    'exposed_data': [
        ('Email addresses', 'site:{domain} intext:"@{domain}"'),
        ('Passwords', 'site:{domain} intext:password | intext:passwd filetype:txt'),
        ('Usernames', 'site:{domain} intext:username | intext:user | intext:userid | intext:user_id'),
        ('Sensitive docs', 'site:{domain} filetype:doc | filetype:docx | filetype:odt | filetype:pdf | filetype:rtf | filetype:sxw | filetype:psw | filetype:ppt | filetype:pptx | filetype:pps | filetype:csv'),
        ('SQL errors', 'site:{domain} intext:"sql syntax near" | intext:"syntax error has occurred" | intext:"incorrect syntax near" | intext:"unexpected end of SQL command" | intext:"Warning: mysql_connect()" | intext:"Warning: mysql_query()" | intext:"Warning: pg_connect()"'),
    ],
    'directories': [
        ('Directory listing', 'site:{domain} intitle:index.of'),
        ('Apache status', 'site:{domain} intitle:"Apache Status"'),
        ('Admin pages', 'site:{domain} inurl:admin | inurl:administrator | inurl:adm'),
        ('phpMyAdmin', 'site:{domain} inurl:phpmyadmin'),
        ('cPanel', 'site:{domain} inurl:cpanel | inurl:2082 | inurl:2083'),
        ('Uploads', 'site:{domain} inurl:upload | inurl:uploads'),
    ],
    'git_exposed': [
        ('Git folders', 'site:{domain} inurl:".git"'),
        ('Git config', 'site:{domain} ".git/config"'),
        ('GitLab files', 'site:{domain} inurl:gitlab'),
    ],
    'cloud_storage': [
        ('AWS S3', 'site:s3.amazonaws.com "{domain}"'),
        ('Azure Blob', 'site:blob.core.windows.net "{domain}"'),
        ('Google Storage', 'site:storage.googleapis.com "{domain}"'),
    ],
    'subdomains': [
        ('Related sites', 'site:*.{domain}'),
        ('Exclude www', 'site:*.{domain} -www'),
    ],
    'wordpress': [
        ('WP Config', 'site:{domain} inurl:wp-config.php'),
        ('WP Debug', 'site:{domain} inurl:wp-content/debug.log'),
        ('WP Uploads', 'site:{domain} inurl:wp-content/uploads'),
        ('WP Plugins', 'site:{domain} inurl:wp-content/plugins'),
    ],
    'vulnerabilities': [
        ('XSS vectors', 'site:{domain} inurl:q= | inurl:s= | inurl:search= | inurl:query= | inurl:keyword='),
        ('LFI vectors', 'site:{domain} inurl:page= | inurl:file= | inurl:path= | inurl:include= | inurl:dir= | inurl:document='),
        ('RCE vectors', 'site:{domain} inurl:cmd= | inurl:exec= | inurl:command= | inurl:execute= | inurl:run= | inurl:ping='),
        ('SQLi vectors', 'site:{domain} inurl:id= | inurl:pid= | inurl:category= | inurl:item= | inurl:product= | inurl:news='),
        ('SSRF vectors', 'site:{domain} inurl:url= | inurl:uri= | inurl:dest= | inurl:redirect= | inurl:link= | inurl:proxy='),
    ],
    'third_party': [
        ('Pastebin leaks', 'site:pastebin.com "{domain}"'),
        ('GitHub leaks', 'site:github.com "{domain}"'),
        ('GitLab leaks', 'site:gitlab.com "{domain}"'),
        ('Trello boards', 'site:trello.com "{domain}"'),
        ('StackOverflow', 'site:stackoverflow.com "{domain}"'),
    ],
}


def generate_dorks(domain: str, categories: list = None) -> dict:
    """Generate dorks for target domain."""
    results = {}

    target_categories = categories if categories else DORK_CATEGORIES.keys()

    for category in target_categories:
        if category not in DORK_CATEGORIES:
            continue

        results[category] = []
        for name, template in DORK_CATEGORIES[category]:
            dork = template.format(domain=domain)
            google_url = f"https://www.google.com/search?q={quote_plus(dork)}"
            results[category].append({
                'name': name,
                'dork': dork,
                'url': google_url
            })

    return results


def main():
    parser = argparse.ArgumentParser(description='Google Dorks Generator')
    parser.add_argument('domain', help='Target domain')
    parser.add_argument('-c', '--categories', nargs='+', help='Specific categories to generate')
    parser.add_argument('-o', '--output', help='Output file')
    parser.add_argument('--list-categories', action='store_true', help='List available categories')
    parser.add_argument('--urls', action='store_true', help='Include Google search URLs')
    args = parser.parse_args()

    if args.list_categories:
        info("Available categories:")
        for cat in DORK_CATEGORIES:
            print(f"  - {cat}")
        sys.exit(0)

    banner("Google Dorks Generator")
    info(f"Target: {args.domain}")

    dorks = generate_dorks(args.domain, args.categories)

    output_lines = []

    for category, items in dorks.items():
        print(f"\n[{category.upper().replace('_', ' ')}]")
        output_lines.append(f"# {category.upper()}")

        for item in items:
            print(f"  {item['name']}:")
            print(f"    {item['dork']}")
            output_lines.append(item['dork'])

            if args.urls:
                print(f"    URL: {item['url']}")

        output_lines.append("")

    if args.output:
        with open(args.output, 'w') as f:
            f.write('\n'.join(output_lines))
        success(f"Dorks saved to {args.output}")


if __name__ == '__main__':
    main()
