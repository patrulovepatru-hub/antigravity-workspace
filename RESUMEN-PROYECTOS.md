# Resumen de Proyectos - Sesiones Claude Code
**Fecha de exportación:** 15 enero 2026
**Usuario:** patricio

---

## Proyectos Trabajados

### 1. GOAT → CORLEONE (Pipeline Multi-Modelo)
**Ubicación:** `/pipeline/`

**Descripción:** Pipeline automatizado para análisis de audiencia que conecta:
- **VM Ubuntu** (orquestación, encriptación)
- **Windows Host** (LM Studio con Llama 3 8B, GPU AMD 9060 XT)
- **Cloud** (Vertex AI / Gemini, Google Sheets)

**Componentes principales:**
| Archivo | Función |
|---------|---------|
| `run-pipeline.sh` | Orquestador principal |
| `encrypt.sh` / `decrypt.sh` | Encriptación RSA 4096-bit |
| `gemini-client.sh` | Cliente API Gemini |
| `ollama-client.sh` | Cliente Ollama (local) |
| `lmstudio-client.sh` | Cliente LM Studio (Windows) |
| `cache.sh` | Sistema de caché |
| `preprocess.sh` | Limpieza de datos |

**Subproyecto CORLEONE:**
- `bridge.sh` - Conexión VM ↔ Windows (Antigravity IDE)
- `gemini.sh` - Cliente simplificado Gemini
- `4exe/` - Forensic Toolkit para análisis de datos

**Configuración GCP:**
- Proyecto: `gen-lang-client-0988614926`
- Service Account: `pipeline-bot`
- APIs habilitadas: Vertex AI, Gemini, Sheets

**Estado:** Scripts principales creados, pendiente test end-to-end

---

### 2. AI Team Tycoon
**Ubicación:** `/ai-team-tycoon/`

**Descripción:** Tycoon web para gestionar equipos de agentes IA que trabajan en proyectos.

**Arquitectura planificada:**
```
Frontend (Firebase Hosting) → React + TailwindCSS
    ↓
Firebase (Auth, Firestore, Functions)
    ↓
Cloud Run (Backend API)
    ↓
Agentes IA (Claude, LM Studio, Gemini)
```

**Funcionalidades:**
- Gestión de equipos de agentes IA
- Asignación de especialidades y tareas
- Sistema de economía virtual
- Monitoreo de costos y rendimiento

**Estado:** Estructura de carpetas creada, desarrollo pendiente

---

## Conexión VM ↔ Windows

**Red:**
- VM Ubuntu: `192.168.192.128`
- Windows Host: `192.168.192.2`

**Endpoints:**
- LM Studio: `http://192.168.192.2:1234/v1`
- CORLEONE Bridge: `http://192.168.192.128:8765`

---

## Archivos de Configuración

- `/pipeline/config.env` - Configuración general del pipeline
- `/pipeline/corleone/config.env` - Configuración CORLEONE
- `/pipeline/keys/` - Llaves RSA y Service Account GCP

---

## Planes de Sesiones Anteriores

Los planes detallados están en `/planes-claude/`:
- `quizzical-doodling-parasol.md` - Plan completo GOAT → CORLEONE
- `wise-napping-moonbeam.md` - Plan AI Team Tycoon

---

## Próximos Pasos Sugeridos

### CORLEONE/Pipeline:
1. [ ] Configurar OAuth para Gemini
2. [ ] Configurar Ollama/LM Studio en Windows
3. [ ] Test end-to-end: datos → procesamiento → Sheets

### AI Team Tycoon:
1. [ ] Configurar proyecto Firebase
2. [ ] Crear backend API en Cloud Run
3. [ ] Desarrollar frontend React
4. [ ] Integrar con pipeline existente
