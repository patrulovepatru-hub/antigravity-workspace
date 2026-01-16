#!/bin/bash
# Curl wrapper that uses saved Cloudflare cookies
# Usage: ./curl_with_cookies.sh <url> [additional curl args]

COOKIES_FILE="/home/l0ve/pen-test/key-drop.com/scripts/cookies.json"

if [ ! -f "$COOKIES_FILE" ]; then
    echo "[-] No cookies file found. Run bypass_cf.py first!"
    exit 1
fi

# Extract cookies from JSON and format for curl
COOKIE_STRING=$(python3 -c "
import json
with open('$COOKIES_FILE') as f:
    cookies = json.load(f)
print('; '.join([f\"{c['name']}={c['value']}\" for c in cookies]))
")

URL="${1:-https://key-drop.com}"
shift

echo "[*] Using cookies from $COOKIES_FILE"
echo "[*] Requesting: $URL"
echo ""

curl -s \
    -H "Cookie: $COOKIE_STRING" \
    -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
    -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8" \
    -H "Accept-Language: en-US,en;q=0.5" \
    -H "Accept-Encoding: gzip, deflate, br" \
    -H "Connection: keep-alive" \
    -H "Upgrade-Insecure-Requests: 1" \
    "$URL" "$@"
