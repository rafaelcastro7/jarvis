# Scraping & Automation — Conocimiento Validado

## CDP Method (técnica principal)
Conectar a Chrome ya logueado sin necesidad de automatizar login:
```python
# 1. Abrir Chrome con: chrome.exe --remote-debugging-port=9222
# 2. Loguearse manualmente en el browser
# 3. Conectar Playwright:
async with async_playwright() as p:
    b = await p.chromium.connect_over_cdp('http://localhost:9222')
    page = b.contexts[0].pages[0]
```

## Reglas críticas validadas

### 1. UTF-8 en Windows (SIEMPRE primero)
```python
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
```

### 2. ClickFunnels login — JS form.submit() no page.fill()
```python
await page.evaluate(f"""() => {{
    for (const f of document.querySelectorAll('form')) {{
        if (f.action && f.action.includes('sign_in')) {{
            f.querySelector('input[name="member[email]"]').value = '{EMAIL}';
            f.querySelector('input[name="member[password]"]').value = '{PASSWORD}';
            f.submit(); break;
        }}
    }}
}}""")
```

### 3. dispatchEvent para elementos ocultos
```python
await page.evaluate(f"""() => {{
    const link = document.querySelector("a[data-lesson-id='{lid}']");
    if (link) link.dispatchEvent(new MouseEvent('click', {{bubbles:true, cancelable:true, view:window}}));
}}""")
```

### 4. Vidalytics HLS — interceptar m3u8 desde dominio host
```python
async def on_resp(resp):
    if "vidalytics.com/video" in resp.url and "stream.m3u8" in resp.url:
        m3u8_map[lid] = resp.url
page.on("response", on_resp)
await navigate_to_lesson(page, lid)
await page.wait_for_timeout(4000)
page.remove_listener("response", on_resp)
```

### 5. yt-dlp para HLS
```python
subprocess.run([
    "python", "-m", "yt_dlp", m3u8_url,
    "-o", str(dest), "-f", "best",
    "--concurrent-fragments", "4",
    "--referer", "https://fast.vidalytics.com/",
    "--add-header", "Origin:https://fast.vidalytics.com",
    "--no-warnings",
], timeout=600)
```

### 6. safe_fname — GUARDAR en JSON, nunca recalcular en JS
```python
import re
def safe_fname(title, lid, ext=".mp4"):
    n = re.sub(r'[^\w\-]', '_', title)[:50].strip('_')
    return f"{lid}_{n}{ext}"
# Python \w incluye Unicode; JS \w solo ASCII → resultados distintos
```

### 7. Descargar PDF con fetch desde browser (signed URLs)
```python
content = await page.evaluate('''async (url) => {
    const resp = await fetch(url, {credentials: "include"});
    const buf = await resp.arrayBuffer();
    const bytes = new Uint8Array(buf);
    let binary = "";
    for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
    return {data: btoa(binary), size: bytes.length};
}''', pdf_url)
import base64
pdf_bytes = base64.b64decode(content['data'])
```

### 8. Limpiar .part antes de npm build
```bash
rm -f public/videos/*.part public/videos/*.part-*
```

### 9. S3 parallel download
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
def download_all_s3(todo_list, max_workers=8):
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(download_s3, url, dest): (url, dest) for url, dest in todo_list}
        done = sum(1 for f in as_completed(futures) if f.result())
```

### 10. Skilljar quiz solver — text-based matching
```python
# No usar índices fijos — las preguntas y opciones son RANDOMIZADAS
# Usar sets de textos correctos/incorrectos
chosen = next((o for o in opts if o['label'] in CORRECT_SET), None)
if not chosen:
    candidates = [o for o in opts if o['label'] not in WRONG_SET]
    chosen = max(candidates, key=lambda o: len(o['label']))  # más largo = más descriptivo
```

## Plataformas y técnicas

| Plataforma | Login | Video | Assets |
|-----------|-------|-------|--------|
| ClickFunnels | JS form.submit() | Vidalytics m3u8 intercept | S3 requests parallel |
| Platzi | CDP (ya logueado) | Vidalytics/Vimeo HLS | yt-dlp |
| Skilljar/Anthropic | CDP (ya logueado) | n/a | PDF fetch browser |
| DevCompass | CDP (ya logueado) | n/a | JSON scrape |
| Kajabi | CDP o email/pw | Vimeo embed | S3 presigned |
| Teachable | CDP o email/pw | Wistia HLS | S3 presigned |
