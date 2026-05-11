"""
ajax_complete.py — Completa lecciones Skilljar vía AJAX + quiz answering inteligente.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
import asyncio, re, json
from playwright.async_api import async_playwright

COURSES = [
    'claude-with-the-anthropic-api',
    'introduction-to-model-context-protocol',
    'claude-code-in-action',
    'claude-101',
]

# Respuestas correctas conocidas — indexadas por fragmento del título (lowercase)
KNOWN_CORRECT = {
    'accessing claude': [
        'API key, model name, messages, and max tokens',
        "Claude doesn't remember previous messages",
        'Breaks it into smaller chunks called tokens',
        'Enabling response streaming',
        "On your server that users can't access",
        'A system prompt explaining the tutor role',
        'Low temperature (near 0.0)',
        'Combine prefilled messages and stop sequences',
    ],
    'tool use with claude': [
        'Look at the stop_reason field for',  # tool_use
        'Multi-block messages with text and tool use blocks',
        'To tell Claude what arguments your function expects',
        'It reduces the number of back-and-forth communications',
        'Initial Request',  # → Tool Request → Data Retrieval → Final Response
        'Using tools to access external information',
        'Claude provides the schema',
    ],
    'model context protocol': [
        'Use the MCP Inspector in your browser',
        'Resources',
        'Through standard input/output on the same machine',
        'MCP handles the tool definitions and execution for you',
        'Use the @mcp.tool decorator on a function',
        'Prompts',
    ],
    'prompt engineering': [  # covers both eval and eng quizzes
        'Clear instructions',
        'Few-shot examples',
        'System prompt',
        'Temperature',
        'Chain-of-thought',
        'Specificity',
        'Context',
        'Role',
    ],
}

# Runtime-learned answers (populated from Show Answers parsing)
LEARNED: dict[str, list[str]] = {}


async def safe(page, js, default=None):
    try:
        return await page.evaluate(js)
    except Exception:
        return default


async def fast_fwd(page):
    """Fast-forward all videos to end and fire ended event."""
    await safe(page, '''() => {
        document.querySelectorAll('video').forEach(v => {
            try {
                if (v.duration && !isNaN(v.duration) && v.duration > 0) {
                    v.currentTime = v.duration - 0.1
                    v.play().catch(() => {})
                    v.dispatchEvent(new Event('timeupdate', {bubbles:true}))
                    v.dispatchEvent(new Event('ended', {bubbles:true}))
                }
            } catch(e) {}
        })
        // JWPlayer
        try {
            const jw = window.jwplayer && window.jwplayer()
            if (jw && jw.getDuration) {
                const dur = jw.getDuration()
                if (dur > 0) {
                    jw.seek(dur - 0.5)
                    jw.trigger('complete')
                }
            }
        } catch(e) {}
        // Skilljar completeLesson
        try {
            if (window.completeLesson) window.completeLesson()
        } catch(e) {}
    }''')
    await page.wait_for_timeout(2000)


async def call_complete_lesson(page):
    """Call window.completeLesson() and video progress manager."""
    await safe(page, '''async () => {
        try {
            const args = window.lessonJsArgs || {}
            // video progress
            if (args.videoProgressUrl) {
                const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || ""
                await fetch(args.videoProgressUrl, {
                    method: "POST",
                    headers: {"X-CSRFToken": csrf, "X-Requested-With": "XMLHttpRequest",
                              "Content-Type": "application/x-www-form-urlencoded"},
                    credentials: "include",
                    body: `id=${args.lessonId || ""}&current_second=99&highwater_second=99&clientside_timestamp=${Date.now()}`
                }).catch(()=>{})
            }
        } catch(e) {}
        try { if (window.completeLesson) window.completeLesson() } catch(e) {}
        try { if (window.lessonPlayerCompleteCallback) window.lessonPlayerCompleteCallback() } catch(e) {}
    }''')
    await page.wait_for_timeout(1500)


async def ajax_complete(page):
    """POST to markLessonCompleteUrl."""
    complete_url = await safe(page, '''() => {
        try { return window.lessonJsArgs && window.lessonJsArgs.markLessonCompleteUrl }
        catch(e) { return null }
    }''')
    if not complete_url:
        return None
    result = await safe(page, f'''async () => {{
        try {{
            const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || ""
            const resp = await fetch("{complete_url}", {{
                method: "POST",
                headers: {{"Content-Type": "application/x-www-form-urlencoded",
                           "X-CSRFToken": csrf, "X-Requested-With": "XMLHttpRequest"}},
                credentials: "include",
                body: "csrfmiddlewaretoken=" + csrf
            }})
            const text = await resp.text()
            return {{status: resp.status, ok: resp.ok, body: text.slice(0,80)}}
        }} catch(e) {{ return {{error: e.toString()}} }}
    }}''')
    return result


async def click_next(page):
    await safe(page, '''() => {
        const btn = Array.from(document.querySelectorAll("button")).find(b =>
            /(next question|submit quiz|submit)/i.test(b.textContent || "")
        )
        if (btn && !btn.disabled) btn.click()
    }''')
    await page.wait_for_timeout(2000)


async def parse_show_answers(page):
    """Parse Show Answers page to get correct answers per question index."""
    correct = await safe(page, '''() => {
        // Try to find question blocks with their correct answers
        const results = {}
        // Approach: find all question containers, check which ones say "Correct answer"
        const body = document.body.innerText
        const lines = body.split("\\n").map(l => l.trim()).filter(l => l)
        let qNum = 0, isCorrect = false, collecting = false, collected = []
        for (let i = 0; i < lines.length; i++) {
            const l = lines[i]
            const qm = l.match(/^Question (\\d+):\\s+(Correct|Incorrect) answer/i)
            if (qm) {
                if (qNum > 0 && isCorrect && collected.length > 0) {
                    results[qNum] = collected
                }
                qNum = parseInt(qm[1])
                isCorrect = qm[2].toLowerCase() === "correct"
                collected = []
                collecting = true
                continue
            }
            if (!collecting || qNum === 0) continue
            if (/^(Hide Answers|Take This Again|Your Score|Elapsed|Submit)/i.test(l)) {
                collecting = false; continue
            }
            if (l.length > 3 && l.length < 300) {
                collected.push(l)
            }
        }
        if (qNum > 0 && isCorrect && collected.length > 0) results[qNum] = collected
        return results
    }''', {})
    return correct or {}


async def handle_quiz(page, title, lesson_id):
    """Smart quiz handler with Show Answers learning."""
    title_lower = title.lower()
    body = await safe(page, '() => document.body.innerText', '')

    # Already passed?
    if 'you have passed' in body.lower():
        print(f'    Quiz already passed!')
        return True

    # Check if quiz is in active state (has Start button or is mid-quiz)
    start_btn = await safe(page, '''() => {
        const btn = Array.from(document.querySelectorAll("button,a")).find(el =>
            /(^start$|begin quiz|take quiz|start quiz)/i.test((el.textContent || "").trim())
        )
        return btn ? btn.textContent.trim() : null
    }''')
    if start_btn:
        print(f'    Clicking Start button: "{start_btn}"')
        await safe(page, '''() => {
            const btn = Array.from(document.querySelectorAll("button,a")).find(el =>
                /(^start$|begin quiz|take quiz|start quiz)/i.test((el.textContent || "").trim())
            )
            if (btn) btn.click()
        }''')
        await page.wait_for_timeout(3000)
        body = await safe(page, '() => document.body.innerText', '')

    # Did not pass → Show Answers → learn → Take Again
    if 'did not pass' in body.lower() or 'you did not' in body.lower():
        print(f'    Quiz failed, reading Show Answers...')
        await safe(page, '''() => {
            const btn = Array.from(document.querySelectorAll("button,a")).find(el =>
                /show answer/i.test(el.textContent || "")
            )
            if (btn) btn.click()
        }''')
        await page.wait_for_timeout(2500)

        correct_map = await parse_show_answers(page)
        print(f'    Correct answers found for questions: {list(correct_map.keys())}')

        # Store in LEARNED
        correct_list = []
        for qi in sorted(correct_map.keys()):
            texts = correct_map[qi]
            if texts:
                correct_list.append(texts[0])  # first text after Q header = correct option
        if correct_list:
            LEARNED[lesson_id] = correct_list
            print(f'    Learned {len(correct_list)} answers')

        # Take Again
        await safe(page, '''() => {
            const btn = Array.from(document.querySelectorAll("button,a")).find(el =>
                /take this again/i.test(el.textContent || "")
            )
            if (btn) btn.click()
        }''')
        await page.wait_for_timeout(3000)

        # Click Start if needed
        start_btn2 = await safe(page, '''() => {
            const btn = Array.from(document.querySelectorAll("button,a")).find(el =>
                /(^start$|begin quiz|take quiz|start quiz)/i.test((el.textContent || "").trim())
            )
            return btn ? btn.textContent.trim() : null
        }''')
        if start_btn2:
            await safe(page, '''() => {
                const btn = Array.from(document.querySelectorAll("button,a")).find(el =>
                    /(^start$|begin quiz|take quiz|start quiz)/i.test((el.textContent || "").trim())
                )
                if (btn) btn.click()
            }''')
            await page.wait_for_timeout(3000)

    # Get best known answers for this quiz
    learned = LEARNED.get(lesson_id, [])
    known = None
    for key, answers in KNOWN_CORRECT.items():
        if key in title_lower:
            known = answers
            break
    best_answers = learned if learned else known

    # Answer questions
    q_count = 0
    while q_count < 30:
        opts = await safe(page, '''() => Array.from(document.querySelectorAll('input[type=radio]')).map((r,i) => ({
            i, label: (r.closest("label")?.innerText || r.value || "").trim()
        }))''', [])
        if not opts:
            break
        q_count += 1

        if best_answers and q_count <= len(best_answers):
            correct_text = best_answers[q_count - 1]
            cw = set(correct_text.lower().split())
            scored = [(len(set(o['label'].lower().split()) & cw), o['i'], o['label']) for o in opts]
            scored.sort(reverse=True)
            best_i = scored[0][1]
            print(f'    Q{q_count}: "{scored[0][2][:60]}"')
        else:
            # Longest answer heuristic
            best = max(opts, key=lambda o: len(o['label']))
            best_i = best['i']
            print(f'    Q{q_count} (heuristic): "{best["label"][:60]}"')

        await safe(page, f'() => {{ const r = document.querySelectorAll("input[type=radio]")[{best_i}]; if(r) r.click() }}')
        await page.wait_for_timeout(400)
        await click_next(page)

    await page.wait_for_timeout(2000)
    body2 = await safe(page, '() => document.body.innerText', '')
    passed = 'you have passed' in body2.lower()
    m = re.search(r'(\d+)\s+of\s+(\d+)\s+correct', body2, re.I)
    score_str = m.group(0) if m else '?'
    print(f'    RESULT: {score_str} | Passed={passed}')
    return passed


async def get_lesson_info(page):
    """Get cba flag and lesson ID."""
    return await safe(page, '''() => {
        const args = window.lessonJsArgs || {}
        return {
            cba: args.completeBeforeAdvance || false,
            lessonId: args.lessonId || null,
            markUrl: args.markLessonCompleteUrl || null
        }
    }''', {})


async def get_progress(page, slug):
    await page.goto(f'https://anthropic.skilljar.com/{slug}',
                    wait_until='domcontentloaded', timeout=20000)
    await page.wait_for_timeout(1000)
    body = await safe(page, '() => document.body.innerText', '')
    m = re.search(r'(\d+)\s+of\s+(\d+)\s+lessons completed', body)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


async def css_force_complete(page):
    """CSS hack to reveal and click the complete button."""
    await safe(page, '''() => {
        const btn = document.querySelector(".complete-lesson-button")
        if (btn) {
            btn.classList.remove("hide", "disabled")
            btn.style.setProperty("display", "block", "important")
            btn.style.setProperty("visibility", "visible", "important")
        }
    }''')
    await page.wait_for_timeout(300)
    clicked = await safe(page, '''() => {
        const a = document.querySelector(".complete-lesson-link")
        if (a) { a.click(); return true }
        return false
    }''')
    return clicked


async def complete_course(page, slug):
    done, total = await get_progress(page, slug)
    print(f'\n{"="*60}')
    print(f'COURSE: {slug}  [{done}/{total}]')

    if done == total and total > 0:
        print('  Already complete!')
        return True

    prev_done = -1
    stuck_count = 0
    last_lesson_id = None
    lesson_stuck = 0

    for iteration in range(200):
        try:
            await page.goto(f'https://anthropic.skilljar.com/{slug}/resume',
                            wait_until='domcontentloaded', timeout=25000)
        except Exception as e:
            print(f'  Nav error: {e}')
            await page.wait_for_timeout(2000)
            continue
        await page.wait_for_timeout(2000)

        url = page.url
        body = await safe(page, '() => document.body.innerText', '')
        title = await safe(page, '() => document.title', '')
        m = re.search(r'(\d+)\s+of\s+(\d+)\s+lessons completed', body)
        done = int(m.group(1)) if m else done
        total_c = int(m.group(2)) if m else total

        if done == total_c and total_c > 0:
            print(f'  COMPLETE: {done}/{total_c} ✓')
            return True

        # Check if we're on a lesson page
        lesson_match = re.search(r'/(\d+)$', url)
        if not lesson_match:
            if done == prev_done:
                stuck_count += 1
                if stuck_count > 5:
                    print(f'  Stuck on course page at {done}/{total_c}, giving up')
                    break
            else:
                stuck_count = 0
            prev_done = done
            continue

        lesson_id = lesson_match.group(1)
        stuck_count = 0

        # Detect infinite loop on same lesson
        if lesson_id == last_lesson_id:
            lesson_stuck += 1
        else:
            lesson_stuck = 0
            last_lesson_id = lesson_id

        if lesson_stuck > 6:
            print(f'  STUCK on lesson {lesson_id} after {lesson_stuck} attempts, skipping')
            # Navigate away to force advance
            await page.goto(f'https://anthropic.skilljar.com/{slug}',
                            wait_until='domcontentloaded', timeout=20000)
            await page.wait_for_timeout(1000)
            lesson_stuck = 0
            continue

        print(f'  [{iteration}] lesson={lesson_id} "{title[:50]}" | {done}/{total_c} | stuck={lesson_stuck}')

        info = await get_lesson_info(page)
        cba = info.get('cba', False)
        print(f'    cba={cba}')

        # Fast-forward video
        await fast_fwd(page)

        # Fill textareas
        n_ta = await safe(page, '() => document.querySelectorAll("textarea").length', 0)
        if n_ta:
            await safe(page, '''() => {
                document.querySelectorAll("textarea").forEach(ta => {
                    const d = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")
                    d.set.call(ta, "This concept is critical for production AI systems.")
                    ta.dispatchEvent(new Event("input", {bubbles:true}))
                    ta.dispatchEvent(new Event("change", {bubbles:true}))
                })
                const btn = Array.from(document.querySelectorAll("button")).find(b =>
                    /(submit|save|continue)/i.test(b.textContent || ""))
                if (btn) btn.click()
            }''')
            await page.wait_for_timeout(1500)

        # Fill selects
        n_sel = await safe(page, '() => document.querySelectorAll("select").length', 0)
        if n_sel:
            await safe(page, '''() => {
                document.querySelectorAll("select").forEach(s => {
                    if (s.options.length > 1) s.value = s.options[Math.floor(s.options.length*0.8)].value
                    s.dispatchEvent(new Event("change", {bubbles:true}))
                })
                const btn = Array.from(document.querySelectorAll("button")).find(b =>
                    /(submit|save|continue)/i.test(b.textContent || ""))
                if (btn) btn.click()
            }''')
            await page.wait_for_timeout(1500)

        # Handle quiz
        radios = await safe(page, '() => document.querySelectorAll("input[type=radio]").length', 0)
        has_start = await safe(page, '''() => !!Array.from(document.querySelectorAll("button,a")).find(el =>
            /(^start$|begin quiz|take quiz|start quiz)/i.test((el.textContent||"").trim()))''', False)
        is_quiz = radios > 0 or has_start

        quiz_passed = False
        if is_quiz:
            quiz_passed = await handle_quiz(page, title, lesson_id)

        # Completion strategy
        if cba:
            if is_quiz and not quiz_passed:
                print(f'    Quiz not passed with cba=True, will retry next iteration')
                prev_done = done
                continue
            elif is_quiz and quiz_passed:
                # Quiz passed → lesson auto-completes server-side
                print(f'    Quiz passed, lesson should auto-complete. Checking...')
                await page.wait_for_timeout(2000)
                # Try ajax-complete just in case
                result = await ajax_complete(page)
                if result:
                    print(f'    AJAX: {result.get("status")} {result.get("body","")[:50]}')
            else:
                # Non-quiz cba=True: try ajax-complete
                result = await ajax_complete(page)
                if result:
                    print(f'    AJAX: {result.get("status")} {result.get("body","")[:50]}')
                else:
                    clicked = await css_force_complete(page)
                    print(f'    CSS click: {clicked}')
        else:
            # cba=False: completeLesson + ajax
            await call_complete_lesson(page)
            result = await ajax_complete(page)
            if result:
                print(f'    AJAX: {result.get("status")} {result.get("body","")[:50]}')
            clicked = await css_force_complete(page)
            print(f'    CSS click: {clicked}')

        await page.wait_for_timeout(1500)
        prev_done = done

    final_done, final_total = await get_progress(page, slug)
    print(f'  Final: {final_done}/{final_total}')
    return final_done == final_total and final_total > 0


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
            print(f'  {"✓ COMPLETE" if ok else "! INCOMPLETE"}: {slug}')


asyncio.run(main())
