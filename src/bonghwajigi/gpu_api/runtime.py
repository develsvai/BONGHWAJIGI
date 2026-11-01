import threading
from contextlib import contextmanager
from time import perf_counter

from bonghwajigi.common.config import Settings
from bonghwajigi.common.gpu_lock import GpuLease
from bonghwajigi.contracts.models import EmbedRequest, GenerateRequest


class ModelBusyError(RuntimeError):
    pass


class ModelRuntime:
    def __init__(self, settings: Settings):
        if not settings.qwen_revision or not settings.embedding_revision:
            raise RuntimeError("두 모델의 고정 revision이 필요합니다.")
        import torch
        from sentence_transformers import SentenceTransformer
        from transformers import AutoModelForCausalLM, AutoTokenizer

        if not torch.cuda.is_available():
            raise RuntimeError("CUDA GPU를 확인할 수 없습니다.")
        self.settings, self.torch = settings, torch
        self.mutex = threading.Lock()
        self.lease = GpuLease(settings.gpu_lock_path)
        self.lease.acquire()
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                settings.qwen_model, revision=settings.qwen_revision, local_files_only=True
            )
            self.generation = (
                AutoModelForCausalLM.from_pretrained(
                    settings.qwen_model,
                    revision=settings.qwen_revision,
                    dtype=torch.bfloat16,
                    attn_implementation="sdpa",
                    local_files_only=True,
                )
                .to("cuda")
                .eval()
            )
            self.embedding = SentenceTransformer(
                settings.embedding_model,
                revision=settings.embedding_revision,
                device="cuda",
                local_files_only=True,
                model_kwargs={"dtype": torch.bfloat16, "attn_implementation": "sdpa"},
                processor_kwargs={"padding_side": "left"},
            )
            self.embedding.max_seq_length = settings.gpu_max_total_tokens
        except BaseException:
            self.lease.close()
            raise

    @contextmanager
    def exclusive(self):
        if not self.mutex.acquire(timeout=2):
            raise ModelBusyError("GPU 요청 처리 중입니다.")
        try:
            yield
        finally:
            self.mutex.release()

    def generate(self, request: GenerateRequest) -> dict:
        with self.exclusive(), self.torch.inference_mode():
            start = perf_counter()
            inputs = self.tokenizer.apply_chat_template(
                [{"role": "user", "content": request.text}],
                tokenize=True,
                add_generation_prompt=True,
                return_dict=True,
                return_tensors="pt",
            ).to("cuda")
            length = inputs["input_ids"].shape[1]
            limit = min(request.max_output_tokens, self.settings.gpu_max_output_tokens)
            if length + limit > self.settings.gpu_max_total_tokens:
                raise ValueError("입력과 출력 토큰 합계가 설정 상한을 초과합니다.")
            output = self.generation.generate(**inputs, max_new_tokens=limit, do_sample=False)
            tokens = output[0, length:]
            return {
                "model": self.settings.qwen_model,
                "revision": self.settings.qwen_revision,
                "text": self.tokenizer.decode(tokens, skip_special_tokens=True),
                "input_tokens": length,
                "output_tokens": len(tokens),
                "elapsed_ms": round((perf_counter() - start) * 1000, 2),
            }

    def embed(self, request: EmbedRequest) -> dict:
        prompt = (
            "Instruct: Retrieve relevant wildfire safety guidance documents.\nQuery: "
            if request.input_type == "query"
            else ""
        )
        with self.exclusive(), self.torch.inference_mode():
            start = perf_counter()
            encoded = self.embedding.tokenizer(
                [prompt + text for text in request.texts], truncation=False
            )
            if any(len(ids) > self.settings.gpu_max_total_tokens for ids in encoded["input_ids"]):
                raise ValueError("임베딩 입력 토큰 수가 설정 상한을 초과합니다.")
            vectors = self.embedding.encode(
                request.texts,
                prompt=prompt,
                batch_size=8,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
            # BF16 정규화의 반올림 오차를 줄여 저장용 float32 벡터의 단위 길이를 맞춘다.
            vectors = vectors.astype("float32")
            norms = (vectors * vectors).sum(axis=1, keepdims=True) ** 0.5
            if not self.torch.from_numpy(vectors).isfinite().all() or (norms <= 0).any():
                raise RuntimeError("유효하지 않은 임베딩 벡터입니다.")
            vectors /= norms
            return {
                "model": self.settings.embedding_model,
                "revision": self.settings.embedding_revision,
                "dimensions": int(vectors.shape[1]),
                "normalized": True,
                "vectors": vectors.tolist(),
                "elapsed_ms": round((perf_counter() - start) * 1000, 2),
            }

    def close(self) -> None:
        del self.generation
        del self.embedding
        self.torch.cuda.empty_cache()
        self.lease.close()
