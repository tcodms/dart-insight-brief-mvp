# 로그인 · SQLite · PDF 저장 설정

이 문서는 React/FastAPI 서비스용이다. 기존 Agent의 `.env`와 분리해 `.env.service`를 사용한다.

## Google OAuth 설정

1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트를 선택하거나 만든다.
2. Google Auth Platform의 Branding에서 앱 이름·지원 이메일·개발자 연락처를 입력한다.
3. Audience를 설정하고, 외부 앱의 테스트 모드에서는 본인과 팀원의 Google 계정을 테스트 사용자로 등록한다.
4. Clients에서 유형을 **웹 애플리케이션**으로 선택해 OAuth 클라이언트를 만든다.
5. 승인된 리디렉션 URI를 정확히 등록한다: `http://127.0.0.1:5173/api/auth/callback`.
6. `.env.service.example`을 `.env.service`로 복사하고 `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`을 로컬에서 입력한다. 채팅·Git·스크린샷에 노출하지 않는다.
7. 아래 명령으로 별도 세션 서명 키를 생성해 `SERVICE_SESSION_SECRET`에 입력한다. 서버를 재시작한다.

```powershell
uv run python -c "import secrets; print(secrets.token_urlsafe(48))"
```

브라우저 주소도 `http://127.0.0.1:5173`로 통일한다. `localhost`와 혼용하면 OAuth 콜백·쿠키·Origin이 맞지 않을 수 있다. 포트/호스트를 바꾸면 `SERVICE_ORIGIN`과 Google의 리디렉션 URI를 함께 변경한다.

개발 서버는 README처럼 `--no-access-log`로 실행한다. 인증 콜백의 쿼리 문자열이 접근 로그에 기록되지 않게 하기 위한 설정이다. 배포 시에도 프록시의 인증 경로 쿼리 로그를 제외한다.

기본 로그인 범위는 `openid email profile`이다. Drive·문서 접근 권한은 요청하지 않는다. Authlib의 OIDC 흐름으로 state·nonce·서명·클레임 검증을 수행하고 검증된 Google `sub`로 계정을 식별한다. Google 토큰을 DB에 저장하지 않는다.

설정이 없으면 로그인 버튼은 설정 대기 상태를 안내한다. 가짜 로그인이나 개발용 로그인 우회 API는 제공하지 않는다.

참고: [Google 공식 OIDC 설정](https://developers.google.com/identity/openid-connect/openid-connect), [Authlib Starlette 클라이언트](https://docs.authlib.org/en/v1.7.0/oauth2/client/web/starlette.html).

## 데이터 저장

- 기본 위치: `.service-data/service.sqlite3`, `.service-data/files/` (Git 제외).
- 관계 테이블: 사용자, 세션, 문서, 기업 브리프, 개인화 분석, 원문 근거, 실행 작업. 문서 버전 할당용 내부 카운터를 별도로 둔다.
- 브리프·개인화·근거·작업은 스키마만 준비했다. Agent 실행이나 결과 생성 API는 아직 연결하지 않는다.
- CV/JD의 버전은 사용자·문서 종류별 등록 순서다. 기존 문서를 덮어쓰지 않으며 삭제 후에도 번호를 재사용하지 않는다.
- 원본은 UUID 파일명으로 저장한다. 로그인·소유권 확인 후에만 다운로드 가능하다.
- PDF만, 최대 20MB·2,000쪽. 손상·암호화·빈 PDF는 거절한다. 등록은 외부 Agent 전송이나 분석을 실행하지 않는다.
- CV/JD 삭제 시 연결된 개인화 결과를 삭제하고 기업 브리프는 유지한다. 사업보고서 삭제는 연결된 브리프와 개인화 결과도 삭제한다. 화면에서 삭제 영향을 먼저 안내한다.
- 삭제 전 파일을 내부 휴지 경로로 이동하고 DB 트랜잭션 실패 시 복원한다. 완료 후 원본을 지운다. 다음 서버 시작 시 DB에 남아 있는 자료의 휴지 파일은 복원하고, 삭제가 확정된 파일은 정리한다.
- ChromaDB는 아직 도입하지 않았다. 검색 인덱스 도입 시 문서 삭제와 함께 인덱스도 정리하도록 확장한다.

## API

| API | 용도 |
|---|---|
| `GET /api/auth/session` | 로그인 상태, 사용자, CSRF 토큰 |
| `GET /api/auth/login` | Google 로그인 시작 |
| `GET /api/auth/callback` | 인증 코드 검증·세션 발급 |
| `POST /api/auth/logout` | 서버 세션 폐기 |
| `GET /api/documents` | 본인 자료 목록 |
| `POST /api/documents` | `kind=report/cv/jd`, `file` PDF 등록 |
| `GET /api/documents/{id}/file` | 본인 원본 다운로드 |
| `GET /api/documents/{id}/impact` | 삭제 영향 조회 |
| `DELETE /api/documents/{id}` | 문서·연결 결과 삭제 |

변경 요청은 세션 쿠키 외에 `Origin: SERVICE_ORIGIN`, `X-CSRF-Token`이 필요하다. 세션은 HttpOnly/SameSite=Lax 쿠키로 전달하고 DB에는 토큰 해시만 저장한다. 기본 만료는 7일이며 로그아웃 시 즉시 폐기한다.

실제 배포는 HTTPS와 `SERVICE_COOKIE_SECURE=true`가 필요하다. 저장 폴더를 정적 서버로 공개하지 않는다. 현재 구성은 로컬 개발 기준이며 다중 서버용 파일 저장소·운영 백업은 별도 구현 대상이다.

## 검증 범위

`uv run pytest -q`는 임시 DB와 가상 사용자·PDF로 접근 차단, 세션 만료·로그아웃, 등록·재조회, 파일 검증, 삭제 연결을 검사한다. 테스트용 세션은 테스트 코드에서만 직접 만든다. 실제 Google 계정의 로그인 완료 여부는 OAuth 설정 후 브라우저에서 별도로 확인해야 한다.
