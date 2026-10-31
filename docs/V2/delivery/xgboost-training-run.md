# XGBoost 학습 시작 방법

사용자가 실행한 첫 CUDA 학습의 실제 완료·성능·서비스 복구 검증은 [학습 결과 검증 문서](xgboost-training-verification.md)를 따른다. 아래 준비 시점의 예상과 실제 측정 결과를 구분한다.

2026-10-31, Task `task-20261031-102643-xgboost-gpu-63a490e2`. 실제 자료 일부로 CPU 학습 실행기를 검증했다. GPU 전체 학습과 Qwen 서비스 중단은 이번 준비 작업에서 실행하지 않았다.

GPU 서버 `/home1/ncloud/bonghwajigi/`에 코드·`training/.venv`·원본 `data/raw/ndws-v2/`·변환 `data/processed/ndws-v2-bootstrap/`을 준비했다. 대용량 Tailnet 전송이 느려 서버에서 같은 원본을 직접 다운로드하고 재생성했다. 원본 SHA256 3개와 train/test Parquet 해시는 맥과 일치한다. validation은 코사인 파생 열에서만 플랫폼에 따른 바이트 차이가 있고, 소수 6자리 반올림 값의 해시는 일치한다. 나머지 19개 입력과 정답의 열 해시는 일치한다. 서버 보고서는 `training/reports/gpu-dataset-report.json`에 별도로 보존해 전체 바이트가 같다고 주장하지 않는다.

## 서버에서 시작

```bash
ssh inno-gpu-011
cd /home1/ncloud/bonghwajigi
systemd-run --user --unit=bonghwajigi-xgboost --collect \
  --working-directory=/home1/ncloud/bonghwajigi \
  /bin/bash training/tools/train_gpu.sh
```

위 명령을 사용자가 실행하면 **Qwen 생성·임베딩 서비스를 잠시 멈추고 GPU 학습 후 복구한다.** 학습 중 두 모델 API는 일시 사용할 수 없다. SSH가 끊겨도 학습은 유지된다. 같은 이름의 unit이 이미 실행 중이면 재시작이 거부된다.

별도 터미널에서 로그와 GPU 사용률을 확인한다.

```bash
journalctl --user -u bonghwajigi-xgboost -f
```

```bash
nvidia-smi -l 1
```

로그의 `train-aucpr`, `validation-aucpr`, `logloss`가 진행 상황을 보여 준다. 로그 보기의 Ctrl+C는 학습을 중단하지 않는다. 실제 중단 명령은 다음과 같다.

```bash
systemctl --user stop bonghwajigi-xgboost
```

스크립트는 정상 종료·오류·INT/TERM 때 기존에 켜져 있던 Qwen 서비스를 복구한다. SIGKILL·전원 차단에서는 쉘 복구를 보장하지 못한다. 시작 전 꺼져 있던 서비스는 자동으로 켜지 않는다. 복구 확인은 다음 명령으로 수행한다.

```bash
systemctl --user status bonghwajigi-gpu.service
systemctl --user start bonghwajigi-gpu.service
.venv-gpu/bin/python tools/gpu_client.py ready
```

서비스 start 성공과 두 모델의 로딩 완료는 구분한다. 실제 준비 완료는 ready로 확인한다.

## 설정과 산출물

서버의 `data/processed/ndws-v2-bootstrap/`에서 train 3,957,875행과 validation 3,978,515행을 사용한다. 기본 설정은 최대 300회, validation AUC-PR이 30회 개선되지 않으면 조기 종료, depth 6, learning rate 0.05, seed 47, CPU thread 4다. 최적화된 설정이라는 뜻은 아니다. validation에서 가장 좋은 회차를 저장한다.

[공식 GPU 사용법](https://xgboost.readthedocs.io/en/stable/gpu/index.html)의 hist/cuda 설정을 사용한다. 실제 장치가 CPU로 대체되면 성공으로 기록하지 않는다. 서빙과 같은 `/home1/ncloud/.cache/bonghwajigi/gpu.lock`을 사용하며 외부 CUDA 프로그램까지 격리하지는 않는다.

결과는 `data/artifacts/xgboost/ndws-<UTC시각>-<PID>/`에 저장되고 경로가 로그에 출력된다.

| 파일 | 내용 |
| --- | --- |
| `model.ubj` | 최적 회차의 모델 |
| `report.json` | 평가·기준선·데이터 해시·장치·피처 순서·CPU 재로딩 일치 검사 |
| `parameters.json` | 학습 설정 |
| `history.json` | 회차별 지표 |
| `feature-gain.json` | 피처 중요도 |
| 디렉터리 옆 같은 이름의 `.log` | 표준 출력·오류 |

성공 시에만 report.json을 기록한다. 실패한 디렉터리를 완성 모델로 취급하지 않는다. 학습 이력의 XGBoost aucpr과 최종 보고서 sklearn average_precision은 계산 정의가 다르다. 기준선은 학습 양성 비율의 상수 예측과 이전 화재 관측을 유지한 persistence다. persistence는 이전 관측이 알려진 행에서만 평가하며 같은 행에서의 모델 점수도 기록한다. 불명 관측은 0으로 바꾸지 않는다.

test는 기본 실행에서 모델 평가에 쓰지 않는다. 설정 고정 후 최종 평가 때만 `--evaluate-test`를 지정한다. validation은 조기 종료에 사용됐으므로 독립 최종 성능 근거가 아니다. 확률 보정은 수행하지 않았고 `operational_use=false`다. 0.5 기준 precision/recall은 진단용이며 대응 레벨 기준이 아니다.

## 환경 준비와 CPU 사전 실행

서버의 독립 환경은 training/.venv다. 다른 체크아웃에서 준비하려면 코드·변환 자료를 먼저 옮긴 뒤 실행한다.

```bash
~/.local/bin/uv sync --project training --frozen --extra train
training/.venv/bin/python -m bonghwa_training.train --help
```

일부 자료로 실행기를 확인하는 CPU 예시다. Qwen을 중단하지 않으며 출력 경로는 매번 새 경로를 지정한다.

```bash
training/.venv/bin/python -u -m bonghwa_training.train \
  --dataset data/processed/ndws-v2-bootstrap \
  --output data/artifacts/xgboost/cpu-preflight-new \
  --device cpu --max-rows 131072 --rounds 12 --early-stopping 4 --threads 2
```

로컬 사전 실행은 각 분할 첫 131,072행으로 조기 종료·4개 트리 저장·CPU 재로딩 최대 차이 0을 확인했다. 제한 표본은 순서에 따른 편향이 크며 최종 성능이 아니다. GPU 전체 학습의 시간·메모리·성능은 아직 측정하지 않았다. [데이터 한계](xgboost-training-data.md)에 따라 미국 1km 다음 일별 위성 관측 연구 모델로만 해석한다.

GPU 서버에서도 CPU 사전 실행을 완료했고 12개 트리 저장·재로딩 차이 0을 확인했다. 서로 다른 플랫폼에서 같은 seed가 동일 모델을 보장하지는 않는다. `/usr/bin/true`의 systemd 사용자 unit 실행과 기존 Qwen 잠금에 의한 학습 진입 거부도 검사했다. training 테스트 15개, Ruff와 bash 문법 검사를 통과했다. 실행 근거는 `training/reports/gpu-training-readiness.json`에 남겼다.
