---
name: English Course Clone Project
description: RAIO English Course clonado desde ClickFunnels. 246 lecciones, 222 videos MP4, 315 MP3, 101 ZIPs. React+Vite+Tailwind v4 con dark theme responsive. Servido en puerto 4200 con tunnel Cloudflare.
type: project
originSessionId: 9d9b6e30-a0be-45b2-b145-f114a4016443
---
# RAIO English Course Clone — Estado COMPLETO

**Estado:** TERMINADO — todos los assets descargados, app funcionando con UX rediseñado.

**Why:** Clonar plataforma privada de curso de inglés para uso local autónomo.

## Credenciales sitio original
- URL: https://kaleanders.clickfunnels.com/members-raio
- Login: leon65.4@hotmail.com / Cristian2086*
- Plataforma: ClickFunnels membership area

## Para levantar el proyecto
```bash
# Servidor local ya corre en puerto 4200 como proceso node
# Si se reinicia:
cd "E:/Documents/PROYECTOS/AgencIA/englishCourse/clone"
npx serve -s dist -l 4200

# Tunnel Cloudflare (relanzar si cae)
cloudflared tunnel --url http://localhost:4200 --no-autoupdate &>/tmp/tunnel.log &
grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/tunnel.log | head -1

# Rebuild (si se modifican sources)
python scripts/rebuild_after_downloads.py  # limpia .part y hace npm run build
```

## Assets descargados (estado final)
| Asset | Cantidad | Tamaño | Ruta |
|-------|----------|--------|------|
| Videos MP4 (Vidalytics HLS) | 222 | ~3.4GB | clone/public/videos/ |
| Audios MP3 (AWS S3) | 315 | 1.6GB | clone/public/audio/ |
| Recursos ZIP (AWS S3) | 101 | 1.2GB | clone/public/resources/ |

## Estructura del curso
- 15 módulos, 246 lecciones total
- 220 con video (type: video), 25 con audio (type: audio), 1 texto puro
- Datos en clone/src/courseData.json (con campo video_file precalculado)

## Plataforma de video — VIDALYTICS (no Vimeo)
Los IDs en el HTML parecen Vimeo pero son de Vidalytics:
- Account: `w0IlLu31` (constante)
- URL: `fast.vidalytics.com/video/w0IlLu31/{HASH}/{ID}/__FFMPEG/stream.m3u8`
- Técnica: Playwright en ClickFunnels (dominio permitido) intercepta stream.m3u8
- 220 URLs capturadas → downloads/m3u8_map.json
- Descarga con yt-dlp desde m3u8 → MP4

## Archivos clave
| Archivo | Descripción |
|---------|-------------|
| `scripts/scrape_final.py` | Scraper principal Playwright (246 lecciones) |
| `scripts/download_assets.py` | Descarga MP3 desde S3 (ThreadPoolExecutor x8) |
| `scripts/download_vidalytics.py` | Fase1: intercepta m3u8, Fase2: yt-dlp descarga |
| `scripts/rebuild_after_downloads.py` | Limpia .part + npm run build |
| `downloads/lessons_content.json` | Raw data 246 lecciones |
| `downloads/m3u8_map.json` | 220 lesson_id → m3u8 URL |
| `downloads/downloaded_videos.json` | Log de videos completados |
| `clone/src/courseData.json` | courseData con video_file fields exactos |

## Técnica de scraping ClickFunnels (probada y funcional)
```python
# Login
await page.evaluate(f"""() => {{
    for (const f of document.querySelectorAll('form')) {{
        if (f.action && f.action.includes('sign_in')) {{
            f.querySelector('input[name="member[email]"]').value = '{EMAIL}';
            f.querySelector('input[name="member[password]"]').value = '{PASSWORD}';
            f.submit(); break;
        }}
    }}
}}""")
async with page.expect_navigation(url="**/members**", timeout=20000):
    pass

# Click lección (bypassa visibilidad)
await page.evaluate(f"""() => {{
    const link = document.querySelector("a.lesson-link[data-lesson-id='{lid}']");
    if (link) link.dispatchEvent(new MouseEvent('click',{{bubbles:true,cancelable:true,view:window}}));
}}""")
await page.wait_for_timeout(1200)

# Extraer contenido
html = await page.evaluate("document.querySelector('[data-de-type=membercontent]').innerHTML")
```

## UX / Tech stack del clon
- React 19 + TypeScript + Vite 8 + Tailwind v4
- Dark theme: `--bg: #080812`, `--accent: #e040a0`, `--accent2: #7c3aed`
- Layout: sidebar 320px fijo desktop, slide-in mobile con backdrop blur
- Topbar mobile con hamburger + título lección + % progreso
- Responsive: 3 breakpoints (1024, 768, 480)
- Accesibilidad: aria-label, aria-expanded, aria-current, tabIndex, Escape key
- sessionStorage para progress (no localStorage — regla global)
- video_file en courseData para match exacto Python→JS (evita mismatch Unicode)

**How to apply:** Para relanzar solo: `npx serve -s dist -l 4200` + cloudflared.
