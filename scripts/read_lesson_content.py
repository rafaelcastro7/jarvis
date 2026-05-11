"""Lee el contenido real de la lección actual (después del sidebar)."""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, json, re
from playwright.async_api import async_playwright

LESSON = int(sys.argv[1]) if len(sys.argv) > 1 else 28
ACTION = sys.argv[2] if len(sys.argv) > 2 else "read"  # read | answer N | submit | next

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
            await page.goto("https://www.devcompass.ai/course/claude-certified-architect-prep/dashboard",
                           wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(5000)

        if ACTION == "read" or ACTION == "goto":
            # Click lesson
            clicked = await page.evaluate(f"""() => {{
                for (const btn of document.querySelectorAll('button')) {{
                    const t = (btn.textContent||'').replace(/\\s+/g,' ').trim()
                    if (t.match(/^{LESSON}[^0-9]/)) {{
                        btn.click()
                        return t.slice(0,80)
                    }}
                }}
                return null
            }}""")
            print(f"Clicked: {clicked}")
            await page.wait_for_timeout(3000)

            # Click Walkthrough tab
            for tab in ["Walkthrough", "Notes"]:
                try:
                    btn = page.locator(f'button:has-text("{tab}")').first
                    if await btn.count() > 0 and await btn.is_visible():
                        await btn.click()
                        await page.wait_for_timeout(2000)
                        print(f"Tab: {tab}")
                        break
                except Exception:
                    pass

            # Get full page text and extract content after sidebar
            full_text = await page.evaluate("document.body.innerText")

            # The sidebar ends with "Capstone: Stage 5 Final Capstone"
            # Content starts after that
            sidebar_end_markers = [
                "Capstone: Stage 5 Final Capstone",
                "MAKE IT TRUSTWORTHY UNDER PRESSURE",
                "Human Review Routing",
            ]
            content_start = 0
            for marker in sidebar_end_markers:
                idx = full_text.find(marker)
                if idx > 0:
                    content_start = idx + len(marker)
                    break

            lesson_content = full_text[content_start:content_start+8000].strip()
            prog = re.search(r'(\d+)/70', full_text)

            print(f"\nProgress: {prog.group(0) if prog else '?'}")
            print(f"\n=== LESSON {LESSON} CONTENT ===")
            print(lesson_content[:5000])

            # Get interactive elements
            state = await page.evaluate("""() => {
                const radios = Array.from(document.querySelectorAll('input[type=radio]')).map((r,i)=>({
                    i, label:(r.closest('label')?.innerText||r.value||'').trim().slice(0,200),
                    checked: r.checked
                }))
                const textareas = Array.from(document.querySelectorAll('textarea')).map((t,i)=>({
                    i, placeholder:t.placeholder, value:t.value.slice(0,100),
                    label:(t.closest('[class]')?.querySelector('h3,h4,p,label')?.innerText||'').trim().slice(0,200)
                }))
                const btns = Array.from(document.querySelectorAll('button')).filter(b=>{
                    const r = b.getBoundingClientRect()
                    const t = (b.textContent||'').trim()
                    return r.x > 250 && !b.disabled && !b.title?.includes('Complete') &&
                           t.length > 2 && t.length < 80 && !t.match(/^\\d/)
                }).map(b => (b.textContent||'').trim())
                return {radios, textareas, btns}
            }""")
            print(f"\nRadios: {json.dumps(state['radios'], ensure_ascii=False)}")
            print(f"Textareas: {json.dumps(state['textareas'], ensure_ascii=False)}")
            print(f"Active buttons: {state['btns']}")

        elif ACTION == "answer":
            idx = int(sys.argv[3]) if len(sys.argv) > 3 else 0
            await page.evaluate(f"""() => {{
                const r = document.querySelectorAll('input[type=radio]')[{idx}]
                if (r) r.click()
            }}""")
            await page.wait_for_timeout(500)
            print(f"Selected radio {idx}")

        elif ACTION == "fill":
            text = sys.argv[3] if len(sys.argv) > 3 else ""
            await page.evaluate(f"""() => {{
                const ta = document.querySelector('textarea')
                if (ta) {{
                    Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value')
                        .set.call(ta, {json.dumps(text)})
                    ta.dispatchEvent(new Event('input', {{bubbles:true}}))
                    ta.dispatchEvent(new Event('change', {{bubbles:true}}))
                }}
            }}""")
            print(f"Filled textarea")

        elif ACTION == "submit":
            for txt in ["Submit Answer", "Submit", "Check Answer", "Submit code"]:
                try:
                    btn = page.locator(f'button:has-text("{txt}")').first
                    if await btn.count() > 0 and await btn.is_visible():
                        await btn.click()
                        await page.wait_for_timeout(2500)
                        print(f"Submitted: {txt}")
                        break
                except Exception:
                    pass
            # Read result
            body = await page.evaluate("document.body.innerText")
            prog = re.search(r'(\d+)/70', body)
            correct = "Correct" in body or "✓" in body
            wrong = "Incorrect" in body or "Wrong" in body or "Try again" in body
            print(f"Progress: {prog.group(0) if prog else '?'} | Correct: {correct} | Wrong: {wrong}")

        elif ACTION == "next":
            for txt in ["Next Lesson", "Next", "Completed"]:
                try:
                    btn = page.locator(f'button:has-text("{txt}"):not([disabled])').first
                    if await btn.count() > 0:
                        await btn.click()
                        await page.wait_for_timeout(3000)
                        print(f"Clicked: {txt}")
                        break
                except Exception as e:
                    print(f"  {txt}: {e}")

asyncio.run(main())
