"""Verify delivered raw files without network access; Python 3.10+."""
import hashlib
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'data/raw_manifest.json').read_text(encoding='utf8'))
failed=[]
for r in manifest:
    path=root/r['path']
    h=hashlib.sha256()
    if not path.exists():
        failed.append(r['path']+' missing');continue
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            h.update(b)
    if h.hexdigest()!=r['sha256'] or path.stat().st_size!=r['bytes']:
        failed.append(r['path']+' mismatch')
if failed:
    raise SystemExit('\n'.join(failed))
print(f'All {len(manifest)} snapshot files match the manifest. This checks file integrity, not source accuracy.')
