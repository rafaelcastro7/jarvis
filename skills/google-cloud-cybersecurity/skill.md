---
name: google-cloud-cybersecurity
description: Google Cloud Cybersecurity Certificate (skills.google path 419). 5 cursos, ~95 horas. Cloud Security Analyst entry-level: IAM, RBAC, NIST CSF, HIPAA, threat detection, incident response, disaster recovery, Generative AI en ciberseguridad.
tools: WebSearch, WebFetch, Bash, Read, Write
---

# Google Cloud Cybersecurity Certificate — Conocimiento Completo

**Fuente:** https://www.skills.google/paths/419  
**Cuenta:** rafaelcastro7@gmail.com  
**Duración:** ~95 horas (~3 meses a 10h/semana)  
**Nivel:** Introductorio / Beginner  
**Outcome:** Certificado + Skill Badges + acceso Google Cloud Affiliate Employer

---

## Los 5 Cursos

### Curso 1 — Introduction to Security Principles in Cloud Computing (~17h)
URL: https://www.skills.google/paths/419/course_templates/1300

**Temas clave:**
- Definición de ciberseguridad en cloud computing
- Roles y responsabilidades del analista entry-level
- Ciclo de vida de seguridad y transformación digital
- Herramientas de automatización para analistas

**Skills:** Cloud Security, Cybersecurity, Infrastructure as Code (IaC), DevSecOps, Cloud Infrastructure, Network Security, Google Cloud Platform, RBAC, IAM, Security Controls, IT Automation

---

### Curso 2 — Strategies for Cloud Security Risk Management (~19h)
URL: https://www.skills.google/paths/419/course_templates/1301

**Temas clave:**
- Frameworks de gestión de riesgo en cloud
- Security governance y compliance lifecycle
- Estándares: **HIPAA, NIST CSF, SOC, ISO/IEC 27001**
- Identificación de riesgos y despliegue de controles
- Evaluación de compliance y protección de datos

**Skills:** Risk Management Framework, Threat Detection, Data Security, Cyber Risk, HIPAA, NIST Cybersecurity Framework, SOC compliance, multi-cloud security, ISO 27001

---

### Curso 3 — Cloud Security Risks: Identify and Protect Against Threats (~28h)
URL: https://www.skills.google/paths/419/course_templates/1302

**Temas clave:**
- IAM (Identity and Access Management) en cloud
- **Framework AAA:** Authentication, Authorization, Auditing
- Credential management y certificate management
- Threat/vulnerability management
- Principios cloud-native y containerización
- Data protection strategies

**Skills:** Authorization, IAM, Vulnerability Assessments, Cloud-Native, Data Governance, Threat Management, Authentication, Key Management, Containerization, Multi-Factor Authentication, Certificate Management

---

### Curso 4 — Detect, Respond, and Recover from Cloud Cybersecurity Attacks (~24h)
URL: https://www.skills.google/paths/419/course_templates/1303

**Temas clave:**
- Sistemas de logging y análisis en cloud
- Security monitoring y alert management
- **Threat feeds** customizados
- Gestión de incidentes (lifecycle completo)
- Crisis communications y Root Cause Analysis
- **Disaster Recovery Planning** y retención de datos

**Skills:** Intrusion Detection/Prevention, Disaster Recovery, Incident Management, Incident Response, Continuous Monitoring, Cyber Threat Hunting, Event Monitoring, Root Cause Analysis, Business Continuity, Crisis Communications

---

### Curso 5 — Put It All Together: Prepare for a Cloud Security Analyst Job (~12h)
URL: https://www.skills.google/paths/419/course_templates/1305

**Temas clave:**
- Capstone: integra todos los conceptos anteriores
- IAM, permisos, roles y responsabilidades
- Plan completo de protección organizacional
- **Generative AI en Cloud Cybersecurity** (módulo opcional)
- Career development: CV, entrevistas, job readiness

**Skills:** Cloud Security, Generative AI, LLMs en ciberseguridad, Incident Response, Risk Management, Vulnerability Assessment

---

## Herramientas Google Cloud usadas en labs

- **Google Cloud Console** — laboratorios interactivos en todos los cursos
- **Security Command Center (SCC)** — monitoreo centralizado de amenazas
- **Cloud Firewall and Logging** — reglas y auditoría
- **Cloud Shell** — comandos CLI en cloud
- **Cloud Storage** — gestión y protección de datos
- **Gemini Enterprise / Vertex AI** — IA generativa aplicada a seguridad

---

## Conceptos clave para aplicar en proyectos

### IAM y Control de Acceso
```
IAM = quién puede hacer qué sobre cuáles recursos
RBAC = roles predefinidos (viewer, editor, admin, custom)
AAA = Authentication (¿quién sos?) + Authorization (¿qué podés?) + Auditing (¿qué hiciste?)
MFA = capa adicional obligatoria para accesos críticos
Principio de menor privilegio = dar solo los permisos mínimos necesarios
```

### Frameworks de Riesgo
```
NIST CSF = Identify → Protect → Detect → Respond → Recover
ISO/IEC 27001 = Sistema de gestión de seguridad de información (ISMS)
SOC 2 = Controls para seguridad, disponibilidad, confidencialidad
HIPAA = Protección de datos de salud (Health Insurance Portability)
```

### Incident Response Lifecycle
```
1. Preparación → 2. Identificación → 3. Contención
4. Erradicación → 5. Recuperación → 6. Lecciones aprendidas
```

### DevSecOps
```
Security left-shifted = integrar seguridad desde el diseño
IaC = Infrastructure as Code → reproducible, auditable, versionado
Containers = aislamiento + surface de ataque reducida
CI/CD security gates = escaneo automático antes de deploy
```

### Generative AI en Ciberseguridad
```
Usos: análisis de logs, threat hunting automatizado, redacción de playbooks,
      generación de reportes de incidentes, threat intelligence summarization
Herramientas: Gemini en GCP, Vertex AI Security Agent
```

---

## Aplicación práctica en proyectos de Rafael

| Concepto aprendido | Aplicación en proyectos |
|---|---|
| IAM/RBAC | Supabase RLS policies, Odoo access groups, Express middleware auth |
| Security Command Center | Monitoring para GobIA Auditor y AgencIA |
| NIST CSF | Framework para auditar seguridad de cualquier proyecto |
| Incident Response | Playbook para cuando fallen servicios en producción |
| IaC Security | Validar Dockerfiles y Compose files con tools |
| Threat Detection | Logging estructurado en Express con alertas |
| Generative AI + Security | Usar Ollama/Gemini para análisis de logs automático |

---

---

## Referencia técnica práctica — Google Cloud

### Security Command Center (SCC)

```bash
# Activar SCC
gcloud scc organizations enable --organization=ORG_ID

# Listar findings críticos
gcloud scc findings list --organization=ORG_ID --filter="severity=CRITICAL"

# Ver amenazas detectadas
gcloud scc findings list --organization=ORG_ID \
  --filter='category=ANOMALOUS_BEHAVIOR or severity=CRITICAL'

# Export continuo a Cloud Logging
gcloud logging sinks create scc-sink \
  logging.googleapis.com/organizations/ORG_ID/logs/scc-threats \
  --log-filter='resource.type=organization severity>=HIGH'
```

**Detectores de Event Threat Detection:**
- Brute force SSH, IAM grants inusuales, buckets expuestos públicamente
- Exfiltración de datos, minería de criptomonedas
- Latencia de detección: < 15 minutos desde el log hasta el finding

**SCC Tiers (2025):**
- Standard: core detection gratuita
- Premium: advanced threats + compliance dashboards
- Enterprise: multi-cloud + SOAR integrations (Cortex XSOAR, Splunk, Snyk)

**Integraciones nativas:** Cloud Armor, DLP, Web Security Scanner, Container Threat Detection, VM Threat Detection

---

### IAM — Mejores prácticas 2025

```bash
# MAL: usar service account default
gcloud compute instances create instance-1 --service-account=default

# BIEN: service account dedicada con rol mínimo
gcloud iam service-accounts create app-sa --display-name="App SA"
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:app-sa@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/storage.objectViewer  # Solo lo que necesita

# Auditar permisos no usados
gcloud recommender recommendations list \
  --project=PROJECT_ID \
  --recommender=google.iam.policy.Recommender
```

**Reglas críticas IAM:**
- Nunca usar `--service-account=default` en producción
- Google Groups para gestión de acceso, no usuarios individuales
- Deshabilitar access scopes en VMs, usar IAM roles
- Domain-wide delegation solo si es absolutamente necesario
- IAM Recommender auto-habilitado desde Oct 2024

**Controles avanzados IAM (2025):**
- **Deny policies**: bloquean acceso aunque exista role grant — prioridad sobre allow
- **Principal Access Boundary**: limita qué recursos puede acceder un principal
- **IAM Conditions**: acceso basado en atributos (tiempo, IP, resource tags)
- **Privileged Access Manager (PAM)**: acceso temporal auditable (reemplaza JIT manual)
- Herencia de políticas: Organization → Folders → Projects → Resources

**Formato de permisos:** `service.resource.verb` — ej: `resourcemanager.projects.list`

---

### NIST CSF → Google Cloud Mapping

| NIST Función | Objetivo | Servicios GCP |
|---|---|---|
| **Identify** | Conocer assets y vulnerabilidades | Asset Inventory API, SCC Scanner |
| **Protect** | Prevenir acceso no autorizado | IAM, VPC Service Controls, Cloud Armor, Secret Manager |
| **Detect** | Identificar amenazas en tiempo real | Event Threat Detection, Cloud Audit Logs |
| **Respond** | Contener y remediar incidentes | SCC Findings, Incident Response API |
| **Recover** | Restaurar operaciones normales | Backup/DR, Deployment Manager, IaC recovery |

---

### DevSecOps — IaC Security con Terraform

```hcl
# Storage bucket seguro
resource "google_storage_bucket" "logs" {
  name = "secure-logs-${var.project_id}"
  versioning { enabled = true }
  encryption { default_kms_key_name = google_kms_crypto_key.key.id }
  uniform_bucket_level_access = true  # Bloquear acceso público
}

# Nunca hardcodear secrets — usar Secret Manager
resource "google_secret_manager_secret" "db_password" {
  secret_id = "db-password"
  replication { automatic = true }
}
```

**CI/CD Security scanning:**
```yaml
devsecops-scan:
  stage: scan
  script:
    - trivy config --exit-code 1 terraform/        # IaC misconfigs
    - checkov -d terraform/ --check CKV_GCP_*      # GCP-specific checks
    - trivy fs --severity HIGH,CRITICAL .           # Secrets + vulns
```

**Checklist DevSecOps:**
- Escanear IaC pre-commit (detect misconfigs antes del merge)
- Terraform state en GCS con encryption + versioning
- Cloud Audit Logs habilitados para todas las creaciones de recursos
- TLS en tránsito, KMS en reposo

---

### Cloud Audit Logging — Referencia 2025

**Tipos de logs y storage:**
| Tipo | Contenido | Bucket | Deshabilitable |
|---|---|---|---|
| Admin Activity | Config changes (IAM, recursos) | `_Required` | ❌ No |
| System Event | Cambios automáticos de GCP | `_Required` | ❌ No |
| Data Access | Lectura/escritura de datos | `_Default` | ✅ Sí |
| Policy Denied | Accesos denegados por security | `_Default` | ✅ Sí |

> Data Access logs deshabilitados por defecto (excepto BigQuery) — requieren habilitación explícita y generan costo.

```bash
# Leer audit logs por proyecto
gcloud logging read "logName : projects/PROJECT_ID/logs/cloudaudit.googleapis.com" \
  --project=PROJECT_ID

# Leer a nivel organización
gcloud logging read "logName : organizations/ORG_ID/logs/cloudaudit.googleapis.com" \
  --organization=ORG_ID
```

**Roles de acceso a logs:**
- `roles/logging.viewer`: Admin Activity + Policy Denied + System Event
- `roles/logging.privateLogViewer`: todos los logs incluyendo Data Access

---

### Incident Response Lifecycle

```
1. Preparación  → playbooks, tools, equipo definido
2. Identificación → SCC alert, log anomaly, user report
3. Contención   → aislar recurso, revocar credenciales comprometidas
4. Erradicación → eliminar malware/acceso, parchear vulnerabilidad
5. Recuperación → restaurar desde backup, verificar integridad
6. Lecciones    → RCA, documentar, mejorar controles
```

---

### Generative AI en Ciberseguridad (Curso 5)

**Usos validados de IA en security:**
- Análisis automático de logs masivos (reducir alert fatigue)
- Threat hunting: patrones anómalos en grandes datasets
- Redacción de playbooks y reportes de incidentes
- Threat intelligence summarization
- Security posture Q&A con Gemini en GCP

```python
# Ejemplo: análisis de logs con Gemini
import vertexai
from vertexai.generative_models import GenerativeModel

vertexai.init(project="my-project", location="us-central1")
model = GenerativeModel("gemini-1.5-pro")

log_sample = """
2024-01-15 03:42:11 WARN: 847 failed login attempts from 192.168.1.105
2024-01-15 03:42:15 ERROR: Privilege escalation attempt detected
2024-01-15 03:42:18 CRITICAL: Unusual outbound data transfer 2.3GB
"""

response = model.generate_content(f"""
Analiza este log de seguridad. Identifica:
1. Tipo de ataque probable
2. Severidad (Critical/High/Medium/Low)
3. Acciones de contención inmediatas
4. Evidencia para preservar

Log: {log_sample}
""")
print(response.text)
```

---

## Acceso al curso
- URL: https://www.skills.google/paths/419
- Login: rafaelcastro7@gmail.com (cuenta Google personal)
- Para labs interactivos: abrir en Chrome directamente
- OpenClaw: requiere extensión conectada en el browser activo
