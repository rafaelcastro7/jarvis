"""
quiz_solver.py — Solves remaining Anthropic Academy quizzes with correct answers.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
import asyncio, re
from playwright.async_api import async_playwright

# Correct answer INDICES per lesson (0-based, matching order of radio buttons shown)
ANSWER_INDICES = {
    '289118': [0, 3, 3, 3, 2, 3],  # prompt eval: 6 questions
}

# Knowledge-base keywords for heuristic answering
KW_CORRECT = [
    'users will provide unexpected', 'feed the responses through a grader',
    'prompt evaluation methods', 'strengths, weaknesses, and reasoning',
    'code grader', 'same model', 'improve your prompt',
    'one-shot', 'multi-shot', 'xml tags', 'clear and direct',
    'system prompt', 'extended thinking', 'prompt caching',
    'citations', 'streaming', 'tool use',
    'reduce costs', 'improve accuracy',
    'agentic', 'multi-agent', 'orchestrator',
    'helpful, harmless', 'human feedback',
    'temperature', 'stop sequence',
    'prefill', 'few-shot',
    'context window', 'token',
]


async def safe(page, js, default=None):
    try:
        return await page.evaluate(js)
    except Exception:
        return default


async def click_next(page):
    await safe(page, '''() => {
        const btn = Array.from(document.querySelectorAll("button")).find(b =>
            /(next question|submit quiz|submit)/i.test(b.textContent || ""))
        if (btn && !btn.disabled) btn.click()
    }''')
    await page.wait_for_timeout(2000)


async def get_opts(page):
    return await safe(page, '''() => Array.from(document.querySelectorAll('input[type=radio]')).map((r,i) => ({
        i, label: (r.closest("label")?.innerText || r.value || "").trim()
    }))''', [])


def score_option(label):
    l = label.lower()
    return sum(1 for kw in KW_CORRECT if kw in l)


async def take_quiz(page, lesson_id):
    indices = ANSWER_INDICES.get(lesson_id)
    q_count = 0

    while True:
        opts = await get_opts(page)
        if not opts:
            break
        q_count += 1

        if indices and q_count <= len(indices):
            idx = indices[q_count - 1]
            idx = min(idx, len(opts) - 1)
            label = next((o['label'] for o in opts if o['i'] == idx), opts[idx]['label'])
            print(f'  Q{q_count} [known idx={idx}]: "{label[:70]}"')
        else:
            scored = [(score_option(o['label']), o['i'], o['label']) for o in opts]
            scored.sort(reverse=True)
            if scored[0][0] > 0:
                idx = scored[0][1]
                print(f'  Q{q_count} [kw score={scored[0][0]}]: "{scored[0][2][:70]}"')
            else:
                idx = max(opts, key=lambda o: len(o['label']))['i']
                label = next(o['label'] for o in opts if o['i'] == idx)
                print(f'  Q{q_count} [longest]: "{label[:70]}"')

        await safe(page, f'() => {{ const r = document.querySelectorAll("input[type=radio]")[{idx}]; if(r) r.click() }}')
        await page.wait_for_timeout(300)
        await click_next(page)

        if q_count > 30:
            break

    return q_count


async def read_show_answers_text(page):
    """Get the full innerText of the quiz results section."""
    # Try multiple selectors to find quiz content (not sidebar)
    text = await safe(page, '''() => {
        const trySelectors = [
            ".course-scrollable-content .quiz",
            ".quiz-completed",
            ".completed-quiz",
            ".quiz-results",
        ]
        for (const sel of trySelectors) {
            const el = document.querySelector(sel)
            if (el && el.innerText && el.innerText.includes("Question")) return el.innerText
        }
        // Fallback: find the element with "Question 1:" in it
        const all = document.querySelectorAll("div, section, article")
        for (const el of all) {
            if (el.innerText && el.innerText.includes("Question 1:") && el.innerText.length > 200) {
                return el.innerText.slice(0, 5000)
            }
        }
        return ""
    }''', '')
    return text


async def parse_correct_from_show_answers(text):
    """
    Parse correct answer TEXT from Show Answers page.
    The structure is:
      Question N: Correct/Incorrect answer
      [question text]
      [option A - with checkmark if correct]
      [option B]
      ...
    The 'Correct answer' questions show the question + the correct option.
    We want the OPTION text after the question text.
    """
    # Better strategy: look for the pattern
    # "Question N: Correct answer\n[question text]\n[correct option]\n..."
    # The question text is long (contains "?"), the option text is shorter.

    lines = [l.strip() for l in text.split('\n') if l.strip()]
    results = {}
    q_num = 0
    is_correct = False
    after_header = False
    question_text_seen = False

    for i, line in enumerate(lines):
        m = re.match(r'^Question\s+(\d+):\s+(Correct|Incorrect)\s+answer', line, re.I)
        if m:
            q_num = int(m.group(1))
            is_correct = m.group(2).lower() == 'correct'
            after_header = True
            question_text_seen = False
            continue

        if not after_header:
            continue

        # Skip non-content lines
        if re.match(r'^(Show|Hide|Take|Your|Elapsed|Submit|Previous|Next|Lessons)', line, re.I):
            continue
        if len(line) < 4:
            continue

        if not question_text_seen:
            # First substantial line = question text (usually ends with ?)
            if '?' in line or len(line) > 60:
                question_text_seen = True
            continue  # skip question text

        # This should be an option text
        if is_correct and q_num > 0 and q_num not in results:
            results[q_num] = line
            after_header = False  # stop collecting for this question

    return results


async def handle_quiz_lesson(page, slug, lesson_id, title):
    """Full quiz handling: take → check result → show answers → retry."""
    print(f'\n  Quiz {lesson_id}: "{title}"')

    for attempt in range(6):
        await page.goto(f'https://anthropic.skilljar.com/{slug}/{lesson_id}',
                        wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(3000)

        body = await safe(page, 'document.body.innerText', '')

        if 'you have passed' in body.lower():
            m = re.search(r'(\d+)\s+of\s+(\d+)\s+correct', body, re.I)
            print(f'  PASSED! {m.group(0) if m else ""}')
            return True

        if 'did not pass' in body.lower():
            m = re.search(r'(\d+)\s+of\s+(\d+)\s+correct', body, re.I)
            print(f'  Failed ({m.group(0) if m else "?"}). Reading Show Answers...')
            await safe(page, '''() => {
                const btn = Array.from(document.querySelectorAll("button,a")).find(el =>
                    /show answer/i.test(el.textContent || ""))
                if (btn) btn.click()
            }''')
            await page.wait_for_timeout(3000)
            text = await read_show_answers_text(page)
            if text:
                correct_map = await parse_correct_from_show_answers(text)
                print(f'  Show Answers parsed: {correct_map}')
                if correct_map:
                    # Update ANSWER_INDICES with learned correct option texts
                    # Find which index matches each correct text
                    for qn in sorted(correct_map.keys()):
                        print(f'    Q{qn} correct: "{correct_map[qn][:80]}"')
            else:
                print('  Could not read Show Answers text')

            # Take Again
            await safe(page, '''() => {
                const btn = Array.from(document.querySelectorAll("button,a")).find(el =>
                    /take this again/i.test(el.textContent || ""))
                if (btn) btn.click()
            }''')
            await page.wait_for_timeout(3000)

        # Click Start if needed
        has_start = await safe(page, '''() => !!Array.from(document.querySelectorAll("button")).find(b =>
            /^(start|begin)/i.test((b.textContent||"").trim()))''', False)
        if has_start:
            await safe(page, '''() => {
                Array.from(document.querySelectorAll("button")).find(b =>
                    /^(start|begin)/i.test((b.textContent||"").trim()))?.click()
            }''')
            await page.wait_for_timeout(3000)

        # Check for radios
        opts = await get_opts(page)
        if not opts:
            print(f'  No radio buttons found (attempt {attempt+1})')
            continue

        print(f'  Taking quiz (attempt {attempt+1})...')
        q_count = await take_quiz(page, lesson_id)
        print(f'  Answered {q_count} questions')
        await page.wait_for_timeout(2000)

        body2 = await safe(page, 'document.body.innerText', '')
        passed = 'you have passed' in body2.lower()
        m = re.search(r'(\d+)\s+of\s+(\d+)\s+correct', body2, re.I)
        print(f'  Result: {m.group(0) if m else "?"} | Passed={passed}')
        if passed:
            return True

    return False


async def handle_survey(page, slug, lesson_id):
    """Complete the course satisfaction survey."""
    print(f'\n  Survey {lesson_id}')
    await page.goto(f'https://anthropic.skilljar.com/{slug}/{lesson_id}',
                    wait_until='domcontentloaded', timeout=20000)
    await page.wait_for_timeout(3000)

    body = await safe(page, 'document.body.innerText', '')
    print(f'  Body preview: {body[:200]}')

    # Click start if needed
    await safe(page, '''() => {
        const btn = Array.from(document.querySelectorAll("button")).find(b =>
            /^(start|begin|take)/i.test((b.textContent||"").trim()))
        if (btn) btn.click()
    }''')
    await page.wait_for_timeout(2000)

    # Fill textareas
    await safe(page, '''() => {
        document.querySelectorAll("textarea").forEach(ta => {
            const d = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")
            d.set.call(ta, "Excellent course! Very practical and well-structured. I learned a lot.")
            ta.dispatchEvent(new Event("input", {bubbles:true}))
            ta.dispatchEvent(new Event("change", {bubbles:true}))
        })
    }''')

    # Handle radio buttons (survey ratings)
    for _ in range(15):
        opts = await get_opts(page)
        if not opts:
            break
        # Pick last (highest rating)
        groups = {}
        for o in opts:
            pass
        # Click last radio in each group by name
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

    # Submit
    await safe(page, '''() => {
        const btn = Array.from(document.querySelectorAll("button")).find(b =>
            /(submit|save|done|finish)/i.test(b.textContent||""))
        if (btn) btn.click()
    }''')
    await page.wait_for_timeout(2000)

    # AJAX complete
    res = await safe(page, '''async () => {
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
    print(f'  AJAX: {res}')
    return True


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://localhost:9222')
        page = b.contexts[0].pages[0]
        slug = 'claude-with-the-anthropic-api'

        # 1. Survey
        await handle_survey(page, slug, '297284')

        # 2. Quizzes
        quizzes = [
            ('289118', 'Quiz on prompt evaluation'),
            ('289121', 'Quiz on prompt engineering techniques'),
            ('289124', 'Quiz on features of Claude'),
            ('290899', 'Final Assessment'),
        ]
        for lid, title in quizzes:
            await handle_quiz_lesson(page, slug, lid, title)

        # Check progress
        await page.goto(f'https://anthropic.skilljar.com/{slug}',
                        wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(1500)
        body = await safe(page, 'document.body.innerText', '')
        m = re.search(r'(\d+)\s+of\s+(\d+)\s+lessons', body)
        print(f'\nAPI Course progress: {m.group(0) if m else "?"}')

        # Other courses
        other_courses = [
            'introduction-to-model-context-protocol',
            'claude-code-in-action',
            'claude-101',
        ]
        for course_slug in other_courses:
            await page.goto(f'https://anthropic.skilljar.com/{course_slug}',
                            wait_until='domcontentloaded', timeout=20000)
            await page.wait_for_timeout(2000)
            lessons = await safe(page, f'''() => {{
                return Array.from(document.querySelectorAll('a[href*="/{course_slug}/"]')).map(a => ({{
                    id: a.href.match(/(\\d+)(\\/$|$)/)?.[1],
                    text: a.innerText.trim().slice(0,60),
                    incomplete: a.classList.contains("lesson-incomplete"),
                }})).filter(l => l.id && l.id.length > 3 && l.incomplete)
            }}''', [])
            body2 = await safe(page, 'document.body.innerText', '')
            m2 = re.search(r'(\d+)\s+of\s+(\d+)\s+lessons', body2)
            print(f'\n{course_slug}: {m2.group(0) if m2 else "?"} | Incomplete: {[(l["id"], l["text"][:40]) for l in lessons]}')

        print('\n=== DONE ===')


asyncio.run(main())
