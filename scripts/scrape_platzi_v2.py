"""
Platzi Full Scraper v2 — Discovery + Download
1. Login → route page → extract real course slugs
2. For each course → expand sidebar → collect class URLs
3. For each class → intercept m3u8 → yt-dlp download
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, json, re, subprocess
from pathlib import Path
from playwright.async_api import async_playwright

EMAIL       = "lumpenvisual@gmail.com"
PASSWORD    = "JacJac891212*"
ROUTE_URL   = "https://platzi.com/mis-rutas/16704423/"
CHROME_PATH = "C:/Program Files/Google/Chrome/Application/chrome.exe"

BASE = Path("E:/Documents/PROYECTOS/AgencIA/platzi_clone")
OUT  = BASE / "downloads"
VID  = OUT / "videos"
PDF  = OUT / "pdfs"
for d in [OUT, VID, PDF]:
    d.mkdir(parents=True, exist_ok=True)

def safe_name(s, max_len=60):
    return re.sub(r'[^\w\-]', '_', s)[:max_len].strip('_') or 'untitled'

async def login(page):
    print("\n[LOGIN] Platzi 2-step")
    await page.goto("https://platzi.com/login/", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(3000)

    # Step 1: email
    try:
        email_inp = page.locator('input[type="email"], input[name="email"]').first
        await email_inp.wait_for(state="visible", timeout=8000)
        await email_inp.fill(EMAIL)
        await page.wait_for_timeout(500)
        await page.locator('button:has-text("Continuar"), button[type="submit"]').first.click()
        await page.wait_for_timeout(3500)
    except Exception as e:
        print(f"  ⚠️  Email step: {e}")

    # Step 2: password
    try:
        pass_inp = page.locator('input[type="password"]').first
        await pass_inp.wait_for(state="visible", timeout=8000)
        await pass_inp.fill(PASSWORD)
        await page.wait_for_timeout(500)
        await page.locator('button[type="submit"]').first.click()
        await page.wait_for_timeout(6000)
    except Exception as e:
        print(f"  ⚠️  Password step: {e}")

    print(f"  URL: {page.url}")
    logged = "login" not in page.url
    print(f"  {'✅ Login OK' if logged else '❌ Login failed'}")
    return logged

async def discover_courses(page):
    """Navigate to the route and extract real course slugs."""
    print(f"\n[DISCOVER] Route: {ROUTE_URL}")
    await page.goto(ROUTE_URL, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(4000)

    # Scroll down to load lazy content
    for _ in range(5):
        await page.evaluate("window.scrollBy(0, 600)")
        await page.wait_for_timeout(800)

    # Extract course links
    courses = await page.evaluate("""() => {
        const seen = new Set()
        const items = []
        document.querySelectorAll('a[href]').forEach(a => {
            const href = a.href || ''
            if (href.includes('platzi.com/cursos/') && !seen.has(href)) {
                seen.add(href)
                const slug = href.replace(/.*\/cursos\//, '').replace(/\/$/, '').split('/')[0]
                const text = (a.textContent?.trim() || '').replace(/\\s+/g, ' ').slice(0, 100)
                if (slug) items.push({ slug, name: text, url: href })
            }
        })
        return items
    }""")

    # Also try /curso/ (singular)
    courses2 = await page.evaluate("""() => {
        const seen = new Set()
        const items = []
        document.querySelectorAll('a[href]').forEach(a => {
            const href = a.href || ''
            if (href.includes('platzi.com/curso/') && !seen.has(href)) {
                seen.add(href)
                const slug = href.replace(/.*\/curso\//, '').replace(/\/$/, '').split('/')[0]
                const text = (a.textContent?.trim() || '').replace(/\\s+/g, ' ').slice(0, 100)
                if (slug) items.push({ slug, name: text, url: href })
            }
        })
        return items
    }""")

    all_courses = courses + [c for c in courses2 if c['slug'] not in {x['slug'] for x in courses}]

    # Save page for debugging
    html = await page.content()
    (OUT / "route_page.html").write_text(html, encoding='utf-8')
    text = await page.evaluate("document.body.innerText")
    (OUT / "route_text.txt").write_text(text, encoding='utf-8')

    print(f"  Cursos encontrados: {len(all_courses)}")
    for c in all_courses:
        print(f"    {c['slug']} — {c['name'][:50]}")

    (OUT / "discovered_courses.json").write_text(
        json.dumps(all_courses, ensure_ascii=False, indent=2), encoding='utf-8')

    return all_courses

async def get_course_classes(page, slug):
    """Navigate to course page and extract all class links."""
    url = f"https://platzi.com/cursos/{slug}/"
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(3000)

    # Check if redirected (real slug might differ)
    real_url = page.url
    real_slug = slug
    if '/cursos/' in real_url:
        real_slug = real_url.rstrip('/').split('/')[-1]

    # Scroll to load lazy content
    for _ in range(3):
        await page.evaluate("window.scrollBy(0, 500)")
        await page.wait_for_timeout(500)

    # Expand all accordion/toggle items
    try:
        toggles = page.locator('button[aria-expanded="false"], [class*="toggle"]:not([aria-expanded="true"])')
        count = await toggles.count()
        for i in range(min(count, 30)):
            try:
                await toggles.nth(i).click()
                await page.wait_for_timeout(200)
            except Exception:
                pass
    except Exception:
        pass

    # Extract class links
    classes = await page.evaluate("""(courseSlug) => {
        const items = []
        const seen = new Set()
        
        // Try the specific class identified by subagent
        const itemLinks = document.querySelectorAll('a[class*="ItemLink-module_ItemLink"]');
        itemLinks.forEach(a => {
            const href = a.href || '';
            if (!seen.has(href)) {
                seen.add(href);
                const titleEl = a.querySelector('h3') || a.querySelector('div > span') || a;
                const text = (titleEl.textContent?.trim() || '').replace(/\\s+/g, ' ').slice(0, 120);
                items.push({ url: href, title: text || href.split('/').filter(Boolean).pop() });
            }
        });

        // Fallback: any link that contains the course slug and is deeper
        if (items.length === 0) {
            document.querySelectorAll('a[href]').forEach(a => {
                const href = a.href || '';
                // Check if it's a class: usually contains /clases/ OR is a sub-path of the course
                const isClass = href.includes('/clases/') || 
                                href.includes('/clase/') || 
                                (href.includes(`/cursos/${courseSlug}/`) && href.replace(/.*\\/cursos\\/[^\\/]+\\//, '').length > 0);
                
                if (isClass && !seen.has(href)) {
                    seen.add(href);
                    const text = (a.textContent?.trim() || '').replace(/\\s+/g, ' ').slice(0, 120);
                    items.push({ url: href, title: text || href.split('/').filter(Boolean).pop() });
                }
            });
        }
        return items
    }""", slug)

    return classes, real_slug

async def intercept_video(page, class_url):
    """Intercept HLS m3u8 stream from a class page."""
    m3u8_urls = []

    async def capture(response):
        u = response.url
        if '.m3u8' in u and response.status == 200:
            if u not in m3u8_urls:
                m3u8_urls.append(u)
                print(f"      🎯 m3u8: {u[:90]}")

    page.on("response", capture)

    try:
        await page.goto(class_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)

        # Try clicking play
        for selector in ['video', 'button[aria-label*="play" i]', '[class*="play" i]', '[class*="Play"]']:
            try:
                el = page.locator(selector).first
                if await el.count() > 0:
                    await el.click()
                    await page.wait_for_timeout(2000)
                    break
            except Exception:
                pass

        # Check video element src
        video_src = await page.evaluate("""() => {
            const v = document.querySelector('video')
            if (!v) return ''
            return v.src || v.currentSrc || v.querySelector?.('source')?.src || ''
        }""")
        if video_src and 'm3u8' in video_src and video_src not in m3u8_urls:
            m3u8_urls.append(video_src)

        # Wait a bit more for network requests
        if not m3u8_urls:
            await page.wait_for_timeout(3000)

    except Exception as e:
        print(f"      ⚠️  Error: {e}")
    finally:
        page.remove_listener("response", capture)

    return m3u8_urls[0] if m3u8_urls else None

async def download_video(m3u8_url, dest_path, referer="https://platzi.com/"):
    """Download HLS stream with yt-dlp."""
    if dest_path.exists() and dest_path.stat().st_size > 100_000:
        print(f"      ✅ Ya existe: {dest_path.name}")
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
        "--add-header", f"Origin:https://platzi.com",
        "--no-warnings", "-q",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if dest_path.exists() and dest_path.stat().st_size > 100_000:
            kb = dest_path.stat().st_size // 1024
            print(f"      ✅ {dest_path.name} ({kb}KB)")
            return True
        print(f"      ⚠️  yt-dlp: {result.stderr[:200]}")
        return False
    except Exception as e:
        print(f"      ⚠️  Download error: {e}")
        return False

async def scrape_class(page, cls, course_slug, course_dir, idx):
    url   = cls['url']
    title = cls['title']
    prefix = f"{idx:03d}_{safe_name(title)}"

    print(f"\n    [{idx:03d}] {title[:60]}")

    m3u8 = await intercept_video(page, url)

    # Save text content
    try:
        text = await page.evaluate("document.body.innerText")
        (course_dir / f"{prefix}.txt").write_text(text[:15000], encoding='utf-8')
    except Exception:
        text = ""

    # Find downloadable materials
    downloads = await page.evaluate("""() => {
        const links = []
        document.querySelectorAll('a[href]').forEach(a => {
            const href = a.href || ''
            const t = (a.textContent?.trim() || '').slice(0, 80)
            if (href.match(/\\.pdf|\\.zip|\\.pptx|\\.xlsx|\\.docx/i) ||
                t.toLowerCase().includes('descarg') ||
                t.toLowerCase().includes('material') ||
                t.toLowerCase().includes('recurso')) {
                links.push({ url: href, text: t })
            }
        })
        return links
    }""")

    result = {
        "index": idx,
        "title": title,
        "url": url,
        "m3u8": m3u8,
        "downloads": downloads,
        "has_content": len(text) > 100,
        "video_file": None,
    }

    if m3u8:
        vid_path = VID / f"{course_slug}_{prefix}.mp4"
        await download_video(m3u8, vid_path, referer=url)
        result["video_file"] = vid_path.name
    else:
        print(f"      ⚠️  No m3u8")

    return result

async def main():
    print("[START] Platzi Full Scraper v2")
    print(f"  Output: {OUT}")

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

        print("[LOGIN] Usando cookies manuales...")
        try:
            cookies = json.loads((OUT / "cookies.json").read_text(encoding="utf-8"))
            await ctx.add_cookies(cookies)
            print("  ✅ Cookies cargadas correctamente.")
        except Exception as e:
            print(f"❌ Error al cargar cookies: {e}")
            await browser.close()
            return

        # Discover real course slugs from route
        courses = await discover_courses(page)

        if not courses:
            print("⚠️  No courses found — using hardcoded list")
            courses = [
                {"slug": "fundamentos-arquitectura-software", "name": "Fundamentos de Arquitectura de Software"},
                {"slug": "arquitectura-software-profesional", "name": "Arquitectura de Software Profesional"},
                {"slug": "arquitecturas-limpias", "name": "Arquitecturas Limpias"},
                {"slug": "arquitectura-backend-practico", "name": "Arquitectura Backend Práctico"},
                {"slug": "alta-concurrencia", "name": "Arquitectura de Alta Concurrencia"},
                {"slug": "frameworks-arquitecturas-frontend", "name": "Frameworks y Arquitecturas Frontend"},
                {"slug": "arquitecturas-css", "name": "Arquitecturas CSS"},
                {"slug": "ssr-react", "name": "Server Side Render con React.js"},
                {"slug": "nextjs-sitios-estaticos", "name": "Next.js: Sitios Estáticos y Jamstack"},
                {"slug": "jamstack", "name": "Introducción a Jamstack"},
                {"slug": "nuxt2-ssr", "name": "Server Side Rendering con Nuxt 2"},
                {"slug": "astro-web", "name": "Creación de Páginas Web con Astro"},
                {"slug": "angular-avanzado", "name": "Angular Avanzado"},
                {"slug": "nextjs-avanzado", "name": "Next.js Avanzado"},
                {"slug": "nodejs-autenticacion-microservicios", "name": "Node.js: Autenticación, Microservicios y Redis"},
                {"slug": "go-avanzado-eventos-cqrs", "name": "Go Avanzado: CQRS"},
                {"slug": "go-avanzado-grpc", "name": "Go Avanzado: gRPC"},
                {"slug": "graphql-nodejs", "name": "GraphQL con Node.js"},
                {"slug": "nodejs-graphql-apollo", "name": "Node.js con GraphQL y Apollo"},
                {"slug": "observabilidad-new-relic", "name": "Observabilidad con New Relic"},
                {"slug": "observabilidad-ingenieria-new-relic", "name": "Ingeniería en Observabilidad"},
                {"slug": "observabilidad-agentes-ai", "name": "Observabilidad de Agentes AI"},
                {"slug": "monorepositorios-nx", "name": "Monorepositorios con NX"},
                {"slug": "cloudflare-workers", "name": "Cloudflare Workers"},
            ]

        all_data = {}
        total_videos = 0
        total_classes = 0

        for course in courses:
            slug = course['slug']
            name = course.get('name', slug)

            print(f"\n{'='*60}")
            print(f"[CURSO] {name}")
            print(f"  Slug: {slug}")

            course_dir = OUT / safe_name(slug)
            course_dir.mkdir(exist_ok=True)

            classes, real_slug = await get_course_classes(page, slug)
            print(f"  Clases: {len(classes)}")

            if not classes and real_slug != slug:
                print(f"  Retrying with real slug: {real_slug}")
                classes, _ = await get_course_classes(page, real_slug)
                print(f"  Clases (real slug): {len(classes)}")

            course_data = {
                "slug": slug, "real_slug": real_slug,
                "name": name,
                "url": f"https://platzi.com/cursos/{slug}/",
                "classes": [],
            }

            for idx, cls in enumerate(classes, 1):
                res = await scrape_class(page, cls, real_slug, course_dir, idx)
                course_data["classes"].append(res)
                total_classes += 1
                if res.get("m3u8"):
                    total_videos += 1

                # Save progress after each class
                (course_dir / "course_data.json").write_text(
                    json.dumps(course_data, ensure_ascii=False, indent=2), encoding='utf-8')

            all_data[slug] = course_data
            (OUT / "progress.json").write_text(
                json.dumps(all_data, ensure_ascii=False, indent=2), encoding='utf-8')

            videos_in_course = sum(1 for c in course_data['classes'] if c.get('m3u8'))
            print(f"  ✅ {name}: {len(classes)} clases, {videos_in_course} videos")

        print(f"\n{'='*60}")
        print(f"[DONE] Scraping completo")
        print(f"  Cursos: {len(all_data)}")
        print(f"  Clases: {total_classes}")
        print(f"  Videos: {total_videos}")

        (OUT / "final_summary.json").write_text(json.dumps({
            "total_courses": len(all_data),
            "total_classes": total_classes,
            "total_videos": total_videos,
            "courses": list(all_data.keys()),
        }, ensure_ascii=False, indent=2), encoding='utf-8')

        await browser.close()

asyncio.run(main())
