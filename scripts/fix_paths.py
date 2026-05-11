import json
from pathlib import Path

def fix_paths():
    downloads_dir = Path('downloads')
    progress_file = downloads_dir / 'progress.json'
    
    if not progress_file.exists():
        print("Progress file not found")
        return
        
    data = json.loads(progress_file.read_text(encoding='utf-8'))
    
    # Map filenames to their relative path
    file_map = {}
    for p in downloads_dir.rglob('*.mp4'):
        file_map[p.name] = p.relative_to(downloads_dir).as_posix()
    
    print(f"Found {len(file_map)} mp4 files on disk.")
    
    updated_count = 0
    for slug, info in data.items():
        for cl in info.get('classes', []):
            fname = cl.get('video_file')
            if fname and fname in file_map:
                cl['video_file'] = file_map[fname]
                updated_count += 1
            elif fname:
                # Check if it already has a path
                if Path(downloads_dir / fname).exists():
                    pass # already correct
                else:
                    print(f"Missing file on disk: {fname}")
                    # cl['video_file'] = None # Optional: disable if missing
                    
    progress_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
    print(f"Updated {updated_count} paths in progress.json")

    # Also update final_summary.json
    summary = {'courses': [], 'total_videos': 0}
    for slug, info in data.items():
        summary['courses'].append({
            'slug': slug, 
            'name': info.get('name', slug), 
            'classes': info.get('classes', [])
        })
        summary['total_videos'] = sum(1 for cl in info.get('classes', []) if cl.get('video_file'))
    
    Path('downloads/final_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print("final_summary.json updated.")

if __name__ == "__main__":
    fix_paths()
