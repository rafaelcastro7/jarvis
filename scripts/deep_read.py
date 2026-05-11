"""Lee el contenido real incluyendo iframes."""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, json, re
from playwright.async_api import async_playwright

LESSON = int(sys.argv[1]) if len(sys.argv) > 1 else 28

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
            print("No devcompass page"); return

        print(f"Page URL: {page.url}")

        # Click the lesson
        clicked = await page.evaluate(f"""() => {{
            const btns = Array.from(document.querySelectorAll('button'))
            for (const btn of btns) {{
                const t = (btn.textContent||'').replace(/\\s+/g,' ').trim()
                if (t.match(/^{LESSON}[^0-9]/)) {{
                    btn.click()
                    return t.slice(0,80)
                }}
            }}
            return null
        }}""")
        print(f"Clicked: {clicked}")
        await page.wait_for_timeout(5000)

        # Check URL change
        print(f"URL after: {page.url}")

        # Check all frames
        frames = page.frames
        print(f"\nFrames: {len(frames)}")
        for i, frame in enumerate(frames):
            try:
                frame_text = await frame.evaluate("document.body?.innerText || ''")
                if len(frame_text) > 100:
                    print(f"\n[Frame {i}] URL: {frame.url[:80]}")
                    print(f"Content: {frame_text[:500]}")
            except Exception as e:
                print(f"[Frame {i}] Error: {e}")

        # Get shadow DOM content too
        shadow_content = await page.evaluate("""() => {
            function getTextFromShadow(root) {
                let text = ''
                root.querySelectorAll('*').forEach(el => {
                    if (el.shadowRoot) text += getTextFromShadow(el.shadowRoot)
                    else if (el.children.length === 0) text += (el.textContent||'').trim() + '\\n'
                })
                return text
            }
            return getTextFromShadow(document.body)
        }""")

        # Find the main content area
        content = await page.evaluate("""() => {
            // Try various content selectors
            const selectors = [
                '[class*="lesson-content"]',
                '[class*="walkthrough"]',
                'main article',
                '[class*="prose"]',
                '[class*="markdown"]',
                '[class*="content"] > div',
                'section',
                'article'
            ]
            for (const sel of selectors) {
                const el = document.querySelector(sel)
                if (el && el.innerText?.length > 200) {
                    return {selector: sel, text: el.innerText.trim().slice(0, 2000)}
                }
            }
            // Get biggest text block
            let biggest = {text: '', len: 0}
            document.querySelectorAll('div, section').forEach(el => {
                const t = el.innerText?.trim() || ''
                const r = el.getBoundingClientRect()
                if (r.x > 250 && r.width > 400 && t.length > biggest.len) {
                    biggest = {text: t, len: t.length, selector: el.className?.slice(0,40)}
                }
            })
            return biggest
        }""")

        print(f"\nMain content:\n{json.dumps(content, ensure_ascii=False, indent=2)}")

        # What does the sidebar show as current?
        active = await page.evaluate("""() => {
            // Find active/selected lesson in sidebar
            const active = document.querySelector('[class*="active"], [class*="current"], [aria-selected="true"]')
            return active ? active.textContent?.trim()?.slice(0,100) : 'not found'
        }""")
        print(f"\nActive lesson: {active}")

        # Screenshot
        await page.screenshot(path=f"E:/Documents/PROYECTOS/AgencIA/platzi_clone/downloads/devcompass/live/lesson_{LESSON:02d}_deep.png")
        print("\n📸 Screenshot saved")

asyncio.run(main())
