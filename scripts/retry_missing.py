"""
Retry descarga de clases con videos faltantes.
Usa cookies guardadas para evitar login. Si no hay cookies, hace login normal.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, json, re, subprocess
from pathlib import Path
from playwright.async_api import async_playwright

EMAIL       = "lumpenvisual@gmail.com"
PASSWORD    = "JacJac891212*"
CHROME_PATH = "C:/Program Files/Google/Chrome/Application/chrome.exe"

BASE = Path("E:/Documents/PROYECTOS/AgencIA/platzi_clone")
OUT  = BASE / "downloads"
VID  = OUT / "videos"

def safe_name(s, max_len=60):
    return re.sub(r'[^\w\-]', '_', s)[:max_len].strip('_') or 'untitled'

def find_missing():
    """Lee todos los course_data.json y retorna clases sin video."""
    missing = []
    for f in OUT.rglob("course_data.json"):
        try:
            d = json.loads(f.read_text(encoding='utf-8'))
            slug = d.get('slug', f.parent.name)
            for cls in d.get('classes', []):
                has_video = cls.get('m3u8') or cls.get('video_file')
                if not has_video:
                    missing.append({
                        'course_slug': slug,
                        'course_dir': str(f.parent),
                        'index': cls.get('index', 0),
                        'title': cls.get('title', ''),
                        'url': cls.get('url', ''),
                        'data_file': str(f),
                    })
        except Exception as e:
            print(f"⚠️ Error reading {f}: {e}")
    return missing

async def login(page):
    print("[LOGIN] Platzi 2-step")
    await page.goto("https://platzi.com/login/", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(4000)
    try:
        email_inp = page.locator('input[type="email"]').first
        await email_inp.wait_for(state="visible", timeout=8000)
        await email_inp.fill(EMAIL)
        await page.wait_for_timeout(500)
        await page.locator('button:has-text("Continuar"), button[type="submit"]').first.click()
        await page.wait_for_timeout(4000)
        pass_inp = page.locator('input[type="password"]').first
        await pass_inp.wait_for(state="visible", timeout=8000)
        await pass_inp.fill(PASSWORD)
        await page.wait_for_timeout(500)
        await page.locator('button[type="submit"]').first.click()
        await page.wait_for_timeout(8000)
    except Exception as e:
        print(f"  ⚠️ {e}")
    logged = "login" not in page.url
    print(f"  {'✅ OK' if logged else '❌ Failed'}: {page.url}")
    return logged

async def intercept_video(page, class_url):
    m3u8_urls = []

    async def capture(response):
        u = response.url
        if '.m3u8' in u and response.status == 200 and u not in m3u8_urls:
            m3u8_urls.append(u)
            print(f"    🎯 {u[:90]}")

    page.on("response", capture)
    try:
        await page.goto(class_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)
        # Try play buttons
        for sel in ['button[aria-label*="play" i]', '[class*="Play"]', 'video']:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.click()
                    await page.wait_for_timeout(2000)
                    break
            except Exception:
                pass
        # Check video element
        src = await page.evaluate("() => { const v=document.querySelector('video'); return v ? v.src||v.currentSrc||'' : '' }")
        if src and '.m3u8' in src and src not in m3u8_urls:
            m3u8_urls.append(src)
        if not m3u8_urls:
            await page.wait_for_timeout(3000)
    except Exception as e:
        print(f"    ⚠️ {e}")
    finally:
        page.remove_listener("response", capture)
    return m3u8_urls[0] if m3u8_urls else None

async def download_video(m3u8_url, dest_path):
    if dest_path.exists() and dest_path.stat().st_size > 100_000:
        print(f"    ✅ Ya existe: {dest_path.name}")
        return True
    cmd = [
        "python", "-m", "yt_dlp", m3u8_url,
        "-o", str(dest_path),
        "--no-playlist", "--concurrent-fragments", "4",
        "--retries", "10", "--fragment-retries", "30",
        "--referer", "https://platzi.com/",
        "--add-header", "Origin:https://platzi.com",
        "--no-warnings", "-q",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if dest_path.exists() and dest_path.stat().st_size > 100_000:
            print(f"    ✅ {dest_path.name} ({dest_path.stat().st_size//1024}KB)")
            return True
        print(f"    ⚠️ yt-dlp: {result.stderr[:200]}")
        return False
    except Exception as e:
        print(f"    ⚠️ {e}")
        return False

def update_course_data(data_file, cls_index, m3u8, video_file):
    """Update the course_data.json with new video info."""
    try:
        path = Path(data_file)
        d = json.loads(path.read_text(encoding='utf-8'))
        for cls in d['classes']:
            if cls.get('index') == cls_index:
                cls['m3u8'] = m3u8
                cls['video_file'] = video_file
                break
        path.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception as e:
        print(f"    ⚠️ update_course_data: {e}")

async def main():
    missing = find_missing()
    print(f"[RETRY] Clases sin video: {len(missing)}")
    for m in missing:
        print(f"  [{m['course_slug']}] #{m['index']} {m['title'][:60]}")

    if not missing:
        print("✅ Nada que reintentar")
        return

    async with async_playwright() as p:
        # Try CDP first (browser already open)
        browser = None
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = await ctx.new_page()
            # Verify session
            await page.goto("https://platzi.com/home/", wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2000)
            if "login" in page.url:
                raise Exception("Session expired")
            print("✅ CDP connected — sesión activa")
        except Exception as e:
            print(f"CDP not available ({e}) — launching new browser")
            if browser:
                await browser.close()
            # Load cookies if available
            cookies_file = OUT / "cookies.json"
            browser = await p.chromium.launch(
                executable_path=CHROME_PATH,
                headless=False,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
            )
            ctx = await browser.new_context(
                viewport={"width": 1400, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            )
            if cookies_file.exists():
                try:
                    cookies = json.loads(cookies_file.read_text(encoding='utf-8'))
                    await ctx.add_cookies(cookies)
                    print(f"✅ Cookies cargadas: {len(cookies)}")
                except Exception as ce:
                    print(f"⚠️ Cookies error: {ce}")
            page = await ctx.new_page()
            await page.goto("https://platzi.com/home/", wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000)
            if "login" in page.url:
                if not await login(page):
                    print("❌ Login failed")
                    await browser.close()
                    return

        # Process missing classes
        done = 0
        for item in missing:
            print(f"\n[{item['course_slug']}] #{item['index']} {item['title'][:60]}")
            if not item['url']:
                print("  ⚠️ No URL")
                continue

            m3u8 = await intercept_video(page, item['url'])
            if m3u8:
                prefix = f"{item['index']:03d}_{safe_name(item['title'])}"
                vid_path = VID / f"{item['course_slug']}_{prefix}.mp4"
                ok = await download_video(m3u8, vid_path)
                if ok:
                    update_course_data(item['data_file'], item['index'], m3u8, vid_path.name)
                    done += 1
            else:
                print("  ⚠️ No m3u8 encontrado")

        print(f"\n[DONE] {done}/{len(missing)} clases recuperadas")
        await browser.close()

asyncio.run(main())
