---
name: simplify
description: Tras un cambio grande, revisar el diff: redundancias, nombres, duplicación, ramas muertas; alinear con convenciones del repo y con /quality-check.
---

# Simplify

1. Leer el diff completo (o los archivos tocados).
2. Buscar código duplicado, helpers que solo se usan una vez, tipos `any` innecesarios, imports no usados.
3. Preferir una sola vía clara frente a ramas especiales que no aportan.
4. Correr `/quality-check` antes de considerar la simplificación cerrada.
