---
name: cybersec-picus
description: Picus Security — Breach and Attack Simulation (BAS) liderante. Micro-emulation plans por cada tecnica MITRE ATT&CK. Analiza logs SIEM/EDR para detectar undetected/unlogged/non-alerted attacks. Integraciones nativas: MS, Palo Alto, CrowdStrike, Splunk, Fortinet, F5, etc.
---

# Picus Security BAS

## Que hace unico

1. **Micro-emulation por tecnica MITRE** - launch ready-to-run para CUALQUIER tactica
2. **Dynamic heat map** ATT&CK coverage
3. **SIEM/EDR log analysis** - detecta:
   - Undetected attacks (no aparece en logs)
   - Unlogged (paso pero no se registro)
   - Non-alerted (logueado pero sin alert)

## Workflow tipico

```
1. Selecciona tecnica MITRE (ej. T1059.001 PowerShell)
2. Picus ejecuta micro-attack controlado
3. Picus mira tus SIEM/EDR logs
4. Reporta: detected? logged? alerted?
5. Si NO: te da regla detection sugerida (Sigma/EQL)
```

## Integraciones criticas

Picus integra nativamente con:
- **Microsoft Defender** (XDR, Sentinel)
- **Palo Alto Cortex** XDR/XSIAM
- **CrowdStrike Falcon**
- **Splunk** (SIEM)
- **Fortinet** FortiSIEM
- **SentinelOne**
- **Check Point**, IBM, **Imperva**, F5

Cuando emula un ataque, automaticamente verifica si TUS herramientas lo detectaron.

## Output value

- ATT&CK coverage % (cuanta cobertura tienes hoy)
- Gap report: que tecnicas NO detectarias hoy
- Mitigation library: sugiere config changes en tus tools

## Stack alternativo (open)

- **Atomic Red Team** (Red Canary) — scripts por tecnica MITRE
- **MITRE CALDERA** — orquestador
- **Sigma rules** — detection rules portables
- **Detection-as-code** (Panther, Splunk Lab)

Source: picussecurity.com
