"""
get_certs.py — Login to Skilljar and download all course certificates.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
import asyncio, os, re
from playwright.async_api import async_playwright

EMAIL = 'rafaelcastro7@gmail.com'
PASSWORD = 'BrainTrainR2026!'
SAVE_DIR = r'E:\Documents\PROYECTOS\AgencIA\platzi_clone\downloads\certificados'

COURSES = [
    ('claude-with-the-anthropic-api',           'Building with the Claude API'),
    ('introduction-to-model-context-protocol',  'Introduction to MCP'),
    ('claude-code-in-action',                    'Claude Code in Action'),
    ('claude-101',                               'Claude 101'),
]

os.makedirs(SAVE_DIR, exist_ok=True)


async def safe(page, js, default=None):
    try:
        return await page.evaluate(js)
    except Exception:
        return default


async def login(page):
    await page.goto('https://anthropic.skilljar.com/accounts/login/',
                    wait_until='domcontentloaded', timeout=25000)
    await page.wait_for_timeout(2000)

    # Try email field
    email_sel = 'input[id*=email], input[name*=email], input[type=email]'
    pw_sel = 'input[id*=password], input[name*=password], input[type=password]'

    await page.locator(email_sel).first.fill(EMAIL)
    await page.locator(pw_sel).first.fill(PASSWORD)
    await page.locator('button[type=submit]').first.click()
    await page.wait_for_timeout(4000)
    print(f'After login: {page.url}')


async def find_certificate(page, slug, name):
    """Navigate to course and find certificate download link."""
    await page.goto(f'https://anthropic.skilljar.com/{slug}',
                    wait_until='domcontentloaded', timeout=20000)
    await page.wait_for_timeout(2000)

    body = await safe(page, 'document.body.innerText', '')
    m = re.search(r'(\d+)\s+of\s+(\d+)\s+lessons', body)
    progress = m.group(0) if m else '?'
    print(f'\n{name}: {progress}')

    # Look for certificate link on course page
    cert_links = await safe(page, '''() => {
        return Array.from(document.querySelectorAll('a')).filter(a =>
            /certificate|cert|diploma/i.test(a.textContent || '') ||
            /certificate|cert/i.test(a.href || '')
        ).map(a => ({text: a.textContent.trim(), href: a.href}))
    }''', [])
    print(f'  Certificate links: {cert_links}')

    # Check my-profile page
    await page.goto('https://anthropic.skilljar.com/my-profile',
                    wait_until='domcontentloaded', timeout=20000)
    await page.wait_for_timeout(2000)

    cert_links2 = await safe(page, '''() => {
        return Array.from(document.querySelectorAll('a')).filter(a =>
            /certificate|cert|diploma/i.test(a.textContent || '') ||
            /certificate|cert/i.test(a.href || '')
        ).map(a => ({text: a.textContent.trim(), href: a.href}))
    }''', [])
    print(f'  Profile cert links: {cert_links2[:5]}')

    return cert_links + cert_links2


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://localhost:9222')
        page = b.contexts[0].pages[0]

        # Check if logged in
        await page.goto('https://anthropic.skilljar.com/', wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(2000)
        url = page.url
        body = await safe(page, 'document.body.innerText', '')

        if 'login' in url.lower() or 'sign in' in body.lower()[:200]:
            print('Not logged in, logging in...')
            await login(page)
        else:
            print(f'Already logged in: {url}')

        # Find and download certificates
        all_certs = []
        for slug, name in COURSES:
            certs = await find_certificate(page, slug, name)
            all_certs.extend(certs)

        print(f'\n\nAll certificates found: {len(all_certs)}')
        for c in all_certs:
            print(f'  {c}')

        # Try downloading each unique cert
        seen = set()
        for cert in all_certs:
            href = cert.get('href', '')
            if not href or href in seen or 'http' not in href:
                continue
            seen.add(href)
            print(f'\nDownloading: {href}')
            try:
                async with page.expect_download(timeout=30000) as dl_info:
                    await page.goto(href, wait_until='domcontentloaded', timeout=20000)
                dl = await dl_info.value
                fname = dl.suggested_filename or 'certificate.pdf'
                save_path = os.path.join(SAVE_DIR, fname)
                await dl.save_as(save_path)
                print(f'  Saved: {save_path}')
            except Exception as e:
                print(f'  Error: {e}')


asyncio.run(main())
