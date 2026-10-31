#!/usr/bin/env bash
# 이미 승인된 국내 연구용 수집을 기다린 뒤 구축/환경 결합/학습/서빙 복구를 실행한다.
set -Eeuo pipefail
cd "$(dirname "$0")/../.."
acquire_unit="${1:?수집 systemd unit 필요}"
pending_contract="${2:?고정할 모델 계약 파일 필요}"
base_dataset="${BONGHWA_KMA_BASE_DATASET:-data/processed/korea-gk2a-hourly-v3}"
context_dataset="${BONGHWA_KMA_CONTEXT_DATASET:-data/processed/korea-gk2a-context-v3}"
context_contract="${BONGHWA_KMA_CONTEXT_CONFIG:-training/configs/korea-gk2a-context-v3.json}"
python_bin=training/.venv/bin/python
for ((attempt=0; attempt<720; attempt++)); do
  if ! systemctl --user is-active --quiet "$acquire_unit"; then
    break
  fi
  sleep 15
done
if systemctl --user is-active --quiet "$acquire_unit"; then
  echo '수집 대기 180분 초과. 학습을 시작하지 않습니다.' >&2
  exit 1
fi
if [[ "$(systemctl --user show "$acquire_unit" -p Result --value)" != success ]]; then
  echo '원본 수집 실패. 누락을 음성으로 채우거나 부분 자료로 자동 학습하지 않습니다.' >&2
  exit 1
fi
raw_dir=data/raw/korea-wildfire/gk2a-ff
if [[ ! -f "$raw_dir/acquisition-config-v1.json" ]]; then
  cp training/configs/korea-gk2a-hourly-v1.json "$raw_dir/acquisition-config-v1.json"
fi
"$python_bin" -u -m bonghwa_training.goes_build \
  --root "$raw_dir" --output "$base_dataset" --config "$pending_contract"
if [[ -n "${BONGHWA_KMA_REFERENCE_DATASET:-}" ]]; then
  "$python_bin" training/tools/verify_hourly_cohort.py \
    --reference "$BONGHWA_KMA_REFERENCE_DATASET" --candidate "$base_dataset" \
    --output "$base_dataset/cohort-verification.json"
fi
"$python_bin" -u -m bonghwa_training.hourly_context \
  --dataset "$base_dataset" --raw data/raw/korea-wildfire \
  --static data/processed/korea-hindcast-v2 --output "$context_dataset" \
  --config-output "$context_contract"
BONGHWA_HOURLY_DATASET="$context_dataset" \
BONGHWA_HOURLY_CONFIG="$context_contract" \
  bash training/tools/train_hourly_gpu.sh
.venv-gpu/bin/python tools/gpu_client.py ready
