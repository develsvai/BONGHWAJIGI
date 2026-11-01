"""Python 3.10+ standard library examples. No model or routing engine included."""
import argparse
import csv
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
KST = dt.timezone(dt.timedelta(hours=9))
SOURCES = {
    'firms0': 'MODIS_C6_1_Global_7d.csv',
    'firms1': 'SUOMI_VIIRS_C2_Global_7d.csv',
    'firms2': 'J1_VIIRS_C2_Global_7d.csv',
    'firms3': 'J2_VIIRS_C2_Global_7d.csv',
}

def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def request(url, path):
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    parsed = urllib.parse.urlsplit(url)
    params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    safe_params = [(k, 'REDACTED' if k.lower() in ('servicekey', 'authkey', 'token') else v) for k,v in params]
    safe_url = urllib.parse.urlunsplit(parsed._replace(query=urllib.parse.urlencode(safe_params)))
    info = {'request_url': safe_url, 'requested_at_utc': started, 'raw_file': path.name}
    try:
        with urllib.request.urlopen(url, timeout=45) as r:
            path.write_bytes(r.read())
            info.update(http=r.status, content_type=r.headers.get('Content-Type'))
    except urllib.error.HTTPError as e:
        path.write_bytes(e.read())
        info.update(http=e.code, content_type=e.headers.get('Content-Type'), status='미수집')
    except (urllib.error.URLError, TimeoutError) as e:
        info.update(status='미수집', error_type=type(e).__name__)
    info['received_at_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    if path.exists():
        info.update(bytes=path.stat().st_size, sha256=sha(path))
    return info

def csv_out(path, rows, fields):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

def filter_firms(raw_dir, dest, start, end, bbox, check_snapshot):
    start_at = dt.datetime.fromisoformat(start).replace(tzinfo=KST)
    end_at = dt.datetime.fromisoformat(end).replace(tzinfo=KST)
    if start_at >= end_at:
        raise ValueError('end must be later than start')
    west, south, east, north = bbox
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError('bbox must be west,south,east,north in degrees')
    manifest = {r['source_id']: r for r in json.loads((ROOT/'data/raw_manifest.json').read_text(encoding='utf8'))}
    hits, control, summary, fields = [], [], [], []
    for sid, filename in SOURCES.items():
        path = raw_dir / filename
        if check_snapshot and sha(path) != manifest[sid]['sha256']:
            raise ValueError('Snapshot hash mismatch: ' + sid)
        n = m = k = 0
        date_min = date_max = None
        with path.open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            required = {'latitude', 'longitude', 'acq_date', 'acq_time'}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError('Not a valid FIRMS CSV: ' + sid)
            for field in [*reader.fieldnames, 'source_id', 'observed_at_utc', 'observed_at_kst']:
                if field not in fields:
                    fields.append(field)
            for r in reader:
                n += 1
                date_min = min(date_min or r['acq_date'], r['acq_date'])
                date_max = max(date_max or r['acq_date'], r['acq_date'])
                hhmm = r['acq_time'].zfill(4)
                observed = dt.datetime.fromisoformat(r['acq_date']+'T'+hhmm[:2]+':'+hhmm[2:]).replace(tzinfo=dt.timezone.utc)
                t = observed.astimezone(KST)
                if not start_at <= t < end_at:
                    continue
                lat, lon = float(r['latitude']), float(r['longitude'])
                r.update(source_id=sid, observed_at_utc=observed.isoformat(), observed_at_kst=t.isoformat())
                for field in r:
                    if field not in fields:
                        fields.append(field)
                if 124 <= lon <= 132 and 33 <= lat <= 39:
                    control.append(r.copy()); k += 1
                if west <= lon <= east and south <= lat <= north:
                    hits.append(r.copy()); m += 1
        # Dates in source must span all UTC calendar days required by the query.
        covered = bool(date_min and date_min <= start_at.astimezone(dt.timezone.utc).date().isoformat()
                       and date_max >= (end_at-dt.timedelta(microseconds=1)).astimezone(dt.timezone.utc).date().isoformat())
        summary.append({'source_id':sid, 'raw_rows':n, 'min_date_utc':date_min, 'max_date_utc':date_max,
                        'date_range_spans_query':covered, 'case_rows':m, 'control_bbox_rows':k,
                        'status':('수집완료' if m else '0건') if covered else '미검증', 'raw_sha256':sha(path)})
    csv_out(dest/'FIRMS_case.csv', hits, fields)
    csv_out(dest/'FIRMS_control_bbox.csv', control, fields)
    result = {'start_kst_inclusive':start_at.isoformat(), 'end_kst_exclusive':end_at.isoformat(),
              'bbox_wsen':bbox, 'source_checks':summary, 'case_rows':len(hits), 'control_rows':len(control),
              'note':'0건은 무화재 정답이 아님. control bbox는 국경이 아니며 일본 등 포함. 탐지 레코드는 독립 화재 사건이 아님.'}
    write_json(dest/'query_summary.json',result)
    print(json.dumps(result, ensure_ascii=False, indent=2))

def main():
    ap = argparse.ArgumentParser(description='재난 데이터 다운로드 표본과 FIRMS 보관본 재현')
    ap.add_argument('mode', choices=['replay','firms-live','asos-sample','messages-sample','sentinel-search'])
    ap.add_argument('--out', type=Path)
    ap.add_argument('--start', default='2026-10-27')
    ap.add_argument('--end', default='2026-10-29', help='KST exclusive upper bound for FIRMS')
    ap.add_argument('--bbox', type=float, nargs=4, default=[127.04,37.46,127.09,37.50], metavar=('W','S','E','N'))
    args = ap.parse_args()
    dest = args.out or ROOT/'runs'/(args.mode+'_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    if dest.exists() and any(dest.iterdir()):
        raise SystemExit('Output directory must be new or empty; previous results are preserved.')
    dest.mkdir(parents=True, exist_ok=True)
    if args.mode == 'replay':
        filter_firms(ROOT/'data/raw', dest, args.start, args.end, args.bbox, True)
        return
    if args.mode == 'firms-live':
        raw = dest/'raw';raw.mkdir()
        logs=[]
        for filename in SOURCES.values():
            logs.append(request('https://firms.modaps.eosdis.nasa.gov/data/active_fire/'+filename, raw/filename))
        write_json(dest/'request_log.json', logs)
        if any(r.get('http')!=200 for r in logs):
            raise SystemExit('Download incomplete; see request_log.json. Do not classify as 0 records.')
        filter_firms(raw, dest, args.start, args.end, args.bbox, False)
        return
    if args.mode in ('asos-sample','messages-sample'):
        env_name = 'KMA_SERVICE_KEY' if args.mode=='asos-sample' else 'SAFETYDATA_SERVICE_KEY'
        key=os.environ.get(env_name)
        if not key:
            raise SystemExit(env_name+' is required. No request was sent. Status: 미수집')
        if args.mode=='asos-sample':
            base='https://apis.data.go.kr/1360000/AsosHourlyInfoService/getWthrDataList'
            params={'serviceKey':key,'dataType':'JSON','pageNo':1,'numOfRows':100,'dataCd':'ASOS','dateCd':'HR','startDt':'20261027','startHh':'00','endDt':'20261028','endHh':'23','stnIds':108}
        else:
            base='https://www.safetydata.go.kr/V2/api/DSSP-IF-00247'
            params={'serviceKey':key,'returnType':'json','pageNo':1,'numOfRows':100,'crtDt':'20261027','rgnNm':'서울특별시 강남구'}
        log=request(base+'?'+urllib.parse.urlencode(params),dest/'response.json')
        log.update(scope='첫 페이지 표본; 전체 페이지·응답코드·종료일 필터 미검증',status='미검증' if log.get('http')==200 else '미수집')
        write_json(dest/'request_log.json',log)
        print('Saved sample and redacted request log. Inspect response code, rows, dates and total count before use.')
        return
    collection='SENTINEL-2'
    west,south,east,north=args.bbox
    poly=f'POLYGON(({west} {south},{east} {south},{east} {north},{west} {north},{west} {south}))'
    expr=f"Collection/Name eq '{collection}' and OData.CSC.Intersects(area=geography'SRID=4326;{poly}') and ContentDate/Start ge 2026-10-25T00:00:00.000Z and ContentDate/Start lt 2026-10-30T00:00:00.000Z"
    url='https://catalogue.dataspace.copernicus.eu/odata/v1/Products?'+urllib.parse.urlencode({'$filter':expr,'$top':100,'$count':'true','$expand':'Attributes','$orderby':'ContentDate/Start asc'})
    log=request(url,dest/'sentinel_catalog.json')
    log.update(status='미검증',scope='카탈로그 검색 표본. value/count/nextLink 검사 후 메타 수집상태 갱신. 원영상 다운로드 없음.')
    write_json(dest/'request_log.json',log)
    print('Catalogue response saved; inspect JSON and pagination. This is not an image download.')

if __name__ == '__main__':
    main()
