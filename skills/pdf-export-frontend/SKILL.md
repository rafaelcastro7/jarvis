---
name: pdf-export-frontend
description: Exportar componentes React a PDF con html2canvas + jsPDF. Lazy loading de dependencias pesadas, alta resolución (scale:2), manejo de CORS y estado de carga. Patrón probado en GobIA Auditor (AuditPlatform.tsx).
tools: Read, Edit
---

# PDF Export Frontend — html2canvas + jsPDF

## Dependencias

```bash
npm install html2canvas jspdf
```

En `vite.config.ts`, aislarlas en chunks propios para no bloquear el bundle principal:
```typescript
manualChunks(id) {
  if (id.includes("html2canvas")) return "html2canvas-vendor";
  if (id.includes("jspdf"))       return "jspdf-vendor";
}
```

---

## Implementación completa (patrón de AuditPlatform.tsx)

```typescript
async function exportToPDF(elementRef: React.RefObject<HTMLElement>, filename: string) {
  if (!elementRef.current) return;

  setExporting(true);
  setExportMessage("Generando PDF...");

  try {
    // Lazy load — no bloquea bundle inicial
    const [{ default: html2canvas }, { jsPDF }] = await Promise.all([
      import("html2canvas"),
      import("jspdf"),
    ]);

    const canvas = await html2canvas(elementRef.current, {
      scale: 2,              // Alta resolución (2x para pantallas retina)
      useCORS: true,         // Permite imágenes cross-origin
      logging: false,        // Sin logs en consola
      backgroundColor: "#ffffff",
    });

    const pdf = new jsPDF({
      orientation: "portrait",
      unit: "px",
      format: [canvas.width, canvas.height],  // Adapta al contenido
    });

    pdf.addImage(
      canvas.toDataURL("image/png"),
      "PNG",
      0, 0,
      canvas.width,
      canvas.height
    );

    pdf.save(`${filename}-${new Date().toISOString().split("T")[0]}.pdf`);
    setExportMessage("PDF exportado correctamente");
  } catch (error) {
    console.error("[PDF Export]", error);
    setExportMessage("Error al exportar. Intenta de nuevo.");
  } finally {
    setExporting(false);
  }
}
```

---

## Botón de exportación en el componente

```tsx
const reportRef = useRef<HTMLDivElement>(null);
const [exporting, setExporting] = useState(false);
const [exportMessage, setExportMessage] = useState("");

// En el JSX:
<div ref={reportRef}>
  {/* Contenido a exportar */}
</div>

<button
  onClick={() => exportToPDF(reportRef, "reporte-auditoria")}
  disabled={exporting}
  className="px-4 py-2 rounded bg-blue-600 text-white disabled:opacity-50"
>
  {exporting ? "Generando..." : "Exportar PDF"}
</button>

{exportMessage && (
  <span className="text-sm text-green-600">{exportMessage}</span>
)}
```

---

## Problemas comunes

| Problema | Causa | Fix |
|----------|-------|-----|
| Imagen en blanco | CORS en recursos externos | `useCORS: true` |
| PDF de baja calidad | Scale por defecto = 1 | `scale: 2` o `scale: 3` |
| Página cortada | format fijo A4 | `format: [canvas.width, canvas.height]` |
| Bundle grande | Import estático | Siempre usar `import()` dinámico |
| Fondo negro | No especificado | `backgroundColor: '#ffffff'` |
| Timeout en elementos con iframes | html2canvas no soporta iframes | Ocultar iframes antes de capturar |

---

## Alternativa: exportar a imagen PNG

```typescript
const canvas = await html2canvas(elementRef.current, { scale: 2, useCORS: true });
const link = document.createElement("a");
link.download = `${filename}.png`;
link.href = canvas.toDataURL("image/png");
link.click();
```

---

## Multipage PDF (para contenido largo)

```typescript
const pdf = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
const pageHeight = pdf.internal.pageSize.getHeight();
const imgWidth = pdf.internal.pageSize.getWidth();
const imgHeight = (canvas.height * imgWidth) / canvas.width;

let yOffset = 0;
while (yOffset < imgHeight) {
  if (yOffset > 0) pdf.addPage();
  pdf.addImage(canvas.toDataURL("image/png"), "PNG", 0, -yOffset, imgWidth, imgHeight);
  yOffset += pageHeight;
}
pdf.save(`${filename}.pdf`);
```
