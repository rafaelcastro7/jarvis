---
name: cybersec-pentera
description: Pentera — Automated Security Validation (ASV). Ejecuta TTPs reales de adversarios en produccion para validar exploitability. Cubre las 5 etapas de CTEM (Continuous Threat Exposure Management). BAS 2.0 = BAS + automated pentest.
---

# Pentera

## Filosofia ASV

"Don't trust your security stack — validate it."

Ejecuta ataques **reales** en produccion (controlados) para probar:
- Que controles SI detienen ataques
- Que gaps son **explotables** (no solo presentes)
- Priorizacion basada en exploitability real, no CVSS

## CTEM 5 Stages (Gartner)

1. **Scoping** - definir attack surface
2. **Discovery** - encontrar assets + vulnerabilidades
3. **Prioritization** - cuales son criticos
4. **Validation** - probar si son explotables (aqui Pentera)
5. **Mobilization** - remediar + comunicar

## Tactics que automatiza

- Network sniffing (capturar creds en transit)
- File enumeration (descubrir secretos en shares)
- Credential dumping (memoria, LSASS, registry)
- Privilege escalation (kernel exploits, mis-config)
- Lateral movement (PsExec, WMI, SMB)
- Domain takeover (golden ticket, kerberoasting)

## BAS 2.0 vs BAS legacy

| Legacy BAS | BAS 2.0 (Pentera) |
|------------|-------------------|
| Simulacion estatica | Adversarial autonomo |
| Scripts pre-definidos | Adapta segun entorno |
| Senalan riesgos | Prueban explotabilidad |
| Periodicos | Continuos |

## Reporting estilo Pentera

Cada hallazgo trae:
- TTP usado (MITRE)
- Camino de ataque step-by-step
- Tiempo total (real-world impact)
- Remediation priority basada en blast radius

## Para mi empresa

Run Pentera Q1, Q2 minimum. Si no presupuesto: Atomic Red Team (open) + Caldera (MITRE)

Source: pentera.io
