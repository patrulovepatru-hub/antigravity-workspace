#!/bin/bash
# PERMS - Gestión rápida de permisos
# Uso: perms <acción> [archivo]

case "$1" in
    x|exec)
        chmod +x "$2" && echo "✅ Ejecutable: $2"
        ;;
    r|read)
        chmod 644 "$2" && echo "✅ Solo lectura: $2"
        ;;
    rw)
        chmod 666 "$2" && echo "✅ Lectura/escritura: $2"
        ;;
    private|priv)
        chmod 600 "$2" && echo "🔒 Privado: $2"
        ;;
    dir)
        chmod 755 "$2" && echo "📁 Directorio: $2"
        ;;
    all)
        chmod -R +x /home/patricio/pipeline/*.sh
        chmod -R +x /home/patricio/pipeline/corleone/**/*.sh 2>/dev/null
        echo "✅ Todos los scripts ejecutables"
        ;;
    show|ls)
        ls -la "${2:-.}"
        ;;
    *)
        echo "perms x <file>      → ejecutable"
        echo "perms r <file>      → solo lectura"
        echo "perms rw <file>     → lectura/escritura"
        echo "perms private <file>→ solo owner"
        echo "perms dir <dir>     → directorio"
        echo "perms all           → todos los .sh ejecutables"
        echo "perms show [path]   → ver permisos"
        ;;
esac
