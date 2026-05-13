---
name: cybersec-defense-stack
description: Stack defensivo completo para proteger empresa - integra EC-Council CEH methodology, RidgeBot/Pentera/Picus validation, Palo Alto Cortex SOC, Fortinet Security Fabric, Radware app protection. Defense-in-depth con evidencia, MITRE ATT&CK coverage, NIST CSF alignment.
---

# Defense Stack Maestro

## Defense-in-Depth Layers

```
[1] PERIMETRO (Internet edge)
    - Radware Cloud (DDoS + WAF + Bot)
    - Palo Alto NGFW (Threat prevention + URL filter + Sandbox)
    - DNS filter (Cisco Umbrella o equivalente)

[2] NETWORK
    - Fortinet Security Fabric (segmentation + IPS)
    - Zero Trust (ZTNA, no flat networks)
    - VLAN micro-segmentation
    - Network DLP

[3] ENDPOINT
    - Cortex XDR Agent o FortiEDR
    - EDR con behavioral detection
    - App control / whitelisting
    - Patch management automatizado

[4] IDENTITY (MAS CRITICO)
    - IdP federado (Okta/Azure AD/Google)
    - MFA OBLIGATORIO (hardware keys preferred)
    - PAM (Privileged Access Mgmt)
    - Conditional Access
    - Identity Threat Detection

[5] DATA
    - Encryption at rest + in transit (AES-256, TLS 1.3)
    - DLP (Microsoft Purview o equivalente)
    - DSPM (Prisma Cloud DSPM, Varonis)
    - Backup 3-2-1 + immutable

[6] APP & CLOUD
    - SAST/DAST en CI/CD
    - SCA (Software Composition Analysis)
    - CNAPP (Prisma Cloud / Wiz)
    - CSPM, CWPP, CIEM, CDR

[7] DETECCION & RESPUESTA
    - SIEM (XSIAM, Splunk, Sentinel, Wazuh)
    - SOAR playbooks IR
    - 24/7 SOC (interno o MDR)
    - Threat hunting proactivo

[8] VALIDACION CONTINUA
    - RidgeBot (auto-pentest semanal)
    - Pentera (ASV - CTEM stage 4)
    - Picus (BAS - MITRE coverage)
    - Red team interno o externo Q
```

## NIST CSF 2.0 mapping

| Funcion | Tools |
|---------|-------|
| **Govern** | Policies + risk register + board reporting |
| **Identify** | Asset inventory + ASM (Cortex Xpanse, Wiz) |
| **Protect** | Toda la stack arriba |
| **Detect** | SIEM + XDR + UEBA + threat intel |
| **Respond** | SOAR + IR playbooks + retainer DFIR |
| **Recover** | Backup + DR site + tabletop exercises |

## MITRE ATT&CK Coverage (medir!)

Picus BAS o Atomic Red Team (open) te dan:
- % cobertura por tactica
- Heatmap de gaps
- Detection rules sugeridas

Meta minima: **>70% coverage en Initial Access + Execution + Persistence + C2**

## Como presentar evidencia (auditoria/board)

```
1. EXECUTIVE SUMMARY
   - Risk score actual (CVSS-weighted)
   - MTTR + MTTD trends
   - Incidents Q-over-Q
   - Cost savings (incidents prevented)

2. TECHNICAL DETAIL
   - Vulns por severidad (CRITICAL/HIGH/MED/LOW)
   - MITRE ATT&CK heatmap
   - Pentest findings + remediation status
   - Compliance status (PCI/HIPAA/ISO 27001)

3. EVIDENCE
   - Screenshots de exploit + remediation
   - Logs correlados (timestamps)
   - PCAP del ataque (si disponible)
   - Reports auto-generados de Pentera/RidgeBot/Picus

4. ROADMAP
   - Top 5 controls a implementar
   - Budget + timeline
   - Success criteria
```

## IR Playbook (top 5 incidentes)

1. **Ransomware** - isolate, identify entry point, restore from backup, hunt for persistence
2. **Phishing successful** - reset creds, MFA enforce, search inbox for similar
3. **Insider threat** - revoke access, preserve forensics, HR/legal
4. **DDoS** - scale up CDN, enable Radware aggressive mode, work with ISP
5. **Data breach** - contain, scope, notify legal (GDPR 72h, etc), forensics

## Stack recomendado para PYME (budget realista)

```
- Cloudflare Pro (WAF + DDoS)              ~$240/yr
- Microsoft Defender for Business           ~$3/user/mo
- 1Password Business (PAM lite)             ~$8/user/mo
- Okta or Google Workspace + MFA            incluido
- Wazuh open-source XDR/SIEM                free
- Atomic Red Team + Sigma rules             free
- Backup: Veeam/restic 3-2-1                ~$200/mo
- Annual pentest externo                    ~$5-15K
```

## Stack enterprise (full vendor)

```
- Palo Alto Cortex XSIAM + XDR + Prisma Cloud
- Fortinet Security Fabric (NGFW + EDR + Analyzer + SOAR)
- Radware Cloud WAF
- RidgeBot continuous pentest
- Pentera ASV
- Picus BAS
- + 24/7 SOC interno o MDR
```

Generado: 2026-05-13T08:56:39.063831
