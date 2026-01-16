# Plan: AI Team Tycoon - Plataforma de Gestión de Equipos IA

## Resumen
Crear un tycoon web donde gestiones equipos de agentes IA que trabajan en proyectos. Los equipos pueden luego desarrollar las otras ideas (esports, deportes, trabajo).

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Firebase Hosting)              │
│                    React/Vue + TailwindCSS                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    FIREBASE                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │    Auth      │  │  Firestore   │  │  Functions   │       │
│  │ (usuarios)   │  │  (equipos,   │  │  (triggers)  │       │
│  │              │  │   agentes)   │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 CLOUD RUN (Backend API)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Tycoon      │  │   Agent      │  │   Task       │       │
│  │  Engine      │  │   Manager    │  │   Queue      │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              AGENTES IA (tu pipeline actual)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Claude A     │  │  LM Studio   │  │   Gemini     │       │
│  │ (Ubuntu VM)  │  │  (Windows)   │  │   (Cloud)    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## Funcionalidades del Tycoon

### 1. Gestión de Equipos
- Crear/editar equipos de agentes
- Asignar especialidades (código, análisis, creatividad)
- Ver estadísticas de rendimiento

### 2. Gestión de Agentes
- Añadir agentes al roster (Claude, Gemini, LM Studio, etc.)
- Configurar parámetros (temperatura, modelo, etc.)
- Monitorear uso y costos

### 3. Sistema de Proyectos
- Crear proyectos/tareas
- Asignar equipos a proyectos
- Tracking de progreso

### 4. Economía del Tycoon
- Presupuesto virtual por equipo
- Costo por uso de cada agente
- Rewards por tareas completadas

---

## Pasos de Implementación

### Fase 1: Setup Infraestructura
1. [ ] Crear proyecto Firebase (o usar existente)
2. [ ] Habilitar Firestore, Auth, Hosting
3. [ ] Configurar Cloud Run en GCP
4. [ ] Conectar con proyecto `gen-lang-client-0988614926`

### Fase 2: Backend (Cloud Run)
1. [ ] Crear API REST con Node.js/Python
2. [ ] Endpoints: `/teams`, `/agents`, `/projects`, `/tasks`
3. [ ] Integración con pipeline existente (`/home/patricio/pipeline`)
4. [ ] Deploy a Cloud Run

### Fase 3: Base de Datos (Firestore)
```
/users/{userId}
  - email, displayName, credits

/teams/{teamId}
  - name, ownerId, agents[], stats{}

/agents/{agentId}
  - type (claude|gemini|lmstudio)
  - config{}, costPerRequest, status

/projects/{projectId}
  - name, teamId, tasks[], status, progress

/tasks/{taskId}
  - description, assignedAgent, status, result
```

### Fase 4: Frontend
1. [ ] React + Vite + TailwindCSS
2. [ ] Dashboard principal
3. [ ] Vistas: Teams, Agents, Projects
4. [ ] Deploy a Firebase Hosting

---

## Comandos para Setup

### Firebase
```bash
# Instalar Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Inicializar proyecto
cd ~/ai-team-tycoon
firebase init

# Seleccionar: Firestore, Hosting, Functions
# Usar proyecto existente o crear nuevo
```

### Cloud Run
```bash
# Autenticar con GCP
gcloud auth login
gcloud config set project gen-lang-client-0988614926

# Habilitar Cloud Run
gcloud services enable run.googleapis.com

# Deploy (después de crear el backend)
gcloud run deploy ai-tycoon-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Archivos a Crear

| Ruta | Descripción |
|------|-------------|
| `~/ai-team-tycoon/` | Directorio raíz del proyecto |
| `~/ai-team-tycoon/backend/` | API Cloud Run (Node.js) |
| `~/ai-team-tycoon/frontend/` | App React |
| `~/ai-team-tycoon/firebase.json` | Config Firebase |
| `~/ai-team-tycoon/firestore.rules` | Reglas de seguridad |

---

## Integración con Pipeline Existente

El tycoon se conectará con tu pipeline actual:

```javascript
// Ejemplo: ejecutar tarea con agente
async function runTask(task, agent) {
  if (agent.type === 'lmstudio') {
    // Usar /home/patricio/pipeline/lmstudio-client.sh
    return await fetch('http://192.168.192.2:1234/v1/chat/completions', {...})
  }
  if (agent.type === 'gemini') {
    // Usar Vertex AI
    return await vertexAI.generateContent({...})
  }
}
```

---

## Verificación

1. [ ] Firebase project creado y configurado
2. [ ] Cloud Run habilitado en GCP
3. [ ] Backend desplegado y accesible
4. [ ] Frontend desplegado en Firebase Hosting
5. [ ] Conexión exitosa con pipeline de agentes
6. [ ] Crear primer equipo y ejecutar tarea de prueba

---

## Costos Estimados (tier gratuito)

- **Firebase**: Spark plan gratis (50K reads/día, 20K writes/día)
- **Cloud Run**: 2M requests/mes gratis
- **Vertex AI**: $0.00125/1K caracteres (Gemini)
- **LM Studio**: Gratis (local en Windows)

Total inicial: **~$0/mes** usando tiers gratuitos
