import math

import httpx

from bonghwajigi.common.config import Settings


class EmbeddingError(RuntimeError):
    def __init__(self, code: str, permanent: bool = False):
        super().__init__(code)
        self.code, self.permanent = code, permanent


class EmbeddingClient:
    def __init__(self, settings: Settings, transport=None):
        self.settings = settings
        if not settings.embedding_service_token or not settings.embedding_revision:
            raise RuntimeError("임베딩 서비스 토큰과 고정 revision이 필요합니다.")
        self.client = httpx.Client(
            base_url=settings.gpu_base_url,
            headers={
                "Authorization": "Bearer " + settings.embedding_service_token.get_secret_value()
            },
            timeout=settings.embedding_timeout_seconds,
            follow_redirects=False,
            transport=transport,
        )

    def close(self):
        self.client.close()

    def encode(self, texts: list[str], input_type: str) -> list[list[float]]:
        result = []
        for offset in range(0, len(texts), 8):
            batch = texts[offset : offset + 8]
            try:
                response = self.client.post(
                    "/internal/v1/embeddings", json={"texts": batch, "input_type": input_type}
                )
            except httpx.HTTPError:
                raise EmbeddingError("EMBEDDING_UNAVAILABLE") from None
            if response.status_code != 200:
                raise EmbeddingError(
                    "EMBEDDING_INPUT_OR_AUTH_ERROR"
                    if response.status_code < 500
                    else "EMBEDDING_UNAVAILABLE",
                    permanent=response.status_code < 500,
                )
            try:
                body = response.json()
                vectors = body["vectors"]
                assert body["model"] == self.settings.embedding_model
                assert body["revision"] == self.settings.embedding_revision
                assert body["dimensions"] == 1024 and len(vectors) == len(batch)
                assert body["normalized"] is True
                for vector in vectors:
                    assert len(vector) == 1024
                    assert all(type(v) in (float, int) and math.isfinite(v) for v in vector)
                    assert abs(math.sqrt(sum(v * v for v in vector)) - 1) < 0.01
            except (KeyError, TypeError, ValueError, AssertionError):
                raise EmbeddingError("EMBEDDING_CONTRACT_MISMATCH", permanent=True) from None
            result.extend(vectors)
        return result
