# Railway 웹 서비스 배포

React 화면을 빌드하고 FastAPI가 화면과 API를 같은 도메인에서 제공한다.
저장소 루트의 Dockerfile과 railway.toml을 사용한다.

## 서비스와 볼륨

1. Railway에서 GitHub 저장소의 main 브랜치를 서비스에 연결한다.
2. Root Directory는 저장소 루트로 둔다.
3. 기존 Streamlit용 Build Command와 Start Command 재정의가 있다면 비운다.
   Dockerfile의 빌드와 시작 명령을 사용한다.
4. 서비스에 Volume을 추가하고 Mount Path를 /data로 설정한다.
5. Networking에서 공개 도메인을 생성한다.
6. 아래 Variables와 Google 콜백 주소를 설정한 뒤 배포한다.

인스턴스는 하나로 운영한다. 현재 SQLite와 로컬 작업 큐는 단일 프로세스를 사용한다.
Serverless/App Sleeping 기능은 끈다. 진행 중인 분석은 서버 재시작 시 중단된다.
헬스체크 경로는 /api/health이고 서버는 Railway가 전달한 PORT에서 수신한다.

## Variables

| 변수 | 설정값 |
|---|---|
| SERVICE_ORIGIN | https://실제서비스도메인 |
| SERVICE_COOKIE_SECURE | true |
| SERVICE_DATA_DIR | /data |
| SERVICE_SESSION_SECRET | 로컬에서 생성한 고정 난수 문자열 |
| GOOGLE_CLIENT_ID | Google 웹 OAuth 클라이언트 ID |
| GOOGLE_CLIENT_SECRET | Google 웹 OAuth 비밀키 |
| DART_API_KEY | OpenDART 인증키 |

SERVICE_SESSION_SECRET은 아래 명령으로 생성해 Railway Variables에 직접 입력한다.

```powershell
uv run python -c "import secrets; print(secrets.token_urlsafe(48))"
```

분석에 사용할 아래 값도 로컬 .env에서 Railway Variables로 직접 옮긴다.
로컬 .env와 .env.service 파일은 컨테이너에 포함하지 않는다.

```text
UPSTAGE_API_KEY
BUSINESS_STRATEGY_AGENT_ID
BUSINESS_STRATEGY_CONFIG_ID
FINANCE_MANAGEMENT_AGENT_ID
FINANCE_MANAGEMENT_CONFIG_ID
WORKFORCE_ESG_AGENT_ID
WORKFORCE_ESG_CONFIG_ID
COMPANY_BRIEF_AGENT_ID
COMPANY_BRIEF_CONFIG_ID
CANDIDATE_UPSTAGE_API_KEY
CV_AGENT_ID
CV_CONFIG_ID
JD_AGENT_ID
JD_CONFIG_ID
CONTRIBUTION_AGENT_ID
CONTRIBUTION_CONFIG_ID
```

SERVICE_DATA_DIR를 생략하면 RAILWAY_VOLUME_MOUNT_PATH를 사용한다.
실제 볼륨이 연결되어 있어야 /data의 DB와 PDF가 재배포 후에도 보존된다.
새 볼륨은 빈 데이터 저장소다. 로컬 자료는 자동으로 옮겨지지 않는다.
자료 이전이 필요하면 분석을 멈춘 상태에서 DB와 files 전체를 일관되게 백업해 이전한다.

## Google 로그인

Google Cloud Console의 웹 OAuth 클라이언트에 아래 주소를 추가한다.
테스트 모드라면 사용할 Google 계정도 테스트 사용자로 등록한다.

- 승인된 JavaScript 원본은 https://실제서비스도메인
- 승인된 리디렉션 URI는 https://실제서비스도메인/api/auth/callback

SERVICE_ORIGIN에도 같은 도메인을 입력한다. 뒤에 경로나 슬래시를 붙이지 않는다.

## 배포 확인

1. /api/health가 status=ok로 응답하는지 확인한다.
2. /에서 React 로그인 화면을 연다.
3. Google 로그인 후 PDF 등록, 브리프 또는 기여 분석을 확인한다.
4. 재배포 후에도 저장한 자료와 결과가 남아 있는지 확인한다.

Docker가 실행 중인 로컬 환경에서 아래 명령으로 이미지를 빌드할 수 있다.

```powershell
docker build -t dart-insight .
```

로컬 개발은 README의 Vite/FastAPI 두 서버 방식으로 진행한다.
