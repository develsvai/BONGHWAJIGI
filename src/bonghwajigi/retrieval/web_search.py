from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from hashlib import sha256
from html.parser import HTMLParser

import httpx
from defusedxml.ElementTree import fromstring

from bonghwajigi.contracts.analysis import RetrievalDocument, Source


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain_text(value: str) -> str:
    parser = PlainText()
    parser.feed(value)
    return " ".join(" ".join(parser.parts).split())


class NewsSearch:
    """인터넷 뉴스 검색 결과의 제목·짧은 설명만 확보한다. 기사 본문은 수집하지 않는다."""

    def __init__(self, max_results: int = 5, transport=None, lookback_days: int = 7):
        self.max_results = max_results
        self.transport = transport
        self.lookback_days = lookback_days

    def search(self, query: str, scenario_id: str, as_of: datetime):
        collected = datetime.now(UTC)
        after = (as_of - timedelta(days=self.lookback_days)).date().isoformat()
        before = (as_of + timedelta(days=1)).date().isoformat()
        search_query = f"산불 {query} after:{after} before:{before}"
        metadata = {
            "provider": "google_news_rss",
            "query": search_query,
            "searched_at": collected.isoformat(),
            "status": "ok",
            "result_count": 0,
        }
        try:
            with httpx.Client(
                timeout=10, transport=self.transport, follow_redirects=False
            ) as client:
                with client.stream(
                    "GET",
                    "https://news.google.com/rss/search",
                    params={
                        "q": search_query,
                        "hl": "ko",
                        "gl": "KR",
                        "ceid": "KR:ko",
                    },
                ) as response:
                    response.raise_for_status()
                    data = bytearray()
                    for chunk in response.iter_bytes():
                        data.extend(chunk)
                        if len(data) > 512_000:
                            raise ValueError("검색 응답 상한 초과")
            root = fromstring(bytes(data))
            documents, seen = [], set()
            for item in root.findall("./channel/item"):
                title = plain_text(item.findtext("title", ""))[:500]
                url = item.findtext("link", "").strip()
                try:
                    published = parsedate_to_datetime(item.findtext("pubDate", ""))
                    if (
                        published.tzinfo is None
                        or published > as_of
                        or published < as_of - timedelta(days=self.lookback_days)
                    ):
                        continue
                    if not title or url in seen:
                        continue
                    document = RetrievalDocument(
                        mode="simulation",
                        scenario_id=scenario_id,
                        document_id="web-"
                        + sha256((url + title + published.isoformat()).encode()).hexdigest()[:40],
                        origin="collected_sample",
                        source_kind="news_search",
                        text=(title + "\n" + plain_text(item.findtext("description", ""))[:500]),
                        source=Source(
                            title=title,
                            url=url,
                            published_at=published,
                            collected_at=collected,
                            verified=False,
                            publisher=item.findtext("source", "")[:200] or None,
                            publisher_url=(
                                item.find("source").get("url")
                                if item.find("source") is not None
                                else None
                            ),
                        ),
                        valid_from=published,
                        valid_until=published + timedelta(days=self.lookback_days),
                    )
                except (ValueError, TypeError):
                    continue
                documents.append(document)
                seen.add(url)
                if len(documents) >= self.max_results:
                    break
            metadata["result_count"] = len(documents)
            if not documents:
                metadata["status"] = "no_results"
            return documents, metadata
        except Exception:
            # 외부 응답/URL·검색어 원문을 예외 로그에 넣지 않는다. 저장 근거로 계속 진행한다.
            metadata.update(status="unavailable", error_code="WEB_SEARCH_UNAVAILABLE")
            return [], metadata
