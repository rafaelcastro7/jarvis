---
name: quality-check
description: Verifica calidad del proyecto activo — TypeScript, linting, tests. Auto-detecta el stack (Node/Python/Go). Úsalo antes de cualquier commit o deploy.
tools: Bash
---

# Quality Check — Universal

Detecta el stack y corre los checks apropiados. Reporta errores con archivo:línea.

## Steps

1. **Detectar stack**
   ```bash
   [ -f package.json ] && echo "NODE" || ([ -f requirements.txt ] && echo "PYTHON" || ([ -f go.mod ] && echo "GO" || echo "UNKNOWN"))
   ```

2. **TypeScript** (si NODE)
   ```bash
   npx tsc --noEmit --skipLibCheck 2>&1 | head -20
   ```
   - 0 output → "✓ TypeScript: 0 errores"
   - Hay output → listar cada `error TS` con archivo:línea

3. **ESLint** (si hay `.eslintrc` o `eslint.config.*`)
   ```bash
   [ -f eslint.config.js ] || [ -f .eslintrc.json ] || [ -f .eslintrc.js ] && npx eslint src/ --max-warnings 0 2>&1 | tail -10 || echo "No ESLint config"
   ```

4. **Tests**
   - Vitest: `npx vitest run 2>&1 | tail -10`
   - Jest: `npx jest --passWithNoTests 2>&1 | tail -10`
   - Python: `python -m pytest --tb=short 2>&1 | tail -10`
   - Auto-detectar cual usar: `[ -f vitest.config.* ] && RUNNER=vitest || RUNNER=jest`

5. **Resultado**
   - Todo OK → "✓ Listo para commit/deploy"
   - Errores → listar con archivos y proponer fix concreto
