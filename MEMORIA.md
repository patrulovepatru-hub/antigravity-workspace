# Memoria del Proyecto y Contexto (Migración de Claude)

Este documento sirve como la "fuente de verdad" para Antigravity, consolidando todo el contexto compartido originalmente con Claude.

## 1. Asistente Legal Inmigrantes (Prioridad: Alta)
**Objetivo:** Chat RAG + análisis de documentos legales para inmigrantes.
- **Stack Tecnológico:**
  - Backend: FastAPI
  - Frontend: Next.js
  - BD: PostgreSQL con extensión `pgvector`
  - Infra: Docker
  - LLM: Vertex AI (Google Cloud) - Presupuesto: $300 créditos gratuitos.
- **Estado:** En desarrollo.
- **Próximos Pasos:** 
  - [ ] Definir esquema de la base de datos para vectores.
  - [ ] Scaffolding de FastAPI y Next.js.
  - [ ] Integración con Vertex AI SDK.

## 2. Fundex (Algorithmic Trading)
**Objetivo:** Trading algorítmico con capacidades de backtesting intensivo.
- **Herramientas:** Backtesting.py, Backtrader, HFTBacktest.
- **Fuentes de Datos:** Kaggle, QuantConnect.
- **Estado:** Idea/Pipeline.

## 3. Granjas Móviles (IoT / Computación Distribuida)
**Objetivo:** Reutilizar hardware antiguo (móviles) como nodos de cómputo.
- **Conceptos:** Ingeniería inversa, firmware custom, mesh networks, mining pools.
- **Estado:** Idea/Investigación.

## 4. Archivos de Transferencia
Lista de archivos pendientes de procesar (procedentes de `/home/l0ve/`):
- `mudanza_binance_*.tar.gz`
- `mudanza_pentest_*.tar.gz`

---
*Nota: Este archivo se actualizará conforme "migremos" más detalles de las conversaciones con Claude.*
