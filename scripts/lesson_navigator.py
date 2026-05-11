"""Navigator inteligente para DevCompass."""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, re, json
from playwright.async_api import async_playwright

TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 28
ACTION = sys.argv[2] if len(sys.argv) > 2 else "read"
SIDEBAR_WIDTH = 200

async def close_modal(page):
    await page.evaluate("""() => {
        const btns = Array.from(document.querySelectorAll("button"))
        const cancel = btns.find(b => ["Cancel","Close","x","X"].includes((b.textContent||"").trim()))
        if (cancel) cancel.click()
    }""")
    await page.wait_for_timeout(500)

async def get_quiz_options(page):
    return await page.evaluate(f"""() => {{
        const EXCLUDE = ["Submit Answer","SUBMIT ANSWER","Walkthrough","Code","Notes","Next Lesson",
                         "Lock In","Connect with Buddy","Submit code","Retake to review",
                         "Complete quizzes first","Subscribe","Open on YouTube","Cancel","Close"]
        return Array.from(document.querySelectorAll("button")).filter(b => {{
            const r = b.getBoundingClientRect()
            const t = (b.textContent||"").trim()
            return r.x > {SIDEBAR_WIDTH} && t.length > 20 && t.length < 400 && !EXCLUDE.includes(t) && !t.match(/^\d+[^.]/)
        }}).map((b,i) => ({{i, text:b.textContent?.trim()?.slice(0,200)}}))
    }}""")

async def get_next_btn(page):
    return await page.evaluate("""() => {
        const n = Array.from(document.querySelectorAll("button")).find(b=>(b.textContent||"").trim()==="Next Lesson")
        return n ? {disabled:n.disabled, title:n.title} : null
    }""")

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
            print("No devcompass page"); return

        await close_modal(page)

        if ACTION == "read":
            # Nav to lesson
            clicked = await page.evaluate(f"""() => {{
                for (const btn of document.querySelectorAll("button")) {{
                    const r = btn.getBoundingClientRect()
                    const t = (btn.textContent||"").replace(/\s+/g," ").trim()
                    if (r.x < {SIDEBAR_WIDTH} && t.match(/^{TARGET}[^0-9]/)) {{
                        btn.scrollIntoView({{block:"center"}}); btn.click(); return t.slice(0,80)
                    }}
                }}
                return null
            }}""")
            print(f"Nav: {clicked}")
            await page.wait_for_timeout(3000)
            
            # Click Walkthrough tab
            await page.evaluate(f"""() => {{
                Array.from(document.querySelectorAll("button")).find(b => {{
                    const r = b.getBoundingClientRect()
                    return r.x > {SIDEBAR_WIDTH} && (b.textContent||"").trim() === "Walkthrough"
                }})?.click()
            }}""")
            await page.wait_for_timeout(1500)

            body = await page.evaluate("document.body.innerText")
            prog = re.search(r"(\d+)/70", body)
            idx = body.find("Capstone: Stage 5 Final Capstone")
            content = body[idx+40:idx+5000] if idx > 0 else body[:5000]
            print(f"Progress: {prog.group(0) if prog else '?'}")
            print(f"Content:\n{content[:3000]}")

            quiz = await get_quiz_options(page)
            print(f"\nQuiz options ({len(quiz)}):")
            for q in quiz: print(f"  [{q['i']}] {q['text'][:120]}")
            
            next_btn = await get_next_btn(page)
            print(f"Next Lesson: {next_btn}")

        elif ACTION == "answer":
            idx = int(sys.argv[3]) if len(sys.argv) > 3 else 0
            result = await page.evaluate(f"""() => {{
                const EXCLUDE = ["Submit Answer","SUBMIT ANSWER","Walkthrough","Code","Notes","Next Lesson","Lock In","Connect with Buddy","Submit code","Retake to review","Complete quizzes first","Subscribe","Open on YouTube","Cancel","Close"]
                const opts = Array.from(document.querySelectorAll("button")).filter(b => {{
                    const r = b.getBoundingClientRect()
                    const t = (b.textContent||"").trim()
                    return r.x > {SIDEBAR_WIDTH} && t.length > 20 && t.length < 400 && !EXCLUDE.includes(t) && !t.match(/^\d+[^.]/)
                }})
                if (opts[{idx}]) {{ opts[{idx}].click(); return opts[{idx}].textContent?.slice(0,80) }}
                return "not found (" + opts.length + " opts)"
            }}""")
            print(f"Selected [{idx}]: {result}")

        elif ACTION == "submit":
            result = await page.evaluate(f"""() => {{
                const sub = Array.from(document.querySelectorAll("button")).find(b => {{
                    const r = b.getBoundingClientRect()
                    return r.x > {SIDEBAR_WIDTH} && (b.textContent||"").trim().toUpperCase().includes("SUBMIT ANSWER")
                }})
                if (sub) {{ sub.click(); return "submitted" }}
                return "not found"
            }}""")
            print(f"Submit: {result}")
            await page.wait_for_timeout(3000)
            body = await page.evaluate("document.body.innerText")
            prog = re.search(r"(\d+)/70", body)
            correct = "Correct" in body
            wrong = "Incorrect" in body or "Try again" in body
            print(f"Progress: {prog.group(0) if prog else '?'} | Correct: {correct} | Wrong: {wrong}")
            next_btn = await get_next_btn(page)
            print(f"Next: {next_btn}")

        elif ACTION == "next":
            result = await page.evaluate("""() => {
                const n = Array.from(document.querySelectorAll("button")).find(b=>(b.textContent||"").trim()==="Next Lesson")
                if (n && !n.disabled) { n.click(); return "clicked" }
                return n ? "disabled: " + n.title : "not found"
            }""")
            print(f"Next: {result}")
            await page.wait_for_timeout(3000)
            body = await page.evaluate("document.body.innerText")
            prog = re.search(r"(\d+)/70", body)
            print(f"Progress: {prog.group(0) if prog else '?'}")

        elif ACTION == "state":
            body = await page.evaluate("document.body.innerText")
            prog = re.search(r"(\d+)/70", body)
            lesson = re.search(r"LESSON (\d+)\n(.+)", body)
            print(f"Progress: {prog.group(0) if prog else '?'}")
            print(f"Lesson: {lesson.group(0) if lesson else '?'}")
            quiz = await get_quiz_options(page)
            print(f"Quiz options: {json.dumps(quiz, ensure_ascii=False)}")
            next_btn = await get_next_btn(page)
            print(f"Next: {next_btn}")

asyncio.run(main())
