"""
DevCompass Claude Certified Architect Prep — Full Scraper v3
70 lecciones via click en botones del sidebar.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright

COURSE_URL = "https://www.devcompass.ai/course/claude-certified-architect-prep/dashboard"
OUT = Path("E:/Documents/PROYECTOS/AgencIA/platzi_clone/downloads/devcompass")
OUT.mkdir(parents=True, exist_ok=True)

def safe_name(s, max_len=80):
    return re.sub(r'[^\w\-]', '_', s)[:max_len].strip('_') or 'untitled'

async def main():
    print("[DevCompass Full] 70 lecciones")

    async with async_playwright() as p:
        browser = None
        for port in [9222, 9223]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://localhost:{port}")
                print(f"✅ CDP port {port}")
                break
            except Exception:
                pass

        if not browser:
            print("❌ No CDP disponible")
            return

        page = None
        for c in browser.contexts:
            for pg in c.pages:
                page = pg
                break
            if page:
                break
        if not page:
            page = await browser.contexts[0].new_page()

        # Navigate to course
        await page.goto(COURSE_URL, wait_until="networkidle", timeout=45000)
        await page.wait_for_timeout(4000)
        print(f"URL: {page.url}")

        # Get all lesson buttons
        lesson_buttons = await page.evaluate("""() => {
            const items = []
            document.querySelectorAll('button').forEach((btn, i) => {
                const text = (btn.textContent?.trim() || '').replace(/\\s+/g, ' ')
                // Lecciones tienen número al inicio: "2What is an LLM..."
                const match = text.match(/^(\\d+)(.+)/)
                if (match) {
                    items.push({
                        index: parseInt(match[1]),
                        title: match[2].trim().slice(0, 120),
                        full_text: text.slice(0, 130),
                        btn_index: i
                    })
                }
            })
            return items
        }""")

        print(f"Lecciones encontradas: {len(lesson_buttons)}")
        for l in lesson_buttons[:5]:
            print(f"  [{l['index']}] {l['title'][:60]}")

        all_lessons = []
        done_file = OUT / "progress_devcompass.json"

        # Load existing progress
        done_indices = set()
        if done_file.exists():
            try:
                existing = json.loads(done_file.read_text(encoding='utf-8'))
                done_indices = {l['index'] for l in existing}
                all_lessons = existing
                print(f"Progreso previo: {len(done_indices)} lecciones")
            except Exception:
                pass

        for lesson_info in lesson_buttons:
            idx = lesson_info['index']
            title = lesson_info['title']
            btn_idx = lesson_info['btn_index']

            if idx in done_indices:
                print(f"  [{idx:02d}] ✅ Ya scrapeado: {title[:50]}")
                continue

            print(f"\n  [{idx:02d}] {title[:60]}")

            # Click the button
            try:
                buttons = page.locator('button')
                btn = buttons.nth(btn_idx)
                await btn.scroll_into_view_if_needed()
                await btn.click()
                await page.wait_for_timeout(2500)
            except Exception as e:
                print(f"    ⚠️ Click error: {e}")
                # Retry by text
                try:
                    await page.locator(f'button:has-text("{title[:30]}")').first.click()
                    await page.wait_for_timeout(2500)
                except Exception:
                    pass

            # Get lesson content
            content_text = await page.evaluate("""() => {
                // Find main content area (not sidebar)
                const candidates = [
                    document.querySelector('main'),
                    document.querySelector('[class*="content"]'),
                    document.querySelector('[class*="lesson"]'),
                    document.querySelector('[class*="article"]'),
                    document.querySelector('[role="main"]'),
                    document.body
                ]
                for (const el of candidates) {
                    if (el) {
                        const text = el.innerText?.trim() || ''
                        if (text.length > 200) return text
                    }
                }
                return document.body.innerText
            }""")

            # Check for video
            has_video = await page.evaluate("""() => {
                return !!(
                    document.querySelector('video') ||
                    document.querySelector('iframe[src*="youtube"]') ||
                    document.querySelector('iframe[src*="loom"]') ||
                    document.querySelector('iframe[src*="vimeo"]') ||
                    document.querySelector('[class*="video"]')
                )
            }""")

            # Get video URL if any
            video_url = await page.evaluate("""() => {
                const iframe = document.querySelector('iframe[src*="youtube"], iframe[src*="loom"], iframe[src*="vimeo"]')
                if (iframe) return iframe.src
                const video = document.querySelector('video[src], video source[src]')
                if (video) return video.src || video.querySelector('source')?.src || ''
                return ''
            }""")

            # Screenshot
            try:
                ss_path = OUT / f"{idx:02d}_{safe_name(title)}.png"
                await page.screenshot(path=str(ss_path), full_page=False)
            except Exception:
                pass

            # Save text
            txt_path = OUT / f"{idx:02d}_{safe_name(title)}.txt"
            txt_path.write_text(f"# Lección {idx}: {title}\n\n{content_text[:15000]}", encoding='utf-8')

            lesson_data = {
                "index": idx,
                "title": title,
                "text": content_text[:15000],
                "has_video": has_video,
                "video_url": video_url,
            }
            all_lessons.append(lesson_data)
            done_indices.add(idx)

            # Save progress
            done_file.write_text(json.dumps(all_lessons, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f"    {'📹' if has_video else '📄'} {len(content_text)} chars {'| Video: '+video_url[:60] if video_url else ''}")

        # Generate STUDY GUIDE
        print("\n[Generando guía de estudio...]")
        all_lessons.sort(key=lambda x: x['index'])

        guide = ["# Claude Certified Architect Prep — Guía de Estudio Completa\n"]
        guide.append(f"Total lecciones: {len(all_lessons)}\n")
        guide.append("---\n")

        for lesson in all_lessons:
            guide.append(f"\n## Lección {lesson['index']}: {lesson['title']}")
            if lesson.get('video_url'):
                guide.append(f"🎥 Video: {lesson['video_url']}")
            guide.append(f"\n{lesson['text'][:5000]}")
            guide.append("\n---")

        (OUT / "STUDY_GUIDE.md").write_text('\n'.join(guide), encoding='utf-8')

        print(f"\n[DONE] {len(all_lessons)}/70 lecciones scrapeadas")
        print(f"Output: {OUT}")

asyncio.run(main())
