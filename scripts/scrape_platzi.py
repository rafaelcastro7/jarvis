"""
Platzi Course Scraper — Phase 1: Discovery
Login 2-step + extrae estructura completa del curso/ruta
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright, Page

EMAIL     = "lumpenvisual@gmail.com"
PASSWORD  = "JacJac891212*"
ROUTE_URL = "https://platzi.com/mis-rutas/16704423/"
CHROME_PATH = "C:/Program Files/Google/Chrome/Application/chrome.exe"

OUT = Path("E:/Documents/PROYECTOS/AgencIA/platzi_clone/downloads")
OUT.mkdir(parents=True, exist_ok=True)

async def ss(page, name):
    await page.screenshot(path=str(OUT / f"{name}.png"), full_page=False)
    print(f"  📸 {name}")

async def main():
    print("[START] Platzi Scraper — Phase 1")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=CHROME_PATH,
            headless=False,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--start-maximized"]
        )
        ctx = await browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        page = await ctx.new_page()

        # ── LOGIN 2-STEP ──────────────────────────────────────────────────────
        print("\n[1] Login Platzi (2 pasos)")
        await page.goto("https://platzi.com/login/", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        await ss(page, "01_login")

        # Step 1: email → Continuar
        try:
            email_inp = page.locator('input[type="email"], input[name="email"], input[placeholder*="correo" i], input[placeholder*="email" i]').first
            await email_inp.wait_for(state="visible", timeout=8000)
            await email_inp.fill(EMAIL)
            print(f"  ✅ Email: {EMAIL}")
            await page.wait_for_timeout(500)

            # Click Continuar
            cont = page.locator('button:has-text("Continuar"), button[type="submit"]').first
            await cont.click()
            print("  🖱️  Continuar (step 1)")
            await page.wait_for_timeout(3000)
            await ss(page, "02_after_email")
        except Exception as e:
            print(f"  ⚠️  Email step: {e}")

        # Step 2: password
        try:
            pass_inp = page.locator('input[type="password"]').first
            await pass_inp.wait_for(state="visible", timeout=8000)
            await pass_inp.fill(PASSWORD)
            print(f"  ✅ Password filled")
            await page.wait_for_timeout(500)

            submit = page.locator('button[type="submit"], button:has-text("Iniciar"), button:has-text("Entrar"), button:has-text("Continuar")').first
            await submit.click()
            print("  🖱️  Submit login")
            await page.wait_for_timeout(6000)
            await ss(page, "03_after_login")
            print(f"  URL: {page.url}")
        except Exception as e:
            print(f"  ⚠️  Password step: {e}")
            await ss(page, "03_error")

        # Si sigue en login, puede ser Google SSO — intentar directo
        if "login" in page.url:
            print("  ⚠️  Aún en login — intentando con /clases/ directo para verificar sesión")
            # Guardar cookies y verificar
            cookies = await ctx.cookies()
            print(f"  Cookies: {len(cookies)}")

        # ── NAVEGAR A LA RUTA ─────────────────────────────────────────────────
        print(f"\n[2] Ruta: {ROUTE_URL}")
        await page.goto(ROUTE_URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)
        await ss(page, "04_route")

        print(f"  URL actual: {page.url}")
        print(f"  Título: {await page.title()}")

        page_text = await page.evaluate("document.body.innerText")
        print(f"\n  Contenido (1500 chars):\n{page_text[:1500]}")
        (OUT / "route_text.txt").write_text(page_text, encoding='utf-8')

        # Guardar HTML
        html = await page.content()
        (OUT / "route_page.html").write_text(html, encoding='utf-8')

        # ── EXTRAER TODOS LOS LINKS ───────────────────────────────────────────
        all_links = await page.evaluate("""() => {
            const seen = new Set()
            const links = []
            document.querySelectorAll('a[href]').forEach(a => {
                const href = a.href
                const text = a.textContent?.trim()?.replace(/\s+/g, ' ') || ''
                if (!seen.has(href) && href.startsWith('http')) {
                    seen.add(href)
                    links.push({ href, text: text.slice(0, 100) })
                }
            })
            return links
        }""")

        course_links = [l for l in all_links if any(x in l['href'] for x in ['/cursos/', '/curso/', '/clases/', '/clase/'])]
        platzi_links = [l for l in all_links if 'platzi.com' in l['href']]

        print(f"\n  Links totales: {len(all_links)}")
        print(f"  Links de cursos/clases: {len(course_links)}")
        print(f"  Links platzi.com: {len(platzi_links)[:50]}")

        for l in platzi_links[:30]:
            print(f"    {l['href']} | {l['text'][:50]}")

        (OUT / "all_links.json").write_text(json.dumps(all_links, ensure_ascii=False, indent=2), encoding='utf-8')
        (OUT / "course_links.json").write_text(json.dumps(course_links, ensure_ascii=False, indent=2), encoding='utf-8')

        # Guardar cookies
        cookies = await ctx.cookies()
        (OUT / "cookies.json").write_text(json.dumps(cookies, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"\n  Cookies guardadas: {len(cookies)}")

        print(f"\n[DONE] Archivos en {OUT}")
        print("  ⏳ Browser abierto 30s...")
        await page.wait_for_timeout(30000)
        await browser.close()

asyncio.run(main())
