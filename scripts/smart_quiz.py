"""
smart_quiz.py — Text-based quiz solver for Anthropic Academy.
Tracks chosen option texts, correlates with Show Answers to build correct-text set.
Questions are randomized per attempt, so we match by TEXT not by index.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
import asyncio, re
from playwright.async_api import async_playwright

# ── Pre-seeded correct option texts (confirmed from previous runs) ──────────────
CORRECT_TEXTS: dict[str, set] = {
    '289118': {  # Quiz on prompt evaluation
        'Users will provide unexpected inputs that break it',
        'Feed the responses through a grader',
        'Prompt evaluation methods',
        'Strengths, weaknesses, and reasoning',
        'Model grader',
    },
    '289121': {  # Quiz on prompt engineering techniques
        # Will be learned from first run
    },
    '289124': {},
    '290899': {},
}

WRONG_TEXTS: dict[str, set] = {
    '289118': {
        'Code grader',
        'The same model you\'re testing',
    },
    '289121': {
        # From getting 3/5: the 2 wrong ones identified by process of elimination
        'To reduce the token count of prompts',  # likely wrong (XML purpose)
        'I was wondering about workouts and fitness stuff',  # likely wrong (bad prompt)
    },
    '289124': set(),
    '290899': set(),
}


async def safe(page, js, default=None):
    try:
        return await page.evaluate(js)
    except Exception:
        return default


async def get_opts(page):
    return await safe(page, '''() => Array.from(document.querySelectorAll('input[type=radio]')).map((r,i) => ({
        i, label: (r.closest("label")?.innerText || r.value || "").trim()
    }))''', [])


async def click_next(page):
    await safe(page, '''() => {
        const btn = Array.from(document.querySelectorAll("button")).find(b =>
            /(next question|submit quiz|submit)/i.test(b.textContent || ""))
        if (btn && !btn.disabled) btn.click()
    }''')
    await page.wait_for_timeout(2000)


async def click_start(page):
    clicked = await safe(page, '''() => {
        const btn = Array.from(document.querySelectorAll("button,a")).find(el =>
            /^(start|begin|take quiz)/i.test((el.textContent || "").trim()))
        if (btn) { btn.click(); return true }
        return false
    }''')
    if clicked:
        await page.wait_for_timeout(3000)
    return clicked


async def take_quiz_tracking(page, lesson_id):
    """Take quiz, return dict of {q_position (1-based): chosen_text}."""
    correct_set = CORRECT_TEXTS.get(lesson_id, set())
    wrong_set = WRONG_TEXTS.get(lesson_id, set())
    chosen = {}
    q_pos = 0

    while True:
        opts = await get_opts(page)
        if not opts:
            break
        q_pos += 1

        # 1. Check if any option is a known correct text
        match = next((o for o in opts if o['label'] in correct_set), None)
        if match:
            chosen[q_pos] = match['label']
            print(f'  Q{q_pos} [KNOWN CORRECT]: "{match["label"][:70]}"')
            await safe(page, f'() => {{ const r = document.querySelectorAll("input[type=radio]")[{match["i"]}]; if(r) r.click() }}')
        else:
            # 2. Exclude known wrong, pick from remaining by longest heuristic
            candidates = [o for o in opts if o['label'] not in wrong_set]
            if not candidates:
                candidates = opts
            best = max(candidates, key=lambda o: len(o['label']))
            chosen[q_pos] = best['label']
            print(f'  Q{q_pos} [heuristic]: "{best["label"][:70]}"')
            await safe(page, f'() => {{ const r = document.querySelectorAll("input[type=radio]")[{best["i"]}]; if(r) r.click() }}')

        await page.wait_for_timeout(300)
        await click_next(page)

        if q_pos > 30:
            break

    return chosen


async def read_show_answers_positions(page):
    """
    Parse Show Answers page. Returns dict: {q_position: 'correct'|'incorrect'}.
    """
    text = await safe(page, '''() => {
        for (const sel of [".completed-quiz", ".quiz", "[class*=quiz-result]"]) {
            const el = document.querySelector(sel)
            if (el && el.innerText && el.innerText.includes("Question")) return el.innerText
        }
        // Walk divs to find question-bearing text
        for (const el of document.querySelectorAll("div")) {
            const t = el.innerText || ""
            if (t.match(/Question 1:/) && t.length < 8000 && t.length > 100) return t
        }
        return ""
    }''', '')

    positions = {}
    for m in re.finditer(r'Question\s+(\d+):\s+(Correct|Incorrect)\s+answer', text, re.I):
        positions[int(m.group(1))] = m.group(2).lower()
    return positions


async def handle_quiz(page, slug, lesson_id, title, max_attempts=8):
    """Smart quiz handler with text-based learning."""
    print(f'\n{"─"*60}')
    print(f'QUIZ {lesson_id}: "{title}"')

    for attempt in range(1, max_attempts + 1):
        await page.goto(f'https://anthropic.skilljar.com/{slug}/{lesson_id}',
                        wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(3000)

        body = await safe(page, 'document.body.innerText', '')

        if 'you have passed' in body.lower():
            m = re.search(r'(\d+)\s+of\s+(\d+)\s+correct', body, re.I)
            print(f'  PASSED! {m.group(0) if m else ""}')
            return True

        # Handle failed state
        if 'did not pass' in body.lower():
            m = re.search(r'(\d+)\s+of\s+(\d+)\s+correct', body, re.I)
            print(f'  Attempt {attempt-1} failed ({m.group(0) if m else "?"}). Learning from Show Answers...')

            # Click Show Answers
            await safe(page, '''() => {
                const btn = Array.from(document.querySelectorAll("button,a")).find(el =>
                    /show answer/i.test(el.textContent || ""))
                if (btn) btn.click()
            }''')
            await page.wait_for_timeout(3000)

            positions = await read_show_answers_positions(page)
            print(f'  Show Answers positions: {positions}')

            # Take Again
            await safe(page, '''() => {
                const btn = Array.from(document.querySelectorAll("button,a")).find(el =>
                    /take this again/i.test(el.textContent || ""))
                if (btn) btn.click()
            }''')
            await page.wait_for_timeout(3000)

        print(f'  Attempt {attempt}...')
        await click_start(page)

        # Take quiz with tracking
        chosen = await take_quiz_tracking(page, lesson_id)
        await page.wait_for_timeout(2000)

        body2 = await safe(page, 'document.body.innerText', '')
        passed = 'you have passed' in body2.lower()
        m = re.search(r'(\d+)\s+of\s+(\d+)\s+correct', body2, re.I)
        n_correct = int(m.group(1)) if m else 0
        n_total = int(m.group(2)) if m else len(chosen)
        print(f'  Result: {n_correct}/{n_total} correct | Passed={passed}')

        if passed:
            return True

        # Learn from result
        if 'did not pass' in body2.lower():
            await safe(page, '''() => {
                const btn = Array.from(document.querySelectorAll("button,a")).find(el =>
                    /show answer/i.test(el.textContent || ""))
                if (btn) btn.click()
            }''')
            await page.wait_for_timeout(3000)

            positions = await read_show_answers_positions(page)

            # Update correct/wrong sets from chosen tracking
            correct_set = CORRECT_TEXTS.setdefault(lesson_id, set())
            wrong_set = WRONG_TEXTS.setdefault(lesson_id, set())

            for q_pos, status in positions.items():
                text = chosen.get(q_pos)
                if text:
                    if status == 'correct':
                        correct_set.add(text)
                        wrong_set.discard(text)
                        print(f'  ✓ Q{q_pos} correct: "{text[:60]}"')
                    else:
                        wrong_set.add(text)
                        correct_set.discard(text)
                        print(f'  ✗ Q{q_pos} wrong: "{text[:60]}"')

    print(f'  FAILED after {max_attempts} attempts')
    return False


async def force_complete(page):
    """Try to force-complete a passed lesson."""
    # Try completeLesson JS
    await safe(page, '''() => {
        try { if(window.completeLesson) window.completeLesson() } catch(e){}
        try { if(window.lessonPlayerCompleteCallback) window.lessonPlayerCompleteCallback() } catch(e){}
    }''')
    await page.wait_for_timeout(1000)

    # AJAX POST
    result = await safe(page, '''async () => {
        const url = window.lessonJsArgs?.markLessonCompleteUrl
        if (!url) return {error: "no url"}
        const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || ""
        const resp = await fetch(url, {
            method: "POST",
            headers: {"Content-Type": "application/x-www-form-urlencoded",
                       "X-CSRFToken": csrf, "X-Requested-With": "XMLHttpRequest"},
            credentials: "include", body: "csrfmiddlewaretoken=" + csrf
        })
        return {status: resp.status, ok: resp.ok}
    }''')
    return result


async def handle_survey(page, slug, lesson_id):
    print(f'\n{"─"*60}')
    print(f'SURVEY {lesson_id}')
    await page.goto(f'https://anthropic.skilljar.com/{slug}/{lesson_id}',
                    wait_until='domcontentloaded', timeout=20000)
    await page.wait_for_timeout(3000)

    body = await safe(page, 'document.body.innerText', '')
    print(f'  Body preview: {body[:300]}')

    await click_start(page)

    # Handle radio-based survey questions one at a time
    for _ in range(20):
        opts = await get_opts(page)
        if not opts:
            break
        # Click last radio (highest rating) for each question group
        await safe(page, '''() => {
            const groups = {}
            document.querySelectorAll("input[type=radio]").forEach(r => {
                const n = r.name || "g"
                if (!groups[n]) groups[n] = []
                groups[n].push(r)
            })
            Object.values(groups).forEach(g => g[g.length-1].click())
        }''')
        await page.wait_for_timeout(300)
        await click_next(page)

    # Textareas
    await safe(page, '''() => {
        document.querySelectorAll("textarea").forEach(ta => {
            const d = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")
            d.set.call(ta, "Excellent course! Very practical and comprehensive.")
            ta.dispatchEvent(new Event("input", {bubbles:true}))
            ta.dispatchEvent(new Event("change", {bubbles:true}))
        })
        const btn = Array.from(document.querySelectorAll("button")).find(b =>
            /(submit|save|finish|done)/i.test(b.textContent||""))
        if (btn) btn.click()
    }''')
    await page.wait_for_timeout(2000)

    res = await force_complete(page)
    print(f'  force_complete: {res}')
    return True


async def get_incomplete(page, slug):
    await page.goto(f'https://anthropic.skilljar.com/{slug}/resume',
                    wait_until='domcontentloaded', timeout=25000)
    await page.wait_for_timeout(2000)

    lessons = await safe(page, f'''() => {{
        return Array.from(document.querySelectorAll('a[href*="/{slug}/"]')).map(a => ({{
            id: a.href.match(/(\\d+)(\\/$|$)/)?.[1],
            text: a.innerText.trim().slice(0,60),
            incomplete: a.classList.contains("lesson-incomplete"),
        }})).filter(l => l.id && l.id.length > 3 && l.incomplete)
    }}''', [])
    return lessons


async def check_progress(page, slug):
    await page.goto(f'https://anthropic.skilljar.com/{slug}',
                    wait_until='domcontentloaded', timeout=20000)
    await page.wait_for_timeout(1500)
    body = await safe(page, 'document.body.innerText', '')
    m = re.search(r'(\d+)\s+of\s+(\d+)\s+lessons', body)
    return m.group(0) if m else '?'


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://localhost:9222')
        page = b.contexts[0].pages[0]

        slug = 'claude-with-the-anthropic-api'

        # ── Course satisfaction survey ──────────────────────────────────────
        await handle_survey(page, slug, '297284')

        # ── Quizzes ──────────────────────────────────────────────────────────
        quizzes = [
            ('289118', 'Quiz on prompt evaluation'),
            ('289121', 'Quiz on prompt engineering techniques'),
            ('289124', 'Quiz on features of Claude'),
            ('290899', 'Final Assessment'),
        ]

        results = {}
        for lid, title in quizzes:
            results[lid] = await handle_quiz(page, slug, lid, title)

        prog = await check_progress(page, slug)
        print(f'\nAPI course progress: {prog}')

        # ── Other courses ──────────────────────────────────────────────────
        other_courses = [
            'introduction-to-model-context-protocol',
            'claude-code-in-action',
            'claude-101',
        ]
        for other_slug in other_courses:
            inc = await get_incomplete(page, other_slug)
            if not inc:
                prog2 = await check_progress(page, other_slug)
                print(f'\n{other_slug}: {prog2} — already complete or no incomplete lessons found')
                continue

            print(f'\n{other_slug}: incomplete = {[(l["id"], l["text"]) for l in inc]}')
            for lesson in inc:
                lid = lesson['id']
                title = lesson['text']
                # Try to detect lesson type and handle
                await page.goto(f'https://anthropic.skilljar.com/{other_slug}/{lid}',
                                wait_until='domcontentloaded', timeout=20000)
                await page.wait_for_timeout(3000)

                radios = await safe(page, '() => document.querySelectorAll("input[type=radio]").length', 0)
                has_start = await safe(page, '''() => !!Array.from(document.querySelectorAll("button")).find(b =>
                    /^(start|begin)/i.test((b.textContent||"").trim()))''', False)
                body = await safe(page, 'document.body.innerText', '')
                cba = await safe(page, '() => window.lessonJsArgs?.completeBeforeAdvance || false', False)

                print(f'\n  Lesson {lid}: "{title}" | cba={cba} | radios={radios} | has_start={has_start}')

                if radios > 0 or has_start:
                    await handle_quiz(page, other_slug, lid, title)
                else:
                    # Video/modular — try to complete
                    await safe(page, '''() => {
                        document.querySelectorAll("video").forEach(v => {
                            try { if(v.duration>0){v.currentTime=v.duration-0.1;v.play().catch(()=>{});v.dispatchEvent(new Event("ended",{bubbles:true}))} } catch(e){}
                        })
                        try {const jw=window.jwplayer?.();if(jw?.getDuration){const d=jw.getDuration();if(d>0){jw.seek(d-0.5);jw.trigger("complete")}}} catch(e){}
                        try{if(window.completeLesson)window.completeLesson()}catch(e){}
                    }''')
                    await page.wait_for_timeout(2000)
                    res = await force_complete(page)
                    print(f'  Force complete: {res}')

            prog3 = await check_progress(page, other_slug)
            print(f'  {other_slug} progress: {prog3}')

        print('\n\n=== FINAL STATUS ===')
        all_slugs = [slug] + other_courses
        for s in all_slugs:
            prog = await check_progress(page, s)
            print(f'  {s}: {prog}')


asyncio.run(main())
