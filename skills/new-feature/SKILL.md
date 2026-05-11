---
name: new-feature
description: Implementa una nueva feature con flujo estructurado — exploración del código existente, plan, implementación, tests, commit. Para cualquier proyecto.
tools: Bash, Read, Grep, Glob, Edit, Write
---

# New Feature — Universal

Proceso de 7 fases para implementar cualquier feature correctamente, reutilizando código existente.

## Steps

1. **Explorar código existente** (no reinventar)
   - Buscar patrones similares: `grep -r "feature_keyword" src/ --include="*.ts" -l`
   - Ver estructura de componentes similares
   - Identificar helpers, hooks, tipos reutilizables

2. **Identificar dependencias**
   - ¿Qué tablas/endpoints necesita?
   - ¿Qué componentes UI ya existen en el proyecto?
   - ¿Hay una edge function similar que extender?

3. **Plan mínimo** (sin over-engineering)
   - Listar exactamente qué archivos crear/modificar
   - Estimar líneas de código
   - Confirmar con usuario antes de proceder

4. **Implementar**
   - Backend primero (si aplica): migración SQL → edge function → hook
   - Frontend: página → componentes → i18n → rutas
   - Reutilizar patrones del proyecto (imports, error handling, loading states)

5. **Tests**
   - Añadir test si hay suite existente
   - Correr `/quality-check` al terminar

6. **Integración**
   - Añadir a nav/router si es página nueva
   - Verificar que no rompió rutas existentes

7. **Commit** con `/git-workflow`
