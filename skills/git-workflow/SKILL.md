---
name: git-workflow
description: Workflow git completo — status, diff, commit semántico, push. Corre quality-check primero. Evita commits con errores TS o tests rotos.
tools: Bash
---

# Git Workflow — Universal

Commit seguro con mensaje semántico. Siempre verifica calidad antes.

## Steps

1. **Pre-check calidad** — invocar `/quality-check`. Si hay errores TS o tests rotos, PARAR.

2. **Estado actual**
   ```bash
   git status --short && echo "---" && git diff --stat HEAD 2>/dev/null | tail -5
   ```

3. **Rama actual**
   ```bash
   git branch --show-current && git log --oneline -3
   ```

4. **Staging y commit**
   - Listar archivos modificados y preguntar qué incluir
   - Usar prefijo semántico: `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, `test:`
   - Formato: `tipo(scope): descripción corta en presente`
   - Ejemplos:
     - `feat(odoo-mind): add HITL confirmation for write operations`
     - `fix(auth): handle expired session tokens`
     - `chore: update dependencies`

5. **Push**
   - Verificar si hay upstream: `git remote -v`
   - Si hay cambios remotos: `git pull --rebase` antes de push
   - Push: `git push origin $(git branch --show-current)`

6. **Confirmar**
   - Mostrar hash del commit y URL del repo si aplica
