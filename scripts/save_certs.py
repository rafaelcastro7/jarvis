"""
save_certs.py — Abre los certificados y los guarda como PDF via print.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
import asyncio, os
from playwright.async_api import async_playwright

SAVE_DIR = r'E:\Documents\PROYECTOS\AgencIA\platzi_clone\downloads\certificados'
os.makedirs(SAVE_DIR, exist_ok=True)

CERTS = [
    ('pm37tgsa25cs', 'Building_with_Claude_API'),
    ('y7nxsogtbk59', 'Introduction_to_MCP'),
    ('yvy7twu3ainb', 'Claude_Code_in_Action'),
    ('xkaer8c2j5th', 'Claude_101'),
]


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://localhost:9222')
        page = b.contexts[0].pages[0]

        for code, name in CERTS:
            url = f'https://verify.skilljar.com/c/{code}'
            print(f'\n{name}: {url}')

            await page.goto(url, wait_until='domcontentloaded', timeout=20000)
            await page.wait_for_timeout(3000)

            body = await page.evaluate('document.body.innerText')
            print(f'  Content: {body[:200]}')

            # Check for download link
            dl_links = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a, button')).filter(el =>
                    /download|pdf|print/i.test(el.textContent || '') ||
                    /download|pdf/i.test(el.href || '')
                ).map(el => ({tag: el.tagName, text: el.textContent.trim(), href: el.href || ''}))
            }''')
            print(f'  Download elements: {dl_links}')

            # Save as PDF via Playwright
            pdf_path = os.path.join(SAVE_DIR, f'{name}.pdf')
            try:
                await page.pdf(path=pdf_path, format='A4', print_background=True)
                size = os.path.getsize(pdf_path)
                print(f'  Saved PDF: {pdf_path} ({size//1024} KB)')
            except Exception as e:
                print(f'  PDF error: {e}')
                # Fallback: screenshot
                img_path = os.path.join(SAVE_DIR, f'{name}.png')
                await page.screenshot(path=img_path, full_page=True)
                size = os.path.getsize(img_path)
                print(f'  Saved screenshot: {img_path} ({size//1024} KB)')

        print(f'\n\nCertificados guardados en: {SAVE_DIR}')
        print('URLs públicas para compartir:')
        for code, name in CERTS:
            print(f'  {name}: https://verify.skilljar.com/c/{code}')


asyncio.run(main())
