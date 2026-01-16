#!/bin/bash
# Encriptación híbrida: AES-256 para datos + RSA para llave
# Uso: ./encrypt.sh <archivo_entrada> <archivo_salida>

set -e

KEYS_DIR="/home/patricio/pipeline/keys"
PUBLIC_KEY="$KEYS_DIR/public.pem"

INPUT_FILE="$1"
OUTPUT_FILE="$2"

if [[ -z "$INPUT_FILE" || -z "$OUTPUT_FILE" ]]; then
    echo "Uso: $0 <archivo_entrada> <archivo_salida>"
    exit 1
fi

if [[ ! -f "$INPUT_FILE" ]]; then
    echo "Error: Archivo no encontrado: $INPUT_FILE"
    exit 1
fi

# Generar llave AES aleatoria (256 bits)
AES_KEY=$(openssl rand -hex 32)
AES_IV=$(openssl rand -hex 16)

# Crear directorio temporal seguro
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Encriptar datos con AES-256-CBC
openssl enc -aes-256-cbc -salt \
    -in "$INPUT_FILE" \
    -out "$TEMP_DIR/data.enc" \
    -K "$AES_KEY" \
    -iv "$AES_IV"

# Encriptar llave AES con RSA pública
echo "${AES_KEY}:${AES_IV}" | openssl pkeyutl -encrypt \
    -pubin -inkey "$PUBLIC_KEY" \
    -out "$TEMP_DIR/key.enc"

# Combinar en archivo final (key.enc + data.enc)
# Formato: [4 bytes tamaño llave][llave encriptada][datos encriptados]
KEY_SIZE=$(stat -c%s "$TEMP_DIR/key.enc")
printf '%08x' "$KEY_SIZE" | xxd -r -p > "$OUTPUT_FILE"
cat "$TEMP_DIR/key.enc" >> "$OUTPUT_FILE"
cat "$TEMP_DIR/data.enc" >> "$OUTPUT_FILE"

echo "Encriptado: $OUTPUT_FILE"
