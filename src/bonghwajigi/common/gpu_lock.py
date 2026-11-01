from pathlib import Path


class GpuLease:
    """Linux에서 모델 상주와 학습 프로세스의 GPU 동시 점유를 막는다."""

    def __init__(self, path: Path):
        self.path = path
        self.file = None

    def acquire(self) -> None:
        import fcntl

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.path.open("a+")
        try:
            fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.close()
            raise RuntimeError("GPU가 다른 서빙 또는 학습 프로세스에서 사용 중입니다.") from None

    def close(self) -> None:
        if self.file:
            self.file.close()
            self.file = None
