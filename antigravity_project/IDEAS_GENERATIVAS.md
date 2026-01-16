# Ideas: Modelo Generativo que Aprende

Este documento explora conceptos para un "Modelo Generativo que Aprende", diferenciando entre tipos de aprendizaje y aplicaciones prácticas para Antigravity.

## 1. Aprendizaje en Contexto (In-Context Learning Avanzado)
El modelo "aprende" durante la sesión manteniendo una memoria dinámica.
- **Idea**: **Antigravity Knowledge Graph**. Un asistente que construye un grafo de conocimiento de todos tus proyectos (`fundex`, `inmigra-legal`, etc.) y aprende las relaciones entre ellos.
- **Mecanismo**: RAG dinámico. Si le corriges sobre cómo funciona una función en `fundex`, guarda esa corrección como una "regla" en su base de datos vectorial/grafo.
- **Stack**: LangChain, Neo4j, OpenAI/Gemini.

## 2. Fine-Tuning Continuo (Online Learning)
Reentrenar o ajustar un modelo pequeño localmente.
- **Idea**: **Personal Coder**. Un modelo Llama-3-8B ajustado (LoRA) que se reentrena cada noche con los cambios que hiciste en tu código ese día. Aprende tu estilo de variable, tus patrones de arquitectura, etc.
- **Mecanismo**: Scripts automatizados que toman los `git diff` del día y crean un dataset de entrenamiento para un ajuste ligero.

## 3. Aprendizaje por Refuerzo (RLHF Personalizado)
El modelo aprende de tus preferencias explícitas.
- **Idea**: **UI Generator con Memoria de Gustos**. Generas componentes de UI (para tus web apps). El modelo te da 2 opciones. Tú eliges una. El modelo guarda un vector de "preferencia" que sesga las futuras generaciones hacia ese estilo (ej. "neon dark mode").

## 4. Agentes Evolutivos
- **Idea**: **Evolución de Estrategias de Trading (Fundex)**.
  - Generas 10 estrategias base con un LLM.
  - Las pones a competir en backtesting.
  - Las mejores se "cruzan" (el LLM combina sus ideas) y "mutan" (el LLM cambia parámetros).
  - Repetir. El "modelo" es el sistema evolutivo que encuentra la estrategia ganadora.

## ¿Por dónde empezamos?
- [ ] Definir el objetivo: ¿Productividad (coding), Creatividad (arte/UI) o Utilidad (trading)?
- [ ] Elegir el stack tecnológico.
