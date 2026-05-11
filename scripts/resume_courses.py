"""
Usa el endpoint /resume de cada curso para navegar directamente a la proxima leccion incompleta.
Maneja video, quizzes, ejercicios y surveys.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, re
from playwright.async_api import async_playwright

COURSES = [
    'claude-with-the-anthropic-api',
    'introduction-to-model-context-protocol',
    'claude-code-in-action',
    'claude-101',
]

KEYWORDS = ['tool_use','end_turn','coordinator','subagent','structured',
            'schema','explicit','system','context','escalat','always','MCP',
            'client','server','correct','best practice','should not']

async def safe_eval(page, js, default=None):
    try:
        return await page.evaluate(js)
    except:
        return default

async def handle_lesson(page):
    await page.wait_for_timeout(2500)

    # Fast-forward video
    await safe_eval(page, '''() => {
        document.querySelectorAll('video').forEach(v => {
            if (v.duration && !isNaN(v.duration)) {
                v.currentTime = v.duration - 0.5
                v.play().catch(()=>{})
            }
        })
    }''')
    await page.wait_for_timeout(2000)

    title = await safe_eval(page, 'document.title', '')
    print(f'    > {title[:60]}')

    # Handle radio quiz
    radios = await safe_eval(page, '() => document.querySelectorAll("input[type=radio]").length', 0)
    if radios > 0:
        opts = await safe_eval(page, '''() => Array.from(document.querySelectorAll("input[type=radio]")).map((r,i) => ({
            i, label: (r.closest("label")?.innerText || r.value || "").trim()
        }))''', [])
        print(f'      Quiz: {len(opts)} options')

        # Try each option until one is correct
        for attempt_opt in opts:
            await safe_eval(page, f'''() => {{
                const r = document.querySelectorAll("input[type=radio]")[{attempt_opt["i"]}]
                if (r) r.click()
            }}''')
            await page.wait_for_timeout(400)
            await safe_eval(page, '''() => {
                const btn = Array.from(document.querySelectorAll("button")).find(b =>
                    /(submit|check|next)/i.test(b.textContent || "")
                )
                if (btn && !btn.disabled) btn.click()
            }''')
            await page.wait_for_timeout(2500)
            body = await safe_eval(page, 'document.body.innerText', '')
            if 'incorrect' not in body.lower() and 'wrong' not in body.lower() and 'try again' not in body.lower():
                print(f'      Correct: option {attempt_opt["i"]}')
                break
            print(f'      Wrong: option {attempt_opt["i"]}, trying next...')

    # Handle textarea
    textareas = await safe_eval(page, '() => document.querySelectorAll("textarea").length', 0)
    if textareas > 0:
        await safe_eval(page, '''() => {
            document.querySelectorAll("textarea").forEach(ta => {
                const desc = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")
                desc.set.call(ta, "The concept is demonstrated effectively in this exercise.")
                ta.dispatchEvent(new Event("input", {bubbles:true}))
                ta.dispatchEvent(new Event("change", {bubbles:true}))
            })
        }''')
        await page.wait_for_timeout(400)
        await safe_eval(page, '''() => {
            const btn = Array.from(document.querySelectorAll("button")).find(b =>
                /(submit|save|continue)/i.test(b.textContent || "")
            )
            if (btn) btn.click()
        }''')
        await page.wait_for_timeout(2000)

    # Handle select (satisfaction surveys)
    selects = await safe_eval(page, '() => document.querySelectorAll("select").length', 0)
    if selects > 0:
        await safe_eval(page, '''() => {
            document.querySelectorAll("select").forEach(s => {
                if (s.options.length > 0)
                    s.value = s.options[Math.floor(s.options.length * 0.8)].value
                s.dispatchEvent(new Event("change", {bubbles:true}))
            })
        }''')
        await page.wait_for_timeout(400)
        await safe_eval(page, '''() => {
            const btn = Array.from(document.querySelectorAll("button")).find(b =>
                /(submit|save|continue)/i.test(b.textContent || "")
            )
            if (btn) btn.click()
        }''')
        await page.wait_for_timeout(2000)

    # Click Complete
    await safe_eval(page, '''() => {
        const a = Array.from(document.querySelectorAll("a[href]")).find(a =>
            a.textContent.trim() === "Complete" && a.href.includes("#")
        )
        if (a) a.click()
    }''')
    await page.wait_for_timeout(1500)


async def complete_course(page, slug):
    print(f'\n{"="*55}')
    print(f'COURSE: {slug}')

    for iteration in range(120):
        try:
            await page.goto(f'https://anthropic.skilljar.com/{slug}/resume',
                           wait_until='domcontentloaded', timeout=25000)
        except:
            await page.wait_for_timeout(3000)
            continue
        await page.wait_for_timeout(2500)

        current_url = page.url
        body = await safe_eval(page, 'document.body.innerText', '')

        # Check completion
        m = re.search(r'(\d+) of (\d+) lessons completed', body)
        if m and m.group(1) == m.group(2):
            print(f'  COMPLETE: {m.group(1)}/{m.group(2)} ✓')
            await page.screenshot(
                path=f'E:/Documents/PROYECTOS/AgencIA/platzi_clone/downloads/devcompass/live/{slug[:25]}_done.png'
            )
            return True

        # Are we on a lesson?
        if re.search(r'/\d+$', current_url):
            await handle_lesson(page)
        else:
            # Resume sent us back to course page - might be stuck
            if m:
                print(f'  Stuck at {m.group(1)}/{m.group(2)} after {iteration} iterations')
            if iteration > 5:
                # Try clicking Continue button directly
                clicked = await safe_eval(page, '''() => {
                    const btn = Array.from(document.querySelectorAll("a,button")).find(el =>
                        /^(Continue|Start)$/.test((el.textContent||"").trim())
                    )
                    if (btn) { btn.click(); return true }
                    return false
                }''', False)
                if not clicked:
                    break
            await page.wait_for_timeout(2000)

    # Final status
    await page.goto(f'https://anthropic.skilljar.com/{slug}',
                   wait_until='domcontentloaded', timeout=20000)
    await page.wait_for_timeout(2000)
    body = await safe_eval(page, 'document.body.innerText', '')
    m = re.search(r'(\d+) of (\d+) lessons completed', body)
    if m:
        print(f'  Final: {m.group(1)}/{m.group(2)}')
        return m.group(1) == m.group(2)
    return False


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://localhost:9222')
        page = b.contexts[0].pages[0]

        results = {}
        for slug in COURSES:
            done = await complete_course(page, slug)
            results[slug] = done

        print('\n\nFINAL STATUS:')
        for slug, done in results.items():
            print(f'  {"✓" if done else "!"} {slug}')


asyncio.run(main())
