#!/usr/bin/env bash
# v4 구축·학습·서빙 복구 후 CPU 기간그룹 CV와 고정 v3/v4 대조를 실행한다.
set -Eeuo pipefail
cd "$(dirname "$0")/../.."
python_bin=training/.venv/bin/python
dataset=data/processed/korea-gk2a-context-v4
config=training/configs/korea-gk2a-context-v4.json
unit=bonghwajigi-kma-research-v4.service
for ((attempt=0; attempt<720; attempt++)); do
  state="$(systemctl --user show "$unit" -p SubState --value)"
  if [[ "$state" != running && "$state" != start ]]; then break; fi
  sleep 15
done
if [[ "$state" == running || "$state" == start ]]; then
  echo 'v4 연구 완료 대기 180분 초과.' >&2
  exit 1
fi
if [[ "$(systemctl --user show "$unit" -p LoadState --value)" == loaded ]] && \
   { [[ "$(systemctl --user show "$unit" -p Result --value)" != success ]] || \
     [[ "$(systemctl --user show "$unit" -p ExecMainStatus --value)" != 0 ]]; }; then
  echo 'v4 연구 실패. 후속 비교를 시작하지 않습니다.' >&2
  exit 1
fi
current_run="$("$python_bin" - "$dataset" "$config" <<'PY'
import json
import sys
from pathlib import Path
from bonghwa_training.download import file_sha256
dataset, config = map(Path, sys.argv[1:])
digest = file_sha256(config)
receipts = [json.loads(p.read_text()) for p in dataset.glob('hourly-*-completion.json')]
receipts = [r for r in receipts if r['config_sha256'] == digest]
if len(receipts) != 1:
    raise ValueError('동일 설정의 학습 완료 영수증이 정확히 하나여야 합니다.')
r = receipts[0]
run = Path(r['run'])
if run.parent != Path('data/artifacts/xgboost') or not run.name.startswith('hourly-'):
    raise ValueError('학습 산출물 경로 오류')
report = json.loads((run / 'report.json').read_text())
if r['report_sha256'] != file_sha256(run / 'report.json'):
    raise ValueError('학습 결과 SHA 불일치')
if r['serving_was_active'] and not r['serving_ready_restored']:
    raise ValueError('기존 Qwen 복구가 확인되지 않았습니다.')
print(run)
PY
)"
output="data/artifacts/xgboost/kma-v4-groupcv-$(date -u +%Y%m%dT%H%M%SZ)"
"$python_bin" -u -m bonghwa_training.expanded_generalization_experiment \
  --dataset "$dataset" --config "$config" --output "$output"
"$python_bin" training/tools/compare_kma_generations.py \
  --previous-run data/artifacts/xgboost/hourly-20261031T135808Z-549349 \
  --previous-dataset data/processed/korea-gk2a-context-v3 \
  --current-run "$current_run" --dataset "$dataset" --cv-run "$output" \
  --output "$output/matched-comparison.json"
echo "v4 기간그룹 CV·동일 표본 비교 완료: $output"
