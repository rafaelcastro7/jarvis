# Venture Investor — Rutan iNNpulsa Colombia

Skill basado en el contenido completo del programa Investor Academy de Rutan.
Cubre 7 módulos de formación en inversión ángel y Venture Capital para el ecosistema colombiano y LATAM.

## Módulos del programa

### Módulo 0 — Punto de partida: La inversión como catalizador
**Lecciones:**
- Bienvenida
- Auto Identificación de roles y oportunidades
- La inversión como catalizador de innovación
- Construcción de portafolio y frontera eficiente
- Cierre y bienvenida al Venture Capital

### module-1-vc-intro
**Lecciones:**
- Introducción al Venture Capital
- Identificación y caracterización de inversionistas
- Criterios de inversión en un venture capital
- Cómo se genera la liquidez en un fondo de venture capital
- Papel del VC en el ecosistema empresarial

### module-2-vc-market
**Lecciones:**
- Introducción a Fundamentos, Estructura y Procesos Operacionales de un Fondo de VC
- Estructura y ciclos de un fondo de venture capital
- Proceso de inversion end-to-end
- Gobernanza en un fondo de venture capital
- Portfolio management + reserves
- Métricas de un fondo de venture capital
- 
- 

### module-3-vc-dynamics
**Lecciones:**
- 
- ¿Qué está pasando con el ecosistema de venture capital a nivel global?
- ¿Qué está pasando con el ecosistema de venture capital en américa latina?
- ¿Qué está pasando con el ecosistema de venture capital en Colombia?

### module-4-vc-instruments-1
**Lecciones:**
- Instrumentos de inversión y análisis de posiciones en venture capital
- Análisis de posiciones en venture capital Parte 1
- Análisis de posiciones en venture capital Parte 2
- Data Room
- Ejercicio 1 - Instrumentos de inversión y análisis de posiciones en Venture Capital
- Ejercicio 2 - Cap Table
- Ejercicio 3 - Unit Economics

### Módulo 6 — Tesis de inversión
**Lecciones:**
- El porqué de la tesis de inversión
- Pilares técnicos de la tesis de inversión
- 
- Redacta tu tesis de inversión (Parte 1)
- Redacta tu tesis de inversión (Parte 2)

### Módulo 7 — Valoración de startups
**Lecciones:**
- Valoración de startups en Venture Capital
- Retos en la valoración de startups en Venture Capital
- Métodos de valoración en Venture Capital
- Método 1: Flujo de Caja Descontado
- Método 2: Scorecard (Método de puntuación)
- Método 3: Comparables (Múltiplos)
- Método 4: VC Method (Método de Venture Capital)

## Conceptos clave

### Venture Capital (VC)
- **Definición:** Capital de riesgo que invierte en startups early-stage a cambio de equity
- **Curva J:** Los fondos VC generan pérdidas iniciales antes de retornos positivos (típicamente años 3-7)
- **Power Law:** Pocos deals generan el 90%+ del retorno del fondo
- **Métricas clave:** TVPI, DPI, RVPI, IRR, MOIC

### Instrumentos de inversión
- **SAFE** (Simple Agreement for Future Equity): instrumento más común en pre-seed/seed
  - Variantes: cap only, discount only, cap + discount, MFN
  - Pro-rata rights: derecho a participar en rondas futuras
- **Convertible Note**: deuda + interés que convierte a equity en siguiente ronda
- **Equity directo**: participación directa vía acciones (más complejo, típico en Series A+)

### Valoración de startups early-stage
- **Berkus Method**: asigna valor a 5 factores de riesgo (idea, prototipo, equipo, alianzas estratégicas, product rollout)
- **Scorecard Method**: compara con startups similares en la región
- **VC Method**: trabaja hacia atrás desde el exit esperado
  - Pre-money = Post-money − inversión
  - Post-money = Exit value / Expected ROI
- **DCF adaptado**: proyección 5-10 años con tasa de descuento alta (50-80%) por riesgo
- **Comparables/Múltiplos**: EV/Revenue, EV/EBITDA vs peers

### Rango de valoraciones Colombia (pre-seed/seed)
- Pre-seed: $200K - $1M pre-money
- Seed: $1M - $5M pre-money
- Factores: equipo, tracción, mercado (TAM), diferenciación tecnológica

### Ecosistema LATAM/Colombia
- **Ruta N**: hub de innovación Medellín, acceso a startups tech
- **iNNpulsa**: agencia colombiana de emprendimiento e innovación
- **LAVCA**: Latin American Venture Capital Association — datos del sector
- **Principales exits LATAM**: Rappi, Mercado Libre, Nubank, NotCo
- **Sectores hot Colombia 2024-2025**: Fintech, AgriTech, ClimaTech, HealthTech

### Due Diligence
- **Data Room checklist**: cap table, financieros, contratos clave, IP, equipo, pipeline
- **Red flags**: founder disputes, deuda oculta, dependencia de 1 cliente, IP sin proteger
- **Unit Economics clave**: CAC, LTV, LTV/CAC ratio (mínimo 3x), Payback period, Churn

### Cap Table management
- **Dilución**: cada ronda diluye a fundadores e inversores anteriores
- **ESOP pool**: típicamente 10-20% para empleados, mejor crear ANTES de valorar
- **Pro-rata rights**: protegen posición en rondas futuras
- **Anti-dilution**: full ratchet vs weighted average

### Tesis de inversión ángel
Componentes obligatorios:
1. **Sectores de foco**: 2-3 verticales donde tienes conocimiento/red
2. **Stage preferido**: pre-seed, seed, Series A
3. **Ticket size**: min/max por deal
4. **Geografía**: Colombia, LATAM, global
5. **Criterios no negociables**: equipo, TAM mínimo, modelo de negocio
6. **Value-add**: qué aportas más allá del dinero (red, expertise, clientes)

### Gobernanza de fondos VC
- **GP** (General Partner): administra el fondo, toma decisiones de inversión
- **LP** (Limited Partner): inversionistas del fondo
- **Management fee**: 2% anual sobre capital comprometido
- **Carried interest**: 20% de las ganancias (after 8% hurdle típicamente)
- **Investment Committee**: decide qué startups reciben inversión
- **Reportes LP**: quarterly updates, annual audits

## Scripts y recursos disponibles

```python
# Búsqueda en RAG local
import json
RAG = 'E:/Documents/PROYECTOS/AgencIA/platzi_clone/rag/venture_chunks.jsonl'

def search_rag(query, top_k=5):
    q = query.lower()
    chunks = [json.loads(l) for l in open(RAG, encoding='utf-8')]
    scored = [(c, sum(w in c['text'].lower() for w in q.split())) for c in chunks]
    return [c for c,s in sorted(scored, key=lambda x:-x[1]) if s > 0][:top_k]
```

## Acceso al portal
- URL: https://www.lanchmon.app/login/rutan/auth
- Credenciales: lumpenvisual@gmail.com / BSV7zmALrYyyoxxI
- Player local: http://localhost:3055 (Venture School tab)
- Tunnel público: https://repository-hdtv-announcements-newport.trycloudflare.com
