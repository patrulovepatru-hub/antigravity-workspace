# GOAT → CORLEONE
## Pipeline Multi-Modelo para Análisis de Audiencia

```
   ██████╗  ██████╗  █████╗ ████████╗
  ██╔════╝ ██╔═══██╗██╔══██╗╚══██╔══╝
  ██║  ███╗██║   ██║███████║   ██║
  ██║   ██║██║   ██║██╔══██║   ██║
  ╚██████╔╝╚██████╔╝██║  ██║   ██║
   ╚═════╝  ╚═════╝ ╚═╝  ╚═╝   ╚═╝
         └── CORLEONE (subproject)
```

## Objetivo
Pipeline automatizado: Instagram/LinkedIn → análisis de audiencia → insights accionables.

## Configuración Confirmada

| Recurso | Estado | Detalle |
|---------|--------|---------|
| **Cuenta Google** | ✅ | patriciomartinmendez@gmail.com |
| **Proyecto GCP** | ✅ | gen-lang-client-0988614926 |
| **Vertex AI API** | ✅ | Habilitado |
| **Gemini API** | ✅ | Habilitado |
| **Billing** | ✅ | Cuenta activa |
| **Sheets API** | 🔄 | Por habilitar |

## Arquitectura Híbrida (VM + Host + Cloud)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            HOST WINDOWS 11                                  │
│                    64GB DDR5 | AMD 9060 XT 16GB                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ OLLAMA (Edge Computing)                                              │   │
│  │ - Pre-procesamiento local con GPU                                    │   │
│  │ - Modelos: llama3, mistral, phi3                                     │   │
│  │ - API: http://localhost:11434                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ▲                                              │
│                              │ NAT/Bridge                                   │
│  ┌───────────────────────────┴─────────────────────────────────────────┐   │
│  │ VMware Ubuntu                                                        │   │
│  │ - Claude CLI (orquestación)                                          │   │
│  │ - Encriptación RSA                                                   │   │
│  │ - Scripts de pipeline                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Vertex AI       │ ──► │ Antigravity IDE  │ ──► │ Google Sheets   │
│ (Gemini Pro)    │     │ (Ejecución)      │     │ (Almacén)       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### Flujo de Datos con Edge Computing

1. **Datos crudos** → VM Ubuntu (encripta)
2. **Datos encriptados** → Host Windows (Ollama pre-procesa)
3. **Datos filtrados** → Vertex AI (Gemini analiza)
4. **Insights** → Google Sheets (almacena)
5. **Validación** → Contrastar con datasets comprados (baseline)

## Estrategia de Datos: Baseline + Propios

### Fuentes de Datasets Baratos (usar créditos)
| Fuente | Tipo de Datos | Costo Aprox |
|--------|---------------|-------------|
| **Kaggle** | Encuestas, trends | Gratis-$50 |
| **data.world** | Social media analytics | Gratis-$100 |
| **Statista** | Market research | $39/mes |
| **Google Dataset Search** | Diversos | Gratis |
| **AWS Data Exchange** | Comerciales | Variable |
| **Hugging Face Datasets** | NLP, sentiment | Gratis |

### Uso del Baseline
```
Datos propios (Instagram/LinkedIn)
         │
         ▼
    ┌─────────┐
    │ Comparar│ ◄── Dataset comprado (baseline)
    └────┬────┘
         │
         ▼
   Insights validados
   (anomalías, tendencias confirmadas)
```

### Beneficios
- Validar si tus datos son representativos
- Detectar sesgos en tu audiencia
- Identificar tendencias que no estás capturando
- Menor costo que estudios de mercado completos

## Implementación por Fases

### Fase 1: Consolidar Google (Primero)
1. Elegir 1 cuenta maestra de Google
2. Vincular Vertex AI a esa cuenta
3. Crear proyecto GCP unificado
4. Habilitar APIs: Vertex AI, Sheets, BigQuery

### Fase 2: Extracción de Datos
**Instagram:**
- Meta Business Suite API (requiere cuenta business)
- Exportar insights de stories/posts

**LinkedIn:**
- LinkedIn Analytics export
- Sales Navigator si tienes

**Destino:** Google Sheets o BigQuery

### Fase 3: Pipeline de Análisis
```bash
# Desde Claude CLI (VMware Ubuntu)
# 1. Orquestar extracción
claude "extraer datos de Instagram insights del último mes"

# 2. Enviar a Vertex AI para optimizar prompt
gcloud ai predict --model=gemini-pro --input="$DATOS"

# 3. Ejecutar en Antigravity con prompt optimizado
# 4. Guardar resultados en Sheets
```

### Fase 4: Automatización
- Google Apps Script para ejecución programada
- Alertas cuando hay nuevos insights relevantes

## Pasos de Implementación

### Paso 1: Configurar proyecto GCP (terminal)
```bash
gcloud config set project gen-lang-client-0988614926
gcloud services enable sheets.googleapis.com
```

### Paso 2: Crear Service Account
```bash
gcloud iam service-accounts create pipeline-bot \
  --display-name="Pipeline Análisis Audiencia"
gcloud iam service-accounts keys create ~/pipeline-key.json \
  --iam-account=pipeline-bot@gen-lang-client-0988614926.iam.gserviceaccount.com
```

### Paso 3: Crear script de conexión Claude → Gemini
Archivo: `/home/patricio/pipeline/gemini-prompt.sh`
- Recibe datos de Instagram/LinkedIn
- Llama a Gemini para optimizar prompt
- Retorna prompt optimizado para Antigravity

### Paso 4: Configurar Google Sheet central
- Crear spreadsheet "Análisis Audiencia"
- Columnas: Fecha | Fuente | Datos Crudos | Prompt Optimizado | Insights

### Paso 5: Script orquestador
Archivo: `/home/patricio/pipeline/run-pipeline.sh`
- Input: datos de encuestas
- Output: insights en Sheets

## Verificación
1. Ejecutar `gcloud ai models list` - debe mostrar modelos Gemini
2. Probar llamada a Gemini con prompt simple
3. Verificar escritura en Google Sheets

## Progreso Actual

### Completado
- [x] gcloud CLI instalado y autenticado
- [x] Proyecto GCP configurado: `gen-lang-client-0988614926`
- [x] Sheets API habilitada
- [x] Service Account creada: `pipeline-bot`
- [x] Encriptación RSA 4096-bit implementada
- [x] Scripts creados:
  - `/home/patricio/pipeline/encrypt.sh`
  - `/home/patricio/pipeline/decrypt.sh`
  - `/home/patricio/pipeline/run-pipeline.sh`
  - `/home/patricio/pipeline/config.env`
  - `/home/patricio/pipeline/keys/` (llaves RSA)

### Pendiente
- [ ] Configurar OAuth para Gemini (sin API key)
- [ ] Configurar Ollama en Host Windows (64GB RAM, 9060 XT)
- [ ] Test end-to-end: datos → Ollama → Gemini → Sheets

## Autenticación OAuth (en lugar de API Key)

Para usar OAuth con Gemini:
```bash
gcloud auth application-default login \
  --scopes="https://www.googleapis.com/auth/generative-language.retriever,https://www.googleapis.com/auth/cloud-platform"
```

Luego visitar el URL generado en navegador y pegar el código de verificación.

## Estructura Actual

```
/home/patricio/pipeline/
├── GOAT (proyecto padre)
│   ├── encrypt.sh / decrypt.sh    ✅ RSA 4096-bit
│   ├── cache.sh                   ✅ Caché respuestas
│   ├── preprocess.sh              ✅ Limpieza local
│   ├── ollama-client.sh           ✅ Conexión a Host
│   ├── gemini-client.sh           ✅ API Gemini
│   ├── run-pipeline.sh            ✅ Orquestador
│   └── keys/                      ✅ Llaves + Service Account
│
└── corleone/ (subproyecto activo)
    ├── config.env                 ✅ Configuración
    ├── gemini.sh                  ✅ Cliente simplificado
    ├── bridge.sh                  ✅ Conexión Antigravity
    ├── data/                      📁 Datos entrada
    ├── prompts/                   📁 Prompts guardados
    ├── outputs/                   📁 Resultados
    │
    └── 4exe/                      🆕 Forensic Toolkit
        ├── 4exe.sh                CLI principal
        ├── evidence/              Datos para análisis
        └── reports/               Reportes generados

## 4EXE (FORENSIC) - Data Analysis Toolkit

```
patru = 4 | exe = executable | 4ensic = forensic
@patru = cuenta Instagram del owner
```

### Funcionalidades
1. **analyze** - Análisis forense de archivos/datos
2. **extract** - Extraer entidades (emails, IPs, URLs, hashes)
3. **ai** - Análisis inteligente con LM Studio
4. **hash** - Calcular checksums
5. **timeline** - Timeline de archivos
6. **social** - Análisis de redes sociales
```

## Configuración Host Windows (LM Studio)

### Modelo seleccionado
- **Llama 3 8B** - Balance óptimo para 16GB VRAM

### Configurar LM Studio para acceso remoto

1. Abrir LM Studio
2. Cargar modelo: `Llama 3 8B` (Q4_K_M o Q5_K_M)
3. Ir a **Local Server** tab
4. Activar **"Enable CORS"**
5. Cambiar puerto si es necesario (default: 1234)
6. Click **Start Server**

### Firewall Windows
```powershell
netsh advfirewall firewall add rule name="LM Studio API" dir=in action=allow protocol=tcp localport=1234
```

### API de LM Studio (compatible con OpenAI)
```bash
# Desde VM Ubuntu
curl http://192.168.192.2:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-model",
    "messages": [{"role": "user", "content": "Analiza estos datos..."}]
  }'
```

### Endpoint
- **URL:** `http://192.168.192.2:1234/v1`
- **Modelo:** `local-model` (LM Studio usa este nombre genérico)

## FASE 2: Infraestructura Distribuida

### Arquitectura Multi-Máquina
```
┌─────────────────────────────────────────────────────────────────┐
│                    RELAY PRIVADA SEGURA                         │
├─────────────────────────────────────────────────────────────────┤
│  VM Ubuntu (Orquestador)                                        │
│  ├── Claude CLI                                                 │
│  ├── Logs auditables (Cámara Comercio)                         │
│  ├── Encriptación E2E                                          │
│  └── Load Balancer                                              │
├─────────────────────────────────────────────────────────────────┤
│  Windows Host (Compute)                                         │
│  ├── LM Studio (Llama 3 8B) :1234                              │
│  ├── Antigravity IDE                                           │
│  └── GPU Processing                                             │
├─────────────────────────────────────────────────────────────────┤
│  Cloud (Overflow)                                               │
│  ├── Vertex AI / Gemini                                        │
│  └── Google Sheets (Storage)                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Logging para Compliance (Cámara de Comercio)
- Timestamps ISO 8601
- Hash de cada transacción
- Firma digital de logs
- Retención configurable
- Exportable a PDF/JSON

### Sharding y Overflow
```
Request → Load Balancer
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
 LM Studio  Gemini   Overflow
 (local)    (cloud)  (queue)
```

## Archivos a crear - Fase 2
- `/home/patricio/pipeline/relay/relay.sh` - Relay segura
- `/home/patricio/pipeline/logs/audit.sh` - Logging compliance
- `/home/patricio/pipeline/lb/balancer.sh` - Load balancer
- `/home/patricio/pipeline/debug/debug.sh` - Debugger
