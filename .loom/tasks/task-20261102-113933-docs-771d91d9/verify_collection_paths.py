"""Test relocated helpers with isolated synthetic files; never download data."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'docs/04_데이터수집'
AUDIT = Path(__file__).parent
manifest = json.loads((SOURCE / '자료/원본_보관본_해시_목록.json').read_text())
fixture_csv = (
    'latitude,longitude,acq_date,acq_time\n'
    '37.48,127.05,2026-10-26,1400\n'
    '37.48,127.05,2026-10-27,0030\n'
    '36,128,2026-10-28,0030\n'
).encode()

with tempfile.TemporaryDirectory(prefix='bonghwa-collection-paths-') as temp:
    folder = Path(temp)
    shutil.copytree(SOURCE / '수집도구', folder / '수집도구')
    for row in manifest:
        path = folder / '자료' / Path(row['path']).relative_to('data')
        path.parent.mkdir(parents=True, exist_ok=True)
        data = fixture_csv if row['source_id'].startswith('firms') else b'synthetic-path-test\n'
        path.write_bytes(data)
        row['sha256'] = hashlib.sha256(data).hexdigest()
        row['bytes'] = len(data)
    (folder / '자료/원본_보관본_해시_목록.json').write_text(json.dumps(manifest))
    verify = [sys.executable, str(folder / '수집도구/원본_보관본_해시_검증.py')]
    matched = subprocess.run(verify, capture_output=True, text=True)
    assert matched.returncode == 0 and 'All 15 snapshot files match' in matched.stdout
    replay = subprocess.run([
        sys.executable, str(folder / '수집도구/공개_자료_수집과_보관본_재생.py'),
        'replay', '--out', str(folder / '실행결과/fixture-replay'),
    ], capture_output=True, text=True)
    assert replay.returncode == 0, replay.stderr
    result = json.loads(replay.stdout)
    assert result['case_rows'] == 4 and result['control_rows'] == 8
    assert all(row['date_range_spans_query'] for row in result['source_checks'])
    corrupt = folder / '자료' / Path(manifest[0]['path']).relative_to('data')
    corrupt.write_bytes(b'corrupted-fixture')
    mismatch = subprocess.run(verify, capture_output=True, text=True)
    assert mismatch.returncode == 1 and '자료/raw/' in mismatch.stderr and 'mismatch' in mismatch.stderr
    corrupt.unlink()
    missing = subprocess.run(verify, capture_output=True, text=True)
    assert missing.returncode == 1 and '자료/raw/' in missing.stderr and 'missing' in missing.stderr

# Real snapshot availability is reported separately from the synthetic checks above.
actual = subprocess.run([
    sys.executable, str(SOURCE / '수집도구/원본_보관본_해시_검증.py'),
], capture_output=True, text=True)
assert actual.returncode == 1 and actual.stderr.count(' missing') == 15
report = {
    'result': 'passed', 'fixture_type': 'synthetic temporary files only',
    'fixture_manifest_files': 15, 'fixture_replay_case_rows': 4,
    'fixture_replay_control_rows': 8, 'corruption_rejected': True, 'missing_rejected': True,
    'real_snapshot': 'not restored; 15 missing, real replay not executed',
    'network_calls': 0,
}
(AUDIT / 'collection-path-verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
