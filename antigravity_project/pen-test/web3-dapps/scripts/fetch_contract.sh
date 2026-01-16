#!/bin/bash
# Fetch verified contract source from Etherscan/BSCScan

# Usage: ./fetch_contract.sh <address> <chain>
# Example: ./fetch_contract.sh 0x1234... eth

ADDRESS=$1
CHAIN=${2:-eth}

case $CHAIN in
  eth)
    API_URL="https://api.etherscan.io/api"
    API_KEY="${ETHERSCAN_API_KEY:-YourApiKeyToken}"
    ;;
  bsc)
    API_URL="https://api.bscscan.com/api"
    API_KEY="${BSCSCAN_API_KEY:-YourApiKeyToken}"
    ;;
  polygon)
    API_URL="https://api.polygonscan.com/api"
    API_KEY="${POLYGONSCAN_API_KEY:-YourApiKeyToken}"
    ;;
  arb)
    API_URL="https://api.arbiscan.io/api"
    API_KEY="${ARBISCAN_API_KEY:-YourApiKeyToken}"
    ;;
  *)
    echo "Unknown chain: $CHAIN"
    exit 1
    ;;
esac

OUTPUT_DIR="contracts/${CHAIN}/${ADDRESS}"
mkdir -p "$OUTPUT_DIR"

echo "[*] Fetching contract $ADDRESS from $CHAIN..."

curl -s "${API_URL}?module=contract&action=getsourcecode&address=${ADDRESS}&apikey=${API_KEY}" \
  | jq -r '.result[0].SourceCode' > "${OUTPUT_DIR}/source.sol"

curl -s "${API_URL}?module=contract&action=getabi&address=${ADDRESS}&apikey=${API_KEY}" \
  | jq -r '.result' > "${OUTPUT_DIR}/abi.json"

echo "[+] Saved to ${OUTPUT_DIR}/"
ls -la "${OUTPUT_DIR}/"
