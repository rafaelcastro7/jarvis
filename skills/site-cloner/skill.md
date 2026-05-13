---
name: site-cloner
description: Clonar sitios de membresía (ClickFunnels, Kajabi, Teachable, Platzi, DevCompass, Skilljar) con Playwright. Anti-detección multicapa: CDP stealth, fingerprint spoofing, delays humanos, rotación UA/IP, proxies rotativos, Tor, SSH tunnel, ProxyManager inteligente, CAPTCHA detection. Técnicas validadas en RAIO English (246 lecciones), Platzi (421 videos, 37GB), Anthropic Academy (4 cursos).
tools: Bash, Read, Write, Edit, Agent
---

# Site Cloner — Membership Areas

## Flujo completo (8 fases)

```
Fase 0: Anti-detección (SIEMPRE primero)
Fase 1: Reconocimiento → Fase 2: Login → Fase 3: Scrape estructura
Fase 4: Scrape contenido → Fase 5: Identificar assets → Fase 6: Descargar assets
Fase 7: Build clon React
```

---

## Fase 0: Anti-Detección — APLICAR EN TODO SCRAPING

### Método preferido: CDP (Chrome ya logueado) — máxima stealth
```python
# El browser ya tiene cookies reales, historial, sesión activa.
# NO se lanza un browser nuevo → no hay señales de automatización.
# Abrir Chrome con: chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\ChromeProfile
async with async_playwright() as p:
    b = await p.chromium.connect_over_cdp('http://localhost:9222')
    page = b.contexts[0].pages[0]
# Resultado: el sitio ve un usuario real, no un bot.
```

### Stealth context (cuando CDP no es posible)
```python
from playwright.async_api import async_playwright
import random, asyncio

STEALTH_UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

async def stealth_context(p):
    ua = random.choice(STEALTH_UA)
    ctx = await p.chromium.launch_persistent_context(
        user_data_dir="./chrome_profile",  # perfil persistente = cookies reales
        headless=False,                     # headless=True → detectable fácilmente
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
            f"--user-agent={ua}",
        ],
        viewport={"width": random.randint(1280, 1920), "height": random.randint(800, 1080)},
        locale="es-CO",
        timezone_id="America/Bogota",
        color_scheme="dark",
        java_script_enabled=True,
        permissions=["geolocation"],
    )
    return ctx
```

### Eliminar huellas de automatización (ejecutar en cada página nueva)
```python
async def mask_automation(page):
    await page.add_init_script("""
        // Ocultar webdriver flag
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        
        // Falsificar plugins (browsers reales tienen plugins)
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // Falsificar idiomas
        Object.defineProperty(navigator, 'languages', {
            get: () => ['es-CO', 'es', 'en-US', 'en'],
        });
        
        // Eliminar window.chrome en contextos no-Chrome
        if (!window.chrome) {
            window.chrome = { runtime: {} };
        }
        
        // Ocultar que Notification.permission es 'denied' por defecto en headless
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (params) =>
            params.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : originalQuery(params);
        
        // Fingir resolución de pantalla real
        Object.defineProperty(screen, 'width', { get: () => 1920 });
        Object.defineProperty(screen, 'height', { get: () => 1080 });
        Object.defineProperty(screen, 'availWidth', { get: () => 1920 });
        Object.defineProperty(screen, 'availHeight', { get: () => 1040 });
        Object.defineProperty(screen, 'colorDepth', { get: () => 24 });
        Object.defineProperty(screen, 'pixelDepth', { get: () => 24 });
        
        // WebGL vendor spoofing
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) return 'Intel Inc.';
            if (parameter === 37446) return 'Intel Iris OpenGL Engine';
            return getParameter.call(this, parameter);
        };
    """)
```

### Delays humanos — OBLIGATORIO entre acciones
```python
import random, asyncio

async def human_delay(min_ms=800, max_ms=2500):
    """Pausa aleatoria que imita tiempo de reacción humano."""
    await asyncio.sleep(random.uniform(min_ms / 1000, max_ms / 1000))

async def human_type(page, selector, text):
    """Escritura con velocidad variable como humano."""
    await page.click(selector)
    await human_delay(200, 500)
    for char in text:
        await page.keyboard.type(char)
        await asyncio.sleep(random.uniform(0.05, 0.18))  # 50-180ms por tecla

async def human_scroll(page, distance=None):
    """Scroll suave con velocidad variable."""
    d = distance or random.randint(300, 800)
    steps = random.randint(3, 8)
    for _ in range(steps):
        await page.mouse.wheel(0, d // steps)
        await asyncio.sleep(random.uniform(0.1, 0.4))
```

### Rate limiting inteligente
```python
import time
from collections import deque

class RateLimiter:
    """Limita requests por dominio para no disparar alertas de rate limiting."""
    def __init__(self, max_per_minute=20, min_gap_s=2.0):
        self.max_per_minute = max_per_minute
        self.min_gap_s = min_gap_s
        self.timestamps = deque()
        self.last_request = 0

    async def wait(self):
        now = time.monotonic()
        # Respetar gap mínimo entre requests
        elapsed = now - self.last_request
        if elapsed < self.min_gap_s:
            await asyncio.sleep(self.min_gap_s - elapsed + random.uniform(0, 1))
        # Respetar límite por minuto
        self.timestamps = deque(t for t in self.timestamps if now - t < 60)
        if len(self.timestamps) >= self.max_per_minute:
            sleep_time = 60 - (now - self.timestamps[0]) + random.uniform(2, 5)
            await asyncio.sleep(sleep_time)
        self.timestamps.append(time.monotonic())
        self.last_request = time.monotonic()

limiter = RateLimiter(max_per_minute=15, min_gap_s=3.0)
```

### Headers realistas para requests directos
```python
import random

REAL_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "es-CO,es;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

def get_headers(referer=None, ua=None):
    h = REAL_HEADERS.copy()
    if ua:
        h["User-Agent"] = ua
    if referer:
        h["Referer"] = referer
        h["Sec-Fetch-Site"] = "same-origin"
    return h
```

### Playwright con stealth plugin (playwright-stealth equivalente)
```python
# pip install playwright-stealth (si está disponible) o usar script manual
async def apply_stealth(page):
    await mask_automation(page)
    # Mover mouse a posición aleatoria al entrar (simula movimiento humano)
    await page.mouse.move(
        random.randint(100, 800),
        random.randint(100, 600),
    )
    await human_delay(300, 700)
```

### Rotación de sesiones / cookies
```python
import json
from pathlib import Path

async def save_cookies(page, path="cookies.json"):
    cookies = await page.context.cookies()
    Path(path).write_text(json.dumps(cookies, ensure_ascii=False))

async def load_cookies(page, path="cookies.json"):
    if Path(path).exists():
        cookies = json.loads(Path(path).read_text())
        await page.context.add_cookies(cookies)
        return True
    return False

# Flujo: cargar cookies → verificar login → si expirado → re-login → guardar cookies
```

### Detección de CAPTCHAs y pausas de seguridad
```python
CAPTCHA_SIGNALS = [
    "captcha", "cloudflare", "challenge", "robot", "human verification",
    "are you human", "access denied", "too many requests", "rate limit",
    "429", "403 forbidden",
]

async def check_blocked(page):
    """Verifica si el sitio detectó el scraper."""
    url = page.url.lower()
    try:
        body = (await page.evaluate('document.body.innerText')).lower()
    except Exception:
        body = ""
    
    for signal in CAPTCHA_SIGNALS:
        if signal in url or signal in body[:500]:
            print(f"[BLOQUEADO] Detectado: {signal}")
            return True
    return False

async def safe_goto(page, url, limiter=None, retries=3):
    """Navigate con retry y detección de bloqueo."""
    for attempt in range(retries):
        if limiter:
            await limiter.wait()
        await page.goto(url, wait_until='domcontentloaded', timeout=25000)
        await human_delay(1000, 2500)
        
        if not await check_blocked(page):
            return True
        
        wait_time = (attempt + 1) * random.uniform(15, 30)
        print(f"[!] Bloqueado — esperando {wait_time:.0f}s antes de reintentar...")
        await asyncio.sleep(wait_time)
    
    return False
```

### Script base completo con anti-detección
```python
"""
scraper_stealth.py — Template base con todas las técnicas anti-detección.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
import asyncio, random, json
from pathlib import Path
from playwright.async_api import async_playwright

limiter = RateLimiter(max_per_minute=12, min_gap_s=4.0)

async def main():
    async with async_playwright() as p:
        # OPCIÓN A: CDP (preferido — máxima stealth)
        try:
            b = await p.chromium.connect_over_cdp('http://localhost:9222')
            page = b.contexts[0].pages[0]
            mode = "CDP"
        except Exception:
            # OPCIÓN B: Stealth context
            ctx = await stealth_context(p)
            page = await ctx.new_page()
            await apply_stealth(page)
            mode = "STEALTH"
        
        print(f"[{mode}] Browser conectado")
        
        # Cargar cookies guardadas si existen
        await load_cookies(page)
        
        # Navegar con protecciones
        target = "https://example.com/protected-page"
        success = await safe_goto(page, target, limiter=limiter)
        
        if not success:
            print("[ERROR] No se pudo acceder sin ser detectado")
            return
        
        # Scroll humano antes de scraping
        await human_scroll(page)
        await human_delay(500, 1200)
        
        # --- Tu scraping aquí ---
        
        # Guardar cookies para próxima sesión
        await save_cookies(page)

asyncio.run(main())
```

---

## Checklist anti-detección (ANTES de cada scraping)

- [ ] ¿Puedo usar CDP? → SÍ: usar siempre CDP primero
- [ ] `headless=False` (headless=True es trivialmente detectable)
- [ ] `mask_automation(page)` ejecutado en cada página nueva
- [ ] User-Agent real de Chrome reciente (no `python-requests/...`)
- [ ] Delays humanos entre TODAS las acciones (800ms-2.5s mínimo)
- [ ] Rate limiter: máx 12-15 req/min, mínimo 3-4s entre requests
- [ ] Headers completos con Sec-Ch-Ua, Sec-Fetch-* correctos
- [ ] Cookies persistentes (cargar → usar → guardar)
- [ ] `check_blocked()` después de cada `goto`
- [ ] Scroll humano antes de interactuar con elementos

---

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
- [ ] Quiz solver: text-based matching (no índices fijos — Skilljar randomiza)
- [ ] Satisfaction surveys: click LAST radio en el grupo (rating más alto)

---

## Skilljar LMS — Técnicas validadas (Anthropic Academy 2026-05-11)

### Quiz Solver con Text-Based Matching
```python
CORRECT_SET = set()  # textos exactos de opciones correctas aprendidas
WRONG_SET = set()    # textos exactos de opciones incorrectas

# Elegir opción
match = next((o for o in opts if o['label'] in CORRECT_SET), None)
if not match:
    candidates = [o for o in opts if o['label'] not in WRONG_SET]
    is_satisfaction = any(kw in ' '.join(o['label'] for o in candidates).lower()
                         for kw in ['very satisfied', 'very likely', 'extremely', 'not at all'])
    match = candidates[-1] if is_satisfaction else max(candidates, key=lambda o: len(o['label']))

# Actualizar sets desde Show Answers
positions = {}  # {q_pos: 'correct'/'incorrect'} del HTML de Show Answers
for q_pos, status in positions.items():
    txt = chosen_history[attempt].get(q_pos)
    if txt:
        (CORRECT_SET if status == 'correct' else WRONG_SET).add(txt)
```

### CDP Connect a Chrome ya logueado
```python
async with async_playwright() as p:
    b = await p.chromium.connect_over_cdp('http://localhost:9222')
    page = b.contexts[0].pages[0]
# Chrome debe iniciarse con: chrome.exe --remote-debugging-port=9222
```

### Descargar PDF con fetch desde browser (CDN signed URLs)
```python
pdf_url = await page.evaluate('''() => {
    const a = Array.from(document.querySelectorAll('a')).find(a =>
        /download.*pdf|pdf.*download/i.test(a.textContent) || /pdf/i.test(a.href));
    return a ? a.href : null;
}''')
content = await page.evaluate('''async (url) => {
    const resp = await fetch(url, {credentials: "include"});
    const buf = await resp.arrayBuffer();
    const bytes = new Uint8Array(buf);
    let binary = "";
    for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
    return {data: btoa(binary)};
}''', pdf_url)
import base64
with open(pdf_path, 'wb') as f:
    f.write(base64.b64decode(content['data']))
```

---

## Decisión rápida por plataforma (validado en producción)

| Plataforma | Login | Video | Descarga |
|---|---|---|---|
| **Udemy** | yt-dlp `--cookies-from-browser chrome` | MP4/Widevine | yt-dlp directo |
| **Platzi** | CDP (Chrome logueado) | HLS m3u8 | yt-dlp |
| **ClickFunnels** | Playwright JS `form.submit()` | Vidalytics HLS | yt-dlp + referer |
| **Lanchmon/MUI** | React state setter vía evaluate | Google Drive iframe | gdown |
| **Skilljar** | CDP Chrome ya logueado | Vimeo/mp4 | yt-dlp |
| **RAIO English** | CDP + localStorage inject | S3 MP3/MP4 | requests paralelo |

---

## UDEMY — Flujo probado

```python
# Extraer estructura (sin descargar)
subprocess.run(['python', '-m', 'yt_dlp',
    '--cookies-from-browser', 'chrome',
    '--flat-playlist', '-J', course_url], capture_output=True)

# Descargar todo
subprocess.run(['python', '-m', 'yt_dlp',
    '--cookies-from-browser', 'chrome',
    '-o', 'downloads/udemy/{slug}/videos/%(playlist_index)03d_%(title)s.%(ext)s',
    '--format', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    '--merge-output-format', 'mp4',
    '--write-subs', '--sub-lang', 'es,en', '--write-auto-subs',
    '--concurrent-fragments', '3', '--retries', '5',
    course_url])
# Script completo: platzi_clone/scripts/udemy_download_all.py
# Cola de 4 cursos: trading, nodejs-rest-api, data-science, english-fluency
```

---

## LANCHMON/MUI — Técnicas clave

```python
# React state setter (page.fill() es ignorado por React)
await page.evaluate(f"""() => {{
    function set(el, v) {{
        const d = Object.getOwnPropertyDescriptor(el.__proto__, 'value');
        d.set.call(el, v); el.dispatchEvent(new Event('input',{{bubbles:true}}));
    }}
    set(document.querySelector('input[type=email]'), '{EMAIL}');
    set(document.querySelector('input[type=password]'), '{PASSWORD}');
}}""")

# Desbloquear módulos vía JWT + API directa
token = (await page.evaluate("() => JSON.parse(localStorage.getItem('userData')||'{}')"))['token']
# POST /api/investor-academy/progress — {userId, courseId, lessonId, completed:true}
# POST /api/investor-academy/modules/{id}/satisfaction — 11 campos

# Drive IDs desde bundle.js cacheado (10x más rápido que navegación)
for m in re.finditer(r'drive\.google\.com/file/d/([A-Za-z0-9_-]+)/preview', bundle):
    drive_id = m.group(1)
    lid = re.findall(r'"(m\d+-\d+)"', bundle[max(0,m.start()-300):m.start()])[-1]

# Descargar: gdown (NO yt-dlp — CDP bloquea cookies de Chrome)
subprocess.run(['python', '-m', 'gdown',
    f'https://drive.google.com/uc?id={drive_id}', '-O', str(dest)], timeout=600)
```

---

## Filenames seguros Python→JS

```python
import unicodedata, re

def safe_fname_ascii(title, prefix='', ext='.mp4'):
    """ASCII puro — sin mismatch Python \w (Unicode) vs JS \w (ASCII)."""
    text = unicodedata.normalize('NFD', title).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^a-zA-Z0-9_\-]', '_', text)
    return f"{prefix}{re.sub(r'_+','_',text).strip('_').lower()[:40]}{ext}"
# SIEMPRE guardar en JSON — NUNCA recalcular en JS
```

---

## Post-descarga: RAG + Skill

```python
from faster_whisper import WhisperModel
model = WhisperModel("small", device="cpu", compute_type="int8")
segments, _ = model.transcribe(str(mp4), language="es", beam_size=1, vad_filter=True)
text = ' '.join(s.text.strip() for s in segments)
# Chunks ~350 palabras, overlap 50 → rag/{platform}_chunks.jsonl
# Script base: platzi_clone/scripts/rutan_build_rag.py
```

---

## Integración al player (localhost:3055)

```js
// server.js
app.use('/udemy-videos', express.static(path.join(DOWNLOADS_DIR, 'udemy')));
// Auto-detectar metadata.json en disco en /api/metadata endpoint

// App.jsx — nueva school
{ id: 'trading', name: 'Trading School', icon: 'dev', key: 'trading', color: '#f59e0b' }
// ClassView videoSrc: lesson.video_file.startsWith('udemy/') → /udemy-videos/...
```

---

## Ofuscación de origen — APLICAR SIEMPRE

- **CDP siempre primero** — Chrome real sin fingerprint de automatización
- **mask_automation(page)** — oculta webdriver flag, falsifica plugins/resolution/WebGL vendor
- **Delays humanos** — `random.uniform(0.8, 2.5)` entre TODAS las acciones
- **User-Agent Chrome real** — nunca `python-requests/...` ni playwright default UA
- **Cookies persistentes** — guardar/cargar entre sesiones (`cookies.json`)
- **Rate limiting** — max 12 req/min, min 3-4s entre requests
- **Headers completos** — `Sec-Ch-Ua`, `Sec-Fetch-*`, `Accept-Language: es-CO` siempre
- **Perfil Chrome persistente** — `--user-data-dir=C:\ChromeProfile` (historial + cookies reales)
- **`headless=False`** — headless=True es trivialmente detectable por Cloudflare/Akamai
- **Origen IP residencial** — si hay bloqueo persistente: proxy residencial o mobile hotspot

## Orden para clonar un curso nuevo

```
1. Identificar plataforma → método (tabla arriba)
2. Chrome abierto: --remote-debugging-port=9222, sesión activa
3. Script de descarga según plataforma
4. metadata.json: {slug, name, platform, school, classes[]}
5. server.js: agregar static route + auto-detect en /api/metadata
6. App.jsx: agregar school si nueva plataforma; SCHOOLS array
7. npm run build + npm restart
8. faster-whisper → RAG chunks → skill actualizado
```
