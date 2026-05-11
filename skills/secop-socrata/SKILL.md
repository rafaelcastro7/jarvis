---
name: secop-socrata
description: Integración con Socrata SODA API para datasets de contratación pública colombiana (datos.gov.co). Incluye IDs de datasets SECOP I/II, patrones de query, mapeo de campos, y manejo de paginación y errores.
tools: Read, Edit, Bash
---

# SECOP / Socrata SODA API — datos.gov.co

## Datasets principales

| Dataset | ID Socrata | Descripción | Registros aprox. |
|---------|-----------|-------------|-----------------|
| SECOP II - Contratos | `p6dx-8zbt` | Contratos electrónicos SECOP II | 5.6M+ |
| SECOP I - DB1 | `jbjy-vk9h` | Base 1 SECOP I | Variable |
| SECOP I - DB2 | `dmgg-8hin` | Base 2 SECOP I (2025+) | Variable |
| SECOP II CSV (hackathon) | *(descarga directa)* | Dataset completo para análisis local | 1M+ filas |

**URL base:** `https://www.datos.gov.co/resource/{DATASET_ID}.json`

---

## Queries SOQL básicas

```typescript
const BASE = "https://www.datos.gov.co/resource";

// Buscar por entidad (LIKE)
const url = `${BASE}/p6dx-8zbt.json?$where=nombre_entidad LIKE '%${entityName}%'&$order=precio_base DESC&$limit=100`;

// Por NIT de entidad
const url = `${BASE}/p6dx-8zbt.json?$where=nit_entidad='${nit}'&$limit=50`;

// Suma total
const url = `${BASE}/p6dx-8zbt.json?$select=sum(precio_base)`;

// Conteo por año
const url = `${BASE}/p6dx-8zbt.json?$select=year_fiscal,count(*)&$group=year_fiscal&$order=year_fiscal DESC`;

// Top proveedores por monto
const url = `${BASE}/p6dx-8zbt.json?$select=nombre_del_contratista,sum(precio_base) as total&$group=nombre_del_contratista&$order=total DESC&$limit=10`;
```

---

## Cliente con timeout y manejo de errores

```typescript
const SOCRATA_APP_TOKEN = process.env.SOCRATA_APP_TOKEN || "";

export async function fetchContractsFromSecop(
  entityName: string,
  limit = 100
): Promise<Contract[]> {
  const encoded = encodeURIComponent(`%${entityName}%`);
  const query = [
    `$where=nombre_entidad LIKE '${encoded}' OR nit_entidad LIKE '${encoded}'`,
    `$order=precio_base DESC`,
    `$limit=${limit}`,
    SOCRATA_APP_TOKEN ? `$$app_token=${SOCRATA_APP_TOKEN}` : "",
  ].filter(Boolean).join("&");

  const res = await fetch(`${BASE}/p6dx-8zbt.json?${query}`, {
    signal: AbortSignal.timeout(20000),
  });

  if (!res.ok) throw new Error(`Socrata ${res.status}: ${await res.text()}`);
  const raw = await res.json();
  return (raw as Record<string, string>[]).map(mapSecopRecord);
}
```

---

## Mapeo de campos SECOP II → interfaz interna

```typescript
function mapSecopRecord(raw: Record<string, string>): Contract {
  return {
    id_contrato:              raw.id_contrato || raw.referencia_proceso || "",
    referencia_proceso:       raw.referencia_proceso || "",
    url_proceso:              raw.url_proceso || raw.urlproceso || "",
    nombre_entidad:           raw.nombre_entidad || "",
    nit_entidad:              raw.nit_entidad || "",
    departamento:             raw.departamento || "",
    ciudad:                   raw.ciudad || raw.municipio || "",
    modalidad_de_contratacion: raw.modalidad_de_contratacion || "",
    estado_contrato:          raw.estado_contrato || "",
    objeto_del_contrato:      raw.objeto_del_contrato || raw.descripcion_del_proceso || "",
    valor_del_contrato:       raw.precio_base || raw.valor_del_contrato || "0",
    nombre_del_contratista:   raw.nombre_del_contratista || raw.proveedor_adjudicado || "",
    documento_proveedor:      raw.documento_proveedor || raw.nit_del_contratista || "",
    fecha_de_firma:           raw.fecha_de_firma || raw.fecha_firma_contrato || "",
    year_fiscal:              raw.year_fiscal || raw.anno_de_firma || "",
  };
}
```

---

## App Token (reducir rate limiting)

Registrarse gratis en [data.socrata.com](https://data.socrata.com) para obtener token.

```env
SOCRATA_APP_TOKEN=tu_token_aqui
```

Sin token: límite ~1000 req/día. Con token: 100K+ req/día.

---

## Campos clave por dataset

### SECOP II (`p6dx-8zbt`)
```
id_contrato, referencia_proceso, nombre_entidad, nit_entidad,
departamento, ciudad, modalidad_de_contratacion, estado_contrato,
objeto_del_contrato, precio_base, nombre_del_contratista,
documento_proveedor, fecha_de_firma, year_fiscal, url_proceso
```

### SECOP I DB1 (`jbjy-vk9h`)
```
anno_firma, nombre_entidad, nit_entidad, departamento_entidad,
ciudad_entidad, modalidad_de_contratacion, tipo_de_contrato,
nombre_contratista, nit_contratista, cuantia_proceso,
fecha_inicio_contrato, fecha_fin_contrato
```

### SECOP I DB2 (`dmgg-8hin`)
```
(misma estructura que DB1, datos 2025+)
```

---

## Agrupación por proveedor

```typescript
export function groupContractsByProvider(
  contracts: Contract[]
): [string, Contract[]][] {
  const map = new Map<string, Contract[]>();

  for (const contract of contracts) {
    const key = `REF:${contract.documento_proveedor || contract.nombre_del_contratista}`;
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(contract);
  }

  // Ordenar grupos por monto total descendente
  return [...map.entries()].sort(([, a], [, b]) => {
    const sumA = a.reduce((s, c) => s + (parseFloat(c.valor_del_contrato) || 0), 0);
    const sumB = b.reduce((s, c) => s + (parseFloat(c.valor_del_contrato) || 0), 0);
    return sumB - sumA;
  });
}
```

---

## Proxy en Express (evita CORS en producción)

```typescript
app.get("/api/secop/contracts", asyncHandler(async (req, res) => {
  const entity = String(req.query.entity || "").trim();
  const limit = Math.min(parseInt(String(req.query.limit || "50")), 200);
  if (!entity) throw new HttpError(400, "entity param required");

  const contracts = await fetchContractsFromSecop(entity, limit);
  res.json({ contracts, total: contracts.length });
}));
```

---

## Descarga de documento fuente

```typescript
app.get("/api/secop/source", asyncHandler(async (req, res) => {
  const sourceUrl = String(req.query.url || "").trim();
  const processId = String(req.query.processId || "").trim();

  const response = await fetch(sourceUrl, { signal: AbortSignal.timeout(20000) });
  const html = await response.text();
  const bodyText = stripHtml(html).slice(0, 20000); // primeros 20KB

  res.json({
    url: sourceUrl, processId,
    statusCode: response.status,
    fetchedAt: new Date().toISOString(),
    excerpt: bodyText.slice(0, 500),
    bodyText,
  });
}));
```
