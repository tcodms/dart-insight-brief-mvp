"""Find DART filings and return official viewer links; never download report contents."""

import io
import re
import time
import zipfile
from datetime import date, timedelta
from xml.etree import ElementTree

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from backend.app.auth import require_session

router = APIRouter(prefix='/api/dart')
_companies: list[dict] = []
_loaded_at = 0.0
_CORP = re.compile(r'^\d{8}$')
_RECEPT = re.compile(r'^\d{14}$')


async def _request(path: str, key: str, **params):
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
            response = await client.get(f'https://opendart.fss.or.kr/api/{path}', params={'crtfc_key': key, **params})
            response.raise_for_status()
            return response
    except httpx.HTTPError as exc:
        raise HTTPException(502, 'DART에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.') from exc


def _key(request: Request) -> str:
    key = request.app.state.settings.dart_api_key
    if not key:
        raise HTTPException(503, 'DART API 키가 등록되지 않았습니다. .env.service에 DART_API_KEY를 설정해 주세요.')
    return key


@router.get('/companies')
async def companies(request: Request, q: str = Query(min_length=2, max_length=60), _session=Depends(require_session)):
    global _companies, _loaded_at
    key = _key(request)
    term = q.strip().casefold()
    if len(term) < 2:
        raise HTTPException(422, '기업명을 두 글자 이상 입력해 주세요.')
    if not _companies or time.monotonic() - _loaded_at > 24 * 3600:
        response = await _request('corpCode.xml', key)
        try:
            with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                entry = next(name for name in archive.namelist() if name.lower().endswith('.xml'))
                if archive.getinfo(entry).file_size > 20 * 1024 * 1024:
                    raise ValueError('DART company listing is too large')
                root = ElementTree.fromstring(archive.read(entry))
            rows = [{'corpCode': item.findtext('corp_code', '').strip(),
                     'name': item.findtext('corp_name', '').strip(),
                     'stockCode': item.findtext('stock_code', '').strip()}
                    for item in root.findall('list')]
            _companies = [row for row in rows if _CORP.fullmatch(row['corpCode']) and row['name']]
            _loaded_at = time.monotonic()
        except (ValueError, KeyError, StopIteration, zipfile.BadZipFile, ElementTree.ParseError) as exc:
            raise HTTPException(502, 'DART 기업 목록을 읽지 못했습니다. API 키를 확인해 주세요.') from exc
    matches = [row for row in _companies if term in row['name'].casefold()]
    matches.sort(key=lambda row: (row['name'].casefold() != term, not row['stockCode'], len(row['name'])))
    return {'companies': matches[:20]}


@router.get('/reports')
async def reports(request: Request, corp_code: str, _session=Depends(require_session)):
    key = _key(request)
    if not _CORP.fullmatch(corp_code):
        raise HTTPException(422, '기업 고유번호를 확인해 주세요.')
    today = date.today()
    response = await _request('list.json', key, corp_code=corp_code,
                              bgn_de=(today - timedelta(days=5 * 366)).strftime('%Y%m%d'),
                              end_de=today.strftime('%Y%m%d'), last_reprt_at='Y',
                              pblntf_ty='A', pblntf_detail_ty='A001',
                              sort='date', sort_mth='desc', page_count=100)
    try:
        payload = response.json()
    except ValueError as exc:
        raise HTTPException(502, 'DART 응답을 읽지 못했습니다.') from exc
    if payload.get('status') == '013':
        return {'reports': []}
    if payload.get('status') != '000':
        raise HTTPException(502, f"DART 조회 실패: {payload.get('message', '알 수 없는 오류')}")
    rows = payload.get('list', [])
    return {'reports': [{'name': row['report_nm'], 'company': row['corp_name'],
                         'date': row['rcept_dt'], 'corrected': row['report_nm'].startswith('['),
                         'url': f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={row['rcept_no']}"}
                        for row in rows if _RECEPT.fullmatch(str(row.get('rcept_no', '')))
                        and '사업보고서' in row.get('report_nm', '')][:5]}
