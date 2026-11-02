"""Offline audit of document navigation, migration coverage, and preserved evidence."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import csv
import hashlib
import json
import os
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
AUDIT = Path(__file__).parent
BASE = 'c002350615696d6dc6490f9099af3fbf23d4e56a'
mapping = json.loads((AUDIT / 'path-map.json').read_text())
merges = json.loads((AUDIT / 'merge-map.json').read_text())
tracked = {p for p in subprocess.check_output(
    ['git', 'ls-tree', '-r', '--name-only', BASE, 'docs']).decode().splitlines()}
# git's default quoted non-ASCII output isn't suitable for path comparison.
tracked = set(subprocess.check_output(
    ['git', 'ls-tree', '-rz', '--name-only', BASE, 'docs']).decode().strip('\0').split('\0'))
assert set(mapping) == tracked
with Path('docs/문서_이동표.csv').open(encoding='utf-8-sig', newline='') as f:
    table = list(csv.DictReader(f))
assert {r['이전_경로']: r['현재_경로'] for r in table} == mapping

def digest(data):
    return hashlib.sha256(data).hexdigest()

original = {}
for row in table:
    old = row['이전_경로']
    original[old] = subprocess.check_output(['git', 'show', f'{BASE}:{old}'])
    assert digest(original[old]) == row['이전_SHA256']
    assert Path(mapping[old]).is_file(), mapping[old]

mutable_formats = {'.md', '.py', '.mjs'}
mutable_manifests = {'docs/HeoNey/archive/manifest.json', 'docs/presentations/manifest.json'}
unchanged = []
for old, new in mapping.items():
    if Path(old).suffix not in mutable_formats and old not in mutable_manifests and not old.endswith('.gitignore'):
        assert Path(new).read_bytes() == original[old], old
        unchanged.append(old)
    if old not in merges and Path(old).suffix == '.md' and '/archive/' in old:
        before = re.findall(r'`````text\n(.*?)\n`````', original[old].decode(), re.S)
        after = re.findall(r'`````text\n(.*?)\n`````', Path(new).read_text(), re.S)
        assert before == after, old

manifest_path = Path(mapping['docs/HeoNey/archive/manifest.json'])
manifest = json.loads(manifest_path.read_text())
for row in manifest['visible_messages']:
    message_file = manifest_path.parent.parent / row['file']
    tail = message_file.read_text().split(f'<a id="{row["anchor"]}"></a>', 1)[1]
    raw = re.search(r'`````text\n(.*?)\n`````', tail, re.S).group(1)
    assert digest(raw.encode()) == row['text_sha256'], row['sequence']
    assert len(raw) == row['text_characters'], row['sequence']

presentation_manifest = json.loads(Path(mapping['docs/presentations/manifest.json']).read_text())
for row in presentation_manifest['files']:
    data = Path(row['path']).read_bytes()
    assert len(data) == row['bytes'] and digest(data) == row['sha256']

def without_fences(text):
    lines = []
    fence = None
    for line in text.splitlines():
        match = re.match(r'^\s*(`{3,}|~{3,})', line)
        if match:
            mark = match[1]
            if fence is None:
                fence = mark
            elif mark[0] == fence[0] and len(mark) >= len(fence):
                fence = None
            continue
        if fence is None:
            lines.append(line)
    return '\n'.join(lines)

def slug(text):
    text = re.sub(r'<[^>]+>', '', text).strip().lower()
    return re.sub(r'\s', '-', re.sub(r'[^\w\-\s]', '', text))

files = [*Path('docs').rglob('*.md'), Path('README.md'), Path('training/README.md'),
         Path('data/scenarios/README.md'), *Path('training/reports').rglob('*.md')]
anchors = {}
for path in files:
    text = without_fences(path.read_text())
    ids = set(re.findall(r'\bid=["\']([^"\']+)', text))
    counts = {}
    for heading in re.findall(r'^#{1,6}\s+(.+?)\s*#*$', text, re.M):
        base = slug(heading)
        n = counts.get(base, 0)
        counts[base] = n + 1
        ids.add(base + (f'-{n}' if n else ''))
    anchors[path.resolve()] = ids
link_count = 0
for path in files:
    text = without_fences(path.read_text())
    targets = re.findall(r'\]\((<[^>]*>|[^\s)]+)\)', text)
    targets += re.findall(r'\b(?:src|href)=["\']([^"\']+)', text)
    for target in targets:
        target = target.strip('<>')
        if urlsplit(target).scheme:
            continue
        name, _, anchor = unquote(target).partition('#')
        resolved = (path.parent / name).resolve() if name else path.resolve()
        assert resolved.exists(), (path, target)
        if anchor and resolved.suffix == '.md' and resolved in anchors:
            assert anchor in anchors[resolved], (path, target, 'anchor')
        link_count += 1

# Remove only completion boilerplate and navigation syntax when checking merged paragraphs.
def plain(text):
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    return re.sub(r'\s+', ' ', text).strip()

for old, (_, heading) in merges.items():
    body = '\n\n'.join(original[old].decode().split('\n\n')[2:]).strip()
    merged = Path(mapping[old]).read_text().split('## ' + heading + '\n', 1)[1]
    # The one self-link is redirected to the actual handoff guide, keeping its meaning.
    body = body.replace('데이터 카탈로그와 Mac 인계', 'Mac 인계 가이드')
    assert plain(body) in plain(merged), old

json_count = 0
for path in Path('docs').rglob('*.json'):
    json.loads(path.read_text())
    json_count += 1
legacy = [p for p in Path('docs/V2').rglob('*.md')]
assert len(legacy) == 4
for path in legacy:
    assert path.stat().st_size < 700 and '경로 호환 안내' in path.read_text()
for path in Path('docs').rglob('*'):
    if path.is_file() and path not in legacy and path.name != '.gitignore':
        assert re.search('[가-힣]', path.stem), path

report = {
    'result': 'passed', 'baseline_commit': BASE,
    'original_files': len(mapping), 'relocated_targets': len(set(mapping.values())),
    'merged_removed_documents': len(merges), 'loom_compatibility_redirects': len(legacy),
    'current_docs_files': len([p for p in Path('docs').rglob('*') if p.is_file()]),
    'byte_identical_evidence_and_assets': len(unchanged),
    'visible_messages_with_original_hashes': len(manifest['visible_messages']),
    'progress_messages_preserved': manifest['progress_message_count'],
    'presentation_manifest_files_verified': len(presentation_manifest['files']),
    'markdown_files_checked': len(files), 'local_links_and_anchors_checked': link_count,
    'json_files_parsed': json_count,
    'scope': 'Offline documentation audit; no app source inspection, deployment, data collection or training.',
}
(AUDIT / 'document-verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
