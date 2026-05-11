"""
DevCompass Claude Certified Architect Prep — Scraper v2
SPA React — espera render completo, navega por módulos manualmente.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright

COURSE_URL  = "https://www.devcompass.ai/course/claude-certified-architect-prep/dashboard"
OUT = Path("E:/Documents/PROYECTOS/AgencIA/platzi_clone/downloads/devcompass")
OUT.mkdir(parents=True, exist_ok=True)

def safe_name(s, max_len=80):
    return re.sub(r'[^\w\-]', '_', s)[:max_len].strip('_') or 'untitled'

async def main():
    print("[DevCompass v2] Claude Certified Architect Prep")
    print(f"Output: {OUT}")

    async with async_playwright() as p:
        # Connect to existing browser
        browser = None
        for port in [9222, 9223]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://localhost:{port}")
                print(f"✅ CDP port {port}")
                break
            except Exception:
                pass

        if not browser:
            print("❌ No CDP — necesitas tener Chrome abierto con --remote-debugging-port=9222")
            return

        page, ctx = None, None
        for c in browser.contexts:
            for pg in c.pages:
                page = pg
                ctx = c
                break
            if page:
                break
        if not page:
            ctx = browser.contexts[0]
            page = await ctx.new_page()

        # Navigate to course
        print(f"\n[1] Navegando...")
        await page.goto(COURSE_URL, wait_until="networkidle", timeout=45000)
        await page.wait_for_timeout(5000)
        print(f"  URL: {page.url}")

        # Wait for SPA to render
        try:
            await page.wait_for_selector('[class*="course"], [class*="lesson"], [class*="module"], main, [role="main"]',
                                         timeout=15000)
        except Exception:
            pass
        await page.wait_for_timeout(3000)

        # Screenshot
        await page.screenshot(path=str(OUT / "01_loaded.png"), full_page=False)

        # Get full text after render
        text = await page.evaluate("document.body.innerText")
        (OUT / "01_text.txt").write_text(text[:30000], encoding='utf-8')
        print(f"  Texto: {len(text)} chars")
        print(f"  Preview:\n{text[:2000]}")

        # Save full HTML
        html = await page.content()
        (OUT / "01_html.html").write_text(html, encoding='utf-8')

        # Extract ALL links from the loaded SPA
        all_links = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a[href]')).map(a => ({
                href: a.href,
                text: (a.textContent?.trim() || '').replace(/\\s+/g, ' ').slice(0, 100)
            })).filter(l => l.href && l.text)
        }""")
        print(f"\n  Links encontrados: {len(all_links)}")
        for l in all_links[:30]:
            print(f"    {l['href'][:80]} | {l['text'][:50]}")

        (OUT / "links.json").write_text(json.dumps(all_links, ensure_ascii=False, indent=2), encoding='utf-8')

        # Extract clickable items that look like lessons
        clickables = await page.evaluate("""() => {
            const items = []
            // Buscar elementos con texto que parezcan lecciones
            const keywords = ['lesson', 'module', 'section', 'quiz', 'intro', 'overview', 'part']
            document.querySelectorAll('button, [role="button"], li, [class*="item"], [class*="card"]').forEach(el => {
                const text = (el.textContent?.trim() || '').replace(/\\s+/g, ' ').slice(0, 100)
                if (text.length > 3 && text.length < 200) {
                    const rect = el.getBoundingClientRect()
                    if (rect.width > 0 && rect.height > 0) {
                        items.push({
                            tag: el.tagName,
                            text,
                            class: (el.className || '').slice(0, 60),
                            x: Math.round(rect.x),
                            y: Math.round(rect.y)
                        })
                    }
                }
            })
            return items.slice(0, 50)
        }""")
        print(f"\n  Elementos clickables: {len(clickables)}")
        for c in clickables[:20]:
            print(f"    [{c['tag']}] {c['text'][:60]}")

        (OUT / "clickables.json").write_text(json.dumps(clickables, ensure_ascii=False, indent=2), encoding='utf-8')

        # Scroll through page capturing all text
        print("\n[2] Scrolling para capturar todo el contenido...")
        full_text_parts = [text]
        for scroll_y in range(0, 8000, 600):
            await page.evaluate(f"window.scrollTo(0, {scroll_y})")
            await page.wait_for_timeout(300)
            t = await page.evaluate("document.body.innerText")
            full_text_parts.append(t)

        # Save consolidated content
        final_text = '\n'.join(set(full_text_parts))
        (OUT / "FULL_CONTENT.txt").write_text(final_text[:50000], encoding='utf-8')

        # Take full page screenshot
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(500)
        await page.screenshot(path=str(OUT / "02_full.png"), full_page=True)

        print(f"\n[DONE] Archivos en {OUT}")
        print(f"  - 01_text.txt — texto de la página")
        print(f"  - links.json — todos los links")
        print(f"  - clickables.json — elementos interactivos")
        print(f"  - FULL_CONTENT.txt — contenido completo")

asyncio.run(main())
