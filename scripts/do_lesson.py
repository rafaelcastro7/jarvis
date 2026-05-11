"""
Completa UNA lección: click Next Lesson, lee contenido, responde si hay pregunta.
Uso: python do_lesson.py [action]
action: next | read | answer N | submit | screenshot
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, re, json
from pathlib import Path
from playwright.async_api import async_playwright

OUT = Path("E:/Documents/PROYECTOS/AgencIA/platzi_clone/downloads/devcompass/live")
OUT.mkdir(parents=True, exist_ok=True)

ACTION = sys.argv[1] if len(sys.argv) > 1 else "read"
PARAM  = sys.argv[2] if len(sys.argv) > 2 else ""

async def get_page():
    p = await async_playwright().start()
    for port in [9222, 9223]:
        try:
            b = await p.chromium.connect_over_cdp(f"http://localhost:{port}")
            for c in b.contexts:
                for pg in c.pages:
                    if 'devcompass' in pg.url:
                        return p, b, pg
            # fallback first page
            for c in b.contexts:
                if c.pages:
                    return p, b, c.pages[0]
        except Exception:
            pass
    return p, None, None

async def read_lesson(page):
    text = await page.evaluate("""() => document.body.innerText""")
    prog = re.search(r'(\d+)/70', text)
    lesson = re.search(r'LESSON (\d+)\n(.+)', text)

    # Get content area only (right of sidebar)
    content = await page.evaluate("""() => {
        const els = []
        document.querySelectorAll('p,h1,h2,h3,h4,li,pre,code').forEach(el => {
            const r = el.getBoundingClientRect()
            const t = el.innerText?.trim() || ''
            if (r.x > 280 && r.width > 200 && t.length > 10) els.push(t)
        })
        return els.join('\\n')
    }""")

    radios = await page.evaluate("""() =>
        Array.from(document.querySelectorAll('input[type=radio]')).map((r,i)=>({
            i, label:(r.closest('label')?.innerText||r.value||'').trim().slice(0,200),
            checked:r.checked
        }))
    """)

    textareas = await page.evaluate("""() =>
        Array.from(document.querySelectorAll('textarea')).map((t,i)=>({
            i, placeholder:t.placeholder, value:t.value,
            label:(t.closest('[class]')?.querySelector('h3,h4,p,label')?.innerText||'').trim().slice(0,200)
        }))
    """)

    btns = await page.evaluate("""() =>
        Array.from(document.querySelectorAll('button')).filter(b=>{
            const r=b.getBoundingClientRect()
            const t=(b.textContent||'').trim()
            return r.x>250 && t.length>2 && t.length<80 && !t.match(/^\\d+/)
        }).map(b=>(b.textContent||'').trim())
    """)

    return {
        'progress': prog.group(0) if prog else '?',
        'lesson_num': lesson.group(1) if lesson else '?',
        'lesson_title': lesson.group(2).strip() if lesson else '?',
        'content': content[:3000],
        'radios': radios,
        'textareas': textareas,
        'buttons': btns
    }

async def main():
    p, browser, page = await get_page()
    if not page:
        print("❌ No page"); return

    if ACTION == "screenshot":
        await page.screenshot(path=str(OUT / "current.png"))
        print("📸 saved")

    elif ACTION == "next":
        # Click Next Lesson
        clicked = False
        for txt in ["Next Lesson", "Next", "Continue"]:
            try:
                btn = page.locator(f'button:has-text("{txt}")').first
                if await btn.count() > 0 and await btn.is_visible():
                    await btn.click()
                    await page.wait_for_timeout(3000)
                    print(f"✅ Clicked: {txt}")
                    clicked = True
                    break
            except Exception:
                pass
        if not clicked:
            print("⚠️ No Next button found")
        state = await read_lesson(page)
        print(f"\nProgress: {state['progress']}")
        print(f"Lesson: {state['lesson_num']} — {state['lesson_title']}")
        print(f"Content ({len(state['content'])} chars):\n{state['content'][:2000]}")
        print(f"\nRadios: {json.dumps(state['radios'], ensure_ascii=False)}")
        print(f"Textareas: {[t['label'][:80] for t in state['textareas']]}")
        print(f"Buttons: {state['buttons']}")

    elif ACTION == "read":
        state = await read_lesson(page)
        print(f"Progress: {state['progress']}")
        print(f"Lesson: {state['lesson_num']} — {state['lesson_title']}")
        print(f"\nContent:\n{state['content'][:3000]}")
        print(f"\nRadios: {json.dumps(state['radios'], ensure_ascii=False)}")
        print(f"Textareas: {json.dumps(state['textareas'], ensure_ascii=False)}")
        print(f"Buttons: {state['buttons']}")

    elif ACTION == "answer":
        idx = int(PARAM) if PARAM else 0
        await page.evaluate(f"""() => {{
            const r = document.querySelectorAll('input[type=radio]')[{idx}]
            if (r) r.click()
        }}""")
        await page.wait_for_timeout(500)
        print(f"✅ Selected radio {idx}")

    elif ACTION == "submit":
        for txt in ["Submit Answer", "Submit", "Check Answer"]:
            try:
                btn = page.locator(f'button:has-text("{txt}")').first
                if await btn.count() > 0 and await btn.is_visible():
                    await btn.click()
                    await page.wait_for_timeout(2000)
                    print(f"✅ Submitted: {txt}")
                    break
            except Exception:
                pass
        # Read result
        result = await page.evaluate("""() => {
            const t = document.body.innerText
            const correct = t.includes('✓') || t.includes('Correct')
            const incorrect = t.includes('Incorrect') || t.includes('Wrong') || t.includes('Try again')
            return {correct, incorrect, progress: t.match(/\\d+\\/70/)?.[0] || '?'}
        }""")
        print(f"Result: {result}")

    elif ACTION == "fill":
        # Fill textarea with PARAM as answer
        text = PARAM or "See lesson content for answer"
        await page.evaluate(f"""() => {{
            const ta = document.querySelector('textarea')
            if (ta) {{
                Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value')
                    .set.call(ta, {json.dumps(text)})
                ta.dispatchEvent(new Event('input', {{bubbles:true}}))
                ta.dispatchEvent(new Event('change', {{bubbles:true}}))
            }}
        }}""")
        print(f"✅ Filled textarea")

    elif ACTION == "click":
        # Click a button by text
        try:
            btn = page.locator(f'button:has-text("{PARAM}")').first
            await btn.click()
            await page.wait_for_timeout(2000)
            print(f"✅ Clicked: {PARAM}")
        except Exception as e:
            print(f"❌ {e}")

    await p.stop()

asyncio.run(main())
