"""
download_certs_pdf.py — Click "Download as PDF" on each certificate page and save the file.
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
        ctx = b.contexts[0]
        page = ctx.pages[0]

        for code, name in CERTS:
            url = f'https://verify.skilljar.com/c/{code}'
            print(f'\n{name}: {url}')

            await page.goto(url, wait_until='domcontentloaded', timeout=20000)
            await page.wait_for_timeout(3000)

            # Find "Download as PDF" link href
            pdf_url = await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                const dl = links.find(a =>
                    /download.*pdf|pdf.*download/i.test(a.textContent) ||
                    /download/i.test(a.textContent) && /pdf/i.test(a.href)
                );
                return dl ? dl.href : null;
            }''')
            print(f'  PDF link: {pdf_url}')

            if pdf_url:
                # Click the download link and capture the file
                pdf_path = os.path.join(SAVE_DIR, f'{name}.pdf')
                try:
                    async with page.expect_download(timeout=30000) as dl_info:
                        await page.evaluate('''(url) => {
                            const a = document.createElement("a");
                            a.href = url;
                            a.download = "certificate.pdf";
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                        }''', pdf_url)
                    dl = await dl_info.value
                    await dl.save_as(pdf_path)
                    size = os.path.getsize(pdf_path)
                    print(f'  Saved PDF: {pdf_path} ({size//1024} KB)')
                except Exception as e:
                    print(f'  expect_download error: {e}')
                    # Try fetching directly via requests in browser context
                    try:
                        content = await page.evaluate('''async (url) => {
                            const resp = await fetch(url, {credentials: "include"});
                            if (!resp.ok) return {error: resp.status};
                            const buf = await resp.arrayBuffer();
                            const bytes = new Uint8Array(buf);
                            let binary = "";
                            for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
                            return {data: btoa(binary), size: bytes.length};
                        }''', pdf_url)
                        if content and 'data' in content:
                            import base64
                            pdf_bytes = base64.b64decode(content['data'])
                            with open(pdf_path, 'wb') as f:
                                f.write(pdf_bytes)
                            print(f'  Saved via fetch: {pdf_path} ({len(pdf_bytes)//1024} KB)')
                        else:
                            print(f'  Fetch error: {content}')
                    except Exception as e2:
                        print(f'  Fetch fallback error: {e2}')
            else:
                print('  No PDF download link found — listing all links:')
                links = await page.evaluate('''() =>
                    Array.from(document.querySelectorAll("a")).map(a => ({
                        text: a.textContent.trim(), href: a.href
                    })).filter(l => l.text || l.href)
                ''')
                for l in links[:20]:
                    print(f'    [{l["text"][:40]}] {l["href"][:80]}')

        print(f'\nDone. Certificados en: {SAVE_DIR}')


asyncio.run(main())
