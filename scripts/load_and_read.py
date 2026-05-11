"""Carga el curso y lee el estado completo."""
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
            ctx = b.contexts[0] if b.contexts else await b.new_context()
            page = await ctx.new_page()

        print(f"URL: {page.url}")

        # Go to dashboard and wait for full load
        await page.goto(
            "https://www.devcompass.ai/course/claude-certified-architect-prep/dashboard",
            wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(5000)

        # Check if loaded
        body = await page.evaluate("document.body.innerText")
        print(f"Body length: {len(body)}")
        print(f"Preview: {body[:300]}")

        # Find and click lesson button
        print(f"\nLooking for lesson {LESSON}...")
        found = await page.evaluate(f"""() => {{
            const all = Array.from(document.querySelectorAll('button, [role=button], li[class], div[class]'))
            for (const el of all) {{
                const t = (el.textContent||'').trim().replace(/\\s+/g,' ')
                // Match "28" at start followed by lesson title text
                if (t.startsWith('{LESSON}') || t.startsWith('{LESSON} ') || t.match(/^{LESSON}[^0-9]/)) {{
                    el.scrollIntoView({{block:'center'}})
                    el.click()
                    return 'clicked: ' + t.slice(0,80)
                }}
            }}
            // Try anchor tags too
            for (const a of document.querySelectorAll('a')) {{
                const t = (a.textContent||'').trim()
                if (t.startsWith('{LESSON}') && t.length < 100) {{
                    a.click()
                    return 'clicked a: ' + t.slice(0,60)
                }}
            }}
            return 'not found'
        }}""")
        print(f"Click result: {found}")
        await page.wait_for_timeout(4000)

        # Read current content
        content = await page.evaluate("document.body.innerText")
        prog = re.search(r'(\d+)/70', content)
        print(f"\nProgress: {prog.group(0) if prog else '?'}")
        print(f"\nContent:\n{content[content.find('LESSON'):content.find('LESSON')+3000] if 'LESSON' in content else content[:3000]}")

        # Interactive elements
        radios = await page.evaluate("""() =>
            Array.from(document.querySelectorAll('input[type=radio]')).map((r,i)=>({
                i, label:(r.closest('label')?.innerText||r.value||'').trim().slice(0,200), checked:r.checked
            }))
        """)
        textareas = await page.evaluate("""() =>
            Array.from(document.querySelectorAll('textarea')).map((t,i)=>({
                i, value:t.value, placeholder:t.placeholder
            }))
        """)
        btns = await page.evaluate("""() =>
            Array.from(document.querySelectorAll('button')).map((b,i)=>({
                i, text:(b.textContent||'').trim().slice(0,60), disabled:b.disabled,
                x:Math.round(b.getBoundingClientRect().x)
            })).filter(b=>b.text.length>0)
        """)
        print(f"\nRadios: {json.dumps(radios[:5], ensure_ascii=False)}")
        print(f"Textareas: {textareas}")
        print(f"Buttons ({len(btns)}): {[(b['i'],b['text'][:40]) for b in btns if b['x']>250][:10]}")

asyncio.run(main())
