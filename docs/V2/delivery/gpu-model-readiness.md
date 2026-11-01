# GPU 서버의 세 모델 실행 준비 결과

확인일: 2026-10-31 18:08~18:13 KST. Loom Task: `task-20261031-085956-gpu-qwen-xgboost-9eea12a5`.

두 Qwen 모델의 다운로드·동시 상주·실제 생성/임베딩과 XGBoost의 합성 CUDA 학습·저장·CPU 재로딩을 확인했다. 사용자 GPU 서비스는 localhost에서 실행 중이며 로그아웃 후 유지와 자동 시작을 설정했다. 실제 산불 모델의 정답·목표·성능이나 개인 대응 정책을 준비한 결과는 아니다.

## 설치 위치와 버전

대상은 `inno-gpu-011`, 계정은 `ncloud`, 프로젝트는 `/home1/ncloud/bonghwajigi`다. 기존 전역 Python과 다른 서비스는 변경하지 않고 새 사용자 환경에 설치했다.

| 환경 | 경로·주요 버전 |
| --- | --- |
| 공통 Python | 서버 기존 Python 3.12.3 |
| GPU 서빙 | `.venv-gpu`: torch 2.11.0+cu128, Transformers 4.57.6, Sentence Transformers 5.7.0 |
| XGBoost | `.venv-ml`: XGBoost 3.4.1, 별도 NumPy/pandas/PyArrow/scikit-learn |
| 의존성 정본 | 저장소의 `pyproject.toml`, `uv.lock` |
| 모델 캐시 | `/home1/ncloud/bonghwajigi/models/hub` |
| 설치 정보 | 서버 `model-manifest.json` |
| 서비스 설정 | `~/.config/bonghwajigi/gpu.env`, 권한 600 |

서비스 토큰은 서버에서 새로 생성했고 출력하거나 저장소에 복사하지 않았다. SSH 비밀번호도 보관하지 않았다. 공식 uv 설치 주소가 403으로 차단돼 공식 PyPI의 uv 0.11.10 wheel SHA256을 대조한 후 사용자 `~/.local/bin/uv`에 설치했다.

| 모델 | 고정 revision |
| --- | --- |
| `Qwen/Qwen3-4B-Instruct-2507` | `cdbee75f17c01a7cc42f958dc650907174af0554` |
| `Qwen/Qwen3-Embedding-0.6B` | `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` |

두 모델은 캐시의 고정 revision을 BF16으로 로딩한다. 실행 중 자동 다운로드는 하지 않는다. Qwen은 사실 정리·설명 도구이며 검토되지 않은 출력을 개인 대응 정책으로 승인하지 않는다.

## 바로 사용하기

```sh
ssh inno-gpu-011
cd /home1/ncloud/bonghwajigi
.venv-gpu/bin/python tools/gpu_client.py ready
.venv-gpu/bin/python tools/gpu_client.py generate --text "한국어로 모델 준비 상태를 한 문장으로 써줘."
.venv-gpu/bin/python tools/gpu_client.py embed --text "임베딩할 문서"
.venv-gpu/bin/python tools/gpu_client.py embed --input-type query --text "찾을 자료에 대한 질문"
```

클라이언트는 서버 설정 파일에서 토큰을 읽어 localhost API를 호출하며 토큰을 출력하지 않는다. `/internal/v1/generate`와 `/internal/v1/embeddings`는 Bearer 서비스 토큰이 필요하다. 일반 서버에서 이 API를 호출하는 서비스 경로·인증 주입은 A3에서 연결한다. 이번에는 공개 포트나 Tailnet 규칙을 변경하지 않았다.

- 입력+출력 합계 4096토큰, 생성 출력 최대 512토큰이다. 초과 입력은 잘라 쓰지 않고 422로 거부한다.
- 임베딩은 요청당 최대 8문서, 문서당 4096토큰 이내다. 1024차원 float32 벡터를 반환하고 단위 길이로 정규화한다. 질의에는 검색 지시 접두사를 적용한다.
- 한 프로세스에 두 모델을 한 번씩 올리고 GPU 요청을 직렬 실행한다. 다른 요청이 점유 중이면 최대 2초 대기 후 503/Retry-After를 반환한다.
- `/health/live`는 프로세스 상태, `/health/ready`는 두 모델의 로딩 상태다. 현재 GPU 서버의 ready는 200이며 기본 로컬 스캐폴딩은 `BONGHWA_GPU_ENABLED=false`라 503을 유지한다.
- 모델 오류를 확률 0이나 안전 판정으로 바꾸지 않는다. 입력과 인증 토큰은 접근 로그에 남기지 않는다.

## 서비스 관리와 XGBoost

```sh
systemctl --user status bonghwajigi-gpu.service
systemctl --user restart bonghwajigi-gpu.service
journalctl --user -u bonghwajigi-gpu.service -n 30 --no-pager
```

사용자 서비스는 `active/enabled`, `Linger=yes`이고 `127.0.0.1:8001`에만 바인딩한다. 기존 관리 SSH 연결을 종료하고 새 로그인에서 준비 상태 200을 재확인했다. 새 서비스의 코드 재시작도 검증했다. 실제 서버 재부팅 시험은 수행하지 않았다.

XGBoost는 설치·CUDA 실행 준비가 끝났다. 실데이터 학습 전에 C1의 예측 목표·정답·피처 계약과 C4의 평가 기준이 필요하다. 생성 모델의 학습 또는 파인튜닝은 수행하지 않았다.

새 합성 CUDA 검사를 실행하려면 모델 서비스를 내린 뒤 새 산출물 디렉터리를 지정한다. 검사가 끝나면 서비스를 다시 시작한다.

```sh
cd /home1/ncloud/bonghwajigi
systemctl --user stop bonghwajigi-gpu.service
.venv-ml/bin/python -m bonghwajigi.ml.cuda_check --output data/artifacts/cuda-check-new
systemctl --user start bonghwajigi-gpu.service
```

서빙과 학습은 같은 사용자 GPU 잠금 파일을 사용한다. 서빙 중 위 검사를 실행하면 학습 전에 거부되며 산출물도 생성하지 않는다. 잠금은 이 프로젝트의 실행기끼리 조율하는 장치이며 외부 CUDA 프로그램을 통제하는 GPU 격리 기능은 아니다.

검증용 `simulation-booster.ubj`는 `data/artifacts/cuda-check-20261031T090759Z/`에 있다. 합성 실행 검사 전용이며 산불 영향 확률 API에 사용하지 않는다.

## 실제 측정

[검증 근거 JSON](gpu-model-evidence.json)에 인증정보 없이 결과를 보관했다.

| 항목 | 결과 |
| --- | --- |
| Qwen 한국어 생성 | 입력 29 / 출력 9토큰, 약 845ms, `모델 준비 완료되었습니다.` |
| 문서 임베딩 | 2문서 × 1024차원, 약 124ms |
| 문서 벡터 길이 | 1.0000000383 / 1.0000000101 |
| 질의 임베딩 | 1024차원, 약 32ms |
| 무인증 요청 | 401 |
| 전체 토큰 상한 초과 | 422 |
| 두 모델 호출 후 GPU 메모리 | 9,134 / 23,034 MiB |
| 서빙 중 XGBoost 학습 시도 | 잠금으로 거부, 산출물 생성 없음 |
| XGBoost 합성 CUDA 학습 | `cuda:0`, 5000행 × 16피처, 20회, 약 0.319초 |
| 저장 후 CPU 재추론 최대 절대 차이 | 약 1.19 × 10⁻⁷ |
| 설치 후 잔여 디스크 | 약 61.23 GiB |

PyTorch CUDA runtime은 12.8이며 실제 L4 사용을 확인했다. 설치된 XGBoost wheel은 CUDA 13.3 빌드이고 같은 드라이버 580.159.04에서 실제 작은 학습이 통과했다. 다른 CUDA 기능·대규모 학습 조합까지 검증한 것은 아니다.

위 지연은 짧은 설치 검사 요청의 한 번 측정이다. 4096토큰·최대 배치·동시 사용자·한국어 문서 품질·장시간 운영 성능을 보장하지 않는다. 실제 자료의 검색 적합성·추출 품질·정책 설명 검증은 D3에서 이어간다. 공식 긴급 원문 경로는 이 모델 API를 기다리지 않아야 한다.
