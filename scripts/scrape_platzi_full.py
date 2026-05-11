"""
Platzi Full Scraper — Fase 2: Clases + Videos + PDFs
Ruta: Arquitecturas Web Modernas y Escalabilidad (24 cursos)
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, json, re, subprocess
from pathlib import Path
from playwright.async_api import async_playwright, Page

EMAIL       = "lumpenvisual@gmail.com"
PASSWORD    = "JacJac891212*"
CHROME_PATH = "C:/Program Files/Google/Chrome/Application/chrome.exe"

BASE = Path("E:/Documents/PROYECTOS/AgencIA/platzi_clone")
OUT  = BASE / "downloads"
VID  = OUT / "videos"
PDF  = OUT / "pdfs"
for d in [OUT, VID, PDF]:
    d.mkdir(parents=True, exist_ok=True)

# 24 cursos detectados en la ruta
COURSES = [
    ("fundamentos-arquitectura-software", "Fundamentos de Arquitectura de Software"),
    ("arquitectura-software-profesional", "Arquitectura de Software Profesional"),
    ("arquitecturas-limpias", "Arquitecturas Limpias para Desarrollo de Software"),
    ("arquitectura-backend-practico", "Arquitectura Backend Práctico"),
    ("alta-concurrencia", "Arquitectura de Alta Concurrencia"),
    ("frameworks-arquitecturas-frontend", "Frameworks y Arquitecturas Frontend"),
    ("arquitecturas-css", "Arquitecturas CSS"),
    ("ssr-react", "Server Side Render con React.js"),
    ("nextjs-sitios-estaticos", "Next.js: Sitios Estáticos y Jamstack"),
    ("jamstack", "Introducción a Jamstack"),
    ("nuxt2-ssr", "Server Side Rendering con Nuxt 2"),
    ("astro-web", "Creación de Páginas Web con Astro"),
    ("angular-avanzado", "Angular Avanzado"),
    ("nextjs-avanzado", "Next.js Avanzado"),
    ("nodejs-autenticacion-microservicios", "Node.js: Autenticación, Microservicios y Redis"),
    ("go-avanzado-eventos-cqrs", "Go Avanzado: Arquitectura de Eventos y CQRS"),
    ("go-avanzado-grpc", "Go Avanzado: Protobuffers y gRPC"),
    ("graphql-nodejs", "GraphQL con Node.js"),
    ("nodejs-graphql-apollo", "Node.js con GraphQL, Apollo Server y Prisma"),
    ("observabilidad-new-relic", "Fundamentos de Observabilidad con New Relic"),
    ("observabilidad-ingenieria-new-relic", "Ingeniería en Observabilidad con New Relic"),
    ("observabilidad-agentes-ai", "Observabilidad de Agentes AI con LangSmith"),
    ("monorepositorios-nx", "Monorepositorios con NX"),
    ("cloudflare-workers", "Cloudflare Workers"),
]

async def ss(page, name):
    try:
        await page.screenshot(path=str(OUT / f"ss_{name}.png"), full_page=False)
    except Exception:
        pass

async def login(page):
    print("\n[LOGIN] Platzi 2-step")
    await page.goto("https://platzi.com/login/", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2500)

    # Step 1: email
    email_inp = page.locator('input[type="email"], input[name="email"]').first
    await email_inp.wait_for(state="visible", timeout=8000)
    await email_inp.fill(EMAIL)
    await page.wait_for_timeout(400)
    await page.locator('button[type="submit"], button:has-text("Continuar")').first.click()
    await page.wait_for_timeout(3000)

    # Step 2: password
    pass_inp = page.locator('input[type="password"]').first
    await pass_inp.wait_for(state="visible", timeout=8000)
    await pass_inp.fill(PASSWORD)
    await page.wait_for_timeout(400)
    await page.locator('button[type="submit"]').first.click()
    await page.wait_for_timeout(5000)
    print(f"  → {page.url}")
    return "login" not in page.url

async def get_course_classes(page, slug):
    """Navega al curso y extrae todas las clases del sidebar."""
    url = f"https://platzi.com/cursos/{slug}/"
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(3000)

    # Expandir todos los módulos del sidebar
    try:
        toggles = page.locator('[class*="toggle"], [class*="accordion"], [class*="collapse"], button[aria-expanded="false"]')
        count = await toggles.count()
        for i in range(count):
            try:
                await toggles.nth(i).click()
                await page.wait_for_timeout(300)
            except Exception:
                pass
    except Exception:
        pass

    # Extraer clases
    classes = await page.evaluate("""() => {
        const items = []
        const seen = new Set()
        // Buscar links de clases en sidebar y contenido
        document.querySelectorAll('a[href*="/clases/"], a[href*="/clase/"]').forEach(a => {
            const href = a.href
            const text = a.textContent?.trim()?.replace(/\\s+/g, ' ') || ''
            if (!seen.has(href) && text) {
                seen.add(href)
                items.push({ url: href, title: text.slice(0, 120) })
            }
        })
        return items
    }""")

    # También buscar por estructura de syllabus de Platzi
    if not classes:
        classes = await page.evaluate("""() => {
            const items = []
            const seen = new Set()
            document.querySelectorAll('[href*="platzi.com"], a').forEach(a => {
                const href = a.href || ''
                if (href.includes('/clases/') && !seen.has(href)) {
                    seen.add(href)
                    items.push({
                        url: href,
                        title: (a.textContent?.trim() || href.split('/').slice(-2,-1)[0]).slice(0,120)
                    })
                }
            })
            return items
        }""")

    return classes

async def intercept_video(page, class_url):
    """Intercepta el stream m3u8 o video URL de una clase."""
    m3u8_urls = []

    async def capture(response):
        url = response.url
        if '.m3u8' in url and response.status == 200:
            m3u8_urls.append(url)
            print(f"    🎯 m3u8: {url[:80]}")

    page.on("response", capture)

    try:
        await page.goto(class_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)

        # Buscar y hacer play del video
        try:
            play_btn = page.locator('video, [class*="play"], button[aria-label*="play" i], [class*="PrimaryButton"]').first
            if await play_btn.count() > 0:
                await play_btn.click()
                await page.wait_for_timeout(3000)
        except Exception:
            pass

        # También buscar en el DOM
        video_src = await page.evaluate("""() => {
            const v = document.querySelector('video')
            if (v) return v.src || v.querySelector('source')?.src || ''
            return ''
        }""")

        if video_src and 'm3u8' in video_src:
            m3u8_urls.append(video_src)

    except Exception as e:
        print(f"    ⚠️  Intercept error: {e}")
    finally:
        page.remove_listener("response", capture)

    return m3u8_urls[0] if m3u8_urls else None

async def download_video(m3u8_url, dest_path, referer="https://platzi.com/"):
    """Descarga video HLS con yt-dlp."""
    if dest_path.exists() and dest_path.stat().st_size > 100_000:
        print(f"    ✅ Ya existe: {dest_path.name}")
        return True

    cmd = [
        "python", "-m", "yt_dlp",
        m3u8_url,
        "-o", str(dest_path),
        "--no-playlist",
        "--concurrent-fragments", "4",
        "--retries", "10",
        "--fragment-retries", "30",
        "--referer", referer,
        "--add-header", f"Origin:{referer.rstrip('/')}",
        "--no-warnings", "-q",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if dest_path.exists() and dest_path.stat().st_size > 100_000:
            print(f"    ✅ Descargado: {dest_path.name} ({dest_path.stat().st_size//1024}KB)")
            return True
        else:
            print(f"    ⚠️  yt-dlp falló: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"    ⚠️  Download error: {e}")
        return False

def safe_name(s, max_len=60):
    return re.sub(r'[^\w\-]', '_', s)[:max_len].strip('_')

async def scrape_class(page, cls, course_slug, course_dir, class_idx):
    """Scrape completo de una clase: contenido + video."""
    class_url   = cls['url']
    class_title = cls['title']
    safe_title  = safe_name(class_title)
    prefix      = f"{class_idx:03d}_{safe_title}"

    print(f"\n    [{class_idx}] {class_title[:60]}")
    print(f"        URL: {class_url}")

    # Interceptar video
    m3u8 = await intercept_video(page, class_url)

    # Extraer contenido texto
    try:
        content = await page.evaluate("document.body.innerText")
        (course_dir / f"{prefix}.txt").write_text(content[:10000], encoding='utf-8')
    except Exception:
        content = ""

    # Extraer materiales descargables (PDFs, slides)
    downloads = await page.evaluate("""() => {
        const links = []
        document.querySelectorAll('a[href]').forEach(a => {
            const href = a.href
            const text = (a.textContent?.trim() || '').slice(0, 80)
            if (href.match(/\\.pdf|\\.zip|\\.pptx|\\.xlsx|\\.docx/i) ||
                text.toLowerCase().includes('descarga') ||
                text.toLowerCase().includes('material') ||
                text.toLowerCase().includes('recurso')) {
                links.push({ url: href, text })
            }
        })
        return links
    }""")

    result = {
        "index":   class_idx,
        "title":   class_title,
        "url":     class_url,
        "m3u8":    m3u8,
        "downloads": downloads,
        "has_content": len(content) > 100,
    }

    # Descargar video si encontramos m3u8
    if m3u8:
        vid_path = VID / f"{course_slug}_{prefix}.mp4"
        await download_video(m3u8, vid_path, referer=class_url)
        result["video_file"] = vid_path.name
    else:
        print(f"        ⚠️  No m3u8 encontrado")
        result["video_file"] = None

    return result

async def main():
    print("[START] Platzi Full Scraper")
    print(f"  Output: {OUT}")
    print(f"  Cursos: {len(COURSES)}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=CHROME_PATH,
            headless=False,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--start-maximized"]
        )
        ctx = await browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        page = await ctx.new_page()

        # Login
        logged_in = await login(page)
        if not logged_in:
            print("  ❌ Login fallido — abortando")
            await page.wait_for_timeout(15000)
            await browser.close()
            return

        print(f"  ✅ Login OK")

        all_data = {}
        total_videos = 0
        total_classes = 0

        for course_slug, course_name in COURSES:
            print(f"\n{'='*60}")
            print(f"[CURSO] {course_name}")
            print(f"  Slug: {course_slug}")

            course_dir = OUT / safe_name(course_slug)
            course_dir.mkdir(exist_ok=True)

            # Obtener clases del curso
            classes = await get_course_classes(page, course_slug)
            print(f"  Clases encontradas: {len(classes)}")

            if not classes:
                # Si no hay clases en el slug, buscar el slug real desde la ruta
                print(f"  ⚠️  No classes found — buscando slug real...")
                await page.goto(f"https://platzi.com/cursos/{course_slug}/", wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)
                real_url = page.url
                print(f"  URL real: {real_url}")
                # Intentar con URL real
                real_slug = real_url.rstrip('/').split('/')[-1]
                if real_slug != course_slug:
                    classes = await get_course_classes(page, real_slug)
                    print(f"  Clases con slug real: {len(classes)}")

            course_data = {
                "slug":    course_slug,
                "name":    course_name,
                "url":     f"https://platzi.com/cursos/{course_slug}/",
                "classes": [],
            }

            for idx, cls in enumerate(classes, 1):
                class_result = await scrape_class(page, cls, course_slug, course_dir, idx)
                course_data["classes"].append(class_result)
                total_classes += 1
                if class_result.get("m3u8"):
                    total_videos += 1

            all_data[course_slug] = course_data

            # Guardar progreso
            (course_dir / "course_data.json").write_text(
                json.dumps(course_data, ensure_ascii=False, indent=2), encoding='utf-8')
            (OUT / "progress.json").write_text(
                json.dumps(all_data, ensure_ascii=False, indent=2), encoding='utf-8')

            print(f"  ✅ {course_name}: {len(classes)} clases, {sum(1 for c in course_data['classes'] if c.get('m3u8'))} videos")

        # Resumen final
        print(f"\n{'='*60}")
        print(f"[DONE] Scraping completo")
        print(f"  Cursos procesados: {len(all_data)}")
        print(f"  Clases totales: {total_classes}")
        print(f"  Videos descargados: {total_videos}")
        print(f"  Output: {OUT}")

        (OUT / "final_summary.json").write_text(
            json.dumps({
                "total_courses": len(all_data),
                "total_classes": total_classes,
                "total_videos": total_videos,
                "courses": list(all_data.keys()),
            }, ensure_ascii=False, indent=2), encoding='utf-8')

        await browser.close()

asyncio.run(main())
