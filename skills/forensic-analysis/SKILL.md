---
name: forensic-analysis
description: Motor de análisis forense de contratos públicos. Reglas heurísticas de riesgo, similitud semántica con embeddings Ollama, scoring ponderado, detección de fraccionamiento/bunching/abuso de directa. Implementado en GobIA Auditor.
tools: Read, Edit, Write
---

# Forensic Analysis — Motor de Riesgo de Contratos

## Resultado de análisis (`AnalysisResult`)

```typescript
interface AnalysisResult {
  groupKey: string;           // "REF:NIT_PROVEEDOR"
  providerName: string;
  contracts: Contract[];
  totalValue: number;
  similarityScore: number;    // promedio cosine similarity entre objetos
  maxDayDiff: number;         // máxima distancia en días entre contratos
  risk: "Red" | "Orange" | "Green";
  redFlags: string[];         // mensajes de reglas disparadas
  detailedFindings: DetailedFinding[];
  riskScore: number;          // 0-100+
}
```

---

## Flujo de análisis (`src/lib/analysis.ts`)

```typescript
export async function analyzeContractGroup(
  groupKey: string,
  contracts: Contract[]
): Promise<AnalysisResult> {
  // 1. Embeddings de objetos de contratos
  const embeddings = await Promise.all(
    contracts.map((c) => getEmbedding(c.objeto_del_contrato || ""))
  );

  // 2. Similitud semántica promedio
  const similarities: number[] = [];
  for (let i = 0; i < embeddings.length; i++) {
    for (let j = i + 1; j < embeddings.length; j++) {
      similarities.push(cosineSimilarity(embeddings[i], embeddings[j]));
    }
  }
  const avgSimilarity = similarities.length > 0
    ? similarities.reduce((a, b) => a + b, 0) / similarities.length
    : 0;

  // 3. Estadísticas de cuantías (bunching)
  const values = contracts.map((c) => parseFloat(c.valor_del_contrato) || 0);
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const variance = values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length;
  const cvPercent = mean > 0 ? (Math.sqrt(variance) / mean) * 100 : 100;

  // 4. Distancias temporales
  const dates = contracts
    .map((c) => new Date(c.fecha_de_firma).getTime())
    .filter((d) => !isNaN(d))
    .sort((a, b) => a - b);
  const maxDayDiff = dates.length > 1
    ? (dates[dates.length - 1] - dates[0]) / (1000 * 60 * 60 * 24)
    : 0;

  // 5. Ejecutar reglas de inteligencia
  const { flags, riskScore: rulesScore } = runIntelligenceAudit(contracts);

  // 6. Scoring compuesto
  let score = rulesScore;
  if (avgSimilarity > 0.85) score += 50;
  else if (avgSimilarity > 0.7) score += 25;
  if (cvPercent < 5 && contracts.length >= 3) score += 35; // bunching crítico
  if (contracts.reduce((s, c) => s + (parseFloat(c.valor_del_contrato) || 0), 0) > 5e9) score += 20;

  // 7. Clasificación de riesgo
  const risk: "Red" | "Orange" | "Green" =
    score >= 75 ? "Red" : score >= 45 ? "Orange" : "Green";

  return {
    groupKey, providerName: contracts[0]?.nombre_del_contratista || "",
    contracts, totalValue: values.reduce((a, b) => a + b, 0),
    similarityScore: avgSimilarity, maxDayDiff,
    risk, redFlags: flags,
    detailedFindings: buildDetailedFindings(contracts, flags),
    riskScore: score,
  };
}
```

---

## Reglas de inteligencia (`src/lib/intelligence.ts`)

```typescript
export interface IntelligenceRule {
  id: string;
  name: string;
  riskWeight: number;  // puntos que suma al score si se dispara
  check: (contracts: Contract[]) => {
    triggered: boolean;
    message: string;
    evidence?: string;
  };
}

export const INITIAL_RULES: IntelligenceRule[] = [
  {
    id: "RULE_DIRECT_ABUSE",
    name: "Abuso de Contratación Directa",
    riskWeight: 40,
    check: (contracts) => {
      const direct = contracts.filter((c) =>
        c.modalidad_de_contratacion?.toLowerCase().includes("directa") ||
        c.modalidad_de_contratacion?.toLowerCase().includes("mínima")
      );
      const ratio = direct.length / contracts.length;
      return {
        triggered: ratio > 0.8 && contracts.length > 3,
        message: `Patrón de contratación directa (${(ratio * 100).toFixed(0)}%)`,
        evidence: `${direct.length} de ${contracts.length} bajo modalidad directa/mínima`,
      };
    },
  },
  {
    id: "RULE_TIME_SQUEEZE",
    name: "Aglomeración Temporal",
    riskWeight: 35,
    check: (contracts) => {
      const dates = contracts
        .map((c) => new Date(c.fecha_de_firma).getTime())
        .filter((d) => !isNaN(d))
        .sort((a, b) => a - b);
      if (dates.length < 3) return { triggered: false, message: "" };
      const spanDays = (dates[dates.length - 1] - dates[0]) / 86400000;
      return {
        triggered: spanDays < 90,
        message: `${contracts.length} contratos en ${spanDays.toFixed(0)} días`,
        evidence: `Span: ${spanDays.toFixed(0)} días (umbral: 90)`,
      };
    },
  },
  {
    id: "RULE_NOTORIOUS_ENTITY",
    name: "Entidad de Alto Riesgo Histórico",
    riskWeight: 25,
    check: (contracts) => {
      const hit = contracts.find((c) =>
        NOTORIOUS_ENTITIES.some((e) => c.nombre_entidad?.toUpperCase().includes(e))
      );
      return {
        triggered: !!hit,
        message: `Contratación con entidad de alto riesgo: ${hit?.nombre_entidad}`,
      };
    },
  },
  {
    id: "RULE_VALUE_SPIKE",
    name: "Concentración Económica Extrema",
    riskWeight: 20,
    check: (contracts) => {
      const total = contracts.reduce(
        (s, c) => s + (parseFloat(c.valor_del_contrato) || 0), 0
      );
      return {
        triggered: total > 5_000_000_000,
        message: `Concentración de $${(total / 1e9).toFixed(1)}B COP en un solo proveedor`,
      };
    },
  },
];

// Entidades con historial de irregularidades
export const NOTORIOUS_ENTITIES = [
  "UNGRD", "GOBERNACION DE LA GUAJIRA", "GOBERNACION DEL CHOCO",
  "GOBERNACION DE CORDOBA", "ALCALDIA DE RIOHACHA", "CARDIQUE",
  "CORPOCESAR", "FONDO ADAPTACION", "INVÍAS",
];
```

---

## Detección de Bunching (fraccionamiento por cuantías)

```typescript
function detectBunching(contracts: Contract[]): boolean {
  const values = contracts.map((c) => parseFloat(c.valor_del_contrato) || 0)
    .filter((v) => v > 0);
  if (values.length < 3) return false;

  const mean = values.reduce((a, b) => a + b) / values.length;
  const cv = Math.sqrt(
    values.reduce((s, v) => s + Math.pow(v - mean, 2), 0) / values.length
  ) / mean;

  // CV < 5% = cuantías casi idénticas = fraccionamiento sospechoso
  return cv < 0.05;
}
```

---

## Clasificación de riesgo

| Score | Risk | Color | Acción |
|-------|------|-------|--------|
| ≥ 75 | Red | `#dc2626` | Requiere revisión inmediata |
| 45-74 | Orange | `#d97706` | Vigilancia activa |
| < 45 | Green | `#16a34a` | Sin alertas críticas |

---

## Caché de análisis (PostgreSQL)

```typescript
// Guardar resultado
await query(
  `INSERT INTO analysis_cache (groupkey, data, timestamp)
   VALUES ($1, $2, $3)
   ON CONFLICT (groupkey) DO UPDATE SET data=$2, timestamp=$3`,
  [groupKey, JSON.stringify(result), Date.now()]
);

// Recuperar resultado
const { rows } = await query<{ data: string }>(
  "SELECT data FROM analysis_cache WHERE groupkey = $1",
  [groupKey]
);
const result = rows.length > 0 ? JSON.parse(rows[0].data) : null;
```

---

## Generación de reporte forense

```typescript
// src/lib/gemini.ts
export async function generateForensicReport(results: AnalysisResult[], lang: "ES" | "EN") {
  const redCases = results.filter((r) => r.risk === "Red");
  const prompt = `
Eres un Auditor Forense Digital. Analiza estos ${redCases.length} casos de alto riesgo:
${redCases.map((r) => `- ${r.providerName}: Score ${r.riskScore}, $${(r.totalValue/1e9).toFixed(2)}B, Flags: ${r.redFlags.join("; ")}`).join("\n")}

Genera INFORME DE AUDITORÍA FORENSE con:
1. RESUMEN EJECUTIVO (3 puntos clave)
2. MATRIZ DE RIESGOS (tabla por proveedor)
3. EVIDENCIA TÉCNICA (patrones detectados)
4. RECOMENDACIONES (acciones concretas)
`;
  // Intenta con generateText() → Ollama fallback → buildDeterministicReport()
}
```
