#!/usr/bin/env bash
# 시간별 관측 접근 위험 연구. 대응 정책/레벨을 설정하거나 모델을 운영 배포하지 않는다.
set -Eeuo pipefail
cd "$(dirname "$0")/../.."
python_bin=training/.venv/bin/python
dataset_dir="${BONGHWA_HOURLY_DATASET:-data/processed/goes-hourly-v3}"
config_file="${BONGHWA_HOURLY_CONFIG:-training/configs/goes-hourly-v1.json}"
run_dir="data/artifacts/xgboost/hourly-$(date -u +%Y%m%dT%H%M%SZ)-$$"
"$python_bin" - "$dataset_dir" "$config_file" <<'PY'
import json
import sys
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq
from bonghwa_training.download import file_sha256
root = Path(sys.argv[1])
config = Path(sys.argv[2])
c = json.loads(config.read_text())
assert file_sha256(config) == file_sha256(root / 'config.json')
for event in c['events']:
    if event['split'] == 'test':
        continue
    name = event['id']
    report = json.loads((root / f'{name}-report.json').read_text())
    assert report['sha256'] == file_sha256(root / f'{name}.parquet')
for split in ('train', 'validation'):
    targets = []
    periods = []
    for event in c['events']:
        if event['split'] != split:
            continue
        table = pq.read_table(root / f"{event['id']}.parquet", columns=['fire_within_horizon', 'horizon_hours'])
        targets.append(table['fire_within_horizon'].to_numpy())
        periods.append(table['horizon_hours'].to_numpy())
    y, h = np.concatenate(targets), np.concatenate(periods)
    for hours in (1, 3, 6):
        if len(np.unique(y[h == hours])) != 2:
            raise ValueError(f'{split} {hours}시간 정답의 양성/음성이 부족합니다. 서빙을 중지하지 않습니다.')
print('사건 분리 학습·검증·보정 자료의 계약과 SHA 확인 완료. 최종 사건은 읽지 않았습니다.')
PY
mkdir -p data/artifacts/xgboost
was_active=0
if systemctl --user is-active --quiet bonghwajigi-gpu.service; then
  was_active=1
fi
restore_serving() {
  result=$?
  trap - EXIT INT TERM
  if [[ "$was_active" == 1 ]]; then
    if systemctl --user start bonghwajigi-gpu.service; then
      serving_ready=0
      for ((ready_attempt=0; ready_attempt<30; ready_attempt++)); do
        if .venv-gpu/bin/python tools/gpu_client.py ready >/dev/null 2>&1; then
          serving_ready=1
          break
        fi
        sleep 2
      done
      if [[ "$serving_ready" == 1 ]]; then
        echo 'Qwen 생성·임베딩 모델 모두 ready 복구 확인.'
      else
        echo 'Qwen 시작 후 ready를 확인하지 못했습니다.' >&2
        result=1
      fi
    else
      echo 'Qwen 복구 실패: 서비스 상태를 확인하세요.' >&2
      result=1
    fi
  fi
  if [[ "$result" == 0 && -f "$run_dir/report.json" ]]; then
    "$python_bin" - "$run_dir" "$dataset_dir" "$config_file" "$was_active" <<'PY'
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from bonghwa_training.download import file_sha256
run, dataset, config = map(Path, sys.argv[1:4])
report = json.loads((run / 'report.json').read_text())
receipt = {
    'completed_at_utc': datetime.now(UTC).isoformat(),
    'run': str(run), 'dataset': str(dataset),
    'config_sha256': file_sha256(config),
    'report_sha256': file_sha256(run / 'report.json'),
    'model_sha256': report['experiments'][report['selected']]['model_sha256'],
    'serving_was_active': sys.argv[4] == '1',
    'serving_ready_restored': sys.argv[4] == '1',
    'operational_use': False,
}
with (dataset / f'{run.name}-completion.json').open('x') as dst:
    dst.write(json.dumps(receipt, indent=2) + '\n')
PY
    receipt_status=$?
    if [[ "$receipt_status" != 0 ]]; then result="$receipt_status"; fi
  fi
  exit "$result"
}
trap restore_serving EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
if [[ "$was_active" == 1 ]]; then
  echo '시간별 연구용 GPU 학습을 위해 Qwen 서비스를 일시 중지합니다.'
  systemctl --user stop bonghwajigi-gpu.service
fi
echo "학습 로그: $run_dir.log"
"$python_bin" -u -m bonghwa_training.goes_train \
  --dataset "$dataset_dir" --config "$config_file" --output "$run_dir" \
  --device cuda "$@" 2>&1 | tee "$run_dir.log"
echo "시간별 연구용 비교 완료: $run_dir/report.json"
