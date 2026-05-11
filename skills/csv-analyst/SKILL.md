---
name: csv-analyst
description: Análisis de CSVs masivos (>500MB) con pandas. Filtros para persona natural vs empresa, limpieza de valores monetarios, agrupaciones por entidad/documento, y respuesta a preguntas de datos de contratos públicos Colombia (SECOP).
tools: Bash, PowerShell, Read, Write, Agent
---

# CSV Analyst — Análisis de datos masivos con pandas

## Carga segura de CSVs grandes

```python
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

# Siempre cargar como str primero para evitar pérdida de ceros en cédulas/NITs
df = pd.read_csv(
    csv_path,
    encoding="utf-8",
    low_memory=False,
    dtype=str,
    on_bad_lines="skip"   # pandas 3.x (antes: error_bad_lines=False)
)
df.columns = df.columns.str.strip().str.strip('"')
print(f"Shape: {df.shape[0]:,} x {df.shape[1]}")
```

---

## Limpieza de valores monetarios (SECOP / contratos Colombia)

```python
# Columna "Valor del Contrato" puede tener $, comas, espacios, comillas
df["_valor"] = (
    df["Valor del Contrato"]
    .str.replace(r'[\$,\s"]', '', regex=True)
    .str.replace(r'[^0-9.\-]', '', regex=True)
)
df["_valor"] = pd.to_numeric(df["_valor"], errors="coerce").fillna(0)
```

---

## Identificar persona natural (CC) en SECOP II

```python
# FILTRO 1: Solo Cédula de Ciudadanía — match EXACTO, no contains
cc = df[df["TipoDocProveedor"].str.strip().str.upper() == "CÉDULA DE CIUDADANÍA"].copy()

# FILTRO 2: Documento numérico 5-12 dígitos (descarta NITs, "No Definido", pasaportes)
cc = cc[cc["Documento Proveedor"].str.strip().str.match(r'^\d{5,12}$', na=False)].copy()

# FILTRO 3: Domicilio válido publicado
dom_mask = (
    cc["Domicilio Representante Legal"].notna() &
    (~cc["Domicilio Representante Legal"].str.upper().str.contains(
        r'^NO DEFINIDO$|^NAN$|^N/A$|^\s*$', na=True, regex=True)) &
    (cc["Domicilio Representante Legal"].str.len() > 5)
)
cc_dom = cc[dom_mask].copy()
```

**Por qué estos filtros:** "No Definido" puede tener el mayor monto pero no es persona natural. NITs de empresas tienen más de 12 dígitos o no son puramente numéricos.

---

## Agregación estándar por documento

```python
agg = cc_dom.groupby("_doc").agg(
    nombre=("Proveedor Adjudicado",
            lambda x: x.mode()[0] if len(x) > 0 else x.iloc[0]),
    n_entidades=("_entidad", "nunique"),    # entidades DISTINTAS
    n_contratos=("_entidad", "count"),      # total contratos
    monto_total=("_valor", "sum"),
    domicilio=("_domicilio", "first"),
).reset_index()

# Condición "Pez Gordo" — 10+ entidades distintas, mayor monto
candidatos = agg[agg["n_entidades"] >= 10].sort_values("monto_total", ascending=False)
ganador = candidatos.iloc[0]
```

---

## Formato de montos COP

```python
def fmt_cop(v):
    if v >= 1e12: return f"${v/1e12:.2f} Billones COP"
    if v >= 1e9:  return f"${v/1e9:.2f} Miles de millones COP"
    if v >= 1e6:  return f"${v/1e6:.1f} Millones COP"
    return f"${v:,.0f} COP"
```

---

## Queries frecuentes SECOP

```python
# Contratista con más entidades distintas
df.groupby("Documento Proveedor")["Nombre Entidad"].nunique().nlargest(10)

# Entidad con mayor gasto
df.groupby("Nombre Entidad")["_valor"].sum().nlargest(10)

# Contratos por año
df["_year"] = pd.to_datetime(df["Fecha de Firma"], errors="coerce").dt.year
df.groupby("_year")["_valor"].sum()

# Tipo de contrato más común
df["Tipo de Contrato"].value_counts().head(10)

# Supervisores únicos
df[["Nombre supervisor", "Número de documento supervisor"]].drop_duplicates()
```

---

## Columnas clave SECOP II (nombres exactos)

| Columna | Descripción |
|---------|-------------|
| `TipoDocProveedor` | Tipo de documento del proveedor |
| `Documento Proveedor` | Número de documento |
| `Proveedor Adjudicado` | Nombre del proveedor |
| `Nombre Entidad` | Entidad contratante |
| `Valor del Contrato` | Monto (con caracteres especiales) |
| `Fecha de Firma` | Fecha del contrato |
| `Domicilio Representante Legal` | Dirección registrada |
| `Nombre supervisor` | Nombre del supervisor |
| `Número de documento supervisor` | Doc del supervisor |

---

## Script autónomo (patrón para hackathon)

```python
# Uso: python3 analisis.py <ruta_al_csv>
import sys, os
def main(csv_path):
    if not os.path.exists(csv_path):
        print(f"[ERROR] Archivo no encontrado: {csv_path}"); sys.exit(1)
    # ... análisis
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 analisis.py <ruta_al_csv>"); sys.exit(1)
    main(sys.argv[1])
```

---

## Estrategia multiagente para preguntas múltiples

Cuando hay 15+ preguntas sobre un CSV, lanzar agentes en paralelo:
- Agente A: preguntas de conteo y sumas globales
- Agente B: preguntas de top N y rankings
- Agente C: preguntas de filtros específicos (fechas, tipos, entidades)

Cada agente carga el CSV independientemente. Reunir resultados en el agente principal.
