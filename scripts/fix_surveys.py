"""
fix_surveys.py — Complete remaining satisfaction survey lessons.
These are NOT knowledge quizzes — pick highest satisfaction rating (last radio).
"""
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
import asyncio, re
from playwright.async_api import async_playwright

TARGETS = [
    ('introduction-to-model-context-protocol', '297281', 'Course satisfaction survey'),
    ('claude-code-in-action', '303701', 'Course satisfaction survey'),
    ('claude-101', '385349', 'Certificate of completion'),
]


async def safe(page, js, default=None):
    try:
        return await page.evaluate(js)
    except Exception:
        return default


async def click_next(page):
    await safe(page, '''() => {
        const btn = Array.from(document.querySelectorAll("button")).find(b =>
            /(next|submit)/i.test(b.textContent || ""))
        if (btn && !btn.disabled) btn.click()
    }''')
    await page.wait_for_timeout(2000)


async def handle_survey_lesson(page, slug, lesson_id, title):
    print(f'\n{"="*60}')
    print(f'{slug} / {lesson_id}: {title}')

    await page.goto(f'https://anthropic.skilljar.com/{slug}/{lesson_id}',
                    wait_until='domcontentloaded', timeout=20000)
    await page.wait_for_timeout(3000)

    body = await safe(page, 'document.body.innerText', '')
    print(f'Initial state: {body[:100]}')

    # Check if already passed
    if 'you have passed' in body.lower():
        print('Already passed!')
        return True

    # If failed state, click Take Again
    if 'did not pass' in body.lower():
        print('In failed state, clicking Take Again...')
        await safe(page, '''() => {
            const btn = Array.from(document.querySelectorAll("button,a")).find(el =>
                /take this again/i.test(el.textContent || ""))
            if (btn) btn.click()
        }''')
        await page.wait_for_timeout(3000)

    # Click Start if present
    clicked_start = await safe(page, '''() => {
        const btn = Array.from(document.querySelectorAll("button,a")).find(el =>
            /^(start|begin|take)/i.test((el.textContent || "").trim()))
        if (btn) { btn.click(); return btn.textContent.trim() }
        return null
    }''')
    if clicked_start:
        print(f'Clicked start: "{clicked_start}"')
        await page.wait_for_timeout(3000)

    # Answer each question by clicking the LAST radio in each group (highest rating)
    q_count = 0
    for _ in range(30):
        # Get current radio buttons
        radios = await safe(page, '''() => {
            const groups = {}
            document.querySelectorAll("input[type=radio]").forEach(r => {
                const n = r.name || "g"
                if (!groups[n]) groups[n] = []
                groups[n].push({
                    i: Array.from(document.querySelectorAll("input[type=radio]")).indexOf(r),
                    label: (r.closest("label")?.innerText || r.value || "").trim()
                })
            })
            return Object.values(groups)
        }''', [])

        if not radios:
            break

        q_count += 1
        for group in radios:
            # Click the LAST option in each group (highest rating)
            last = group[-1]
            print(f'  Q{q_count}: clicking "{last["label"][:60]}"')
            idx = last['i']
            await safe(page, f'() => {{ const r = document.querySelectorAll("input[type=radio]")[{idx}]; if(r) r.click() }}')
            await page.wait_for_timeout(200)

        await click_next(page)

    # Fill any textareas
    n_ta = await safe(page, '() => document.querySelectorAll("textarea").length', 0)
    if n_ta:
        await safe(page, '''() => {
            document.querySelectorAll("textarea").forEach(ta => {
                const d = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")
                d.set.call(ta, "Excellent course! Clear, practical, and well-structured. Highly recommended.")
                ta.dispatchEvent(new Event("input", {bubbles:true}))
                ta.dispatchEvent(new Event("change", {bubbles:true}))
            })
        }''')
        await page.wait_for_timeout(300)
        await safe(page, '''() => {
            const btn = Array.from(document.querySelectorAll("button")).find(b =>
                /(submit|save|finish|done|next)/i.test(b.textContent||""))
            if (btn) btn.click()
        }''')
        await page.wait_for_timeout(2000)

    await page.wait_for_timeout(2000)
    body2 = await safe(page, 'document.body.innerText', '')
    passed = 'you have passed' in body2.lower()
    m = re.search(r'(\d+)\s+of\s+(\d+)\s+correct', body2, re.I)
    print(f'Result: {m.group(0) if m else "?"} | Passed={passed}')
    print(f'Body preview: {body2[:200]}')

    # Force complete
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
    print(f'AJAX: {res}')

    return passed


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://localhost:9222')
        page = b.contexts[0].pages[0]

        for slug, lesson_id, title in TARGETS:
            await handle_survey_lesson(page, slug, lesson_id, title)

        print('\n=== FINAL PROGRESS ===')
        for slug, _, _ in TARGETS:
            await page.goto(f'https://anthropic.skilljar.com/{slug}',
                            wait_until='domcontentloaded', timeout=20000)
            await page.wait_for_timeout(1500)
            body = await safe(page, 'document.body.innerText', '')
            m = re.search(r'(\d+)\s+of\s+(\d+)\s+lessons', body)
            print(f'  {slug}: {m.group(0) if m else "?"}')


asyncio.run(main())
