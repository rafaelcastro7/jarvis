"""
DevCompass Claude Certified Architect Prep — Course Scraper
Conecta al browser abierto via CDP, lee todo el contenido del curso y lo guarda.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright

COURSE_URL  = "https://www.devcompass.ai/course/claude-certified-architect-prep/dashboard"
CHROME_PATH = "C:/Program Files/Google/Chrome/Application/chrome.exe"
OUT = Path("E:/Documents/PROYECTOS/AgencIA/platzi_clone/downloads/devcompass")
OUT.mkdir(parents=True, exist_ok=True)

def safe_name(s, max_len=80):
    return re.sub(r'[^\w\-]', '_', s)[:max_len].strip('_') or 'untitled'

async def try_cdp(p):
    """Intenta conectar al browser ya abierto."""
    for port in [9222, 9223, 9876]:
        try:
            b = await p.chromium.connect_over_cdp(f"http://localhost:{port}")
            print(f"✅ CDP conectado en puerto {port}")
            return b
        except Exception:
            pass
    return None

async def launch_browser(p):
    return await p.chromium.launch(
        executable_path=CHROME_PATH,
        headless=False,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--start-maximized"]
    )

async def get_page(browser):
    """Obtiene o crea una página."""
    for ctx in browser.contexts:
        for pg in ctx.pages:
            return pg, ctx
    ctx = browser.contexts[0] if browser.contexts else await browser.new_context(
        viewport={"width":1400,"height":900},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    return await ctx.new_page(), ctx

async def extract_lessons(page):
    """Extrae todos los links de lecciones del sidebar."""
    lessons = await page.evaluate("""() => {
        const items = []
        const seen = new Set()
        // Buscar links del sidebar/curriculum
        const selectors = [
            'a[href*="/lesson/"]',
            'a[href*="/lecture/"]',
            'a[href*="/module/"]',
            'a[href*="/section/"]',
            '[class*="curriculum"] a[href]',
            '[class*="sidebar"] a[href]',
            '[class*="lesson"] a[href]',
            '[class*="course"] a[href]',
            'nav a[href]',
        ]
        selectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(a => {
                const href = a.href || ''
                const text = (a.textContent?.trim() || '').replace(/\\s+/g, ' ').slice(0, 120)
                if (href && !seen.has(href) && text) {
                    seen.add(href)
                    items.push({ url: href, title: text })
                }
            })
        })
        return items
    }""")
    return lessons

async def read_lesson(page, url, title, idx):
    """Lee el contenido de una lección."""
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(3000)

    # Scroll to load all content
    for _ in range(4):
        await page.evaluate("window.scrollBy(0, 600)")
        await page.wait_for_timeout(400)

    # Get text content
    text = await page.evaluate("""() => {
        // Remove nav/header/footer noise
        ['nav','header','footer','[class*="nav"]','[class*="header"]','[class*="sidebar"]'].forEach(sel => {
            document.querySelectorAll(sel).forEach(el => el.remove())
        })
        return document.body.innerText
    }""")

    # Get all questions/answers if it's a quiz
    quiz = await page.evaluate("""() => {
        const qs = []
        document.querySelectorAll('[class*="question"], [class*="quiz"], [class*="exam"]').forEach(el => {
            qs.push(el.innerText?.trim())
        })
        return qs
    }""")

    # Screenshot
    ss_path = OUT / f"{idx:03d}_{safe_name(title)}.png"
    try:
        await page.screenshot(path=str(ss_path), full_page=True)
    except Exception:
        pass

    content = {
        "index": idx,
        "title": title,
        "url": url,
        "text": text[:20000],
        "quiz_items": quiz,
        "has_video": bool(await page.evaluate("() => !!document.querySelector('video, iframe[src*=\"youtube\"], iframe[src*=\"vimeo\"], iframe[src*=\"loom\"]')")),
    }

    # Save individual lesson
    lesson_file = OUT / f"{idx:03d}_{safe_name(title)}.txt"
    lesson_file.write_text(f"# {title}\nURL: {url}\n\n{text[:20000]}", encoding='utf-8')

    print(f"  [{idx:03d}] {title[:60]} — {len(text)} chars {'📹' if content['has_video'] else '📄'}")
    return content

async def main():
    print("[DevCompass] Claude Certified Architect Prep Scraper")
    print(f"Output: {OUT}")

    async with async_playwright() as p:
        # Try CDP first
        browser = await try_cdp(p)
        cdp_mode = browser is not None

        if not cdp_mode:
            print("CDP no disponible — abriendo browser nuevo")
            browser = await launch_browser(p)
            ctx = await browser.new_context(
                viewport={"width":1400,"height":900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await ctx.new_page()
        else:
            page, ctx = await get_page(browser)

        # Navigate to course
        print(f"\n[1] Navegando al curso...")
        await page.goto(COURSE_URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(4000)
        print(f"  URL: {page.url}")
        print(f"  Título: {await page.title()}")

        # Take screenshot of dashboard
        await page.screenshot(path=str(OUT / "00_dashboard.png"), full_page=False)

        # Get full page text for overview
        overview = await page.evaluate("document.body.innerText")
        (OUT / "00_overview.txt").write_text(overview[:30000], encoding='utf-8')
        print(f"  Overview: {len(overview)} chars")

        # Scroll to load lazy content
        for _ in range(6):
            await page.evaluate("window.scrollBy(0, 800)")
            await page.wait_for_timeout(600)

        # Extract lessons
        print("\n[2] Extrayendo lecciones...")
        lessons = await extract_lessons(page)
        print(f"  Lecciones encontradas: {len(lessons)}")

        # Save lesson list
        (OUT / "lesson_list.json").write_text(
            json.dumps(lessons, ensure_ascii=False, indent=2), encoding='utf-8')

        if not lessons:
            # Save HTML for debugging
            html = await page.content()
            (OUT / "debug_dashboard.html").write_text(html, encoding='utf-8')
            print("  ⚠️  No se encontraron lecciones — HTML guardado para debug")
            print(f"\n  Texto de la página:")
            print(overview[:3000])

        # Read each lesson
        all_content = []
        for idx, lesson in enumerate(lessons, 1):
            try:
                content = await read_lesson(page, lesson['url'], lesson['title'], idx)
                all_content.append(content)
            except Exception as e:
                print(f"  ⚠️  Error en lección {idx}: {e}")

            # Save progress
            (OUT / "all_content.json").write_text(
                json.dumps(all_content, ensure_ascii=False, indent=2), encoding='utf-8')

        # Generate study guide
        print("\n[3] Generando guía de estudio...")
        guide_lines = ["# Claude Certified Architect Prep — Guía de Estudio\n"]
        for item in all_content:
            guide_lines.append(f"\n## Lección {item['index']}: {item['title']}")
            guide_lines.append(f"URL: {item['url']}")
            if item.get('quiz_items'):
                guide_lines.append("\n### Preguntas:")
                for q in item['quiz_items']:
                    guide_lines.append(f"- {q[:200]}")
            guide_lines.append(f"\n{item['text'][:3000]}\n---")

        guide = '\n'.join(guide_lines)
        (OUT / "STUDY_GUIDE.md").write_text(guide, encoding='utf-8')

        print(f"\n[DONE]")
        print(f"  Lecciones: {len(all_content)}")
        print(f"  Output: {OUT}")

        if not cdp_mode:
            print("⏳ Browser abierto 30s...")
            await page.wait_for_timeout(30000)
            await browser.close()

asyncio.run(main())
