---
name: site-cloner
description: Clonar sitios de membresía (ClickFunnels, Kajabi, Teachable, Platzi, DevCompass) con Playwright. Login anti-bot, cookies CDP, scraping de contenido protegido, intercepción m3u8 HLS, descarga masiva con yt-dlp, y build de clon React LMS. Técnicas validadas en RAIO English (246 lecciones) y Platzi Arquitecturas Web (24 cursos, 421 videos, 37GB).
tools: Bash, Read, Write, Edit, Agent
---

# Site Cloner — Membership Areas

## Flujo completo (7 fases)

```
Fase 1: Reconocimiento → Fase 2: Login → Fase 3: Scrape estructura
Fase 4: Scrape contenido → Fase 5: Identificar assets → Fase 6: Descargar assets
Fase 7: Build clon React
```

---

## Fase 1: Reconocimiento de la plataforma

```python
"""
Captura TODOS los requests de red al cargar las primeras 5 páginas.
Identifica CDN, player, y cómo se cargan los assets.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright

SKIP_DOMAINS = ["google", "facebook", "analytics", "doubleclick", "hotmart"]

async def capture_network(LOGIN_URL, EMAIL, PASSWORD, test_urls, OUT):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width":1280,"height":900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124"
        )
        page = await ctx.new_page()
        all_requests = {}

        async def capture(resp):
            if any(d in resp.url for d in SKIP_DOMAINS):
                return
            lesson = getattr(capture, "_current", "?")
            all_requests.setdefault(lesson, []).append({
                "url": resp.url, "status": resp.status,
                "ct": resp.headers.get("content-type","")[:40],
            })
        page.on("response", capture)

        # Login
        await clickfunnels_login(page, LOGIN_URL, EMAIL, PASSWORD)

        for url_id, url in test_urls.items():
            capture._current = url_id
            await page.goto(url, wait_until="load", timeout=30000)
            await page.wait_for_timeout(5000)

            reqs = all_requests.get(url_id, [])
            print(f"\n=== {url_id} | {len(reqs)} requests ===")
            for r in reqs:
                if any(x in r["url"].lower() for x in
                       ["video","mp4","m3u8","cdn","stream","play","media","vimeo","vidalytics"]):
                    print(f"  [MEDIA] {r['status']} {r['url'][:100]}")

        (OUT / "network_capture.json").write_text(
            json.dumps(all_requests, indent=2, ensure_ascii=False), encoding="utf-8")
        await browser.close()
```

---

## Fase 2: Login anti-bot (ClickFunnels)

```python
async def clickfunnels_login(page, LOGIN_URL, EMAIL, PASSWORD):
    """Login seguro para ClickFunnels — bypasa múltiples forms superpuestos."""
    await page.goto(LOGIN_URL, wait_until="load", timeout=30000)
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
    await page.wait_for_timeout(3000)
    print(f"  Logged in → {page.url}")
```

**Reglas críticas:**
- NUNCA `page.fill()` — falla en forms superpuestos
- SIEMPRE buscar form por `action.includes('sign_in')`
- SIEMPRE `expect_navigation` después del submit

---

## Fase 3: Scrape de estructura (índice de lecciones)

```python
async def scrape_lesson_index(page):
    """Extrae estructura de módulos/lecciones desde el sidebar."""
    return await page.evaluate("""() => {
        const lessons = []
        document.querySelectorAll('a.lesson-link').forEach(link => {
            lessons.push({
                id: link.dataset.lessonId,
                title: link.querySelector('.lesson-title-text')?.textContent?.trim() || link.textContent.trim(),
                section: link.closest('.module-group')?.querySelector('.module-title')?.textContent?.trim() || '',
                href: link.href,
            })
        })
        return lessons
    }""")
```

---

## Fase 4: Scrape de contenido (todos los items)

```python
async def scrape_all_lessons(page, lesson_list, OUT):
    results = {}
    for i, lesson in enumerate(lesson_list):
        lid = lesson['id']

        # Click sin verificar visibilidad (elementos ocultos en sidebar colapsado)
        await page.evaluate(f"""() => {{
            const link = document.querySelector("a.lesson-link[data-lesson-id='{lid}']");
            if (link) link.dispatchEvent(new MouseEvent('click',{{bubbles:true,cancelable:true,view:window}}));
        }}""")
        await page.wait_for_timeout(1200)

        # Extraer contenido
        content = await page.evaluate("""() => {
            const el = document.querySelector('[data-de-type="membercontent"]');
            if (!el) return null;
            return {
                html: el.innerHTML,
                vimeo_ids: [...el.querySelectorAll('[data-id]')].map(e => e.dataset.id),
                audio_srcs: [...el.querySelectorAll('audio source')].map(e => e.src),
                text: el.innerText?.trim() || '',
            }
        }""")

        results[lid] = {**lesson, **(content or {})}
        if (i+1) % 20 == 0:
            (OUT / "lessons_content.json").write_text(
                json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  [{i+1}/{len(lesson_list)}] saved checkpoint")

    (OUT / "lessons_content.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    return results
```

---

## Fase 5: Detección de tipo de video

### Detectar Vidalytics (parece Vimeo)
```python
async def detect_vidalytics(page, lid, m3u8_map):
    """Intercepta stream.m3u8 de Vidalytics mientras navega en la página host."""
    async def on_resp(resp):
        if ("vidalytics.com/video" in resp.url and
            "stream.m3u8" in resp.url and resp.status == 200):
            m3u8_map[lid] = resp.url
            print(f"    [M3U8] {resp.url[:80]}")
    page.on("response", on_resp)
    # Navegar al lesson — la URL m3u8 se carga automáticamente
    await click_lesson(page, lid)
    await page.wait_for_timeout(4000)
    page.remove_listener("response", on_resp)
```

### Detectar Vimeo real
```python
async def detect_vimeo(ctx, vid_id):
    """Obtiene URLs directas de Vimeo con referer del dominio permitido."""
    resp = await ctx.request.get(
        f"https://player.vimeo.com/video/{vid_id}/config",
        headers={"Referer": "https://tu-dominio.clickfunnels.com/"}
    )
    if resp.status == 200:
        data = await resp.json()
        progressive = data.get("request",{}).get("files",{}).get("progressive",[])
        progressive.sort(key=lambda x: int(x.get("height",0) or 0), reverse=True)
        return [{"url": f["url"], "quality": f"{f.get('height',0)}p"} for f in progressive]
    return []  # 404 = es Vidalytics o domain-restricted
```

---

## Fase 6: Descarga masiva de assets

### Vidalytics HLS → MP4
```python
def download_hls(m3u8_url, dest, referer="https://fast.vidalytics.com/"):
    result = subprocess.run([
        "python", "-m", "yt_dlp", m3u8_url,
        "-o", str(dest), "-f", "best", "--no-playlist",
        "--concurrent-fragments", "4",
        "--referer", referer,
        "--add-header", f"Origin:{referer.rstrip('/')}",
        "--no-warnings",
    ], capture_output=True, text=True, timeout=600)
    return dest.exists() and dest.stat().st_size > 100_000
```

### S3 MP3/ZIP paralelo
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

def download_s3(url, dest, session=None):
    s = session or requests.Session()
    r = s.get(url, stream=True, timeout=60)
    if r.status_code == 200:
        with open(dest, "wb") as f:
            for chunk in r.iter_content(65536):
                f.write(chunk)
        return True
    return False

def download_all_s3(todo_list, max_workers=8):
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(download_s3, url, dest): (url, dest) for url, dest in todo_list}
        done, failed = 0, []
        for fut in as_completed(futures):
            url, dest = futures[fut]
            if fut.result():
                done += 1
            else:
                failed.append(url)
        print(f"Downloaded {done}/{len(todo_list)}, failed {len(failed)}")
        return failed
```

---

## Fase 7: safe_fname Python→JS consistente

```python
import re

def safe_fname(title, lid, ext=".mp4"):
    """Nombre de archivo seguro. GUARDAR en JSON — no recalcular en JS (Unicode mismatch)."""
    n = re.sub(r'[^\w\-]', '_', title)[:50].strip('_')
    return f"{lid}_{n}{ext}"
```

**IMPORTANTE:** Guardar el resultado en `courseData.json` como `video_file`.
JS `\w` solo es ASCII; Python `\w` incluye Unicode. Recalcular en JS genera paths incorrectos.

---

## Limpieza pre-build

```bash
# Eliminar archivos temporales de yt-dlp antes de npm run build
rm -f public/videos/*.part public/videos/*.part-* public/videos/*.ytdl
```

**Why:** Vite copia todo public/ al dist. Los `.part` files se crean y eliminan durante descarga, causando ENOENT race condition en el build.

---

## Checklist final

- [ ] `sys.stdout.reconfigure(encoding='utf-8')` en todos los scripts Python (Windows)
- [ ] Login vía JS form.submit(), no page.fill()
- [ ] dispatchEvent para elementos ocultos
- [ ] Network capture para identificar player real
- [ ] safe_fname guardado en JSON, nunca recalculado en JS
- [ ] Limpiar .part antes de build
- [ ] sessionStorage (no localStorage) para progreso en el clon
