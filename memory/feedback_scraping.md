---
name: Scraping Techniques — ClickFunnels + Vidalytics + HLS
description: Técnicas validadas para scraping de membership areas, interceptación de streams HLS protegidos, y descarga de video/audio desde plataformas CDN.
type: feedback
originSessionId: 9d9b6e30-a0be-45b2-b145-f114a4016443
---
# Técnicas de Scraping — ClickFunnels + Vidalytics + Assets

## REGLA 1: ClickFunnels requiere Playwright real
**Regla:** Nunca usar requests/curl para ClickFunnels. Siempre Playwright.
**Why:** Cloudflare bot detection bloquea con 403 aunque las credenciales sean válidas.
**How to apply:** Usar `playwright.async_api` con chromium headless.

---

## REGLA 2: Login ClickFunnels via JS form.submit()
**Regla:** No usar `page.fill()` ni `page.click()` para el login form.
**Why:** Hay 3+ forms superpuestos (signup/login/etc). `page.fill()` apunta al primero (oculto) y da timeout.
**How to apply:**
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
async with page.expect_navigation(url="**/members**", timeout=20000):
    pass
```

---

## REGLA 3: Clicks en elementos ocultos via dispatchEvent
**Regla:** Para elementos colapsados/hidden en sidebar, usar `dispatchEvent` no `page.click()`.
**Why:** `page.click()` verifica visibilidad y lanza error. dispatchEvent bypasea eso.
**How to apply:**
```python
await page.evaluate(f"""() => {{
    const link = document.querySelector("a.lesson-link[data-lesson-id='{lid}']");
    if (link) link.dispatchEvent(new MouseEvent('click', {{bubbles:true, cancelable:true, view:window}}));
}}""")
await page.wait_for_timeout(1200)
```

---

## REGLA 4: Videos que "parecen Vimeo" pueden ser Vidalytics
**Regla:** Siempre hacer network capture para identificar el player real antes de asumir Vimeo.
**Why:** ClickFunnels cursos pueden embeber Vidalytics con IDs numéricos similares a Vimeo. La API de Vimeo retorna 404 para estos IDs.
**How to apply:** Usar full_network_capture.py para interceptar responses y filtrar por "video|stream|m3u8|cdn".

---

## REGLA 5: Vidalytics HLS — interceptar desde dominio permitido
**Regla:** Para streams HLS de Vidalytics, interceptar la URL m3u8 mientras se navega DESDE el dominio original.
**Why:** Las URLs m3u8 de Vidalytics incluyen tokens temporales y están domain-restricted.
**How to apply:**
```python
async def on_resp(resp):
    if "vidalytics.com/video" in resp.url and "stream.m3u8" in resp.url and resp.status == 200:
        m3u8_map[lid] = resp.url

page.on("response", on_resp)
# Navegar DENTRO de la página de ClickFunnels (dominio permitido)
# La URL queda en m3u8_map para descargar después con yt-dlp
```

---

## REGLA 6: yt-dlp para descargar HLS m3u8
**Regla:** Usar yt-dlp con `--concurrent-fragments 4` y referer correcto para HLS.
**How to apply:**
```python
subprocess.run([
    "python", "-m", "yt_dlp", m3u8_url,
    "-o", str(dest),
    "-f", "best", "--no-playlist",
    "--concurrent-fragments", "4",
    "--referer", "https://fast.vidalytics.com/",
    "--add-header", "Origin:https://fast.vidalytics.com",
], timeout=600)
```

---

## REGLA 7: safe_fname Python→JS debe ser consistente
**Regla:** Precalcular `video_file` en Python y guardarlo en JSON; no recalcular en JS.
**Why:** Python `\w` en regex es Unicode-aware (mantiene ó, Í), JS `\w` es solo ASCII. Esto causa mismatch en filenames con caracteres especiales.
**How to apply:**
```python
def safe_fname(title, lid):
    n = re.sub(r'[^\w\-]', '_', title)[:50].strip('_')
    return f"{lid}_{n}.mp4"
# Guardar en courseData.json como lesson.video_file
```

---

## REGLA 8: Archivos .part de yt-dlp rompen build de Vite
**Regla:** Limpiar `.part`, `.part-*` y `.ytdl` de public/ antes de `npm run build`.
**Why:** Vite/rolldown intenta copiar TODOS los archivos de public/ incluyendo temporales, y falla con ENOENT al ser borrados durante el proceso.
**How to apply:**
```python
for ext in ['*.part', '*.ytdl']:
    for f in VID_DIR.glob(ext):
        f.unlink()
```
O: `rm -f public/videos/*.part* public/videos/*.ytdl`

---

## REGLA 9: stdout.reconfigure para Windows UTF-8
**Regla:** Siempre agregar al inicio de scripts Python en Windows.
**Why:** Windows usa cp1252 por defecto y lanza UnicodeEncodeError con caracteres especiales en print().
**How to apply:** `import sys; sys.stdout.reconfigure(encoding='utf-8')` — primera línea del script.

---

## REGLA 11: Lanchmon/MUI — videos son Google Drive embeds
**Regla:** En portales React MUI como Lanchmon, interceptar iframe src DESPUÉS de click en cada lección.
**Why:** Videos no cargan hasta que la lección es seleccionada en el sidebar. El iframe aparece con `drive.google.com/file/d/{ID}/preview`.
**How to apply:**
```python
async def wait_for_embed(page, timeout=15):
    for _ in range(timeout):
        src = await safe(page, """() => {
            for (const f of document.querySelectorAll('iframe')) {
                const s = f.src || f.getAttribute('data-src') || '';
                if (s.includes('drive.google') || s.includes('youtube')) return s;
            }
            return null;
        }""")
        if src: return src
        await asyncio.sleep(1)
    return None
```
Drive ID: `/file/d/([a-zA-Z0-9_\-]{20,})/preview`

---

## REGLA 12: MUI sidebar — excluir nav items por texto
**Regla:** Al hacer click en lecciones MUI, excluir: Onboarding, Inv. Academy, Recursos, Bots IA, Glosario, Volver, Ver ruta, Ver curso, INVEST.
**Why:** `.MuiListItemButton-root` incluye tanto nav items como lecciones. Sin filtro, el script hace click en botones de navegación.
**How to apply:** En el JS `find()`, verificar `!NAV.some(n => t.toLowerCase().startsWith(n.toLowerCase()))` antes de retornar el elemento.

---

## REGLA 13: Portales con módulos secuenciales — acceso limitado
**Regla:** En portales con unlock secuencial (completa módulo N para desbloquear N+1), el scraper SOLO puede extraer el módulo actual desbloqueado.
**Why:** Al hacer "Ver Curso" en cualquier módulo, el player abre siempre el módulo disponible (el más bajo sin completar). No es posible saltar módulos.
**How to apply:** Extraer lo que esté disponible, guardar progreso incremental, pedir al usuario completar el módulo en el portal para desbloquear el siguiente.

---

## REGLA 14: gdown para Google Drive embeds públicos — sin cookies
**Regla:** Usar `python -m gdown https://drive.google.com/uc?id={ID} -O dest.mp4` para Drive IDs de Lanchmon.
**Why:** yt-dlp falla con "Could not copy Chrome cookie database" porque Chrome está corriendo con CDP y tiene el SQLite locked. Los archivos Drive de Lanchmon son públicamente accesibles.
**How to apply:**
```python
subprocess.run(['python', '-m', 'gdown', f'https://drive.google.com/uc?id={drive_id}', '-O', str(dest)],
               capture_output=True, text=True, timeout=600, encoding='utf-8', errors='replace')
```
**Nota:** NO usar `--fuzzy` (no existe en esta versión). NO pasar bare ID (pasar URL completa).
**Filename encoding:** Usar unicodedata.normalize + ascii para evitar filenames con Mojibake en Windows.

---

## REGLA 15: Lanchmon — el player carga el módulo activo, no el seleccionado
**Regla:** Hacer click en "Ver Curso" de CUALQUIER módulo carga el módulo actualmente en progreso (el menor incompleto).
**Why:** La URL del player es siempre `/dashboard/rutan/investors/school/videos` — el módulo se determina por estado React, no por URL.
**How to apply:** Para avanzar de módulo: (1) completar todos los videos del módulo actual, (2) encontrar y completar la "Encuesta de satisfacción" visible en el sidebar del player, (3) verificar que el siguiente módulo aparece sin "Bloqueado" en la lista academy.

---

## REGLA 16: Lanchmon encuesta — no llenar el search bar accidentalmente
**Regla:** Al llenar la encuesta, filtrar inputs con placeholder `Buscar ⌘K` o que contengan 'Buscar'.
**Why:** El input de búsqueda global está en el DOM antes de los campos de la encuesta. Sin filtro, el documento de identidad va al search bar.
**How to apply:**
```python
inputs = [...querySelectorAll('input[type=text],input:not([type]),textarea')]
    .filter(el => el.type !== 'hidden' && el.placeholder !== 'Buscar ⌘K')
```

---

## REGLA 17: Portales con lock secuencial — desbloquear via API directa
**Regla:** Si el portal expone una API REST, usar JWT + POST directo en lugar de navegar el UI para desbloquear módulos.
**Why:** Navegación UI requiere horas de scraping; la API directa toma segundos. JWT en localStorage[userData].token.
**How to apply (Lanchmon):**
```python
# GET token from browser
storage = await page.evaluate("() => JSON.parse(localStorage.getItem('userData') || '{}')")
token = storage['token']
# Mark lesson complete
await client.post(f'{BASE_API}/api/investor-academy/progress',
    json={'userId': uid, 'courseId': module_id, 'lessonId': 'm1-01', 'completed': True},
    headers={'Authorization': f'Bearer {token}'})
# Submit survey
await client.post(f'{BASE_API}/api/investor-academy/modules/{mid}/satisfaction',
    json={'userId':uid, 'documentoIdentidad':'...', 'programaResponsable':'...', 
          'nombreActividad':'...', 'actividadRealizada':'...', 'calificacionGeneral':'5', ...})
```
**How to find fields:** Probe the endpoint — it returns "X is required" one field at a time, OR search the JS bundle.

---

## REGLA 18: Drive IDs de lecciones — extraer del bundle.js en lugar del browser
**Regla:** Buscar Drive IDs directamente en el bundle JS cacheado con regex, no navegando lección por lección.
**Why:** Navegación es frágil (sidebar scroll, timeouts). Bundle tiene TODOS los IDs hardcoded y es 10MB.
**How to apply:**
```python
bundle = Path('downloads/bundle.js').read_text(encoding='utf-8', errors='replace')
drive_re = re.compile(r'drive\.google\.com/file/d/([A-Za-z0-9_-]+)/preview')
lesson_id_re = re.compile(r'"(m\d+-\d+)"')
for dm in drive_re.finditer(bundle):
    drive_id = dm.group(1)
    nearby = bundle[max(0, dm.start()-300):dm.start()]
    lid_matches = list(lesson_id_re.finditer(nearby))
    lesson_id = lid_matches[-1].group(1) if lid_matches else None
```
Cache the bundle to disk on first download; reuse for subsequent extractions.

---

## REGLA 10: Descargas paralelas para assets S3
**Regla:** Para muchos archivos pequeños/medianos de S3, usar ThreadPoolExecutor(max_workers=8).
**Why:** Las descargas secuenciales para 300+ MP3 toman horas. Paralelas toman minutos.
**How to apply:**
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
with ThreadPoolExecutor(max_workers=8) as ex:
    futures = {ex.submit(download_one, url, dest): url for url, dest in todo}
    for f in as_completed(futures):
        result = f.result()
```
