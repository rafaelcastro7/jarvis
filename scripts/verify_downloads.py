import json
from pathlib import Path

def verify():
    p = Path('downloads/progress.json')
    if not p.exists():
        print("Progress file not found")
        return
        
    data = json.loads(p.read_text(encoding='utf-8'))
    missing = []
    total_videos = 0
    
    for slug, info in data.items():
        for cl in info.get('classes', []):
            if cl.get('video_file'):
                total_videos += 1
                f = Path('downloads') / cl['video_file']
                if not f.exists():
                    missing.append(cl['video_file'])
                    
    print(f"Total Videos in Metadata: {total_videos}")
    print(f"Missing Files on Disk: {len(missing)}")
    if missing:
        print("First 5 missing:", missing[:5])

if __name__ == "__main__":
    verify()
