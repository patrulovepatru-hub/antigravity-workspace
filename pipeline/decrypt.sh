#!/bin/bash
# Desencriptación híbrida: RSA para llave + AES-256 para datos
# Uso: ./decrypt.sh <archivo_encriptado> <archivo_salida>

set -e

KEYS_DIR="/home/patricio/pipeline/keys"
PRIVATE_KEY="$KEYS_DIR/private.pem"

INPUT_FILE="$1"
OUTPUT_FILE="$2"

if [[ -z "$INPUT_FILE" || -z "$OUTPUT_FILE" ]]; then
    echo "Uso: $0 <archivo_encriptado> <archivo_salida>"
    exit 1
fi

if [[ ! -f "$INPUT_FILE" ]]; then
    echo "Error: Archivo no encontrado: $INPUT_FILE"
    exit 1
fi

# Crear directorio temporal seguro
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Leer tamaño de llave encriptada (primeros 4 bytes en hex)
KEY_SIZE=$(xxd -p -l 4 "$INPUT_FILE" | sed 's/^0*//')
KEY_SIZE=$((16#$KEY_SIZE))

# Extraer llave encriptada
dd if="$INPUT_FILE" of="$TEMP_DIR/key.enc" bs=1 skip=4 count="$KEY_SIZE" 2>/dev/null

# Extraer datos encriptados
dd if="$INPUT_FILE" of="$TEMP_DIR/data.enc" bs=1 skip=$((4 + KEY_SIZE)) 2>/dev/null

# Desencriptar llave AES con RSA privada
AES_COMBINED=$(openssl pkeyutl -decrypt \
    -inkey "$PRIVATE_KEY" \
    -in "$TEMP_DIR/key.enc")

AES_KEY=$(echo "$AES_COMBINED" | cut -d: -f1)
AES_IV=$(echo "$AES_COMBINED" | cut -d: -f2)

# Desencriptar datos con AES-256-CBC
openssl enc -aes-256-cbc -d \
    -in "$TEMP_DIR/data.enc" \
    -out "$OUTPUT_FILE" \
    -K "$AES_KEY" \
    -iv "$AES_IV"

echo "Desencriptado: $OUTPUT_FILE"
