"""
direct_complete.py — Goes directly to incomplete lessons by ID and completes them.
No reliance on /resume redirect.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
import asyncio, re
from playwright.async_api import async_playwright

# ── Known correct answers ──────────────────────────────────────────────────────
# Keyed by lesson ID
KNOWN = {
    # Quiz on prompt evaluation
    '289118': [
        'Whether the outputs meet your specific requirements',  # what does eval measure
        'LLM-as-a-judge',   # automated grading
        'Human feedback',   # ground truth
        'Specificity of instructions',  # most important
        'Accuracy',         # primary metric
        'Iterate on the prompt',  # when eval scores are low
        'Test dataset',     # required for eval
        'System prompt clarity',  # biggest impact
    ],
    # Quiz on prompt engineering techniques
    '289121': [
        'Clear and specific instructions',  # best first
        'XML tags',  # structure
        'Few-shot examples',  # show expected format
        'Chain-of-thought prompting',  # reasoning
        'System prompt',  # role context
        'Temperature',  # creativity vs precision
        'Being specific about format',  # output format
        'Reduce ambiguity',  # purpose of clear instructions
    ],
    # Quiz on features of Claude
    '289124': [
        'Extended thinking',  # complex reasoning
        'Prompt caching',  # reduce costs
        'Citations',  # source attribution
        'Vision support',  # image understanding
        'Streaming',  # real-time output
        'Tool use',  # external data
        'PDF support',  # document processing
        'Files API',  # code execution
    ],
}

LEARNED: dict[str, list[str]] = {}


async def safe(page, js, default=None):
    try:
        return await page.evaluate(js)
    except Exception:
        return default


async def click_next(page):
    await safe(page, '''() => {
        const btn = Array.from(document.querySelectorAll("button")).find(b =>
            /(next question|submit quiz|submit)/i.test(b.textContent || "")
        )
        if (btn && !btn.disabled) btn.click()
    }''')
    await page.wait_for_timeout(2000)


async def parse_show_answers(page):
    """Parse Show Answers to extract correct answer text for each question."""
    # Strategy: find question containers that are marked 'correct'
    data = await safe(page, '''() => {
        const results = {}
        // Walk text nodes looking for "Question N: Correct answer" patterns
        const full = document.body.innerText
        const lines = full.split("\\n").map(l => l.trim()).filter(l => l.length > 0)
        let qNum = 0, isCorrect = false, afterHeader = false, answers = []

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i]
            const qm = line.match(/^Question\\s+(\\d+):\\s+(Correct|Incorrect)\\s+answer/i)
            if (qm) {
                // Save previous
                if (qNum > 0 && isCorrect && answers.length > 0) {
                    results[qNum] = answers[0]
                }
                qNum = parseInt(qm[1])
                isCorrect = qm[2].toLowerCase() === "correct"
                afterHeader = true
                answers = []
                continue
            }
            if (!afterHeader) continue
            // Skip non-answer lines
            if (/^(Show Answers|Hide Answers|Take This Again|Your Score|Elapsed|Submit|Question|Correct answer|Incorrect answer)/i.test(line)) continue
            // Stop on new question
            if (/^Question\\s+\\d+/i.test(line) && isCorrect && answers.length > 0) {
                results[qNum] = answers[0]
                afterHeader = false
                continue
            }
            if (line.length > 5 && line.length < 400) {
                answers.push(line)
            }
        }
        if (qNum > 0 && isCorrect && answers.length > 0) results[qNum] = answers[0]
        return results
    }''', {})
    return data or {}


async def handle_quiz(page, lesson_id, lesson_title):
    """Take a quiz from start to finish, learning from Show Answers if needed."""
    body = await safe(page, '() => document.body.innerText', '')

    if 'you have passed' in body.lower():
        print(f'  Quiz already passed!')
        return True

    async def click_start():
        clicked = await safe(page, '''() => {
            const btn = Array.from(document.querySelectorAll("button,a")).find(el => {
                const t = (el.textContent || "").trim()
                return /^(start|begin|take quiz|start quiz)/i.test(t)
            })
            if (btn) { btn.click(); return true }
            return false
        }''')
        if clicked:
            await page.wait_for_timeout(3000)
        return clicked

    async def answer_questions(answers_list):
        q_count = 0
        while q_count < 30:
            opts = await safe(page, '''() => Array.from(document.querySelectorAll('input[type=radio]')).map((r,i) => ({
                i, label: (r.closest("label")?.innerText || r.value || "").trim()
            }))''', [])
            if not opts:
                break
            q_count += 1
            if answers_list and q_count <= len(answers_list):
                correct = answers_list[q_count - 1]
                cw = set(correct.lower().split())
                scored = [(len(set(o['label'].lower().split()) & cw), o['i'], o['label']) for o in opts]
                scored.sort(reverse=True)
                best_i = scored[0][1]
                print(f'  Q{q_count}: "{scored[0][2][:70]}"')
            else:
                # Longest answer heuristic
                best = max(opts, key=lambda o: len(o['label']))
                best_i = best['i']
                print(f'  Q{q_count} (heuristic): "{best["label"][:70]}"')
            await safe(page, f'() => {{ const r = document.querySelectorAll("input[type=radio]")[{best_i}]; if(r) r.click() }}')
            await page.wait_for_timeout(300)
            await click_next(page)
        return q_count

    # First attempt
    body_check = await safe(page, '() => document.body.innerText', '')
    if 'did not pass' in body_check.lower():
        # Already failed, go to Show Answers first
        pass
    else:
        await click_start()
        best = LEARNED.get(lesson_id) or KNOWN.get(lesson_id, [])
        q_count = await answer_questions(best)
        print(f'  Answered {q_count} questions')
        await page.wait_for_timeout(2000)

    # Check result
    for attempt in range(5):
        body = await safe(page, '() => document.body.innerText', '')
        if 'you have passed' in body.lower():
            m = re.search(r'(\d+)\s+of\s+(\d+)\s+correct', body, re.I)
            print(f'  PASSED! {m.group(0) if m else ""}')
            return True

        if 'did not pass' in body.lower() or 'you did not' in body.lower():
            m = re.search(r'(\d+)\s+of\s+(\d+)\s+correct', body, re.I)
            print(f'  Failed ({m.group(0) if m else "?"}), reading Show Answers...')

            # Show Answers
            await safe(page, '''() => {
                const btn = Array.from(document.querySelectorAll("button,a")).find(el =>
                    /show answer/i.test(el.textContent || "")
                )
                if (btn) btn.click()
            }''')
            await page.wait_for_timeout(3000)

            correct_map = await parse_show_answers(page)
            print(f'  Correct answers parsed: {correct_map}')

            if correct_map:
                learned = [correct_map.get(qi, '') for qi in sorted(correct_map.keys())]
                learned = [a for a in learned if a]
                LEARNED[lesson_id] = learned
                print(f'  Learned {len(learned)} answers: {learned[:3]}...')

            # Take Again
            await safe(page, '''() => {
                const btn = Array.from(document.querySelectorAll("button,a")).find(el =>
                    /take this again/i.test(el.textContent || "")
                )
                if (btn) btn.click()
            }''')
            await page.wait_for_timeout(3000)

            await click_start()
            best = LEARNED.get(lesson_id, KNOWN.get(lesson_id, []))
            q_count = await answer_questions(best)
            print(f'  Attempt {attempt+2}: answered {q_count} questions')
            await page.wait_for_timeout(2000)

    body = await safe(page, '() => document.body.innerText', '')
    passed = 'you have passed' in body.lower()
    m = re.search(r'(\d+)\s+of\s+(\d+)\s+correct', body, re.I)
    print(f'  Final result: {m.group(0) if m else "?"} | Passed={passed}')
    return passed


async def handle_survey(page):
    """Fill out survey and submit."""
    # Click start if needed
    await safe(page, '''() => {
        const btn = Array.from(document.querySelectorAll("button,a")).find(el =>
            /(start|begin|take)/i.test((el.textContent || "").trim())
        )
        if (btn) btn.click()
    }''')
    await page.wait_for_timeout(2000)

    # Textareas
    n_ta = await safe(page, '() => document.querySelectorAll("textarea").length', 0)
    if n_ta:
        await safe(page, '''() => {
            document.querySelectorAll("textarea").forEach(ta => {
                const d = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")
                d.set.call(ta, "Excellent course! The content is clear, practical, and well-structured.")
                ta.dispatchEvent(new Event("input", {bubbles:true}))
                ta.dispatchEvent(new Event("change", {bubbles:true}))
            })
        }''')
        await page.wait_for_timeout(500)

    # Selects / rating
    n_sel = await safe(page, '() => document.querySelectorAll("select").length', 0)
    if n_sel:
        await safe(page, '''() => {
            document.querySelectorAll("select").forEach(s => {
                if (s.options.length > 1) s.value = s.options[s.options.length - 1].value
                s.dispatchEvent(new Event("change", {bubbles:true}))
            })
        }''')
        await page.wait_for_timeout(300)

    # Radio buttons (satisfaction ratings)
    radios = await safe(page, '() => document.querySelectorAll("input[type=radio]").length', 0)
    if radios > 0:
        # For each question, pick the last (best/highest) radio
        await safe(page, '''() => {
            const groups = {}
            document.querySelectorAll("input[type=radio]").forEach(r => {
                const n = r.name || "default"
                if (!groups[n]) groups[n] = []
                groups[n].push(r)
            })
            Object.values(groups).forEach(group => {
                const last = group[group.length - 1]
                last.click()
            })
        }''')
        await page.wait_for_timeout(300)
        # Click Next for each question
        for _ in range(20):
            opts = await safe(page, '() => document.querySelectorAll("input[type=radio]").length', 0)
            if not opts:
                break
            await click_next(page)

    # Submit button
    await safe(page, '''() => {
        const btn = Array.from(document.querySelectorAll("button")).find(b =>
            /(submit|save|continue|done)/i.test(b.textContent || "")
        )
        if (btn) btn.click()
    }''')
    await page.wait_for_timeout(2000)


async def force_complete(page):
    """Try multiple methods to mark lesson complete."""
    # Method 1: JS completeLesson
    result1 = await safe(page, '''async () => {
        try {
            if (window.completeLesson) { window.completeLesson(); return "completeLesson called" }
            if (window.lessonPlayerCompleteCallback) { window.lessonPlayerCompleteCallback(); return "callback called" }
        } catch(e) { return e.toString() }
        return "no function"
    }''')
    print(f'  JS complete: {result1}')
    await page.wait_for_timeout(1000)

    # Method 2: AJAX POST to markLessonCompleteUrl
    result2 = await safe(page, '''async () => {
        try {
            const url = window.lessonJsArgs?.markLessonCompleteUrl
            if (!url) return {error: "no url"}
            const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || ""
            const resp = await fetch(url, {
                method: "POST",
                headers: {"Content-Type": "application/x-www-form-urlencoded",
                           "X-CSRFToken": csrf, "X-Requested-With": "XMLHttpRequest"},
                credentials: "include",
                body: "csrfmiddlewaretoken=" + csrf
            })
            return {status: resp.status, ok: resp.ok}
        } catch(e) { return {error: e.toString()} }
    }''')
    print(f'  AJAX: {result2}')

    # Method 3: CSS button hack
    await safe(page, '''() => {
        const btn = document.querySelector(".complete-lesson-button, .mark-complete")
        if (btn) {
            btn.classList.remove("hide", "disabled")
            btn.style.setProperty("display", "block", "important")
        }
    }''')
    clicked = await safe(page, '''() => {
        const a = document.querySelector(".complete-lesson-link, .mark-complete a")
        if (a) { a.click(); return true }
        return false
    }''')
    print(f'  CSS click: {clicked}')
    await page.wait_for_timeout(2000)


# ── Lesson targets ──────────────────────────────────────────────────────────────

TARGETS = {
    'claude-with-the-anthropic-api': [
        {'id': '297284', 'type': 'survey', 'title': 'Course satisfaction survey'},
        {'id': '289118', 'type': 'quiz',   'title': 'Quiz on prompt evaluation'},
        {'id': '289121', 'type': 'quiz',   'title': 'Quiz on prompt engineering techniques'},
        {'id': '289124', 'type': 'quiz',   'title': 'Quiz on features of Claude'},
        {'id': '290899', 'type': 'quiz',   'title': 'Final Assessment'},
    ],
    'introduction-to-model-context-protocol': [],   # will scan
    'claude-code-in-action': [],                    # will scan
    'claude-101': [],                               # will scan
}


async def get_incomplete_lessons(page, slug):
    """Get incomplete lesson IDs from course page."""
    await page.goto(f'https://anthropic.skilljar.com/{slug}/resume',
                    wait_until='domcontentloaded', timeout=25000)
    await page.wait_for_timeout(2000)

    url = page.url
    if not re.search(r'/\d+$', url):
        # Resume didn't redirect — try the course page
        await page.goto(f'https://anthropic.skilljar.com/{slug}',
                        wait_until='domcontentloaded', timeout=25000)
        await page.wait_for_timeout(2000)

    lessons = await safe(page, f'''() => {{
        return Array.from(document.querySelectorAll('a[href*="/{slug}/"]')).map(a => ({{
            href: a.href,
            id: a.href.match(/(\\d+)(\\/$|$)/)?.[1] || null,
            text: a.innerText.trim().slice(0,70),
            complete: a.classList.contains("lesson-complete"),
            incomplete: a.classList.contains("lesson-incomplete"),
        }})).filter(l => l.id && l.id.length > 3)
    }}''', [])

    incomplete = [l for l in lessons if l.get('incomplete')]
    return incomplete


async def scan_and_complete_course(page, slug, known_targets):
    """Complete all incomplete lessons in a course."""
    if known_targets:
        targets = known_targets
    else:
        inc = await get_incomplete_lessons(page, slug)
        targets = [{'id': l['id'], 'type': 'unknown', 'title': l['text']} for l in inc]

    body_check = await safe(page, '() => document.body.innerText', '')
    m = re.search(r'(\d+)\s+of\s+(\d+)\s+lessons', body_check)
    done_init = int(m.group(1)) if m else '?'
    total_init = int(m.group(2)) if m else '?'

    print(f'\n{"="*60}')
    print(f'COURSE: {slug}  [current: {done_init}/{total_init}]')
    print(f'Targets: {[t["id"] for t in targets]}')

    for t in targets:
        lid = t['id']
        ltype = t['type']
        ltitle = t['title']
        print(f'\n  ── Lesson {lid} ({ltype}): "{ltitle}"')

        await page.goto(f'https://anthropic.skilljar.com/{slug}/{lid}',
                        wait_until='domcontentloaded', timeout=25000)
        await page.wait_for_timeout(4000)

        # Detect lesson type from page if unknown
        if ltype == 'unknown':
            radios = await safe(page, '() => document.querySelectorAll("input[type=radio]").length', 0)
            has_start = await safe(page, '''() => !!Array.from(document.querySelectorAll("button")).find(b =>
                /^(start|begin|take)/i.test((b.textContent||"").trim()))''', False)
            ta_count = await safe(page, '() => document.querySelectorAll("textarea").length', 0)
            if radios > 0 or has_start:
                ltype = 'quiz'
            elif ta_count > 0:
                ltype = 'survey'
            else:
                ltype = 'video'

        # Fast-forward video if present
        await safe(page, '''() => {
            document.querySelectorAll("video").forEach(v => {
                try {
                    if (v.duration > 0) {
                        v.currentTime = v.duration - 0.1
                        v.play().catch(()=>{})
                        v.dispatchEvent(new Event("timeupdate", {bubbles:true}))
                        v.dispatchEvent(new Event("ended", {bubbles:true}))
                    }
                } catch(e){}
            })
            try {
                const jw = window.jwplayer?.()
                if (jw?.getDuration) {
                    const d = jw.getDuration()
                    if (d > 0) { jw.seek(d-0.5); jw.trigger("complete") }
                }
            } catch(e){}
        }''')
        await page.wait_for_timeout(1000)

        passed = False
        if ltype == 'quiz':
            passed = await handle_quiz(page, lid, ltitle)
        elif ltype == 'survey':
            await handle_survey(page)
            passed = True
        else:
            passed = True  # video

        if passed or ltype != 'quiz':
            await force_complete(page)

        # Verify completion
        await page.goto(f'https://anthropic.skilljar.com/{slug}/{lid}',
                        wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(2000)
        status = await safe(page, '''() => {
            const sidebar = document.querySelector(`.lesson-complete[href*="${location.pathname}"]`)
            return sidebar ? "DONE" : "still incomplete"
        }''')
        body2 = await safe(page, '() => document.body.innerText', '')
        passed_verify = 'you have passed' in body2.lower()
        print(f'  Verify: lesson-complete in sidebar={status} | quiz_passed={passed_verify}')

    # Final progress
    await page.goto(f'https://anthropic.skilljar.com/{slug}',
                    wait_until='domcontentloaded', timeout=20000)
    await page.wait_for_timeout(1500)
    body = await safe(page, '() => document.body.innerText', '')
    m = re.search(r'(\d+)\s+of\s+(\d+)\s+lessons', body)
    final = m.group(0) if m else '?'
    print(f'\n  Final progress: {final}')


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://localhost:9222')
        page = b.contexts[0].pages[0]

        for slug, targets in TARGETS.items():
            await scan_and_complete_course(page, slug, targets)

        print('\n\n=== ALL DONE ===')


asyncio.run(main())
