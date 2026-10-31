#!/usr/bin/env bash
# 시간별 관측 접근 위험 연구. 대응 정책/레벨을 설정하거나 모델을 운영 배포하지 않는다.
set -Eeuo pipefail
cd "$(dirname "$0")/../.."
python_bin=training/.venv/bin/python
dataset_dir=data/processed/goes-hourly-v3
config_file=training/configs/goes-hourly-v1.json
run_dir="data/artifacts/xgboost/hourly-$(date -u +%Y%m%dT%H%M%SZ)-$$"
"$python_bin" - <<'PY'
import json
from pathlib import Path
from bonghwa_training.download import file_sha256
root = Path('data/processed/goes-hourly-v3')
config = Path('training/configs/goes-hourly-v1.json')
c = json.loads(config.read_text())
assert file_sha256(config) == file_sha256(root / 'config.json')
for event in c['events']:
    if event['split'] == 'test':
        continue
    name = event['id']
    report = json.loads((root / f'{name}-report.json').read_text())
    assert report['sha256'] == file_sha256(root / f'{name}.parquet')
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
      echo 'Qwen 서비스 시작 완료. ready 명령으로 두 모델의 준비 상태를 확인하세요.'
    else
      echo 'Qwen 복구 실패: 서비스 상태를 확인하세요.' >&2
      result=1
    fi
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
