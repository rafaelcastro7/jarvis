---
name: cybersec-palo-alto-cortex
description: Palo Alto Networks Cortex stack — XDR + XSIAM + Prisma Cloud + Cortex Cloud. Arquitectura 3 capas (Sensor + Storage Cortex Data Lake en GCP + Application). Consolida SIEM+SOAR+XDR+UEBA+ASM. Visibilidad cloud nativa (AWS/Azure/GCP APIs).
---

# Palo Alto Cortex Stack

## Arquitectura 3 capas

```
[Sensor Layer]
  - Cortex XDR Agent (endpoint)
  - NGFW Palo Alto
  - Prisma Access (SASE)
  - Cloud APIs (AWS/Azure/GCP)
       v
[Storage Layer]
  - Cortex Data Lake (GCP-hosted)
  - Audit logs + config + telemetry
       v
[Application Layer]
  - Cortex XDR (detection+response)
  - XSIAM (SecOps platform)
  - Prisma Cloud (CNAPP)
```

## XSIAM = unificacion

XSIAM consolida en una sola plataforma:
- **SIEM** (logs + correlation)
- **SOAR** (automation playbooks)
- **XDR** (endpoint+network+cloud)
- **UEBA** (user behavior analytics)
- **ASM** (attack surface management)

Resultado: menos licensing, menos pivotes entre tools, MTTR mucho menor.

## Cortex Cloud (anuncio 2025)

Native integration de cloud data con XSIAM. Workflow unificado para cloud + endpoint + network.

## Prisma Cloud (CNAPP)

- **CSPM** - cloud security posture (mis-config)
- **CWPP** - workload protection (containers, VMs)
- **CIEM** - cloud identity entitlements
- **DSPM** - data security posture (donde estan los secrets)
- **CDR** - cloud detection & response

## Deploy en mi empresa

1. **Foundation**: NGFW + Cortex XDR agents en endpoints
2. **Visibility**: enviar todos los logs a Cortex Data Lake
3. **SecOps**: XSIAM con playbooks SOAR top-10 incidentes
4. **Cloud**: Prisma Cloud conectado a AWS/Azure org

## Stack alternativo (open)

- **Wazuh** (XDR open)
- **TheHive + Cortex (StrangeBee)** (no PaloAlto Cortex) SOAR
- **Zeek + Suricata** network monitoring
- **OpenCTI** threat intel

Source: paloaltonetworks.com docs-cortex
