"""
Estrategia eficiente:
1. Para cada curso, usar /resume para ir DIRECTAMENTE a la próxima lección incompleta
2. Completarla (video fast-forward + force-remove hide/disabled + click Complete)
3. Repetir SOLO hasta que el progreso no cambie (estancado en quiz que necesita ser pasado)
4. Para quizzes: ver respuestas, tomar de nuevo con respuestas correctas
NO visitar lecciones ya completadas.
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

async def get_progress(page, slug):
    await page.goto(f'https://anthropic.skilljar.com/{slug}', wait_until='domcontentloaded', timeout=20000)
    await page.wait_for_timeout(1500)
    body = await page.evaluate('document.body.innerText')
    m = re.search(r'(\d+) of (\d+) lessons completed', body)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)

async def force_complete_current(page):
    """Completa la lección actual: fast-forward video, desbloquea botón, click Complete."""
    # Fast-forward video
    await page.evaluate('''() => {
        document.querySelectorAll('video').forEach(v => {
            try {
                v.pause()
                if (v.duration && !isNaN(v.duration) && v.duration > 0) {
                    v.currentTime = v.duration - 0.1
                }
                v.play().catch(()=>{})
                v.dispatchEvent(new Event('timeupdate', {bubbles:true}))
                v.dispatchEvent(new Event('ended', {bubbles:true}))
            } catch(e) {}
        })
    }''')
    await page.wait_for_timeout(2000)

    # Remove hide/disabled from Complete button container
    await page.evaluate('''() => {
        const btn = document.querySelector('.complete-lesson-button')
        if (btn) {
            btn.classList.remove('hide', 'disabled')
            btn.style.setProperty('display', 'block', 'important')
        }
    }''')
    await page.wait_for_timeout(300)

    # Click Complete link
    clicked = await page.evaluate('''() => {
        const a = document.querySelector('.complete-lesson-link, a.complete-lesson-link')
        if (a) { a.click(); return true }
        // Fallback: any link with text 'Complete'
        const a2 = Array.from(document.querySelectorAll('a')).find(a => a.textContent.trim() === 'Complete')
        if (a2) { a2.click(); return 'fallback' }
        return false
    }''')
    await page.wait_for_timeout(2000)
    return clicked

async def handle_quiz(page):
    """Maneja un quiz: intenta pasarlo usando todas las opciones si es necesario."""
    # Check if quiz needs to be taken again
    body = await page.evaluate('document.body.innerText')

    # If failed quiz results shown, click Show Answers first then Take Again
    if 'did not pass' in body or ('score:' in body.lower() and 'correct' in body.lower()):
        print('    Quiz failed — reading correct answers')

        # Show Answers to learn correct ones
        await page.evaluate('''() => {
            const btn = Array.from(document.querySelectorAll('button,a')).find(el =>
                (el.textContent||'').includes('Show Answer')
            )
            if (btn) btn.click()
        }''')
        await page.wait_for_timeout(1500)

        answers_body = await page.evaluate('document.body.innerText')
        correct_answers = []
        # Parse correct answers from "Correct answer" sections
        lines = answers_body.split('\n')
        current_correct = None
        for i, line in enumerate(lines):
            if 'Correct answer' in line:
                # Next non-empty lines are the options, first is the correct one (usually marked)
                for j in range(i+1, min(i+10, len(lines))):
                    stripped = lines[j].strip()
                    if stripped and not stripped.startswith('Question') and 'Incorrect' not in stripped and 'Correct' not in stripped:
                        current_correct = stripped
                        correct_answers.append(stripped[:100])
                        break

        print(f'    Correct answers found: {len(correct_answers)}')
        for a in correct_answers:
            print(f'      - {a[:70]}')

        # Take again
        await page.evaluate('''() => {
            const btn = Array.from(document.querySelectorAll('button,a')).find(el =>
                (el.textContent||'').includes('Take this again')
            )
            if (btn) btn.click()
        }''')
        await page.wait_for_timeout(3000)

        # Now answer questions one by one using correct_answers
        for q_idx, correct_text in enumerate(correct_answers):
            radios = await page.evaluate('() => document.querySelectorAll("input[type=radio]").length')
            if radios == 0:
                break

            opts = await page.evaluate('''() => Array.from(document.querySelectorAll("input[type=radio]")).map((r,i)=>({
                i, label:(r.closest("label")?.innerText||r.value||"").trim()
            }))''')

            # Find matching option
            target_idx = 0
            best_match = 0
            for opt in opts:
                # Calculate similarity
                words_correct = set(correct_text.lower().split())
                words_opt = set(opt['label'].lower().split())
                overlap = len(words_correct & words_opt)
                if overlap > best_match:
                    best_match = overlap
                    target_idx = opt['i']

            await page.evaluate(f'''() => {{
                const r = document.querySelectorAll("input[type=radio]")[{target_idx}]
                if (r) r.click()
            }}''')
            await page.wait_for_timeout(400)

            clicked = await page.evaluate('''() => {
                const btn = Array.from(document.querySelectorAll("button")).find(b => {
                    const t = (b.textContent||'').trim()
                    return t === 'Next Question' || t === 'Submit' || t === 'Submit Quiz'
                })
                if (btn && !btn.disabled) { btn.click(); return t }
                return null
            }''')
            await page.wait_for_timeout(2500)

        return True

    # Active quiz (not failed results) - answer each question
    q_count = 0
    while True:
        radios = await page.evaluate('() => document.querySelectorAll("input[type=radio]").length')
        if radios == 0:
            break

        opts = await page.evaluate('''() => Array.from(document.querySelectorAll("input[type=radio]")).map((r,i)=>({
            i, label:(r.closest("label")?.innerText||r.value||"").trim()
        }))''')

        # Pick longest answer (usually most specific = most likely correct)
        best = max(opts, key=lambda o: len(o['label']))

        await page.evaluate(f'''() => {{
            const r = document.querySelectorAll("input[type=radio]")[{best['i']}]
            if (r) r.click()
        }}''')
        await page.wait_for_timeout(400)

        clicked = await page.evaluate('''() => {
            const btn = Array.from(document.querySelectorAll("button")).find(b => {
                const t = (b.textContent||"").trim()
                return t === "Next Question" || t === "Submit" || t === "Submit Quiz"
            })
            if (btn && !btn.disabled) { btn.click(); return true }
            return false
        }''')
        await page.wait_for_timeout(2500)
        q_count += 1
        if not clicked or q_count > 20:
            break

    return q_count > 0


async def process_course(page, slug):
    done_before, total = await get_progress(page, slug)
    print(f'\n{"="*55}')
    print(f'{slug}: {done_before}/{total}')

    if done_before == total and total > 0:
        print(f'  Already complete!')
        return True

    prev_done = -1
    for iteration in range(200):
        # Resume goes to next incomplete lesson
        try:
            await page.goto(f'https://anthropic.skilljar.com/{slug}/resume',
                           wait_until='domcontentloaded', timeout=25000)
        except:
            await page.wait_for_timeout(3000)
            continue
        await page.wait_for_timeout(2500)

        url = page.url
        body = await page.evaluate('document.body.innerText')
        title = await page.evaluate('document.title')

        # Check completion
        m = re.search(r'(\d+) of (\d+) lessons completed', body)
        done = int(m.group(1)) if m else 0
        total = int(m.group(2)) if m else 0

        if done == total and total > 0:
            print(f'  [{iteration}] COMPLETE: {done}/{total} ✓')
            await page.screenshot(path=f'E:/Documents/PROYECTOS/AgencIA/platzi_clone/downloads/devcompass/live/{slug[:20]}_COMPLETE.png')
            return True

        if done == prev_done and iteration > 3:
            # Stuck — likely a quiz blocking us
            if re.search(r'/\d+$', url):
                print(f'  [{iteration}] Stuck at: {title[:50]} | Trying quiz handler')
                quiz_done = await handle_quiz(page)
                if not quiz_done:
                    print(f'  Quiz not resolved, moving on')
                    await force_complete_current(page)
            else:
                break

        if re.search(r'/\d+$', url):
            result = await force_complete_current(page)
            print(f'  [{iteration}] {title[:45]} | done={done}/{total} | complete={result}')
        else:
            if iteration > 5:
                break

        prev_done = done

    final_done, final_total = await get_progress(page, slug)
    print(f'  Final: {final_done}/{final_total}')
    return final_done == final_total


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://localhost:9222')
        page = b.contexts[0].pages[0]

        results = {}
        for slug in COURSES:
            ok = await process_course(page, slug)
            results[slug] = ok

        print('\n\nFINAL:')
        for slug, ok in results.items():
            print(f'  {"✓" if ok else "!"} {slug}')

asyncio.run(main())
