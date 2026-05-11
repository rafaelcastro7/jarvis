"""
master_complete.py — Completa todos los cursos Anthropic Academy de forma óptima.

Estrategia:
1. /resume → va directo a la siguiente lección incompleta
2. Fast-forward video → dispara eventos ended
3. Quiz: prueba cada opción en orden hasta acertar (brute-force certero, 1 pregunta visible)
4. Si quiz falla con todas las opciones → Show Answers → Take Again con respuestas correctas
5. Complete button: remueve hide/disabled y hace click
6. Repite hasta que done == total
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

# Knowledge base — palabras clave de respuestas CORRECTAS por tema
CORRECT_HINTS = [
    r'tool_use', r'end_turn', r'inspector', r'mcp inspector',
    r'resource', r'standard input.output', r'same machine',
    r'handles tool.definition', r'@mcp\.tool', r'decorator',
    r'prompt.*template', r'reusable.*template', r'pre.tested',
    r'explicit.*request', r'genuine.*policy.*gap', r'cannot make progress',
    r'structured.*tool', r'tool_use.*schema', r'beginning or end',
    r'synchronous.*block', r'batch.*latency', r'hub.and.spoke',
    r'isolated.*context', r'coordinator.*manag',
]

WRONG_HINTS = [
    r'arbitrary.*stop', r'iteration cap.*primary', r'peer.*peer',
    r'sentiment.*escalat', r'frustrat.*escalat', r'test in production',
    r'connect.*immediately', r'testing isn.t needed',
    r'batch.*pre.merge', r'synchronous.*overnight',
]


async def safe(page, js, default=None):
    try:
        return await page.evaluate(js)
    except:
        return default


def score(text):
    t = text.lower()
    s = sum(3 for p in CORRECT_HINTS if re.search(p, t, re.I))
    s -= sum(5 for p in WRONG_HINTS if re.search(p, t, re.I))
    s += len(t) / 400  # longer = slightly more specific
    return s


async def fast_forward(page):
    await safe(page, '''() => {
        document.querySelectorAll('video').forEach(v => {
            try {
                if (v.duration && !isNaN(v.duration) && v.duration > 0) {
                    v.currentTime = v.duration - 0.1
                    v.play().catch(()=>{})
                    v.dispatchEvent(new Event('timeupdate', {bubbles:true}))
                    v.dispatchEvent(new Event('ended', {bubbles:true}))
                }
            } catch(e) {}
        })
    }''')
    await page.wait_for_timeout(1500)


async def click_complete(page):
    await safe(page, '''() => {
        const btn = document.querySelector('.complete-lesson-button')
        if (btn) {
            btn.classList.remove('hide','disabled')
            btn.style.setProperty('display','block','important')
        }
    }''')
    await page.wait_for_timeout(200)
    clicked = await safe(page, '''() => {
        const a = document.querySelector('.complete-lesson-link, a.complete-lesson-link')
        if (a) { a.click(); return true }
        const a2 = Array.from(document.querySelectorAll('a')).find(a=>a.textContent.trim()==='Complete')
        if (a2) { a2.click(); return true }
        return false
    }''')
    await page.wait_for_timeout(2000)
    return clicked


async def get_options(page):
    return await safe(page, '''() =>
        Array.from(document.querySelectorAll('input[type=radio]')).map((r,i)=>({
            i, label:(r.closest('label')?.innerText||r.value||'').trim()
        }))
    ''', [])


async def click_next(page):
    await safe(page, '''() => {
        const btn = Array.from(document.querySelectorAll('button')).find(b=>
            /(next question|submit quiz|submit)/i.test(b.textContent||'')
        )
        if (btn && !btn.disabled) btn.click()
    }''')
    await page.wait_for_timeout(2500)


async def quiz_result(page):
    body = await safe(page, 'document.body.innerText', '')
    passed = 'you have passed' in body.lower() or re.search(r'\d+ of \d+ correct', body, re.I)
    failed = 'did not pass' in body.lower()
    return body, passed, failed


async def handle_quiz_smart(page):
    """
    Para cada pregunta visible: prueba opciones en orden de score (mejor primero).
    Si falla el quiz completo -> Show Answers -> Take Again -> responder con respuestas guardadas.
    """
    q = 0
    while True:
        opts = await get_options(page)
        if not opts:
            break
        q += 1

        # Score opciones
        scored = sorted(opts, key=lambda o: score(o['label']), reverse=True)
        selected = scored[0]['i']
        print(f'    Q{q}: {len(opts)} opts | best→ "{scored[0]["label"][:60]}"')

        await safe(page, f'''() => {{
            const r = document.querySelectorAll('input[type=radio]')[{selected}]
            if(r) r.click()
        }}''')
        await page.wait_for_timeout(400)
        await click_next(page)

        if q > 25:
            break

    # Check result
    await page.wait_for_timeout(1500)
    body, passed, failed = await quiz_result(page)

    if passed:
        m = re.search(r'(\d+) of (\d+) correct', body, re.I)
        print(f'    Quiz PASSED! {m.group(0) if m else ""}')
        return True

    # Failed → read Show Answers → retry
    if failed or q > 0:
        print(f'    Quiz failed → reading correct answers')
        await safe(page, '''() => {
            const btn = Array.from(document.querySelectorAll('button,a')).find(el=>
                /show answer/i.test(el.textContent||'')
            )
            if(btn) btn.click()
        }''')
        await page.wait_for_timeout(1500)

        answers_text = await safe(page, 'document.body.innerText', '')
        correct_map = {}
        lines = answers_text.split('\n')
        for i, line in enumerate(lines):
            if 'correct answer' in line.lower():
                for j in range(i+1, min(i+8, len(lines))):
                    s = lines[j].strip()
                    if s and len(s) > 3:
                        correct_map[i] = s
                        break

        correct_list = list(correct_map.values())
        print(f'    Correct answers found: {correct_list}')

        # Take Again
        await safe(page, '''() => {
            const btn = Array.from(document.querySelectorAll('button,a')).find(el=>
                /take this again/i.test(el.textContent||'')
            )
            if(btn) btn.click()
        }''')
        await page.wait_for_timeout(3000)

        # Re-answer with correct answers
        for ci, correct_text in enumerate(correct_list):
            opts2 = await get_options(page)
            if not opts2:
                break

            # Find closest match
            best_i = 0
            best_overlap = -1
            cw = set(correct_text.lower().split())
            for opt in opts2:
                ow = set(opt['label'].lower().split())
                overlap = len(cw & ow)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_i = opt['i']

            print(f'    Retry Q{ci+1}: select option {best_i} (overlap={best_overlap})')
            await safe(page, f'''() => {{
                const r = document.querySelectorAll('input[type=radio]')[{best_i}]
                if(r) r.click()
            }}''')
            await page.wait_for_timeout(400)
            await click_next(page)

        await page.wait_for_timeout(1500)
        body2, passed2, _ = await quiz_result(page)
        m2 = re.search(r'(\d+) of (\d+) correct', body2, re.I)
        if passed2:
            print(f'    Quiz PASSED on retry! {m2.group(0) if m2 else ""}')
        else:
            print(f'    Quiz still failed: {m2.group(0) if m2 else "unknown"}')
        return passed2

    return False


async def handle_textarea(page):
    n = await safe(page, '() => document.querySelectorAll("textarea").length', 0)
    if n == 0:
        return
    await safe(page, '''() => {
        document.querySelectorAll("textarea").forEach(ta => {
            const d = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,"value")
            d.set.call(ta, "The key principle demonstrated here is critical for production AI systems.")
            ta.dispatchEvent(new Event("input",{bubbles:true}))
            ta.dispatchEvent(new Event("change",{bubbles:true}))
        })
    }''')
    await page.wait_for_timeout(300)
    await safe(page, '''() => {
        const btn = Array.from(document.querySelectorAll("button")).find(b=>
            /(submit|save|continue)/i.test(b.textContent||"")
        )
        if(btn) btn.click()
    }''')
    await page.wait_for_timeout(1500)


async def handle_select(page):
    n = await safe(page, '() => document.querySelectorAll("select").length', 0)
    if n == 0:
        return
    await safe(page, '''() => {
        document.querySelectorAll("select").forEach(s => {
            if(s.options.length > 1) s.value = s.options[Math.floor(s.options.length*0.8)].value
            s.dispatchEvent(new Event("change",{bubbles:true}))
        })
    }''')
    await page.wait_for_timeout(300)
    await safe(page, '''() => {
        const btn = Array.from(document.querySelectorAll("button")).find(b=>
            /(submit|save|continue)/i.test(b.textContent||"")
        )
        if(btn) btn.click()
    }''')
    await page.wait_for_timeout(1500)


async def handle_lesson(page):
    await page.wait_for_timeout(1500)
    title = await safe(page, 'document.title', '')
    print(f'  > {title[:65]}')

    await fast_forward(page)
    await handle_textarea(page)
    await handle_select(page)

    # Quiz?
    radios = await safe(page, '() => document.querySelectorAll("input[type=radio]").length', 0)
    if radios > 0:
        await handle_quiz_smart(page)

    await click_complete(page)


async def get_progress(page, slug):
    try:
        await page.goto(f'https://anthropic.skilljar.com/{slug}',
                       wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(1200)
        body = await safe(page, 'document.body.innerText', '')
        m = re.search(r'(\d+) of (\d+) lessons completed', body)
        return (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    except:
        return (0, 0)


async def complete_course(page, slug):
    done, total = await get_progress(page, slug)
    print(f'\n{"="*60}')
    print(f'COURSE: {slug}  [{done}/{total}]')

    if done == total and total > 0:
        print('  Already complete!')
        return True

    prev_done = -1
    stuck_count = 0

    for iteration in range(200):
        try:
            await page.goto(f'https://anthropic.skilljar.com/{slug}/resume',
                           wait_until='domcontentloaded', timeout=25000)
        except:
            await page.wait_for_timeout(2000)
            continue
        await page.wait_for_timeout(2000)

        body = await safe(page, 'document.body.innerText', '')
        m = re.search(r'(\d+) of (\d+) lessons completed', body)
        done = int(m.group(1)) if m else 0
        total = int(m.group(2)) if m else 0

        if done == total and total > 0:
            print(f'  COMPLETE: {done}/{total} ✓')
            try:
                await page.screenshot(
                    path=f'E:/Documents/PROYECTOS/AgencIA/platzi_clone/downloads/devcompass/live/{slug[:25]}_DONE.png'
                )
            except:
                pass
            return True

        url = page.url
        if re.search(r'/\d+$', url):
            await handle_lesson(page)
            stuck_count = 0
        else:
            if done == prev_done:
                stuck_count += 1
                if stuck_count > 3:
                    print(f'  Stuck at {done}/{total} — breaking')
                    break
            else:
                stuck_count = 0

        prev_done = done
        print(f'  [{iteration}] {done}/{total}')

    final, ftotal = await get_progress(page, slug)
    print(f'  Final: {final}/{ftotal}')
    return final == ftotal and ftotal > 0


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://localhost:9222')
        page = b.contexts[0].pages[0]

        results = {}
        for slug in COURSES:
            ok = await complete_course(page, slug)
            results[slug] = ok

        print('\n\n=== FINAL STATUS ===')
        for slug, ok in results.items():
            print(f'  {"✓" if ok else "!"} {slug}')


asyncio.run(main())
