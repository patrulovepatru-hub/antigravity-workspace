# CORLEONE → ANTIGRAVITY Setup (Windows)

## Conexión VM ↔ Windows

```
┌─────────────────────────────────────────────────────┐
│  VM Ubuntu (192.168.192.128)                        │
│  └── CORLEONE Bridge :8765                          │
│         ↕ HTTP                                      │
│  Windows (192.168.192.2)                            │
│  └── Antigravity IDE                                │
└─────────────────────────────────────────────────────┘
```

## 1. Verificar Conexión

Desde PowerShell:
```powershell
# Ping a la VM
ping 192.168.192.128

# Probar acceso al bridge (cuando esté corriendo)
curl http://192.168.192.128:8765/
```

## 2. Iniciar Bridge (en VM Ubuntu)

```bash
cd /home/patricio/pipeline/corleone
./bridge.sh start
```

## 3. Acceder desde Windows

Abre en navegador o Antigravity:
- **Datos:**    http://192.168.192.128:8765/data/
- **Outputs:**  http://192.168.192.128:8765/outputs/
- **Prompts:**  http://192.168.192.128:8765/prompts/

## 4. Configurar Antigravity

En Antigravity, configura como fuente de datos:
```
CORLEONE_ENDPOINT=http://192.168.192.128:8765
```

## 5. Workflow

```
[Antigravity] → solicita datos → [Bridge VM]
                                      ↓
[Antigravity] ← recibe outputs ← [CORLEONE procesa]
```

## Carpeta de Sincronización (Opcional)

Si prefieres carpeta compartida local en Windows:

```powershell
# Crear carpeta
mkdir C:\CORLEONE

# Mapear como drive (opcional)
subst X: C:\CORLEONE
```

Luego descarga archivos del bridge a esta carpeta.
