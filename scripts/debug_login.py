"""Debug Platzi login — screenshots at each step."""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

EMAIL       = "lumpenvisual@gmail.com"
PASSWORD    = "JacJac891212*"
CHROME_PATH = "C:/Program Files/Google/Chrome/Application/chrome.exe"
OUT = Path("E:/Documents/PROYECTOS/AgencIA/platzi_clone/downloads")
OUT.mkdir(parents=True, exist_ok=True)

async def ss(page, name):
    p = str(OUT / f"debug_{name}.png")
    await page.screenshot(path=p, full_page=False)
    print(f"  📸 {p}")

async def main():
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

        print("[1] Navegando a login")
        await page.goto("https://platzi.com/login/", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(4000)
        await ss(page, "01_initial")
        print(f"  URL: {page.url}")

        # Print all inputs visible
        inputs = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('input')).map(i => ({
                type: i.type, name: i.name, placeholder: i.placeholder,
                id: i.id, visible: i.offsetParent !== null
            }))
        }""")
        print(f"  Inputs: {inputs}")

        # Print all buttons
        buttons = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('button')).map(b => ({
                text: b.textContent?.trim().slice(0,50),
                type: b.type
            }))
        }""")
        print(f"  Buttons: {buttons}")

        # Try email fill
        print("\n[2] Filling email")
        try:
            email_inp = page.locator('input[type="email"], input[name="email"], input[placeholder*="correo" i], input[placeholder*="email" i]').first
            await email_inp.wait_for(state="visible", timeout=10000)
            await email_inp.click()
            await page.wait_for_timeout(300)
            await email_inp.type(EMAIL, delay=80)
            await page.wait_for_timeout(500)
            await ss(page, "02_email_filled")
        except Exception as e:
            print(f"  ⚠️  {e}")
            await ss(page, "02_email_error")

        # Click Continuar
        print("\n[3] Clicking Continuar")
        try:
            btn = page.locator('button:has-text("Continuar"), button[type="submit"]').first
            await btn.wait_for(state="visible", timeout=5000)
            print(f"  Button text: {await btn.text_content()}")
            await btn.click()
            await page.wait_for_timeout(4000)
            await ss(page, "03_after_continuar")
            print(f"  URL: {page.url}")
        except Exception as e:
            print(f"  ⚠️  {e}")

        # Check new inputs
        inputs2 = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('input')).map(i => ({
                type: i.type, name: i.name, placeholder: i.placeholder,
                id: i.id, visible: i.offsetParent !== null
            }))
        }""")
        print(f"  Inputs after: {inputs2}")

        # Password
        print("\n[4] Filling password")
        try:
            pass_inp = page.locator('input[type="password"]').first
            await pass_inp.wait_for(state="visible", timeout=10000)
            await pass_inp.click()
            await page.wait_for_timeout(300)
            await pass_inp.type(PASSWORD, delay=80)
            await page.wait_for_timeout(500)
            await ss(page, "04_password_filled")
        except Exception as e:
            print(f"  ⚠️  {e}")
            await ss(page, "04_password_error")

        print("\n[5] Submitting")
        try:
            btn2 = page.locator('button[type="submit"]').first
            await btn2.click()
            await page.wait_for_timeout(8000)
            await ss(page, "05_after_submit")
            print(f"  URL: {page.url}")
        except Exception as e:
            print(f"  ⚠️  {e}")

        print("\n⏳ Browser open 60s for manual inspection...")
        await page.wait_for_timeout(60000)
        await browser.close()

asyncio.run(main())
