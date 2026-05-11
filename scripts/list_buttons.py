"""Lista todos los botones de la página para entender el sidebar."""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://localhost:9222")
        page = None
        for c in b.contexts:
            for pg in c.pages:
                if "devcompass" in pg.url:
                    page = pg; break
            if page: break
        if not page:
            print("No page"); return

        # Navigate to dashboard fresh
        await page.goto(
            "https://www.devcompass.ai/course/claude-certified-architect-prep/dashboard",
            wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(4000)

        # List ALL buttons
        btns = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('button')).map((b,i) => ({
                i: i,
                text: (b.textContent||'').trim().replace(/\\s+/g,' ').slice(0,80),
                disabled: b.disabled,
                x: Math.round(b.getBoundingClientRect().x)
            })).filter(b => b.text.length > 0)
        }""")

        print(f"Total buttons: {len(btns)}")
        for btn in btns:
            mark = "❌" if btn['disabled'] else "✅"
            print(f"  [{btn['i']:3d}] x={btn['x']:4d} {mark} {btn['text']}")

asyncio.run(main())
