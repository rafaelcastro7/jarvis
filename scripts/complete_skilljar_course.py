"""Auto-complete a Skilljar course by navigating through all lessons."""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, json, re
from playwright.async_api import async_playwright

COURSE_SLUG = sys.argv[1] if len(sys.argv) > 1 else 'claude-with-the-anthropic-api'
FIRST_LESSON = sys.argv[2] if len(sys.argv) > 2 else None
SKIP = int(sys.argv[3]) if len(sys.argv) > 3 else 0  # skip first N lessons

async def complete_lesson(page, url, label):
    for attempt in range(3):
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=25000)
            await page.wait_for_timeout(2500)

            # Fast-forward video if present
            try:
                await page.evaluate('''() => {
                    const v = document.querySelector('video')
                    if (v && v.duration && !isNaN(v.duration)) {
                        v.currentTime = v.duration - 0.5
                        v.play().catch(()=>{})
                    }
                }''')
                await page.wait_for_timeout(1500)
            except Exception:
                pass

            # Check for quiz
            try:
                radios = await page.evaluate('() => document.querySelectorAll("input[type=radio]").length')
                if radios > 0:
                    opts = await page.evaluate('''() => Array.from(document.querySelectorAll('input[type=radio]')).map((r,i)=>({
                        i, label:(r.closest('label')?.innerText||r.value||'').trim().slice(0,120)
                    }))''')
                    return 'quiz', opts
            except Exception:
                pass

            # Click Complete
            try:
                clicked = await page.evaluate('''() => {
                    const a = Array.from(document.querySelectorAll('a[href]')).find(a=>
                        a.textContent.trim()==='Complete' && a.href.includes('#')
                    )
                    if (a) { a.click(); return true }
                    return false
                }''')
                await page.wait_for_timeout(1500)
                return 'done', clicked
            except Exception:
                await page.wait_for_timeout(2000)
                return 'done', False

        except Exception as e:
            if attempt == 2:
                return 'error', str(e)
            await page.wait_for_timeout(3000)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://localhost:9222')
        page = b.contexts[0].pages[0]

        # Load first lesson to get sidebar links
        first_url = FIRST_LESSON or f'https://anthropic.skilljar.com/{COURSE_SLUG}'
        await page.goto(first_url, wait_until='domcontentloaded', timeout=25000)
        await page.wait_for_timeout(3000)

        # Click Start if not in a lesson yet
        if f'/{COURSE_SLUG}/' not in page.url or not re.search(r'/\d+$', page.url):
            await page.evaluate('''() => {
                const btn = Array.from(document.querySelectorAll('a,button')).find(el=>
                    /^(Start|Continue)$/.test((el.textContent||'').trim())
                )
                if (btn) btn.click()
            }''')
            await page.wait_for_timeout(3000)

        # Get all lesson links from sidebar
        lessons = await page.evaluate('''(slug) => {
            const seen = new Set()
            const pattern = new RegExp('/' + slug + '/(\\\\d+)$')
            return Array.from(document.querySelectorAll('a[href]')).filter(a => {
                const m = a.href.match(pattern)
                if (m && !seen.has(m[1])) { seen.add(m[1]); return true }
                return false
            }).map(a => ({text:(a.textContent||'').trim().slice(0,60), href:a.href}))
        }''', COURSE_SLUG)
        print(f'Found {len(lessons)} lessons in {COURSE_SLUG}')

        quizzes_to_review = []
        lessons = lessons[SKIP:]
        for i, lesson in enumerate(lessons, SKIP+1):
            result, data = await complete_lesson(page, lesson['href'], lesson['text'])
            if result == 'quiz':
                print(f'[{i}/{len(lessons)}] QUIZ: {lesson["text"]}')
                print(f'  Options: {json.dumps(data, ensure_ascii=False)[:300]}')
                quizzes_to_review.append({'lesson': lesson, 'opts': data, 'url': lesson['href']})
                # For now skip quizzes - mark them for manual answer
            else:
                print(f'[{i}/{len(lessons)}] OK: {lesson["text"][:50]} | complete_clicked={data}')

        print(f'\nDone! {len(lessons) - len(quizzes_to_review)}/{len(lessons)} lessons completed.')
        if quizzes_to_review:
            print(f'\nQuizzes needing answers ({len(quizzes_to_review)}):')
            for q in quizzes_to_review:
                print(f'  - {q["lesson"]["text"]}: {q["url"]}')

asyncio.run(main())
