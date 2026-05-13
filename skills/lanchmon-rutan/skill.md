---
name: lanchmon-rutan
description: Portal Lanchmon / Rutan para inversionistas ángel — Investment Academy (módulos 0 y 1), Bots IA de inversión (Valuation Check, Pitch Deck, Market Size), recursos globales (Carta, Kauffman Fellows). Plataforma iNNpulsa/Ruta N Colombia para dealflow y toma de decisiones de inversión.
tools: Read, WebFetch, Bash
---

# Lanchmon — Portal Rutan (Inversionistas Ángel)

## Acceso
- **URL:** https://www.lanchmon.app/login/rutan/auth
- **Programa:** iNNpulsa Colombia / Ruta N — ecosistema de startups e inversión
- **Perfil:** Investor (inversionista ángel)

## Secciones del portal

### 1. Onboarding (Dashboard principal)
- Panel de descubrimiento con módulos recomendados
- Acceso a: Investor Academy, AI Investor Education
- Módulo 0 y Módulo 1 disponibles

### 2. Inv. Academy (Investment Academy)
Cursos internos para aprender, evaluar y ejecutar inversiones con playbook profesional.

**Módulo 0 — Punto de partida: La inversión como catalizador de innovación**
- Glosario general (recomendado antes de iniciar)
- Conceptos base de inversión ángel

**Recursos disponibles:**
- Glosario general
- Ruta completa de aprendizaje
- Módulos secuenciales (0, 1, ...)

### 3. Recursos (Centro de Recursos para Inversionistas)
Aliados y recursos globales con beneficios para el programa:

| Recurso | Tipo | Beneficio |
|---------|------|-----------|
| **Carta** | Preferred Partner | 20% OFF para startups referidas, 0% fees implementación (nuevos clientes). 7,500+ fondos/SPVs, $145B AUA |
| **Kauffman Fellows** | Red global | Venture capital fellows network |
| **Otros aliados** | Varios | Descuentos y acceso preferencial |

### 4. Bots IA (AI Investor Tools)
Agentes de IA especializados para inversión:

| Bot | Función |
|-----|---------|
| **Invest. AI** | Asistente general de inversión |
| **Investor Edu.** | Coach de micro-aprendizaje personalizado, preguntas sobre inversión |
| **Valuation Check** | Análisis y validación de valuaciones de startups |
| **Pitch Deck** | Evaluación y feedback de pitch decks |
| **Market Size** | Análisis de tamaño de mercado (TAM/SAM/SOM) |

---

## Conceptos clave de inversión ángel (del programa)

### Tesis de inversión
- Definir: sectores preferidos, stage (pre-seed/seed), ticket mínimo/máximo
- Criterios: equipo, mercado, tracción, diferenciación
- Geografía: Colombia/LATAM o global

### Dealflow
- Fuentes: aceleradoras (Ruta N), redes ángeles, pitch events
- Filtros iniciales: deck review, one-pager, reunión inicial
- Due diligence: financiero, legal, mercado, equipo

### Estructura de inversiones ángel
- **SAFE** (Simple Agreement for Future Equity): instrumento más común en early-stage
- **Convertible note**: deuda que convierte a equity
- **Equity directo**: participación directa (más complejo, menos común en ángel)

### Valuación de startups early-stage
- Pre-revenue: basada en equipo, mercado, tracción temprana
- Métodos: Berkus, Scorecard, VC Method
- Rango típico Colombia: $500K - $3M pre-money en pre-seed

### Recursos de Carta (beneficio del programa)
- Gestión de cap table
- SPV (Special Purpose Vehicle) para co-inversión
- Documentos legales estandarizados
- Reportes a inversionistas automatizados

---

## Script de acceso (CDP)

```python
import asyncio
from playwright.async_api import async_playwright

EMAIL = 'lumpenvisual@gmail.com'
PASSWORD = 'BSV7zmALrYyyoxxI'

async def login_lanchmon():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://localhost:9222')
        ctx = b.contexts[0]
        page = await ctx.new_page()

        await page.goto('https://www.lanchmon.app/login/rutan/auth',
                        wait_until='domcontentloaded', timeout=25000)
        await asyncio.sleep(2)

        # Login con React state setter
        await page.evaluate(f"""() => {{
            function set(el, v) {{
                const d = Object.getOwnPropertyDescriptor(el.__proto__, 'value');
                d.set.call(el, v);
                el.dispatchEvent(new Event('input', {{bubbles:true}}));
                el.dispatchEvent(new Event('change', {{bubbles:true}}));
            }}
            set(document.querySelector('input[type=email]'), '{EMAIL}');
            set(document.querySelector('input[type=password]'), '{PASSWORD}');
        }}""")
        await asyncio.sleep(1)
        await page.evaluate("""() => {
            [...document.querySelectorAll('button')]
                .find(b => /iniciar|login/i.test(b.textContent))?.click();
        }""")
        await asyncio.sleep(5)
        print(f'Logueado: {page.url}')
        return page
```

---

## Lanchmon como plataforma

Lanchmon es infraestructura de datos para ecosistemas de innovación:
- **Empresas**: visibilidad, conexiones estratégicas, inteligencia de mercado
- **Startups**: preparación para inversión, dealflow, visibilidad ante inversores
- **Inversionistas**: discovery de startups, herramientas de evaluación IA
- **Aliados**: programas, conexiones, datos del ecosistema

**Diferenciador**: datos verificados en tiempo real del ecosistema startup colombiano.
