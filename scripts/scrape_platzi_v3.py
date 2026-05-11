"""
Platzi MEGA Scraper v3 — Full Route Download + Resilient
Features:
- Cookie-based auth (no bot-detection issues)
- Discovers all courses from route page
- Scrapes all class m3u8 URLs via network interception
- Downloads with yt-dlp (concurrent fragments)
- Saves progress after each class (resumable)
- Extracts transcripts, downloadable materials
- Generates course_data.json per course
- Hardcoded fallback course list if discovery fails
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, json, re, subprocess, time, random
from pathlib import Path
from playwright.async_api import async_playwright

# ─── CONFIG ──────────────────────────────────────────────────────────────────
ROUTE_URL   = "https://platzi.com/mis-rutas/apps-co/"
CHROME_PATH = "C:/Program Files/Google/Chrome/Application/chrome.exe"
BASE        = Path("E:/Documents/PROYECTOS/AgencIA/platzi_clone")
OUT         = BASE / "downloads"
VID         = OUT / "videos"

# Obfuscation & Proxy Config
PROXY_URL   = None # Example: "http://user:pass@host:port" or "socks5://127.0.0.1:9050"
STEALTH     = True
USE_VPN_CLI = False # Set to True if you want to rotate IP via a local VPN CLI

for d in [OUT, VID]:
    d.mkdir(parents=True, exist_ok=True)

# ─── Fallback course list ─────────────────────────────────────────────────────
FALLBACK_COURSES = [
    {"slug": "fundamentos-arquitectura-software",       "name": "Fundamentos de Arquitectura de Software"},
    {"slug": "pro-arquitectura",                        "name": "Arquitectura Profesional"},
    {"slug": "arquitecturas-limpias",                   "name": "Arquitecturas Limpias"},
    {"slug": "practico-backend",                        "name": "Práctico de Backend"},
    {"slug": "arquitectura-alta-concurrencia",          "name": "Curso de Arquitectura de Alta Concurrencia"},
    {"slug": "arquitectura-frontend",                   "name": "Arquitectura Frontend"},
    {"slug": "arquitecturas-css",                       "name": "Arquitecturas CSS"},
    {"slug": "react-ssr",                               "name": "React SSR"},
    {"slug": "nextjs-jamstack",                         "name": "Next.js Jamstack"},
    {"slug": "jamstack",                                "name": "Introducción a Jamstack"},
    {"slug": "nuxt",                                    "name": "Nuxt.js"},
    {"slug": "astro",                                   "name": "Astro"},
    {"slug": "angular-avanzado",                        "name": "Angular Avanzado"},
    {"slug": "nextjs15",                                "name": "Novedades de Next.js 15"},
    {"slug": "nodejs-microservicios",                   "name": "Node.js Microservicios"},
    {"slug": "go-eventos-cqrs",                         "name": "Go: Eventos y CQRS"},
    {"slug": "go-protobuffers-grpc",                    "name": "Go: Protobuffers y gRPC"},
    {"slug": "nodejs-graphql",                          "name": "Node.js con GraphQL"},
    {"slug": "nodejs-graphql-avanzado",                 "name": "Node.js con GraphQL Avanzado"},
    {"slug": "new-relic",                               "name": "New Relic"},
    {"slug": "ingeniero-observabilidad-newrelic",       "name": "Ingeniería en Observabilidad con New Relic"},
    {"slug": "observabilidad-ai",                       "name": "Observabilidad de Agentes de IA"},
    {"slug": "monorepo",                                "name": "Monorepositorios"},
    {"slug": "cloudflare-workers",                      "name": "Cloudflare Workers"},
]

# ─── Helpers ──────────────────────────────────────────────────────────────────
def safe_name(s, max_len=60):
    return re.sub(r'[^\w\-]', '_', str(s))[:max_len].strip('_') or 'untitled'

def log(msg):
    print(msg, flush=True)

# ─── Load cookies ─────────────────────────────────────────────────────────────
async def load_cookies(ctx):
    cookie_file = OUT / "cookies.json"
    if not cookie_file.exists():
        log("❌ No cookies.json found at " + str(cookie_file))
        return False
    cookies = json.loads(cookie_file.read_text(encoding='utf-8'))
    # Filter to platzi-only and fix sameSite
    platzi = []
    for c in cookies:
        if 'platzi' not in c.get('domain', ''):
            continue
        c.pop('sameSite', None)
        c.pop('storeId', None)
        c.pop('hostOnly', None)
        c.pop('session', None)
        c.pop('id', None)
        c.pop('size', None)
        platzi.append(c)
    await ctx.add_cookies(platzi)
    log(f"  ✅ {len(platzi)} Platzi cookies loaded")
    return True

# ─── Verify auth ──────────────────────────────────────────────────────────────
async def verify_auth(page):
    await page.goto("https://platzi.com/home/", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)
    url = page.url
    logged = 'login' not in url and 'platzi.com' in url
    log(f"  Auth check: {url} → {'✅ Logged in' if logged else '❌ NOT logged in'}")
    return logged

# ─── Discover courses ─────────────────────────────────────────────────────────
async def discover_courses(page):
    log(f"\n[DISCOVER] {ROUTE_URL}")
    try:
        await page.goto(ROUTE_URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        # Scroll to load lazy content
        for _ in range(8):
            await page.evaluate("window.scrollBy(0, 700)")
            await page.wait_for_timeout(600)
    except Exception as e:
        log(f"  ⚠️  Route load error: {e}")
        return []

    # Save HTML for debug
    html = await page.content()
    (OUT / "route_page.html").write_text(html, encoding='utf-8')

    courses = await page.evaluate("""() => {
        const seen = new Set()
        const items = []
        document.querySelectorAll('a[href]').forEach(a => {
            const href = a.href || ''
            const match = href.match(/platzi\\.com\\/cursos?\\/([^/?#]+)/)
            if (match) {
                const slug = match[1]
                if (!seen.has(slug) && slug.length > 3) {
                    seen.add(slug)
                    const text = (a.textContent?.trim() || '').replace(/\\s+/g, ' ').slice(0, 100)
                    items.push({ slug, name: text || slug, url: href })
                }
            }
        })
        return items
    }""")

    log(f"  Discovered {len(courses)} courses")
    for c in courses:
        log(f"    · {c['slug']} — {c['name'][:50]}")

    (OUT / "discovered_courses.json").write_text(
        json.dumps(courses, ensure_ascii=False, indent=2), encoding='utf-8')
    return courses

# ─── Get class list ────────────────────────────────────────────────────────────
async def get_course_classes(page, slug):
    url = f"https://platzi.com/cursos/{slug}/"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2500)
    except Exception as e:
        log(f"  ⚠️  Course page error: {e}")
        return [], slug

    real_url = page.url
    real_slug = slug
    if '/cursos/' in real_url:
        real_slug = real_url.rstrip('/').split('/')[-1]

    # Scroll to trigger lazy load
    for _ in range(4):
        await page.evaluate("window.scrollBy(0, 500)")
        await page.wait_for_timeout(400)

    # Expand accordions
    for sel in ['button[aria-expanded="false"]', '[data-testid="accordion-button"]']:
        try:
            btns = page.locator(sel)
            cnt = await btns.count()
            for i in range(min(cnt, 50)):
                try:
                    await btns.nth(i).click()
                    await page.wait_for_timeout(150)
                except Exception:
                    pass
        except Exception:
            pass

    # Extract all class links
    classes = await page.evaluate("""(slug) => {
        const seen = new Set()
        const items = []

        // Primary: ItemLink class components
        document.querySelectorAll('a[class*="ItemLink"]').forEach(a => {
            const href = a.href || ''
            if (!seen.has(href) && href.includes(slug)) {
                seen.add(href)
                const title = (a.querySelector('h3,h4,[class*="title"],[class*="Title"]')?.textContent
                    || a.textContent || '').trim().replace(/\\s+/g,' ').slice(0,120)
                items.push({ url: href, title })
            }
        })

        // Fallback: any link deeper in the course path
        if (items.length < 2) {
            document.querySelectorAll('a[href]').forEach(a => {
                const href = a.href || ''
                const isClass = (href.includes('/clases/') || href.includes('/clase/') ||
                    (href.includes(`/cursos/${slug}/`) && href.replace(/.*\\/cursos\\/[^\\/]+\\//, '').length > 2))
                if (isClass && !seen.has(href)) {
                    seen.add(href)
                    const text = (a.textContent?.trim() || '').replace(/\\s+/g,' ').slice(0,120)
                    items.push({ url: href, title: text || href.split('/').filter(Boolean).pop() })
                }
            })
        }
        return items
    }""", real_slug)

    return classes, real_slug

# ─── Intercept m3u8 ───────────────────────────────────────────────────────────
async def intercept_m3u8(page, class_url):
    m3u8_list = []

    async def capture(response):
        u = response.url
        if '.m3u8' in u and response.status == 200 and u not in m3u8_list:
            m3u8_list.append(u)

    page.on("response", capture)
    # Add human-like jitter
    await page.wait_for_timeout(random.randint(2000, 5000))
    
    try:
        # Increase timeout and wait for network idle to catch all m3u8s
        await page.goto(class_url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(random.randint(4000, 8000))

        # Human-like interaction: Scroll a bit
        await page.evaluate("window.scrollBy(0, 300)")
        await page.wait_for_timeout(1000)

        # Aggressive Play Button Search
        play_selectors = [
            'video', 
            'button[aria-label*="play" i]', 
            '[class*="play" i]', 
            '[data-testid*="play"]',
            '.vjs-big-play-button',
            'div[class*="PlayButton"]'
        ]
        
        for sel in play_selectors:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible():
                    await el.click(timeout=3000)
                    log(f"        ▶️  Triggered play via: {sel}")
                    await page.wait_for_timeout(3000)
                    break
            except Exception:
                pass

        # Final check: is there a video src?
        vsrc = await page.evaluate("""() => {
            const v = document.querySelector('video')
            if (!v) return ''
            return v.src || v.currentSrc || (v.querySelector('source') ? v.querySelector('source').src : '')
        }""")
        if vsrc and '.m3u8' in vsrc and vsrc not in m3u8_list:
            m3u8_list.append(vsrc)
            
        # Give it a bit more time if still empty
        if not m3u8_list:
            await page.wait_for_timeout(5000)

    except Exception as e:
        log(f"        ⚠️  Intercept error: {e}")
    finally:
        page.remove_listener("response", capture)

    if not m3u8_list:
        log(f"        ❌ No video found for: {class_url}")

    return m3u8_list[0] if m3u8_list else None

# ─── Download video ────────────────────────────────────────────────────────────
def download_video(m3u8_url, dest_path, referer="https://platzi.com/"):
    if dest_path.exists() and dest_path.stat().st_size > 200_000:
        log(f"        ✅ Already exists: {dest_path.name}")
        return True

    cmd = [
        "python", "-m", "yt_dlp",
        m3u8_url,
        "-o", str(dest_path),
        "--no-playlist",
        "--concurrent-fragments", "5",
        "--retries", "15",
        "--fragment-retries", "30",
        "--referer", referer,
        "--add-header", "Origin:https://platzi.com",
        "--add-header", "Accept-Language:es-ES,es;q=0.9",
        "--no-warnings", "-q",
        "--merge-output-format", "mp4",
    ]
    if PROXY_URL:
        cmd.extend(["--proxy", PROXY_URL])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=900, encoding='utf-8')
        if dest_path.exists() and dest_path.stat().st_size > 200_000:
            mb = dest_path.stat().st_size / (1024 * 1024)
            log(f"        ✅ {dest_path.name} ({mb:.1f}MB)")
            return True
        log(f"        ⚠️  yt-dlp failed: {(result.stderr or result.stdout)[:200]}")
        return False
    except subprocess.TimeoutExpired:
        log(f"        ⚠️  Download timeout: {dest_path.name}")
        return False
    except Exception as e:
        log(f"        ⚠️  Download error: {e}")
        return False

# ─── Scrape single class ───────────────────────────────────────────────────────
async def scrape_class(page, cls, real_slug, course_dir, idx):
    url   = cls['url']
    title = cls.get('title', f'clase_{idx}')
    prefix = f"{idx:03d}_{safe_name(title)}"

    log(f"\n      [{idx:03d}] {title[:70]}")
    log(f"        URL: {url}")

    # Intercept m3u8
    m3u8 = await intercept_m3u8(page, url)
    if m3u8:
        log(f"        🎯 m3u8 found")
    else:
        log(f"        ⚠️  No m3u8 found")

    # Extract page text
    text = ""
    try:
        text = await page.evaluate("document.body.innerText")
        txt_path = course_dir / f"{prefix}.txt"
        txt_path.write_text(text[:20000], encoding='utf-8', errors='replace')
    except Exception:
        pass

    # Extract downloadable materials
    downloads = []
    try:
        downloads = await page.evaluate("""() => {
            const links = []
            const seen = new Set()
            document.querySelectorAll('a[href]').forEach(a => {
                const href = a.href || ''
                const t = (a.textContent?.trim() || '').slice(0, 80)
                if (seen.has(href)) return
                if (href.match(/\\.pdf|\\.zip|\\.pptx|\\.xlsx|\\.docx|\\.png|\\.jpg/i) ||
                    t.toLowerCase().includes('descarg') ||
                    t.toLowerCase().includes('material') ||
                    t.toLowerCase().includes('recurso') ||
                    t.toLowerCase().includes('slides') ||
                    t.toLowerCase().includes('presentación')) {
                    seen.add(href)
                    links.push({ url: href, text: t })
                }
            })
            return links
        }""")
    except Exception:
        pass

    result = {
        "index": idx,
        "title": title,
        "url": url,
        "m3u8": m3u8,
        "downloads": downloads,
        "has_content": len(text) > 100,
        "video_file": None,
    }

    # Download video
    if m3u8:
        vid_name = f"{real_slug}_{prefix}.mp4"
        vid_path = VID / vid_name
        success = download_video(m3u8, vid_path, referer=url)
        if success:
            result["video_file"] = vid_name

    return result

# ─── Process one course ────────────────────────────────────────────────────────
async def process_course(page, course, all_data):
    slug = course['slug']
    name = course.get('name', slug)

    log(f"\n{'═'*65}")
    log(f"[CURSO] {name}")
    log(f"  Slug: {slug}")

    course_dir = OUT / safe_name(slug)
    course_dir.mkdir(exist_ok=True)

    # Load existing progress
    data_file = course_dir / "course_data.json"
    if data_file.exists():
        existing = json.loads(data_file.read_text(encoding='utf-8'))
        done_indices = {c['index'] for c in existing.get('classes', []) if c.get('m3u8')}
    else:
        existing = None
        done_indices = set()

    classes, real_slug = await get_course_classes(page, slug)
    log(f"  Classes found: {len(classes)}")

    if not classes and real_slug != slug:
        classes, _ = await get_course_classes(page, real_slug)
        log(f"  Classes (real slug '{real_slug}'): {len(classes)}")

    if not classes:
        log(f"  ⚠️  No classes found for {slug}")
        # Try alternate slug from fallback
        for alt in FALLBACK_COURSES:
            if alt['slug'] != slug and name and alt['name'] == name:
                log(f"  Trying alternate slug: {alt['slug']}")
                classes, real_slug = await get_course_classes(page, alt['slug'])
                if classes:
                    break

    course_data = {
        "slug": slug, "real_slug": real_slug,
        "name": name,
        "url": f"https://platzi.com/cursos/{slug}/",
        "classes": existing['classes'] if existing else [],
        "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    existing_classes = {c['index']: c for c in course_data['classes']}

    for idx, cls in enumerate(classes, 1):
        if idx in done_indices:
            log(f"      [{idx:03d}] ✅ Already done — skipping")
            continue

        res = await scrape_class(page, cls, real_slug, course_dir, idx)

        # Update or append
        existing_classes[idx] = res
        course_data['classes'] = [existing_classes[i] for i in sorted(existing_classes)]

        # Save progress after every class
        data_file.write_text(
            json.dumps(course_data, ensure_ascii=False, indent=2), encoding='utf-8')

    all_data[slug] = course_data
    (OUT / "progress.json").write_text(
        json.dumps(all_data, ensure_ascii=False, indent=2), encoding='utf-8')

    videos = sum(1 for c in course_data['classes'] if c.get('video_file'))
    log(f"\n  ✅ {name}: {len(course_data['classes'])} clases, {videos} videos descargados")
    return course_data

# ─── MAIN ─────────────────────────────────────────────────────────────────────
async def main():
    log("╔══════════════════════════════════════════════════════════════╗")
    log("║         Platzi MEGA Scraper v3 — Full Route Download        ║")
    log("╚══════════════════════════════════════════════════════════════╝")
    log(f"Output: {OUT}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=CHROME_PATH,
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
                "--disable-web-security",
            ]
        )
        # Random User-Agent for obfuscation
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
        ]
        
        # Configure proxy for the context
        context_args = {
            "viewport": {"width": 1400, "height": 900},
            "user_agent": random.choice(user_agents),
        }
        if PROXY_URL:
            context_args["proxy"] = {"server": PROXY_URL}

        ctx = await browser.new_context(**context_args)
        page = await ctx.new_page()

        # Load cookies
        ok = await load_cookies(ctx)
        if not ok:
            log("❌ Cannot proceed without cookies")
            await browser.close()
            return

        # Verify auth
        logged = await verify_auth(page)
        if not logged:
            log("❌ Not authenticated — cookies may be expired. Please refresh cookies.")
            await browser.close()
            return

        # Discover courses
        courses = await discover_courses(page)
        if not courses:
            log("⚠️  Discovery failed — using FALLBACK course list")
            courses = FALLBACK_COURSES

        log(f"\n📚 Total courses to process: {len(courses)}")

        all_data = {}
        # Load existing progress
        progress_file = OUT / "progress.json"
        if progress_file.exists():
            try:
                all_data = json.loads(progress_file.read_text(encoding='utf-8'))
            except Exception:
                pass

        total_classes = 0
        total_videos  = 0

        for i, course in enumerate(courses, 1):
            slug = course['slug']
            
            # Skip if already fully scraped (has classes AND all videos)
            if slug in all_data and len(all_data[slug].get('classes', [])) > 0:
                classes = all_data[slug]['classes']
                # A class is missing if it has no video_file 
                # Exclude readings, quizzes, etc.
                non_video_terms = ['lectura', 'quiz', 'examen', 'recurso', 'guía', 'pdf']
                missing_videos = [
                    c for c in classes 
                    if not c.get('video_file') 
                    and not any(term in c.get('title', '').lower() for term in non_video_terms)
                ]
                
                if not missing_videos and len(classes) > 2:
                    log(f"[{i}/{len(courses)}] Skipping {slug} — 100% Complete")
                    continue
                else:
                    log(f"[{i}/{len(courses)}] ⚠️  {slug} has {len(missing_videos)} missing videos. Re-scanning...")

            log(f"\n[{i}/{len(courses)}] Processing: {course['slug']}")
            try:
                cd = await process_course(page, course, all_data)
                total_classes += len(cd['classes'])
                total_videos  += sum(1 for c in cd['classes'] if c.get('video_file'))
            except Exception as e:
                log(f"  ❌ Course error: {e}")
                # If browser crashed, we should probably stop or restart
                if "Target page, context or browser has been closed" in str(e):
                    log("  🛑 Browser crashed. Aborting run.")
                    break
                continue

        log(f"\n{'═'*65}")
        log(f"[DONE] Scraping completo!")
        log(f"  Cursos:  {len(all_data)}")
        log(f"  Clases:  {total_classes}")
        log(f"  Videos:  {total_videos}")

        summary = {
            "total_courses": len(all_data),
            "total_classes": total_classes,
            "total_videos": total_videos,
            "courses": [{"slug": k, "name": v.get('name'), "classes": len(v.get('classes',[])),
                         "videos": sum(1 for c in v.get('classes',[]) if c.get('video_file'))}
                        for k, v in all_data.items()],
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        (OUT / "final_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        log(f"  Summary saved to {OUT / 'final_summary.json'}")

        await browser.close()

asyncio.run(main())