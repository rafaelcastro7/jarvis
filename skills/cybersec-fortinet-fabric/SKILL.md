---
name: cybersec-fortinet-fabric
description: Fortinet Security Fabric — arquitectura integrada que conecta FortiGate (NGFW) + FortiEDR + FortiAnalyzer (SIEM) + FortiSOAR + FortiManager. Max 35 downstream FortiGates. Requiere FortiAnalyzer 6.2+ para Security Fabric. Best practices hardening incluidos.
---

# Fortinet Security Fabric

## Componentes

| Producto | Funcion |
|----------|---------|
| **FortiGate** | NGFW (firewall, IPS, VPN, SD-WAN) — root del fabric |
| **FortiEDR** | Endpoint detection & response (anti-malware behavioral) |
| **FortiAnalyzer** | Log aggregation, SIEM, reporting |
| **FortiSOAR** | Security orchestration & automated response |
| **FortiManager** | Central management de FortiGates |
| **FortiSandbox** | Detonacion de malware |
| **FortiClient** | Endpoint agent + ZTNA |
| **FortiMail/FortiWeb** | Email + WAF |

## Requisitos Security Fabric

- FortiGate root con VDOMs disabled (o split-task VDOM)
- Operacion en NAT mode
- Max 35 downstream FortiGates
- FortiAnalyzer 6.2+ obligatorio

## Hardening best practices FortiGate

```
1. Cambiar admin port (default 443/80)
2. Habilitar 2FA en admins
3. Restringir trusted hosts en admin profile
4. Disable HTTP (solo HTTPS)
5. Strong password policy
6. NTP enabled (logs correlados)
7. Logs a FortiAnalyzer
8. Update FortiGuard frecuente (AV, IPS, App Control, WebFilter)
9. SSL inspection en perimetro
10. Geo-IP blocking para paises high-risk
```

## FortiAnalyzer security

- Detras de FortiGate (no expuesto)
- Password policy + admin lockout
- NTP sync
- Logs centralizados
- Backup automatizado

## Security Rating Checks

Built-in en FortiGate. Analiza fabric deployment y senala:
- Vulnerabilidades de config
- Best practices ausentes
- Compliance gaps (PCI-DSS, HIPAA)

## Para mi empresa

Topologia recomendada:
```
Internet -> FortiGate (NGFW) -> LAN
                |-> FortiAnalyzer (logs)
                |-> FortiManager (config)
FortiClient en endpoints -> FortiEDR cloud
FortiSandbox para detonacion
FortiSOAR para playbooks IR
```

Source: docs.fortinet.com
