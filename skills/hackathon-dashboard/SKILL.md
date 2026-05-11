---
name: hackathon-dashboard
description: Crea dashboards de hackathon con React+Recharts+Framer Motion. Tabs por reto, BigAnswer cards, QCard con preguntas numeradas, datos desde API REST o CSV. Publicación vía Cloudflare tunnel.
tools: Bash, PowerShell, Read, Edit, Write, Glob, Grep, Agent
---

# Hackathon Dashboard — Flujo completo

## Estructura de componentes probada

```
SECOPAnalysis (o nombre del proyecto)
├── Tabs: RETO1 | RETO2 | RETO3 | API
├── PanelRetoN()         — panel por cada reto
│   ├── BigAnswer        — respuesta destacada (número grande)
│   └── QCard            — card por pregunta con número
└── PanelAPI()           — endpoints documentados con curl
```

### `QCard` — card de pregunta
```tsx
interface QCardProps {
  n: string | number;      // número de pregunta
  title: string;           // texto de la pregunta
  color?: string;          // color del borde/acento
  light?: string;          // fondo suave
  children: React.ReactNode;
}
```

### `BigAnswer` — respuesta grande destacada
```tsx
interface BigAnswerProps {
  value: string | number;
  label: string;           // descripción debajo
  color?: string;
}
```

---

## Tab navigation con Framer Motion

```tsx
const TABS = [
  { id: 'RETO1', label: 'Reto 1', sub: 'Descripción', color: '#2563eb' },
  { id: 'RETO2', label: 'Reto 2', sub: 'Descripción', color: '#16a34a' },
  { id: 'RETO3', label: 'Reto 3', sub: 'Descripción', color: '#dc2626', badge: 'Etiqueta' },
  { id: 'API',   label: 'API',    sub: 'Endpoints',   color: '#7c3aed' },
];

// AnimatePresence con key={activeTab} para transiciones suaves
<AnimatePresence mode="wait">
  <motion.div key={activeTab} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}>
    {activeTab === 'RETO1' && <PanelReto1 />}
    {/* ... */}
  </motion.div>
</AnimatePresence>
```

---

## Datos desde Socrata SODA API

```typescript
// Patrón para datasets de datos abiertos Colombia (datos.gov.co)
const BASE = "https://www.datos.gov.co/resource";
const DATASET_ID = "jbjy-vk9h";  // ejemplo SECOP I

async function fetchSocrata(datasetId: string, query: string) {
  const url = `${BASE}/${datasetId}.json?${query}&$$app_token=...`;
  const res = await fetch(url, { signal: AbortSignal.timeout(15000) });
  return res.json();
}

// Ejemplos de queries SODA
// Suma: $select=sum(valor_del_contrato)&$where=anno_firma='2024'
// Conteo distintos: $select=count(distinct nit_entidad)
// Top N: $order=total desc&$limit=10
```

---

## Script Python descargable desde dashboard

```tsx
// En el panel del reto:
<a href="/script_analisis.py" download="script_analisis.py"
   className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-white text-xs font-black"
   style={{ background: COLOR }}>
  ⬇ Descargar script
</a>
```

```json
// package.json — copiar script a dist en cada build
"build": "vite build && node -e \"require('fs').copyFileSync('script.py','dist/script.py')\""
```

---

## Checklist de publicación

1. `npm run build` — verificar 0 errores TS
2. Verificar cloudflared activo: `Get-Process | Where-Object { $_.ProcessName -like "*cloudflared*" }`
3. `npm run restart` — usar restart-server.ps1 (ver `/tunnel-manager`)
4. Probar URL pública: `Invoke-WebRequest "https://url.trycloudflare.com/" -UseBasicParsing`
5. Verificar cada tab manualmente en browser
6. `git add`, commit semántico, push

---

## Colores por reto (convención usada)

```typescript
const COLOR_R1 = '#2563eb';  // azul — institucional
const COLOR_R2 = '#16a34a';  // verde — datos/análisis
const COLOR_R3 = '#dc2626';  // rojo — stress test / seguridad
const COLOR_API = '#7c3aed'; // violeta — técnico
```

---

## Errores comunes

| Error | Causa | Fix |
|-------|-------|-----|
| Props TS mismatch en QCard/BigAnswer | Componente base no acepta prop nueva | Extender con `??` fallback: `n ?? number` |
| Bundle >1MB | Lazy loading no aplicado | `const Heavy = React.lazy(() => import('./Heavy'))` |
| CORS en Socrata | Sin app_token en producción | Agregar `$$app_token` o proxy en Express |
| Script no descarga | Build limpia dist/ | Agregar copia en script `build` de package.json |
