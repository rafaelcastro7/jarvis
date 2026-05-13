---
name: lab10-reto-agentes
description: Knowledge base del programa "Reto Agentes" de Lab10.ai. 13 modulos sobre construccion de agentes IA autonomos con OpenClaw — planificacion, instalacion, personalidad, tools/skills, memoria, autonomia. Para consultar: usa el RAG (lab10-rag skill) o lee los transcripts en E:\Documents\PROYECTOS\AgencIA\lab10-clone\transcripts\.
---

# Lab10 - Reto Agentes

## Estructura del programa

13 modulos en 13 clases descargadas. Inscripcion gratuita.

| # | Modulo |
|---|--------|
| 1 | DIA 1: Planificación Estratégica de tu Agente de IA |
| 2 | Introducción a los Agentes Autónomos y OpenClaw |
| 3 | DIA 2: Instalación y Configuración de Agentes IA con OpenClaw |
| 4 | Instalación y Configuración de OpenClaw |
| 5 | Estructura de Costos y Modelos de Precios para IA |
| 6 | DIA 3: Creación de Personalidad e Identidad para Agentes en OpenClaw |
| 7 | DIA 4:  Implementación de Tools y Skills |
| 8 | Anatomía de las Skills |
| 9 | Arquitectura de Skills |
| 10 | Instalación de Skills en OpenClaw |
| 11 | DIA 5: Creación de skills desde 0 |
| 12 | DIA 6: Configuración de Memoria en OpenCloud |
| 13 | DIA 7: Autonomía en Agentes IA: Crons y Heartbeat |


## Recursos locales

- **Videos**: `E:\Documents\PROYECTOS\AgencIA\lab10-clone\videos\` (27 transcripciones disponibles)
- **HTMLs**: `lab10-clone/mirror/modules/` (13 paginas guardadas)
- **Transcripts**: `lab10-clone/transcripts/` (27 .txt)
- **RAG chunks**: `lab10-clone/rag/lab10_chunks.jsonl` (227 chunks)

## Como usar este conocimiento

1. **Pregunta directa**: Lee transcripts relevantes con Grep + Read
2. **RAG semantico**: Lanza `python scripts/rag_query.py "tu pregunta"` (cuando se cree)
3. **Build de agentes**: Sigue el flujo - planificacion -> instalacion -> personalidad -> tools/skills -> memoria -> autonomia

## Stack canonico de OpenClaw

- Modelos LLM (Claude, GPT) con fallback chain
- Tools/Skills modulares (anatomia: yaml + python handler)
- Memoria persistente (key-value + RAG)
- Crons + heartbeat para autonomia

Generado: 2026-05-13T07:34:48.267927
