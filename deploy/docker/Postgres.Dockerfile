# 실행 기반 초안. A3에서 실제 확장 버전과 이미지 digest를 고정한다.
FROM postgis/postgis:16-3.5
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*
COPY deploy/postgres/001-extensions.sql /docker-entrypoint-initdb.d/001-extensions.sql
