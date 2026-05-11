"""Navega a una lección específica y lee su contenido completo."""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright

TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 28
OUT = Path("E:/Documents/PROYECTOS/AgencIA/platzi_clone/downloads/devcompass/live")
OUT.mkdir(parents=True, exist_ok=True)

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
            print("No devcompass page found"); return

        print(f"Navegando a lección {TARGET}...")

        # Click sidebar button for target lesson
        result = await page.evaluate(f"""() => {{
            let clicked = false
            document.querySelectorAll('button').forEach(btn => {{
                const text = (btn.textContent || '').trim().replace(/\\s+/g, ' ')
                const match = text.match(/^({TARGET})\\s+(.+)/)
                if (match && !clicked) {{
                    btn.scrollIntoView({{block: 'center'}})
                    btn.click()
                    clicked = true
                    return match[2].trim()
                }}
            }})
            return clicked
        }}""")
        print(f"Clicked: {result}")
        await page.wait_for_timeout(3000)

        # Read lesson content (wait for it to load)
        for attempt in range(3):
            content = await page.evaluate("""() => {
                const lesson = document.body.innerText.match(/LESSON \\d+\\n[\\s\\S]{50,}/)?.[0] || ''
                return lesson.slice(0, 5000)
            }""")
            if len(content) > 200:
                break
            await page.wait_for_timeout(1500)

        full_text = await page.evaluate("document.body.innerText")
        prog = re.search(r'(\d+)/70', full_text)
        lesson_header = re.search(r'LESSON (\d+)\n(.+)', full_text)

        print(f"\nProgress: {prog.group(0) if prog else '?'}")
        print(f"Lesson: {lesson_header.group(1) if lesson_header else '?'} — {lesson_header.group(2).strip() if lesson_header else '?'}")

        # Get content area
        content_els = await page.evaluate("""() => {
            const texts = []
            document.querySelectorAll('p,h2,h3,h4,li,pre,blockquote').forEach(el => {
                const r = el.getBoundingClientRect()
                const t = (el.innerText || '').trim()
                if (r.x > 280 && t.length > 20) texts.push(t)
            })
            return texts.join('\\n')
        }""")
        print(f"\n--- CONTENIDO ---\n{content_els[:4000]}\n---")

        # Interactive elements
        radios = await page.evaluate("""() =>
            Array.from(document.querySelectorAll('input[type=radio]')).map((r,i)=>({
                i, label:(r.closest('label')?.innerText||r.value||'').trim().slice(0,200), checked:r.checked
            }))
        """)
        textareas = await page.evaluate("""() =>
            Array.from(document.querySelectorAll('textarea')).map((t,i)=>({
                i, placeholder:t.placeholder, value:t.value,
                label:(t.parentElement?.parentElement?.querySelector('h3,h4,p')?.innerText||'').trim().slice(0,200)
            }))
        """)
        btns = await page.evaluate("""() =>
            Array.from(document.querySelectorAll('button')).filter(b=>{
                const r=b.getBoundingClientRect()
                const t=(b.textContent||'').trim()
                const disabled = b.disabled || b.title?.includes('Complete')
                return r.x>250 && t.length>2 && t.length<80 && !t.match(/^\\d+/) && !disabled
            }).map(b=>({text:(b.textContent||'').trim(), disabled:b.disabled}))
        """)

        print(f"\nRadios: {json.dumps(radios, ensure_ascii=False)}")
        print(f"Textareas: {json.dumps(textareas, ensure_ascii=False)}")
        print(f"Active buttons: {[b['text'] for b in btns]}")

        # Screenshot
        await page.screenshot(path=str(OUT / f"lesson_{TARGET:02d}.png"), full_page=False)
        print(f"\n📸 Screenshot saved")

asyncio.run(main())
