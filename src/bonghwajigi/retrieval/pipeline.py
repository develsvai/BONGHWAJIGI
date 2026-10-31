from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import aliased

from bonghwajigi.contracts.analysis import AnalysisInput, RetrievalDocument
from bonghwajigi.db.analysis_models import AnalysisJob, AnalysisOutbox, DocumentChunk, now
from bonghwajigi.retrieval.embedding import EmbeddingError


def index_document(session, document: RetrievalDocument, embedder, settings):
    existing = session.scalar(
        select(DocumentChunk.id)
        .where(
            DocumentChunk.scenario_id == document.scenario_id,
            DocumentChunk.document_id == document.document_id,
            DocumentChunk.revision == document.revision,
            DocumentChunk.embedding_revision == settings.embedding_revision,
        )
        .limit(1)
    )
    if existing:
        return
    chunks = [document.text[start : start + 512] for start in range(0, len(document.text), 448)]
    vectors = embedder.encode(chunks, "document")
    for index, (text, vector) in enumerate(zip(chunks, vectors, strict=True)):
        session.execute(
            insert(DocumentChunk)
            .values(
                scenario_id=document.scenario_id,
                document_id=document.document_id,
                revision=document.revision,
                chunk_index=index,
                disaster_type=document.disaster_type,
                source_kind=document.source_kind,
                text=text,
                source=document.source.model_dump(mode="json"),
                origin=document.origin,
                valid_from=document.valid_from,
                valid_until=document.valid_until,
                published_at=document.source.published_at,
                embedding_model=settings.embedding_model,
                embedding_revision=settings.embedding_revision,
                embedding=vector,
            )
            .on_conflict_do_nothing(
                index_elements=[
                    "scenario_id",
                    "document_id",
                    "revision",
                    "chunk_index",
                    "embedding_revision",
                ]
            )
        )
    session.flush()


def search_chunks(session, scenario_id, payload, vector, settings):
    previous = aliased(DocumentChunk)
    latest = (
        select(func.max(previous.revision))
        .where(
            previous.scenario_id == DocumentChunk.scenario_id,
            previous.document_id == DocumentChunk.document_id,
            previous.valid_from <= payload.as_of,
            previous.published_at <= payload.as_of,
        )
        .correlate(DocumentChunk)
        .scalar_subquery()
    )
    distance = DocumentChunk.embedding.cosine_distance(vector)
    rows = session.execute(
        select(DocumentChunk, distance.label("distance"))
        .where(
            DocumentChunk.scenario_id == scenario_id,
            DocumentChunk.disaster_type == payload.disaster_type,
            DocumentChunk.embedding_model == settings.embedding_model,
            DocumentChunk.embedding_revision == settings.embedding_revision,
            DocumentChunk.revision == latest,
            DocumentChunk.valid_from <= payload.as_of,
            DocumentChunk.published_at <= payload.as_of,
            or_(DocumentChunk.valid_until.is_(None), DocumentChunk.valid_until > payload.as_of),
        )
        .order_by(distance, DocumentChunk.document_id, DocumentChunk.chunk_index)
        .limit(settings.retrieval_top_k * 4)
    ).all()
    evidence, seen = [], set()
    for chunk, difference in rows:
        url = chunk.source["url"]
        if url in seen:
            continue
        seen.add(url)
        evidence.append(
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "revision": chunk.revision,
                "text": chunk.text,
                "source": chunk.source,
                "origin": chunk.origin,
                "source_kind": chunk.source_kind,
                "score": round(1 - float(difference), 6),
                "score_kind": "cosine_similarity",
                "approved_policy": False,
            }
        )
        if len(evidence) >= settings.retrieval_top_k:
            break
    return evidence


def analyze(session, job, embedder, web_search, settings):
    payload = AnalysisInput.model_validate(job.body["payload"])
    web = {"status": "disabled", "result_count": 0}
    if settings.web_search_enabled:
        documents, web = web_search.search(payload.search_query, job.scenario_id, payload.as_of)
        for document in documents:
            index_document(session, document, embedder, settings)
    vector = embedder.encode([payload.search_query + "\n" + payload.text], "query")[0]
    evidence = search_chunks(session, job.scenario_id, payload, vector, settings)
    warnings = []
    if web["status"] == "unavailable":
        warnings.append("WEB_SEARCH_UNAVAILABLE")
    if not evidence:
        warnings.append("NO_RETRIEVED_EVIDENCE")
    return {
        "schema_version": "0.1.0",
        "mode": "simulation",
        "scenario_id": job.scenario_id,
        "event_id": job.external_id,
        "event_origin": job.body["origin"],
        "stage": "ready_for_qwen",
        "event": payload.model_dump(mode="json"),
        "retrieved_evidence": evidence,
        "web_search": web,
        "embedding": {
            "model": settings.embedding_model,
            "revision": settings.embedding_revision,
            "dimensions": 1024,
        },
        "retrieval_status": "partial" if warnings else "complete",
        "warnings": warnings,
        "qwen_invoked": False,
        "token_budget_checked": False,
        "evidence_is_untrusted_data": True,
    }


def run_job(job_id, sessions, embedder, web_search, settings):
    with sessions.begin() as session:
        job = session.scalar(select(AnalysisJob).where(AnalysisJob.id == job_id).with_for_update())
        if job is None:
            return {"status": "not_found"}
        if job.status in {"indexed", "ready_for_qwen", "failed"}:
            return {"status": job.status, "duplicate": True}
        job.attempts += 1
        job.status = "processing"
        try:
            # SAVEPOINT에 작업 결과를 묶어 실패 시 부분 벡터나 전달 자료가 남지 않게 한다.
            with session.begin_nested():
                if job.kind == "document":
                    index_document(
                        session, RetrievalDocument.model_validate(job.body), embedder, settings
                    )
                    result, state = {"indexed": True}, "indexed"
                else:
                    result, state = (
                        analyze(session, job, embedder, web_search, settings),
                        "ready_for_qwen",
                    )
            job.result, job.status, job.error_code = result, state, None
        except EmbeddingError as exc:
            job.error_code = exc.code
            job.status = "failed" if exc.permanent or job.attempts >= 3 else "retry"
        if job.status == "retry":
            from datetime import timedelta

            outbox = session.scalar(select(AnalysisOutbox).where(AnalysisOutbox.job_id == job.id))
            outbox.next_dispatch_at = now() + timedelta(seconds=min(5 * 2**job.attempts, 60))
        return {"status": job.status, "attempts": job.attempts, "error_code": job.error_code}
