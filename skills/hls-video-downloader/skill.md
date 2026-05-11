---
name: hls-video-downloader
description: Descargar streams HLS (m3u8) y videos protegidos de Vidalytics, Vimeo, Wistia, Bunny.net. Interceptar con Playwright desde dominio permitido, descargar con yt-dlp o ffmpeg. Técnicas 2025 validadas.
tools: Bash, Write, Read
---

# HLS Video Downloader — Streams Protegidos (2025)

## Identificar el tipo de protección

| Signal en network | Plataforma | Estrategia |
|-------------------|-----------|-----------|
| `fast.vidalytics.com` | Vidalytics | Interceptar m3u8 desde dominio host |
| `player.vimeo.com/config` → 404 | Vimeo domain-restricted | Playwright en iframe desde dominio permitido |
| `player.vimeo.com/config` → 200 | Vimeo normal | API directa con Referer correcto |
| `*.b-cdn.net` / `iframe.mediadelivery.net` | Bunny.net | Interceptar playlist desde host |
| `*.wistia.com/medias/*.m3u8` | Wistia | Interceptar con Playwright |
| `(DRM)` en yt-dlp --list-formats | Widevine/FairPlay | **No se puede** legalmente |

---

## Estrategia universal: interceptar m3u8 en Playwright

```python
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, subprocess
from pathlib import Path
from playwright.async_api import async_playwright

async def intercept_and_download(page_url, dest: Path, login_fn=None,
                                  referer="https://fast.vidalytics.com/"):
    stream_url = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124"
        )
        page = await ctx.new_page()

        async def capture(resp):
            nonlocal stream_url
            url = resp.url
            if any(x in url for x in [".m3u8", "stream.m3u8"]) and resp.status == 200:
                stream_url = url
        page.on("response", capture)

        if login_fn:
            await login_fn(page)

        await page.goto(page_url, wait_until="load", timeout=30000)
        await page.wait_for_timeout(5000)
        await browser.close()

    if stream_url:
        return download_m3u8(stream_url, dest, referer)
    return False
```

---

## yt-dlp — Flags 2025 más importantes

```bash
# Descarga HLS robusta (producción)
yt-dlp \
  --concurrent-fragments 16 \
  --retries 20 \
  --fragment-retries 100 \
  --hls-use-mpegts \
  --downloader ffmpeg \
  --format "bv*+ba/best" \
  --referer "https://fast.vidalytics.com/" \
  --add-header "Origin:https://fast.vidalytics.com" \
  "https://fast.vidalytics.com/.../stream.m3u8"

# Con cookies del browser (signed URLs)
yt-dlp --cookies-from-browser chrome "URL"

# Verificar si es DRM
yt-dlp --list-formats "URL"  # Buscar "(DRM)" en la lista
```

### Python wrapper con fallback ffmpeg

```python
import subprocess
from pathlib import Path

def download_m3u8(m3u8_url: str, dest: Path, referer: str) -> bool:
    """yt-dlp con fallback a ffmpeg."""
    # Intento 1: yt-dlp
    r = subprocess.run([
        "python", "-m", "yt_dlp", m3u8_url,
        "-o", str(dest), "-f", "best", "--no-playlist",
        "--concurrent-fragments", "4",
        "--retries", "10", "--fragment-retries", "50",
        "--referer", referer,
        "--add-header", f"Origin:{referer.rstrip('/')}",
        "--no-warnings",
    ], capture_output=True, text=True, timeout=600)

    if dest.exists() and dest.stat().st_size > 100_000:
        return True

    # Fallback: ffmpeg
    r2 = subprocess.run([
        "ffmpeg", "-y",
        "-headers", f"Referer: {referer}\r\nOrigin: {referer}\r\n",
        "-i", m3u8_url, "-c", "copy", str(dest)
    ], capture_output=True, text=True, timeout=600)

    return dest.exists() and dest.stat().st_size > 100_000
```

---

## Vimeo con Referer correcto

```python
import requests

def get_vimeo_direct(video_id: str, allowed_domain: str) -> list:
    """URLs directas MP4 de Vimeo unlisted. Retorna [] si domain-restricted."""
    resp = requests.get(
        f"https://player.vimeo.com/video/{video_id}/config",
        headers={
            "Referer": f"https://{allowed_domain}/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }, timeout=15
    )
    if resp.status_code != 200:
        return []  # Es Vidalytics o domain-restricted — cambiar estrategia

    data = resp.json()
    progressive = data.get("request", {}).get("files", {}).get("progressive", [])
    progressive.sort(key=lambda x: int(x.get("height", 0) or 0), reverse=True)
    return [{"url": f["url"], "quality": f"{f.get('height',0)}p"} for f in progressive]
```

---

## safe_fname — CRÍTICO: calcular en Python, guardar en JSON

```python
import re

def safe_fname(title: str, lid: str, ext=".mp4") -> str:
    """
    Python \w es Unicode-aware (mantiene ó, Í, ñ).
    JS \w es solo ASCII. NUNCA recalcular en JS — genera mismatch.
    Guardar resultado en courseData.json como lesson.video_file
    """
    n = re.sub(r'[^\w\-]', '_', title)[:50].strip('_')
    return f"{lid}_{n}{ext}"
```

---

## Descarga paralela assets S3 (MP3/ZIP)

```python
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def download_s3_batch(items: list[tuple[str, Path]], max_workers=8):
    """items: [(url, dest_path), ...]"""
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    def dl_one(url, dest):
        r = session.get(url, stream=True, timeout=60)
        if r.status_code == 200:
            with open(dest, "wb") as f:
                for chunk in r.iter_content(65536):
                    f.write(chunk)
            return True
        return False

    failed = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(dl_one, url, dest): url for url, dest in items}
        for fut in as_completed(futs):
            if not fut.result():
                failed.append(futs[fut])
    return failed
```

---

## Limpieza pre-build (crítico con Vite)

```bash
# SIEMPRE antes de npm run build si hay descargas activas
rm -f public/videos/*.part public/videos/*.part-* public/videos/*.ytdl
```

Vite copia todo `public/` al `dist/`. Los `.part` creados por yt-dlp durante descarga activa causan `ENOENT` race condition que aborta el build.

---

## Referers por plataforma

| Plataforma | Referer | Origin |
|-----------|---------|--------|
| Vidalytics | `https://fast.vidalytics.com/` | `https://fast.vidalytics.com` |
| Vimeo embed | `https://player.vimeo.com/` | `https://player.vimeo.com` |
| Bunny.net | dominio del site embebedor | mismo |
| Wistia | dominio del site embebedor | mismo |
| Platzi | `https://platzi.com/` | `https://platzi.com` |

---

## Platzi — Descarga masiva de cursos (validado 2025)

### Técnica CDP para login anti-bot
Platzi bloquea login automatizado. Solución: conectar Playwright al Chrome del usuario ya logueado.

```python
async def connect_to_open_browser(p):
    """Chrome debe estar abierto con --remote-debugging-port=9222"""
    for port in [9222, 9223]:
        try:
            b = await p.chromium.connect_over_cdp(f"http://localhost:{port}")
            return b
        except Exception:
            pass
    return None
```

**Iniciar Chrome con CDP:**
```bat
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome-debug"
```

### Interceptar m3u8 en clases Platzi
```python
m3u8_urls = []
async def capture(response):
    u = response.url
    if '.m3u8' in u and response.status == 200 and u not in m3u8_urls:
        m3u8_urls.append(u)
page.on("response", capture)
await page.goto(class_url, wait_until="domcontentloaded")
await page.wait_for_timeout(5000)  # esperar que el player cargue
page.remove_listener("response", capture)
m3u8 = m3u8_urls[0] if m3u8_urls else None
```

### Selector de clases en Platzi (2025)
```javascript
// Selector principal (CSS modules)
document.querySelectorAll('a[class*="ItemLink-module_ItemLink"]')

// Fallback
document.querySelectorAll('a[href*="/clases/"], a[href*="/clase/"]')
```

### Resultado validado: Platzi Arquitecturas Web Modernas
- 24 cursos scrapeados
- 421 videos descargados (37.77 GB)
- 11 clases sin video = quizzes/feedback (normal, no son video)
- Output: `downloads/{course_slug}/001_titulo.txt` + `downloads/videos/{slug}_001_titulo.mp4`

### yt-dlp para Platzi HLS
```bash
python -m yt_dlp "https://...m3u8" \
  -o "output.mp4" \
  --concurrent-fragments 4 \
  --retries 10 \
  --fragment-retries 30 \
  --referer "https://platzi.com/" \
  --add-header "Origin:https://platzi.com" \
  --no-warnings -q
```
