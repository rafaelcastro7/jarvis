# Google Cloud Cybersecurity — Notas Completas de los 5 Cursos

## CURSO 1 — Introduction to Security Principles in Cloud Computing (~18h)

### Módulos clave
- Cloud Security Fundamentals (IaaS/PaaS/SaaS, shared responsibility model)
- IAM en profundidad + **AAA Framework**: Authentication → Authorization → Auditing
- Resource Hierarchy GCP: Organization → Folders → Projects → Resources
- Zero Trust approach + Least Privilege

### Conceptos para dominar
- Shared Responsibility Model: Google gestiona infraestructura, cliente gestiona datos/acceso
- RBAC: roles predefinidos viewer/editor/owner/admin vs. custom roles
- MFA: capa extra obligatoria en accesos críticos
- Cloud Shell + gcloud CLI básico

---

## CURSO 2 — Strategies for Cloud Security Risk Management (~22h)

### Frameworks de compliance
| Framework | Para qué | Clave |
|---|---|---|
| NIST CSF | Risk management | 5 funciones: Identify/Protect/Detect/Respond/Recover |
| HIPAA | Datos de salud | PHI protection, Breach notification <60 días |
| SOC 2 | Servicios cloud | 5 criterios: Security/Availability/Integrity/Confidentiality/Privacy |
| ISO 27001 | ISMS completo | Risk assessment + tratamiento continuo |
| GDPR | Datos personales EU | Lawful basis, right to erasure, DPA notification <72h |
| FedRAMP | Gobierno USA | ATO (Authority to Operate) para cloud federal |
| PCI DSS | Tarjetas de crédito | Cardholder data protection |

### NIST CSF — Mapping a GCP
```
Identify  → Asset Inventory API, Cloud Asset Inventory
Protect   → IAM, VPC Service Controls, Cloud Armor, Secret Manager
Detect    → Event Threat Detection, Cloud Audit Logs, Cloud Logging
Respond   → SCC Findings, Incident Response playbooks
Recover   → Cloud Backup/DR, Deployment Manager IaC recovery
```

### Tipos de controles
- **Preventivos**: IAM, firewall rules, encryption
- **Detectivos**: Cloud Logging, SCC alerts, audit logs
- **Correctivos**: patches, incident response, recovery

---

## CURSO 3 — Cloud Security Risks: Identify and Protect (~28h)

### Amenazas cloud más comunes
1. Misconfiguration (bucket público, firewall abierto)
2. Insecure APIs (sin auth, rate limiting)
3. Account compromise (credential theft, phishing)
4. Insider threats
5. Supply chain attacks
6. Ransomware / data exfiltration
7. DDoS

### STRIDE — Threat Modeling
| Letra | Amenaza | Ejemplo |
|---|---|---|
| S | Spoofing | Impersonar service account |
| T | Tampering | Modificar logs |
| R | Repudiation | Negar acción realizada |
| I | Information Disclosure | Data leak en bucket público |
| D | Denial of Service | DDoS a API |
| E | Elevation of Privilege | Privilege escalation |

### IAM Avanzado en GCP
```bash
# Service account con permisos mínimos
gcloud iam service-accounts create app-sa
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:app-sa@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/storage.objectViewer

# JIT access — acceso temporal
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=user:admin@domain.com \
  --role=roles/editor \
  --condition="expression=request.time < timestamp('2024-12-31T00:00:00Z'),title=Temporary"
```

### Credential Management
- Rotar API keys y service account keys regularmente
- Usar Secret Manager, NUNCA hardcodear en código
- Certificate lifecycle: crear → deploy → renovar → revocar
- CMEK (Customer Managed Encryption Keys) via Cloud KMS

### CVSS — Scoring de vulnerabilidades
- 0.0–3.9: Low | 4.0–6.9: Medium | 7.0–8.9: High | 9.0–10.0: Critical
- Factores: Attack Vector, Attack Complexity, Privileges Required, User Interaction, Impact

---

## CURSO 4 — Detect, Respond, and Recover (~26h)

### Cloud Logging — Tipos de logs
| Tipo | Qué captura |
|---|---|
| Admin Activity | Cambios de config (IAM, recursos) — siempre activo |
| Data Access | Quién leyó/escribió datos — requiere habilitar |
| System Events | Acciones automáticas de GCP |
| VPC Flow Logs | Tráfico de red entre VMs |

```bash
# Query logs para security investigation
gcloud logging read 'resource.type="gce_instance" severity>=WARNING' \
  --project=PROJECT_ID --limit=100

# Sink para exportar a BigQuery para análisis
gcloud logging sinks create security-sink \
  bigquery.googleapis.com/projects/PROJECT_ID/datasets/security_logs \
  --log-filter='severity>=WARNING'
```

### IOCs — Indicators of Compromise
- IP sospechosas, dominios, URLs maliciosas
- File hashes (MD5, SHA-256) de malware
- Patrones de comportamiento: login fallido masivo, acceso a horas inusuales
- Data exfiltration: transferencias grandes e inusuales

### Incident Response Lifecycle
```
1. Preparación    → playbooks, tools, equipo, contactos
2. Identificación → SCC alert, log anomaly, user report, IOC match
3. Contención     → aislar recurso, revocar creds comprometidas, bloquear IP
4. Erradicación   → eliminar malware, parchear vuln, remediar misconfiguration
5. Recuperación   → restaurar backup, verificar integridad, monitorear
6. Lessons        → RCA, timeline, mejoras a controles, actualizar playbooks
```

### RTO vs RPO
- **RTO** (Recovery Time Objective): tiempo máximo tolerable de downtime
- **RPO** (Recovery Point Objective): pérdida máxima tolerable de datos
- Estrategia: RTO bajo → alta disponibilidad; RPO bajo → backups frecuentes

### Crisis Communications
- Interno primero: ejecutivos → equipo técnico → empleados
- Externo: clientes afectados → reguladores → público (si aplica)
- Breach notification: GDPR = 72h, HIPAA = 60 días, varies by jurisdiction
- Nunca especular públicamente, siempre verificar antes de comunicar

---

## CURSO 5 — Capstone: Cloud Security Analyst Job Prep (~11h)

### Capstone Project
1. Scenario-based incident investigation completo
2. Risk Assessment Report del entorno
3. Remediation recommendations con priorización
4. Portfolio artifacts para empleadores

### Interview — Preguntas técnicas clave
- "Explica el AAA framework" → Authentication/Authorization/Auditing
- "¿Cómo implementas least privilege?" → Custom roles, JIT access, IAM Recommender
- "Walk me through incident response" → 6 fases NIST
- "Explica NIST CSF" → 5 funciones Identify/Protect/Detect/Respond/Recover
- "¿Qué es shared responsibility model?" → Google infra, cliente datos/acceso
- "¿Cómo detectas una cuenta comprometida?" → Failed logins, geo anomalies, unusual API calls

### Certificaciones de siguiente nivel
- **Google Cloud Professional Cloud Security Engineer** (siguiente paso)
- **CISSP** (avanzado, requiere experiencia)
- **CCSK** (Cloud Security Knowledge)
- **CompTIA Security+** (general, buen fundamento)

---

## RECURSOS DE ESTUDIO DESCUBIERTOS

- GitHub study materials: github.com/matpakke/Google-Cybersecurity
- Quiz answers: certificationanswers.com/google-cybersecurity-professional-certificate-answers
- Flashcards: quizlet.com (buscar "Google Cloud Cybersecurity Certificate")
- YouTube walkthroughs: playlist con soluciones de weekly challenges
- Credly badge: credly.com/org/google-cloud/badge/google-cloud-cybersecurity-certificate

## ESTADO DE COMPLETUD

| Curso | Contenido aprendido | Labs interactivos |
|---|---|---|
| Curso 1 | ✅ Completo | ⏳ Pendiente (requiere browser) |
| Curso 2 | ✅ Completo | ⏳ Pendiente |
| Curso 3 | ✅ Completo | ⏳ Pendiente |
| Curso 4 | ✅ Completo | ⏳ Pendiente |
| Curso 5 | ✅ Completo | ⏳ Pendiente |

Para completar labs: conectar extensión OpenClaw en Chrome o navegar manualmente a skills.google con rafaelcastro7@gmail.com
