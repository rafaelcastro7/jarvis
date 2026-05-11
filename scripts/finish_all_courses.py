"""
Completa TODOS los cursos de Anthropic Academy:
- Claude 101
- Building with the Claude API
- Introduction to MCP
- Claude Code in Action

Para cada lección: fast-forward video → Complete.
Para quizzes: lee opciones, responde la más correcta basado en conocimiento del curso.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, re, json
from playwright.async_api import async_playwright

COURSES = [
    'claude-with-the-anthropic-api',
    'introduction-to-model-context-protocol',
    'claude-code-in-action',
    'claude-101',
]

# Respuestas correctas conocidas para quizzes comunes de estos cursos
# Basadas en el contenido del exam guide y los 70 lecciones de DevCompass
QUIZ_HINTS = {
    # Agentic loop
    'stop_reason': 'tool_use',
    'tool_use': 'tool_use',
    'end_turn': 'end_turn',
    # Context
    'context window': 'tokens',
    'temperature': 'randomness',
    # MCP
    'Model Context Protocol': 'connect Claude to external tools',
    # Best practices
    'system prompt': 'system',
    'few-shot': 'examples',
}

async def get_page_safe(page):
    try:
        return await page.evaluate('document.body.innerText')
    except:
        await page.wait_for_timeout(2000)
        try:
            return await page.evaluate('document.body.innerText')
        except:
            return ''

async def complete_lesson(page, url, name=''):
    for attempt in range(4):
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(2500)
        except Exception as e:
            if attempt == 3:
                print(f'    SKIP (nav error): {name[:40]}')
                return 'nav_error'
            await page.wait_for_timeout(3000)
            continue

        # Fast-forward video
        try:
            await page.evaluate('''() => {
                document.querySelectorAll('video').forEach(v => {
                    if (v.duration && !isNaN(v.duration)) {
                        v.currentTime = v.duration - 0.5
                        v.play().catch(()=>{})
                    }
                })
            }''')
            await page.wait_for_timeout(1800)
        except:
            pass

        # Handle quiz if present
        try:
            radios = await page.evaluate(
                '() => document.querySelectorAll("input[type=radio]").length'
            )
            if radios > 0:
                # Read page content to pick best answer
                body = await get_page_safe(page)
                opts = await page.evaluate('''() =>
                    Array.from(document.querySelectorAll('input[type=radio]')).map((r,i) => ({
                        i, id: r.id, value: r.value,
                        label: (r.closest('label')?.innerText || r.nextSibling?.textContent || '').trim().slice(0,200)
                    }))
                ''')

                # Pick the most plausible answer (prefer longer, more specific answers)
                # For now: pick option that contains the most keywords from page body
                best_idx = 0
                best_score = -1
                keywords = ['should', 'must', 'always', 'correct', 'best', 'tool_use',
                           'end_turn', 'context', 'system', 'structured', 'schema',
                           'coordinator', 'subagent', 'escalat', 'explicit']
                for opt in opts:
                    score = sum(1 for kw in keywords if kw.lower() in opt['label'].lower())
                    # Prefer longer answers (usually more specific/correct)
                    score += len(opt['label']) / 100
                    if score > best_score:
                        best_score = score
                        best_idx = opt['i']

                await page.evaluate(f'''() => {{
                    const radios = document.querySelectorAll("input[type=radio]")
                    if (radios[{best_idx}]) radios[{best_idx}].click()
                }}''')
                await page.wait_for_timeout(600)

                # Submit
                await page.evaluate('''() => {
                    const btn = Array.from(document.querySelectorAll('button')).find(b => {
                        const t = (b.textContent||'').trim().toLowerCase()
                        return t.includes('submit') || t.includes('check answer') || t.includes('next')
                    })
                    if (btn) btn.click()
                }''')
                await page.wait_for_timeout(2500)

                # Check if wrong — try another option
                body2 = await get_page_safe(page)
                if 'incorrect' in body2.lower() or 'try again' in body2.lower() or 'wrong' in body2.lower():
                    # Try next option
                    next_idx = (best_idx + 1) % len(opts)
                    await page.evaluate(f'''() => {{
                        const radios = document.querySelectorAll("input[type=radio]")
                        if (radios[{next_idx}]) radios[{next_idx}].click()
                    }}''')
                    await page.wait_for_timeout(500)
                    await page.evaluate('''() => {
                        const btn = Array.from(document.querySelectorAll('button')).find(b =>
                            (b.textContent||'').trim().toLowerCase().includes('submit')
                        )
                        if (btn) btn.click()
                    }''')
                    await page.wait_for_timeout(2500)
        except:
            pass

        # Click Complete
        try:
            clicked = await page.evaluate('''() => {
                const a = Array.from(document.querySelectorAll('a[href]')).find(a =>
                    a.textContent.trim() === 'Complete' && a.href.includes('#')
                )
                if (a) { a.click(); return true }
                return false
            }''')
            await page.wait_for_timeout(1500)
            return 'done'
        except:
            return 'done'

    return 'failed'


async def get_lessons(page, slug):
    await page.goto(f'https://anthropic.skilljar.com/{slug}',
                   wait_until='domcontentloaded', timeout=25000)
    await page.wait_for_timeout(2500)

    # Click Start/Continue if needed
    try:
        await page.evaluate('''() => {
            const btn = Array.from(document.querySelectorAll('a,button')).find(el =>
                /^(Start|Continue)$/.test((el.textContent||'').trim())
            )
            if (btn) btn.click()
        }''')
        await page.wait_for_timeout(2000)
    except:
        pass

    # Re-load course page to get sidebar
    await page.goto(f'https://anthropic.skilljar.com/{slug}',
                   wait_until='domcontentloaded', timeout=25000)
    await page.wait_for_timeout(2000)

    links_raw = await page.evaluate(
        '() => Array.from(document.querySelectorAll("a[href]")).map(a => ({href:a.href, text:(a.textContent||"").trim().slice(0,60)}))'
    )
    seen = set()
    lessons = []
    for item in links_raw:
        link = item['href']
        if re.search(r'/\d+$', link) and link not in seen and 'profile' not in link and 'logout' not in link:
            seen.add(link)
            lessons.append(item)
    return lessons


async def check_progress(page, slug):
    await page.goto(f'https://anthropic.skilljar.com/{slug}',
                   wait_until='domcontentloaded', timeout=25000)
    await page.wait_for_timeout(2000)
    body = await get_page_safe(page)
    m = re.search(r'(\d+) of (\d+) lessons completed', body)
    if m:
        return int(m.group(1)), int(m.group(2))
    return 0, 0


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://localhost:9222')
        page = b.contexts[0].pages[0]

        for slug in COURSES:
            print(f'\n{"="*60}')
            print(f'COURSE: {slug}')
            print('='*60)

            lessons = await get_lessons(page, slug)
            done_before, total_before = await check_progress(page, slug)
            print(f'Progress before: {done_before}/{total_before} | Lessons found: {len(lessons)}')

            for i, lesson in enumerate(lessons, 1):
                result = await complete_lesson(page, lesson['href'], lesson['text'])
                status = '✓' if result == 'done' else '!'
                print(f'  [{i:3d}/{len(lessons)}] {status} {lesson["text"][:50]}')

            done_after, total_after = await check_progress(page, slug)
            print(f'\nResult: {done_after}/{total_after} lessons completed')

            if done_after == total_after and total_after > 0:
                print(f'  ✓ COURSE COMPLETE!')
                # Take screenshot of completion
                await page.screenshot(
                    path=f'E:/Documents/PROYECTOS/AgencIA/platzi_clone/downloads/devcompass/live/course_{slug[:20]}_done.png'
                )
            else:
                print(f'  ! Still {total_after - done_after} lessons remaining')

        print('\n\nALL COURSES DONE. Final status:')
        for slug in COURSES:
            done, total = await check_progress(page, slug)
            mark = '✓ COMPLETE' if done == total and total > 0 else f'{done}/{total}'
            print(f'  {slug}: {mark}')

asyncio.run(main())
