-- 새 개발 볼륨 초기화 시에만 실행된다. 기존 DB 업그레이드는 마이그레이션으로 관리한다.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
