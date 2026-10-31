import io
import zipfile

from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import create_app
from backend.tests.test_service import sign_in


def test_find_company_and_latest_business_report(tmp_path, monkeypatch):
    xml = b'<result><list><corp_code>00000001</corp_code><corp_name>Test Company</corp_name><stock_code>123456</stock_code></list></result>'
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr('CORPCODE.xml', xml)

    class Response:
        content = buffer.getvalue()
        def json(self):
            return {'status': '000', 'list': [
                {'report_nm': '사업보고서 (2025.12)', 'corp_name': 'Test Company',
                 'rcept_dt': '20260318', 'rcept_no': '20260318000001'},
                {'report_nm': '분기보고서', 'corp_name': 'Test Company',
                 'rcept_dt': '20260518', 'rcept_no': '20260518000001'}]}

    calls = []
    async def fake_request(path, key, **params):
        calls.append((path, params))
        return Response()
    monkeypatch.setattr('backend.app.dart._request', fake_request)
    monkeypatch.setattr('backend.app.dart._companies', [])
    app = create_app(Settings(data_dir=tmp_path, dart_api_key='test-key'), start_jobs=False)
    with TestClient(app) as client:
        assert client.get('/api/dart/companies?q=Test').status_code == 401
        sign_in(app, client)
        assert client.get('/api/dart/companies?q=Test').json()['companies'][0]['corpCode'] == '00000001'
        reports = client.get('/api/dart/reports?corp_code=00000001').json()['reports']
        assert len(reports) == 1
        assert reports[0]['url'] == 'https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260318000001'
        assert calls[1][1]['pblntf_detail_ty'] == 'A001'
        assert calls[1][1]['last_reprt_at'] == 'Y'
