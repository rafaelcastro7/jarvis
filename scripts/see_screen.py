"""Ve la pantalla actual y lee el contenido de la lección activa."""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, re
from pathlib import Path
from playwright.async_api import async_playwright

OUT = Path("E:/Documents/PROYECTOS/AgencIA/platzi_clone/downloads/devcompass/live")
OUT.mkdir(parents=True, exist_ok=True)

async def main():
    async with async_playwright() as p:
        browser = None
        for port in [9222, 9223, 9224]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://localhost:{port}")
                print(f"CDP OK port {port}")
                break
            except Exception as e:
                print(f"Port {port}: {e}")
        if not browser:
            print("NO CDP"); return

        # Find devcompass tab
        page = None
        for c in browser.contexts:
            for pg in c.pages:
                print(f"  Tab: {pg.url[:80]}")
                if 'devcompass' in pg.url:
                    page = pg
                    break
            if page: break
        if not page:
            # Use first available page
            for c in browser.contexts:
                if c.pages:
                    page = c.pages[0]; break

        if not page:
            print("No page found"); return

        print(f"\nActive page: {page.url}")

        # Screenshot
        ss = str(OUT / "current.png")
        await page.screenshot(path=ss, full_page=False)
        print(f"Screenshot: {ss}")

        # Read content - main area only (skip sidebar)
        content = await page.evaluate("""() => {
            const body = document.body.innerText
            return body
        }""")
        print(f"\n=== PAGE TEXT ===\n{content[:4000]}")

        # Get current lesson number
        prog = re.search(r'(\d+)/70', content)
        lesson_match = re.search(r'LESSON (\\d+)', content)
        print(f"\nProgress: {prog.group(0) if prog else '?'}")
        print(f"Current lesson: {lesson_match.group(1) if lesson_match else '?'}")

        # Get interactive elements
        els = await page.evaluate("""() => {
            const radios = Array.from(document.querySelectorAll('input[type=radio]')).map((r,i) => ({
                i, label: (r.closest('label')?.innerText || r.value || '').trim().slice(0,150), checked: r.checked
            }))
            const textareas = Array.from(document.querySelectorAll('textarea')).map((t,i) => ({
                i, placeholder: t.placeholder, value: t.value.slice(0,100)
            }))
            const buttons = Array.from(document.querySelectorAll('button')).filter(b => {
                const t = b.textContent?.trim() || ''
                const r = b.getBoundingClientRect()
                return r.x > 250 && t.length > 2 && t.length < 80 && !t.match(/^\\d+/)
            }).map(b => b.textContent?.trim())
            return { radios, textareas, buttons }
        }""")
        print(f"\nRadios: {els['radios']}")
        print(f"Textareas: {els['textareas']}")
        print(f"Action buttons: {els['buttons']}")

asyncio.run(main())
