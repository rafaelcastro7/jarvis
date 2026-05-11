---
name: project-audit
description: Auditoría rápida de cualquier proyecto — stack, deuda técnica, seguridad básica, estado del repo. Genera reporte accionable.
tools: Bash, Read, Glob, Grep
---

# Project Audit — Universal

Audita el proyecto activo y genera un reporte con los hallazgos más importantes.

## Steps

1. **Identificar stack**
   ```bash
   ls package.json requirements.txt go.mod Cargo.toml pom.xml 2>/dev/null
   cat package.json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('Node', d.get('version','?'), '| deps:', len(d.get('dependencies',{})))" 2>/dev/null || true
   ```

2. **Estado del repo**
   ```bash
   git log --oneline -5 && echo "---" && git status --short | head -10
   ```

3. **Seguridad básica**
   - Buscar secrets hardcodeados: `grep -rn "password\s*=\s*['\"]" src/ --include="*.ts" --include="*.js" -l 2>/dev/null | head -5`
   - Verificar .gitignore tiene .env: `grep -c "^\.env" .gitignore 2>/dev/null || echo "⚠ .gitignore sin .env"`
   - Buscar console.log en prod: `grep -rn "console\.log" src/ --include="*.ts" -l 2>/dev/null | wc -l`

4. **Deuda técnica**
   - TODOs: `grep -rn "TODO\|FIXME\|HACK\|XXX" src/ --include="*.ts" --include="*.tsx" | wc -l`
   - Archivos grandes: `find src/ -name "*.ts" -o -name "*.tsx" 2>/dev/null | xargs wc -l 2>/dev/null | sort -rn | head -5`

5. **Tests**
   - Cobertura: `[ -f vitest.config.* ] && npx vitest run --coverage 2>&1 | grep "Coverage" | head -3 || echo "Sin coverage configurado"`

6. **Reporte final**
   ```
   ## Audit: [nombre proyecto]
   - Stack: ...
   - Tests: X/Y passing
   - Seguridad: [OK / N issues]
   - Deuda técnica: N TODOs
   - Acción prioritaria: ...
   ```
