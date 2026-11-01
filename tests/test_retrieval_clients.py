from datetime import UTC, datetime

import httpx
import pytest

from bonghwajigi.common.config import Settings
from bonghwajigi.retrieval.embedding import EmbeddingClient, EmbeddingError
from bonghwajigi.retrieval.web_search import NewsSearch


def config(**kwargs):
    return Settings(
        embedding_service_token="test-only", embedding_revision="test-revision", **kwargs
    )


def embedding_response():
    return {
        "model": "Qwen/Qwen3-Embedding-0.6B",
        "revision": "test-revision",
        "dimensions": 1024,
        "normalized": True,
        "vectors": [[1.0] + [0.0] * 1023],
    }


@pytest.mark.parametrize("failure", ["revision", "dimensions", "nan", "norm", "count"])
def test_embedding_contract_rejects_incompatible_vectors(failure):
    body = embedding_response()
    if failure == "revision":
        body["revision"] = "other"
    if failure == "dimensions":
        body["dimensions"] = 3
    if failure == "nan":
        body["vectors"][0][0] = "NaN"
    if failure == "norm":
        body["vectors"][0][0] = 0.0
    if failure == "count":
        body["vectors"] = []
    client = EmbeddingClient(
        config(), httpx.MockTransport(lambda request: httpx.Response(200, json=body))
    )
    try:
        with pytest.raises(EmbeddingError, match="CONTRACT_MISMATCH"):
            client.encode(["시연 문장"], "query")
    finally:
        client.close()


def test_embedding_client_only_calls_embedding_endpoint_and_classifies_retry():
    paths = []

    def response(request):
        paths.append(request.url.path)
        return httpx.Response(503)

    client = EmbeddingClient(config(), httpx.MockTransport(response))
    try:
        with pytest.raises(EmbeddingError) as error:
            client.encode(["시연 문장"], "document")
        assert not error.value.permanent
    finally:
        client.close()
    assert paths == ["/internal/v1/embeddings"]


def test_news_search_filters_future_and_duplicate_results_and_marks_unverified():
    xml = b"""<rss><channel>
      <item><title>demo fire</title><link>https://example.invalid/news</link>
      <pubDate>Sat, 31 Oct 2026 00:00:00 GMT</pubDate>
      <description>&lt;b&gt;demo&lt;/b&gt;</description></item>
      <item><title>duplicate</title><link>https://example.invalid/news</link>
      <pubDate>Sat, 31 Oct 2026 00:00:00 GMT</pubDate></item>
      <item><title>future</title><link>https://example.invalid/future</link>
      <pubDate>Sun, 01 Nov 2026 00:00:00 GMT</pubDate></item>
      </channel></rss>"""
    provider = NewsSearch(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=xml))
    )
    documents, meta = provider.search(
        "시연 검색", "scenario-one", datetime(2026, 10, 31, 12, tzinfo=UTC)
    )
    assert len(documents) == 1 and meta["status"] == "ok"
    assert documents[0].source.verified is False
    assert documents[0].scenario_id == "scenario-one"
    assert documents[0].text == "demo fire\ndemo"


def test_unavailable_or_unsafe_web_response_does_not_become_evidence():
    xml = b'<!DOCTYPE x [<!ENTITY x SYSTEM "file:///etc/passwd">]><rss>&x;</rss>'
    provider = NewsSearch(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=xml))
    )
    documents, meta = provider.search("시연", "scenario-one", datetime.now(UTC))
    assert not documents and meta["status"] == "unavailable"
