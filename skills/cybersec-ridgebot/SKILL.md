---
name: cybersec-ridgebot
description: RidgeBot - automated penetration testing AI-driven. Agentless blackbox + internal + external + lateral movement. Botlets que ejecutan sin riesgo a produccion. Mapeo automatico a MITRE ATT&CK. Continuous testing diario/semanal/mensual.
---

# RidgeBot (Ridge Security)

## Que hace

RidgeBot autonomamente:
1. **Scanea** infraestructura (agentless)
2. **Valida** vulnerabilidades
3. **Exploita** de forma segura (Botlets — agentes especializados)
4. **Documenta** evidencia hard de gaps

## Diferenciadores vs nmap+nessus

- No solo encuentra CVEs — los **explota** y prueba exploitability real
- Lateral movement automatico
- Auto-mapeo MITRE ATT&CK
- Modo continuous: cada dia/semana/mes
- Real-time attack visualization

## Tipos de tests

| Tipo | Que prueba |
|------|-----------|
| **Blackbox external** | Perimetro web/cloud sin credenciales |
| **Internal LAN** | Pivot desde inside, escalada privilegios |
| **Lateral movement** | Cross-VLAN, AD compromise, golden ticket |
| **Web app** | OWASP Top 10 con explotacion real |

## Output

- HTML reports con kill-chain visual
- CVSS + MITRE ATT&CK tag por hallazgo
- Re-test automatico despues de remediation

## Use case en empresa

```
Semana 1: Run blackbox sobre IP publica
Semana 2: Run internal (instalar Botlet en LAN)
Semana 3: Run lateral movement
Mensual: Continuous monitoring + auto-retest
```

## Stack alternativo (open)

Si no tienes RidgeBot: **Nuclei + Metasploit + BloodHound + CrackMapExec** + scripting cron = 70% del valor

Source: ridgesecurity.ai
