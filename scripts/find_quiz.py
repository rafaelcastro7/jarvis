"""Busca quiz en la página actual scrolleando."""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://localhost:9222")
        page = None
        for c in b.contexts:
            for pg in c.pages:
                if "devcompass" in pg.url:
                    page = pg; break
            if page: break
        if not page:
            print("No page"); return

        # Click "Walkthrough" tab first
        for tab in ["Walkthrough", "Notes", "Code"]:
            try:
                btn = page.locator(f'button:has-text("{tab}")').first
                if await btn.count() > 0:
                    await btn.click()
                    await page.wait_for_timeout(1000)
                    print(f"Clicked tab: {tab}")
            except Exception:
                pass

        # Scroll through page
        for scroll_y in range(0, 5000, 400):
            await page.evaluate(f"window.scrollTo(0, {scroll_y})")
            await page.wait_for_timeout(200)

            state = await page.evaluate("""() => {
                const radios = Array.from(document.querySelectorAll('input[type=radio]')).map((r,i)=>({
                    i, label:(r.closest('label')?.innerText||r.value||'').trim().slice(0,150), checked:r.checked
                }))
                const textareas = Array.from(document.querySelectorAll('textarea')).map((t,i)=>({
                    i, value:t.value.slice(0,50)
                }))
                const submitBtn = !!document.querySelector('button:not([disabled]):not([title*="Complete"])')
                return {radios, textareas, submitBtn}
            }""")

            if state["radios"] or state["textareas"]:
                print(f"\nFound at scroll {scroll_y}!")
                print(f"Radios: {json.dumps(state['radios'], ensure_ascii=False)}")
                print(f"Textareas: {state['textareas']}")
                break

        # If still nothing, get full page text to find the question
        full_text = await page.evaluate("document.body.innerText")
        # Look for question patterns
        import re
        questions = re.findall(r'([A-Z][^?]+\?)', full_text)
        print(f"\nQuestions found on page:")
        for q in questions[:10]:
            print(f"  - {q[:120]}")

        # Check if "Complete quizzes first" refers to the CODE tab
        await page.evaluate("window.scrollTo(0,0)")
        code_btn = page.locator('button:has-text("Code")').first
        if await code_btn.count() > 0:
            await code_btn.click()
            await page.wait_for_timeout(1500)
            code_content = await page.evaluate("document.body.innerText")
            print(f"\nCode tab content:\n{code_content[code_content.find('LESSON'):code_content.find('LESSON')+2000]}")

asyncio.run(main())
