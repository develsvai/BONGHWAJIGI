#!/usr/bin/env bash
# 이 명령을 직접 실행하면 Qwen 서비스를 잠시 멈추고 GPU 학습 종료 후 복구한다.
set -Eeuo pipefail
cd "$(dirname "$0")/../.."
python_bin=training/.venv/bin/python
dataset_dir=data/processed/ndws-v2-bootstrap
run_dir="data/artifacts/xgboost/ndws-$(date -u +%Y%m%dT%H%M%SZ)-$$"
if [[ ! -x "$python_bin" ]]; then
  echo 'training 환경이 없습니다. uv sync --project training --frozen --extra train 먼저 실행하세요.' >&2
  exit 1
fi
# 자료 검증은 서빙을 내리기 전에 수행한다.
"$python_bin" -m bonghwa_training.cli verify --output "$dataset_dir"
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
      echo 'Qwen 서비스 시작 명령을 완료했습니다. 모델 준비 상태는 ready 명령으로 확인하세요.'
    else
      echo 'Qwen 복구 실패: systemctl --user status bonghwajigi-gpu.service 를 확인하세요.' >&2
      result=1
    fi
  fi
  exit "$result"
}
trap restore_serving EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
if [[ "$was_active" == 1 ]]; then
  echo 'GPU 학습을 위해 Qwen 서비스를 일시 중지합니다.'
  systemctl --user stop bonghwajigi-gpu.service
fi
echo "학습 로그: $run_dir.log"
"$python_bin" -u -m bonghwa_training.train \
  --dataset "$dataset_dir" --output "$run_dir" --device cuda "$@" \
  2>&1 | tee "$run_dir.log"
echo "학습 완료: $run_dir/report.json"
