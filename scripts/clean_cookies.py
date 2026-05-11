import json
from pathlib import Path

def clean_cookies():
    cookie_path = Path('downloads/cookies.json')
    if not cookie_path.exists():
        print("Cookies file not found.")
        return

    try:
        cookies = json.loads(cookie_path.read_text(encoding='utf-8'))
        original_count = len(cookies)
        
        # Keep only relevant domains
        relevant_domains = ['platzi.com', 'google.com', 'cloudflare.com', 'vimeo.com']
        cleaned = [c for c in cookies if any(domain in c.get('domain', '') for domain in relevant_domains)]
        
        # Write back
        cookie_path.write_text(json.dumps(cleaned, indent=2), encoding='utf-8')
        print(f"Cleaned cookies: {original_count} -> {len(cleaned)}")
    except Exception as e:
        print(f"Error cleaning cookies: {e}")

if __name__ == "__main__":
    clean_cookies()
