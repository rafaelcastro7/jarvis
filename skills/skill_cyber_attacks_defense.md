# Skill: Fundamentos de Ataques Cibernéticos y Defensa (Blue Teaming)

## Objetivo
Comprender la anatomía de los ataques cibernéticos más comunes desde una perspectiva de defensa. Este conocimiento permite a Jarvis y al usuario auditar código y arquitecturas propias para identificar y mitigar vulnerabilidades antes de que puedan ser explotadas.

## Anatomía de Ataques Comunes (Basado en OWASP Top 10)

### 1. Inyección (ej. SQL Injection, Command Injection)
*   **Mecanismo:** Un atacante envía datos no confiables a un intérprete (como una base de datos o una shell de sistema) como parte de un comando o consulta. El intérprete ejecuta los datos maliciosos como si fueran instrucciones legítimas.
*   **Impacto:** Robo de datos, modificación de bases de datos, ejecución de comandos remotos en el servidor.
*   **Defensa (Mitigación):** Utilizar siempre consultas parametrizadas (Prepared Statements) o frameworks ORM que abstraigan las consultas. Validar y sanear (sanitize) estrictamente todo input del usuario. Nunca concatenar cadenas de texto para formar consultas.

### 2. Cross-Site Scripting (XSS)
*   **Mecanismo:** El atacante logra inyectar scripts maliciosos (generalmente JavaScript) en las páginas web vistas por otros usuarios. Esto ocurre cuando una aplicación incluye datos no confiables en una página web sin la validación o el escape adecuados.
*   **Impacto:** Secuestro de sesiones (robo de cookies), redirecciones maliciosas, defacement de sitios web.
*   **Defensa (Mitigación):** Escapar (encode) correctamente todos los datos dinámicos antes de renderizarlos en el HTML. Utilizar cabeceras de seguridad como Content Security Policy (CSP). Usar frameworks modernos (como React o Angular) que escapan el texto por defecto.

### 3. Falsificación de Peticiones en Sitios Cruzados (CSRF)
*   **Mecanismo:** Obliga al navegador de un usuario final a ejecutar acciones no deseadas en una aplicación web en la que actualmente está autenticado. Aprovecha que las cookies de sesión se envían automáticamente con cada petición al dominio.
*   **Impacto:** Transferencias de fondos no autorizadas, cambios de contraseña o correo electrónico sin el consentimiento del usuario.
*   **Defensa (Mitigación):** Implementar tokens anti-CSRF únicos e impredecibles para cada petición que altere el estado. Configurar las cookies de sesión con el atributo `SameSite=Lax` o `Strict`.

### 4. Broken Access Control (Control de Acceso Roto)
*   **Mecanismo:** Los usuarios pueden actuar fuera de sus permisos previstos. Por ejemplo, acceder a la cuenta de otro usuario modificando un parámetro en la URL (IDOR - Insecure Direct Object Reference) o acceder a rutas de administrador sin serlo.
*   **Impacto:** Acceso no autorizado a datos sensibles de otros usuarios o toma de control del sistema.
*   **Defensa (Mitigación):** Implementar controles de acceso a nivel de servidor (no solo ocultar botones en el frontend). Verificar que el usuario autenticado tiene permisos para acceder al recurso específico (verificación de propiedad).

## Metodología de Defensa
*   **Principio de Menor Privilegio:** Los servicios, contenedores y usuarios deben tener solo los permisos mínimos necesarios para funcionar.
*   **Defensa en Profundidad:** Aplicar múltiples capas de seguridad (ej. WAF, validación de input, red interna aislada, base de datos encriptada) para que si falla una capa, el sistema siga protegido.
*   **Auditorías Regulares:** Utilizar herramientas estáticas (SAST) y dinámicas (DAST) para escanear el código y la infraestructura en busca de vulnerabilidades conocidas durante el ciclo de CI/CD.
